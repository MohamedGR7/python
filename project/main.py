import time
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from .database import Base, engine
from .routers import auth_router, exams_router, questions_router, answers_router, results_router
from .dashboard import router as dashboard_router
from .logger_config import logger


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Online Examination System API",
    description="FastAPI backend for online exams with JWT, RBAC, Redis caching, logging, monitoring, and tests.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.request_count = 0
app.state.total_response_time = 0.0
app.state.error_count = 0
app.state.recent_errors = []
app.state.recent_auth_failures = []
app.state.endpoint_stats = {}


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    app.state.request_count += 1

    endpoint_key = f"{request.method} {request.url.path}"

    if endpoint_key not in app.state.endpoint_stats:
        app.state.endpoint_stats[endpoint_key] = {
            "count": 0,
            "error_count": 0,
            "total_response_time": 0.0,
            "average_response_time": 0.0,
            "last_status_code": None,
            "last_duration": 0.0
        }

    endpoint_data = app.state.endpoint_stats[endpoint_key]
    endpoint_data["count"] += 1

    try:
        response = await call_next(request)

        duration = round(time.time() - start, 4)
        duration_ms = round(duration * 1000, 2)

        response.headers["X-Response-Time-ms"] = str(duration_ms)

        app.state.total_response_time += duration

        endpoint_data["total_response_time"] += duration
        endpoint_data["average_response_time"] = round(
            endpoint_data["total_response_time"] / endpoint_data["count"],
            4
        )
        endpoint_data["last_status_code"] = response.status_code
        endpoint_data["last_duration"] = duration

        if response.status_code >= 400:
            app.state.error_count += 1
            endpoint_data["error_count"] += 1

            error_data = {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration": duration,
                "time": datetime.utcnow().isoformat()
            }

            app.state.recent_errors.append(error_data)
            app.state.recent_errors = app.state.recent_errors[-10:]

        if response.status_code in [401, 403]:
            auth_failure = {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration": duration,
                "time": datetime.utcnow().isoformat()
            }

            app.state.recent_auth_failures.append(auth_failure)
            app.state.recent_auth_failures = app.state.recent_auth_failures[-10:]

        logger.info(
            f"{request.method} {request.url.path} - "
            f"{response.status_code} - {duration}s"
        )

        return response

    except Exception as e:
        duration = round(time.time() - start, 4)

        app.state.error_count += 1
        endpoint_data["error_count"] += 1
        endpoint_data["total_response_time"] += duration
        endpoint_data["average_response_time"] = round(
            endpoint_data["total_response_time"] / endpoint_data["count"],
            4
        )
        endpoint_data["last_status_code"] = 500
        endpoint_data["last_duration"] = duration

        app.state.recent_errors.append({
            "method": request.method,
            "path": request.url.path,
            "error": str(e),
            "duration": duration,
            "time": datetime.utcnow().isoformat()
        })
        app.state.recent_errors = app.state.recent_errors[-10:]

        logger.exception(f"Unhandled error in {request.method} {request.url.path}: {e}")
        raise





@app.get("/")
def home():
    return RedirectResponse(url="/docs")


app.include_router(auth_router.router)
app.include_router(exams_router.router)
app.include_router(questions_router.router)
app.include_router(answers_router.router)
app.include_router(results_router.router)
app.include_router(dashboard_router)