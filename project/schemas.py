
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, PositiveInt, ConfigDict


class MessageOut(BaseModel):
    message: str


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class AdminCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    admin_secret: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class ExamCreate(BaseModel):
    title: str
    duration_minutes: PositiveInt


class ExamOut(BaseModel):
    id: int
    title: str
    duration_minutes: int

    model_config = ConfigDict(from_attributes=True)

class QuestionCreate(BaseModel):
    exam_id: int
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: Literal["a", "b", "c", "d"]


class QuestionUpdate(BaseModel):
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: Literal["a", "b", "c", "d"]


class QuestionOut(BaseModel):
    id: int
    exam_id: int
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str

    model_config = ConfigDict(from_attributes=True)


class QuestionAdminOut(QuestionOut):
    correct_option: str


class AnswerCreate(BaseModel):
    exam_id: int
    question_id: int
    selected_option: Literal["a", "b", "c", "d"]


class AnswerSubmitOut(BaseModel):
    message: str


class AttemptOut(BaseModel):
    exam_id: int
    start_time: datetime
    end_time: datetime
    is_submitted: bool

    model_config = ConfigDict(from_attributes=True)


class ResultOut(BaseModel):
    id: int
    student_id: int
    exam_id: int
    score: float
    total_questions: int
    percentage: float

    model_config = ConfigDict(from_attributes=True)

class ResultCreate(BaseModel):
    student_id: int
    exam_id: int
    score: float
    total_questions: int



class StudentAnswerOut(BaseModel):
    id: int
    student_id: int
    exam_id: int
    question_id: int
    selected_option: str
    is_correct: bool

    model_config = ConfigDict(from_attributes=True)


class FinishExamOut(BaseModel):
    message: str