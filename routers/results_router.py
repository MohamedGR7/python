
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Result, Exam, User
from ..schemas import ResultOut, ResultCreate
from ..deps import get_current_user, require_admin
from ..logger_config import logger

router = APIRouter(prefix="/results", tags=["Results"])

@router.post("/", response_model=ResultOut, status_code=201)
def create_result(
    result_data: ResultCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    student = db.query(User).filter(User.id == result_data.student_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if student.role != "student":
        raise HTTPException(status_code=400, detail="User is not a student")

    exam = db.query(Exam).filter(Exam.id == result_data.exam_id).first()

    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    if result_data.total_questions <= 0:
        raise HTTPException(
            status_code=400,
            detail="Total questions must be greater than zero"
        )

    if result_data.score < 0:
        raise HTTPException(
            status_code=400,
            detail="Score cannot be negative"
        )

    if result_data.score > result_data.total_questions:
        raise HTTPException(
            status_code=400,
            detail="Score cannot be greater than total questions"
        )

    percentage = (result_data.score / result_data.total_questions) * 100

    existing_result = db.query(Result).filter(
        Result.student_id == result_data.student_id,
        Result.exam_id == result_data.exam_id
    ).first()

    if existing_result:
        existing_result.score = result_data.score
        existing_result.total_questions = result_data.total_questions
        existing_result.percentage = percentage

        db.commit()
        db.refresh(existing_result)

        logger.info(
            f"Admin {admin.username} updated result for student "
            f"{result_data.student_id} exam {result_data.exam_id}"
        )

        return existing_result

    new_result = Result(
        student_id=result_data.student_id,
        exam_id=result_data.exam_id,
        score=result_data.score,
        total_questions=result_data.total_questions,
        percentage=percentage
    )

    db.add(new_result)
    db.commit()
    db.refresh(new_result)

    logger.info(
        f"Admin {admin.username} posted result for student "
        f"{result_data.student_id} exam {result_data.exam_id}"
    )

    return new_result
@router.get("/my", response_model=list[ResultOut])
def my_results(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    results = db.query(Result).filter(Result.student_id == user.id).all()
    logger.info(f"User {user.username} viewed own results")
    return results


@router.get("/all", response_model=list[ResultOut])
def all_results(
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    logger.info(f"Admin {admin.username} viewed all results")
    return db.query(Result).all()


@router.get("/analytics")
def analytics(
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    results = db.query(Result).all()

    if not results:
        return {
            "average_score": 0,
            "average_percentage": 0,
            "total_results": 0,
            "per_exam": []
        }

    avg_score = sum(r.score for r in results) / len(results)
    avg_percentage = sum(r.percentage for r in results) / len(results)

    exams = db.query(Exam).all()
    per_exam = []

    for exam in exams:
        exam_results = [r for r in results if r.exam_id == exam.id]

        if exam_results:
            per_exam.append({
                "exam_id": exam.id,
                "exam_title": exam.title,
                "attempts": len(exam_results),
                "average_score": round(
                    sum(r.score for r in exam_results) / len(exam_results),
                    2
                ),
                "average_percentage": round(
                    sum(r.percentage for r in exam_results) / len(exam_results),
                    2
                )
            })

    logger.info(f"Admin {admin.username} viewed analytics")

    return {
        "average_score": round(avg_score, 2),
        "average_percentage": round(avg_percentage, 2),
        "total_results": len(results),
        "per_exam": per_exam
    }


@router.get("/{result_id}", response_model=ResultOut)
def get_result_by_id(
    result_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    result = db.query(Result).filter(Result.id == result_id).first()

    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    if user.role != "admin" and result.student_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own result"
        )

    logger.info(f"User {user.username} viewed result {result_id}")
    return result


@router.delete("/{result_id}")
def delete_result(
    result_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    result = db.query(Result).filter(Result.id == result_id).first()

    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    db.delete(result)
    db.commit()

    logger.info(f"Admin {admin.username} deleted result {result_id}")

    return {"message": "Result deleted successfully"}