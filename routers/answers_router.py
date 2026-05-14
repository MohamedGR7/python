
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Question, StudentAnswer, Result, Exam, ExamAttempt
from ..schemas import AnswerCreate, AttemptOut, AnswerSubmitOut , StudentAnswerOut, FinishExamOut
from ..deps import get_current_user
from ..logger_config import logger

router = APIRouter(prefix="/answers", tags=["Answers"])


def update_result(db: Session, student_id: int, exam_id: int):
    total_questions = db.query(Question).filter(
        Question.exam_id == exam_id
    ).count()

    answers = db.query(StudentAnswer).filter(
        StudentAnswer.student_id == student_id,
        StudentAnswer.exam_id == exam_id
    ).all()

    correct = sum(1 for answer in answers if answer.is_correct)

    percentage = 0
    if total_questions > 0:
        percentage = (correct / total_questions) * 100

    result = db.query(Result).filter(
        Result.student_id == student_id,
        Result.exam_id == exam_id
    ).first()

    if not result:
        result = Result(
            student_id=student_id,
            exam_id=exam_id,
            score=correct,
            total_questions=total_questions,
            percentage=percentage
        )
        db.add(result)
    else:
        result.score = correct
        result.total_questions = total_questions
        result.percentage = percentage

    db.commit()


@router.post("/start", response_model=AttemptOut)
def start_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Students only")

    exam = db.query(Exam).filter(Exam.id == exam_id).first()

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    old_attempt = db.query(ExamAttempt).filter(
        ExamAttempt.student_id == user.id,
        ExamAttempt.exam_id == exam_id
    ).first()

    if old_attempt and old_attempt.is_submitted:
        raise HTTPException(
            status_code=400,
            detail="You already submitted this exam"
        )

    if old_attempt and not old_attempt.is_submitted:
        if datetime.utcnow() > old_attempt.end_time:
            old_attempt.is_submitted = True
            db.commit()
            raise HTTPException(status_code=403, detail="Previous exam attempt time is over")

        raise HTTPException(
            status_code=400,
            detail="You already have an active attempt for this exam"
        )

    now = datetime.utcnow()

    attempt = ExamAttempt(
        student_id=user.id,
        exam_id=exam_id,
        start_time=now,
        end_time=now + timedelta(minutes=exam.duration_minutes),
        is_submitted=False
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    logger.info(f"Student {user.username} started exam {exam_id}")
    return attempt


@router.post("/", response_model=AnswerSubmitOut)
def submit_answer(
    answer: AnswerCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Students only")

    attempt = db.query(ExamAttempt).filter(
        ExamAttempt.student_id == user.id,
        ExamAttempt.exam_id == answer.exam_id,
        ExamAttempt.is_submitted == False
    ).first()

    if not attempt:
        raise HTTPException(status_code=400, detail="Start the exam first")

    if datetime.utcnow() > attempt.end_time:
        attempt.is_submitted = True
        db.commit()
        logger.warning(f"Student {user.username} tried to submit after time ended")
        raise HTTPException(status_code=403, detail="Exam time is over")

    question = db.query(Question).filter(
        Question.id == answer.question_id
    ).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    if question.exam_id != answer.exam_id:
        raise HTTPException(
            status_code=400,
            detail="Question does not belong to this exam"
        )

    is_correct = question.correct_option.lower() == answer.selected_option.lower()

    existing_answer = db.query(StudentAnswer).filter(
        StudentAnswer.student_id == user.id,
        StudentAnswer.exam_id == answer.exam_id,
        StudentAnswer.question_id == answer.question_id
    ).first()

    if existing_answer:
        existing_answer.selected_option = answer.selected_option
        existing_answer.is_correct = is_correct
        logger.info(
            f"Student {user.username} updated answer for question {answer.question_id}"
        )
    else:
        student_answer = StudentAnswer(
            student_id=user.id,
            exam_id=answer.exam_id,
            question_id=answer.question_id,
            selected_option=answer.selected_option,
            is_correct=is_correct
        )
        db.add(student_answer)
        logger.info(
            f"Student {user.username} submitted answer for question {answer.question_id}"
        )

    db.commit()
    update_result(db, user.id, answer.exam_id)

    return {
        "message": "Answer submitted"
    }


@router.post("/finish/{exam_id}", response_model=FinishExamOut)
def finish_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Students only")

    attempt = db.query(ExamAttempt).filter(
        ExamAttempt.student_id == user.id,
        ExamAttempt.exam_id == exam_id,
        ExamAttempt.is_submitted == False
    ).first()

    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    attempt.is_submitted = True
    db.commit()

    update_result(db, user.id, exam_id)

    logger.info(f"Student {user.username} finished exam {exam_id}")

    return {"message": "Exam finished"}


@router.get("/my", response_model=list[StudentAnswerOut])
def my_answers(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Students only")

    answers = db.query(StudentAnswer).filter(
        StudentAnswer.student_id == user.id
    ).all()

    return answers