# routers/feedback.py
from fastapi import APIRouter
from models.schemas import FeedbackData
from database.supabase_client import get_supabase

router = APIRouter()
db = get_supabase()

@router.post("/feedback")
async def submit_feedback(data: FeedbackData):
    """
    User tells us: "Bus actually came in X minutes"
    We use this to retrain the Greykite ML model.
    """
    # Update the ETA log with actual time
    db.table("eta_logs").update({
        "actual_eta": data.actual_eta,
        "accuracy_pct": None  # Will be calculated in background
    }).eq("id", data.log_id).execute()
    
    # Trigger model retraining if enough new data
    from services.ml_model import maybe_retrain
    await maybe_retrain(route_id=None)  # Retrain all routes
    
    return {"message": "Feedback received. Model will retrain. Thank you!"}

