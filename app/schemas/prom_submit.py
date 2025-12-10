from pydantic import BaseModel
from typing import List

class PromAnswer(BaseModel):
    id: str | int
    value: int

class PromSubmitIn(BaseModel):
    answers: List[PromAnswer]
