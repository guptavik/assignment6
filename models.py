from pydantic import BaseModel
from typing import List

class AddInput(BaseModel):
    a: int
    b: int

class AddOutput(BaseModel):
    result: int

class SqrtInput(BaseModel):
    a: float

class SqrtOutput(BaseModel):
    result: float

class StringsToIntsInput(BaseModel):
    string: str

class StringsToIntsOutput(BaseModel):
    ints: List[int]

class ExpSumInput(BaseModel):
    int_list: List[int]

class ExpSumOutput(BaseModel):
    result: float 