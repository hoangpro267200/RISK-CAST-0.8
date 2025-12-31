from pydantic import Field
from .base import BaseSchema


class RiskModule(BaseSchema):
    title: str = Field(default="")
    score: int = Field(default=0, ge=0, le=100)
    level: str = Field(default="LOW")
    message: str = Field(default="No data")




