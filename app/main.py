from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.routers import webhook
from app.database import engine, Base, get_db_context
from app.models.load import Load, CallLog
from sqlalchemy import func, case
from datetime import datetime, timedelta
import os

app = FastAPI(title="HappyRobot Inbound Carrier Sales API", version="1.0.0")

# Create tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(webhook.router)

@app.get("/", response_class=HTMLResponse)
def read_root():
    """Serve the dashboard HTML template"""
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "dashboard.html")
    with open(template_path, "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/dashboard-metrics")
def get_dashboard_metrics():
    """Get key metrics for the dashboard"""
    try:
        with get_db_context() as db:
            # Get total loads
            total_loads = db.query(Load).count()
            available_loads = db.query(Load).filter(Load.status == "available").count()
            
            # Get call log metrics
            total_calls = db.query(CallLog).count()
            unique_carriers = db.query(CallLog.mc_number).distinct().count()
            
            # Get call outcomes
            booked_calls = db.query(CallLog).filter(CallLog.call_outcome == "booked").count()
            declined_calls = db.query(CallLog).filter(CallLog.call_outcome == "declined").count()
            no_match_calls = db.query(CallLog).filter(CallLog.call_outcome == "no_match").count()
            callback_needed = db.query(CallLog).filter(CallLog.call_outcome == "callback-needed").count()
            
            # Calculate success rate
            success_rate = 0
            if total_calls > 0:
                success_rate = round((booked_calls / total_calls) * 100, 1)
            
            # Get sentiment breakdown
            positive_sentiment = db.query(CallLog).filter(CallLog.sentiment == "positive").count()
            negative_sentiment = db.query(CallLog).filter(CallLog.sentiment == "negative").count()
            neutral_sentiment = db.query(CallLog).filter(CallLog.sentiment == "neutral").count()
            
            # Get today's metrics
            today = datetime.now().date()
            today_calls = db.query(CallLog).filter(func.date(CallLog.created_at) == today).count()
            today_booked = db.query(CallLog).filter(
                func.date(CallLog.created_at) == today,
                CallLog.call_outcome == "booked"
            ).count()
            
            # Get this week's metrics
            week_ago = datetime.now() - timedelta(days=7)
            week_calls = db.query(CallLog).filter(CallLog.created_at >= week_ago).count()
            week_booked = db.query(CallLog).filter(
                CallLog.created_at >= week_ago,
                CallLog.call_outcome == "booked"
            ).count()
            
            # Get recent call activity (last 7 days)
            recent_activity = []
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).date()
                day_calls = db.query(CallLog).filter(func.date(CallLog.created_at) == date).count()
                day_booked = db.query(CallLog).filter(
                    func.date(CallLog.created_at) == date,
                    CallLog.call_outcome == "booked"
                ).count()
                recent_activity.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "calls": day_calls,
                    "booked": day_booked
                })
            
            # Get top carriers by call volume
            top_carriers = db.query(
                CallLog.mc_number,
                func.count(CallLog.id).label('call_count'),
                func.sum(case((CallLog.call_outcome == "booked", 1), else_=0)).label('booked_count')
            ).group_by(CallLog.mc_number).order_by(func.count(CallLog.id).desc()).limit(5).all()
            
            # Get duration analytics
            avg_duration = db.query(func.avg(CallLog.duration)).scalar() or 0
            max_duration = db.query(func.max(CallLog.duration)).scalar() or 0
            min_duration = db.query(func.min(CallLog.duration)).scalar() or 0
            
            # Get duration by outcome
            duration_by_outcome = db.query(
                CallLog.call_outcome,
                func.avg(CallLog.duration).label('avg_duration'),
                func.count(CallLog.id).label('call_count')
            ).group_by(CallLog.call_outcome).all()
            
            # Get hourly call distribution (if we have enough data)
            hourly_calls = []
            for hour in range(24):
                hour_calls = db.query(CallLog).filter(
                    func.extract('hour', CallLog.created_at) == hour
                ).count()
                hourly_calls.append({"hour": hour, "calls": hour_calls})
            
            return {
                "total_loads": total_loads,
                "available_loads": available_loads,
                "total_calls": total_calls,
                "unique_carriers": unique_carriers,
                "booked_calls": booked_calls,
                "declined_calls": declined_calls,
                "no_match_calls": no_match_calls,
                "callback_needed": callback_needed,
                "success_rate": success_rate,
                "positive_sentiment": positive_sentiment,
                "negative_sentiment": negative_sentiment,
                "neutral_sentiment": neutral_sentiment,
                "today_calls": today_calls,
                "today_booked": today_booked,
                "week_calls": week_calls,
                "week_booked": week_booked,
                "recent_activity": recent_activity,
                "top_carriers": [{"mc_number": c.mc_number, "call_count": c.call_count, "booked_count": c.booked_count} for c in top_carriers],
                "avg_duration": round(avg_duration, 1),
                "max_duration": max_duration,
                "min_duration": min_duration,
                "duration_by_outcome": [{"outcome": d.call_outcome, "avg_duration": round(d.avg_duration or 0, 1), "call_count": d.call_count} for d in duration_by_outcome],
                "hourly_calls": hourly_calls
            }
    except Exception as e:
        print(f"Error in dashboard metrics: {e}")
        return {"error": str(e)}

@app.get("/loads")
def get_loads():
    """Get all available loads"""
    with get_db_context() as db:
        loads = db.query(Load).filter(Load.status == "available").all()
        return loads

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "HappyRobot Inbound API"}