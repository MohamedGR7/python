
import json
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Exam
from ..schemas import ExamCreate, ExamOut
from ..deps import get_current_user, require_admin
from ..cache import get_cache, set_cache, delete_cache
from ..logger_config import logger

router = APIRouter(prefix="/exams", tags=["Exams"])


def exam_to_dict(exam: Exam):
    return {
        "id": exam.id,
        "title": exam.title,
        "duration_minutes": exam.duration_minutes
    }


@router.post("/", response_model=ExamOut, status_code=201)
def create_exam(
    exam: ExamCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    new_exam = Exam(
        title=exam.title,
        duration_minutes=exam.duration_minutes,
        created_by=admin.id
    )

    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)

    delete_cache("all_exams")

    logger.info(f"Exam created by admin {admin.username}: {new_exam.title}")
    return new_exam


@router.get("/", response_model=list[ExamOut])
@router.get("/", response_model=list[ExamOut])
def get_all_exams(
    response: Response,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    cached = get_cache("all_exams")

    if cached:
        response.headers["X-Cache"] = "HIT"
        logger.info("Cache hit: all_exams")
        return json.loads(cached)

    exams = db.query(Exam).all()
    data = [exam_to_dict(e) for e in exams]

    set_cache("all_exams", data)

    response.headers["X-Cache"] = "MISS"
    logger.info("Cache set: all_exams")
    return data


@router.get("/{exam_id}", response_model=ExamOut)
@router.get("/{exam_id}", response_model=ExamOut)
def get_exam(
    exam_id: int,
    response: Response,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    cache_key = f"exam:{exam_id}"
    cached = get_cache(cache_key)

    if cached:
        response.headers["X-Cache"] = "HIT"
        logger.info(f"Cache hit: {cache_key}")
        return json.loads(cached)

    exam = db.query(Exam).filter(Exam.id == exam_id).first()

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    data = exam_to_dict(exam)
    set_cache(cache_key, data)

    response.headers["X-Cache"] = "MISS"
    logger.info(f"Cache set: {cache_key}")
    return data


@router.put("/{exam_id}", response_model=ExamOut)
def update_exam(
    exam_id: int,
    exam_data: ExamCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    exam.title = exam_data.title
    exam.duration_minutes = exam_data.duration_minutes

    db.commit()
    db.refresh(exam)

    delete_cache("all_exams")
    delete_cache(f"exam:{exam_id}")

    logger.info(f"Exam updated by admin {admin.username}: {exam.id}")
    return exam


@router.delete("/{exam_id}")
def delete_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    db.delete(exam)
    db.commit()

    delete_cache("all_exams")
    delete_cache(f"exam:{exam_id}")

    logger.info(f"Exam deleted by admin {admin.username}: {exam_id}")

    return {"message": "Exam deleted successfully"}