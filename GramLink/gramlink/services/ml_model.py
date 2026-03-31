# services/ml_model.py
# Bus delay prediction using LinkedIn's Greykite library

import os
import pandas as pd
import numpy as np
from typing import List, Dict
from database.queries import get_historical_delays

# We'll store trained models in memory (one per route)
_trained_models = {}


def prepare_training_data(delays: List[Dict]) -> pd.DataFrame:
    """
    Convert raw delay logs from Supabase into format Greykite needs.
    
    Greykite needs columns: 'ts' (timestamp) and 'y' (value to predict)
    """
    if not delays:
        return pd.DataFrame()
    
    df = pd.DataFrame(delays)
    
    # Only use rows where we have both predicted and actual
    df = df.dropna(subset=["actual_eta", "predicted_eta"])
    
    # Calculate delay (positive = late, negative = early)
    df["y"] = df["actual_eta"] - df["predicted_eta"]
    df["ts"] = pd.to_datetime(df["timestamp"])
    
    # Sort by time
    df = df.sort_values("ts").reset_index(drop=True)
    
    return df[["ts", "y"]]


def train_delay_model(route_id: str):
    """
    Train Greykite model for a specific route.
    
    This predicts: "How many extra minutes will this bus be delayed?"
    """
    try:
        from greykite.framework.templates.autogen.forecast_config import ForecastConfig
        from greykite.framework.templates.model_templates import ModelTemplateEnum
        from greykite.framework.forecaster import Forecaster
        
        # Get historical data
        delays = get_historical_delays(route_id)
        df = prepare_training_data(delays)
        
        if len(df) < 20:
            print(f"⚠️ Not enough data for route {route_id} (need 20+, have {len(df)})")
            return None
        
        # Create Greykite forecaster
        forecaster = Forecaster()
        
        # Run forecast with SILVERKITE model
        result = forecaster.run_forecast_config(
            df=df,
            config=ForecastConfig(
                model_template=ModelTemplateEnum.SILVERKITE.name,
                forecast_horizon=12,  # Predict next 12 × 30min slots
                metadata_param=dict(
                    time_col="ts",
                    value_col="y",
                    freq="30min"
                )
            )
        )
        
        # Save the trained model
        model = result.model[-1]
        _trained_models[route_id] = model
        print(f"✅ Model trained for route {route_id}")
        return model
        
    except ImportError:
        print("⚠️ Greykite not installed. Using fallback delay prediction.")
        return None
    except Exception as e:
        print(f"❌ Model training error: {e}")
        return None


def predict_delay(route_id: str, current_hour: int = None) -> float:
    """
    Predict how many extra minutes a bus will be delayed.
    
    Returns: delay in minutes (0 if no model available)
    """
    import datetime
    
    if current_hour is None:
        current_hour = datetime.datetime.now().hour
    
    model = _trained_models.get(route_id)
    
    if model is None:
        # Try to train model
        model = train_delay_model(route_id)
    
    if model is None:
        # Fallback: rule-based prediction
        return _rule_based_delay(current_hour)
    
    try:
        # Create future dataframe for prediction
        future_df = pd.DataFrame({
            "ts": [pd.Timestamp.now() + pd.Timedelta(minutes=30 * i) 
                   for i in range(1, 3)]
        })
        
        prediction = model.predict(future_df)
        delay = float(prediction["forecast"].iloc[0])
        
        # Clamp to reasonable range (-10 to +30 minutes)
        return max(-10, min(30, delay))
        
    except Exception as e:
        print(f"Prediction error: {e}")
        return _rule_based_delay(current_hour)


def _rule_based_delay(hour: int) -> float:
    """
    Simple rule-based delay prediction when ML model unavailable.
    Based on typical traffic patterns.
    """
    # Peak hours have more delay
    if 8 <= hour <= 10:     # Morning rush
        return 8.0
    elif 17 <= hour <= 19:  # Evening rush
        return 10.0
    elif 12 <= hour <= 14:  # Afternoon
        return 3.0
    else:                   # Off-peak
        return 2.0


async def maybe_retrain(route_id: str = None):
    """Retrain model if enough new feedback data available"""
    from database.queries import get_historical_delays
    
    routes_to_train = [route_id] if route_id else ["47C"]  # Add all routes
    
    for route in routes_to_train:
        delays = get_historical_delays(route)
        if len(delays) >= 20:
            train_delay_model(route)