import json
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Question, Exam
from ..schemas import QuestionCreate, QuestionUpdate, QuestionOut, QuestionAdminOut
from ..deps import get_current_user, require_admin
from ..cache import get_cache, set_cache, delete_cache
from ..logger_config import logger


router = APIRouter(prefix="/questions", tags=["Questions"])


def question_to_student_dict(q: Question):
    return {
        "id": q.id,
        "exam_id": q.exam_id,
        "text": q.text,
        "option_a": q.option_a,
        "option_b": q.option_b,
        "option_c": q.option_c,
        "option_d": q.option_d
    }


def question_to_admin_dict(q: Question):
    data = question_to_student_dict(q)
    data["correct_option"] = q.correct_option
    return data


@router.post("/", response_model=QuestionAdminOut, status_code=201)
def create_question(
    question: QuestionCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    exam = db.query(Exam).filter(Exam.id == question.exam_id).first()

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    q = Question(**question.model_dump())

    db.add(q)
    db.commit()
    db.refresh(q)

    delete_cache("all_questions")
    delete_cache(f"questions:exam:{question.exam_id}")

    logger.info(f"Question created by admin {admin.username} for exam {question.exam_id}")
    return q


@router.get("/", response_model=list[QuestionAdminOut])
def get_all_questions(
    response: Response,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    cache_key = "all_questions"
    cached = get_cache(cache_key)

    if cached:
        response.headers["X-Cache"] = "HIT"
        logger.info(f"Cache hit: {cache_key}")
        return json.loads(cached)

    questions = db.query(Question).all()
    data = [question_to_admin_dict(q) for q in questions]

    set_cache(cache_key, data)

    response.headers["X-Cache"] = "MISS"
    logger.info(f"Cache set: {cache_key}")

    return data


@router.get("/exam/{exam_id}", response_model=list[QuestionOut])
def get_exam_questions(
    exam_id: int,
    response: Response,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    cache_key = f"questions:exam:{exam_id}"
    cached = get_cache(cache_key)

    if cached:
        response.headers["X-Cache"] = "HIT"
        logger.info(f"Cache hit: {cache_key}")
        return json.loads(cached)

    exam = db.query(Exam).filter(Exam.id == exam_id).first()

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    questions = db.query(Question).filter(Question.exam_id == exam_id).all()
    data = [question_to_student_dict(q) for q in questions]

    set_cache(cache_key, data)

    response.headers["X-Cache"] = "MISS"
    logger.info(f"Cache set: {cache_key}")

    return data


@router.get("/{question_id}", response_model=QuestionOut)
def get_question_by_id(
    question_id: int,
    response: Response,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    cache_key = f"question:{question_id}"
    cached = get_cache(cache_key)

    if cached:
        response.headers["X-Cache"] = "HIT"
        logger.info(f"Cache hit: {cache_key}")
        return json.loads(cached)

    question = db.query(Question).filter(Question.id == question_id).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    data = question_to_student_dict(question)

    set_cache(cache_key, data)

    response.headers["X-Cache"] = "MISS"
    logger.info(f"Cache set: {cache_key}")

    return data


@router.put("/{question_id}", response_model=QuestionAdminOut)
def update_question(
    question_id: int,
    question_data: QuestionUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    question = db.query(Question).filter(Question.id == question_id).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    old_exam_id = question.exam_id

    question.text = question_data.text
    question.option_a = question_data.option_a
    question.option_b = question_data.option_b
    question.option_c = question_data.option_c
    question.option_d = question_data.option_d
    question.correct_option = question_data.correct_option

    db.commit()
    db.refresh(question)

    delete_cache("all_questions")
    delete_cache(f"questions:exam:{old_exam_id}")
    delete_cache(f"question:{question_id}")

    logger.info(f"Question updated by admin {admin.username}: {question_id}")
    return question


@router.delete("/{question_id}")
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    question = db.query(Question).filter(Question.id == question_id).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    exam_id = question.exam_id

    db.delete(question)
    db.commit()

    delete_cache("all_questions")
    delete_cache(f"questions:exam:{exam_id}")
    delete_cache(f"question:{question_id}")

    logger.info(f"Question deleted by admin {admin.username}: {question_id}")

    return {"message": "Question deleted successfully"}