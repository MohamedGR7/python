from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text

from .database import get_db
from .models import User, Exam, Result
from .deps import require_admin
from .cache import r


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def check_redis_health():
    if r is None:
        return {
            "status": "DOWN",
            "message": "Redis client is not available"
        }

    try:
        r.ping()
        return {
            "status": "OK",
            "message": "Redis is connected"
        }
    except Exception as e:
        return {
            "status": "DOWN",
            "message": str(e)
        }


def check_db_health(db: Session):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "OK",
            "message": "Database is connected"
        }
    except Exception as e:
        return {
            "status": "DOWN",
            "message": str(e)
        }


@router.get("/stats")
def get_stats(
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    users = db.query(User).count()
    exams = db.query(Exam).count()
    results = db.query(Result).all()

    avg_percentage = 0
    if results:
        avg_percentage = sum(r.percentage for r in results) / len(results)

    request_count = request.app.state.request_count
    total_response_time = request.app.state.total_response_time

    avg_response_time = 0
    if request_count > 0:
        avg_response_time = total_response_time / request_count

    redis_health = check_redis_health()
    db_health = check_db_health(db)

    endpoint_stats = []

    for endpoint, stats in request.app.state.endpoint_stats.items():
        endpoint_stats.append({
            "endpoint": endpoint,
            "request_count": stats["count"],
            "error_count": stats["error_count"],
            "average_response_time": stats["average_response_time"],
            "last_status_code": stats["last_status_code"],
            "last_duration": stats["last_duration"]
        })

    endpoint_stats = sorted(
        endpoint_stats,
        key=lambda item: item["request_count"],
        reverse=True
    )

    health = "OK"

    if redis_health["status"] != "OK" or db_health["status"] != "OK":
        health = "DEGRADED"

    return {
        "health": health,
        "database_health": db_health,
        "redis_health": redis_health,

        "total_users": users,
        "total_exams": exams,
        "total_results": len(results),
        "average_percentage": round(avg_percentage, 2),

        "api_request_count": request_count,
        "average_response_time": round(avg_response_time, 4),
        "error_count": request.app.state.error_count,

        "endpoint_stats": endpoint_stats,
        "recent_errors": request.app.state.recent_errors,
        "recent_auth_failures": request.app.state.recent_auth_failures
    }