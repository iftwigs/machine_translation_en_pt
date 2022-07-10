from pydantic import BaseModel
from typing import Dict


class ResponseModel(BaseModel):
    task_id: str
    task_status: str
    bundle: Dict
    error: Dict


class ResponseModelPlain(BaseModel):
    text: str
    translation: str


class RequestModel(BaseModel):
    document_id: str
    source_locale: str
    target_locale: str


class RequestModelPlain(BaseModel):
    text: str
    source_locale: str
    target_locale: str


class Results(BaseModel):
    document_id: str
    content: str
