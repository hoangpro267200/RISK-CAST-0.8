from pydantic import Field
from .base import BaseSchema


class Cargo(BaseSchema):
    type: str = Field(default="Unknown")
    hsCode: str = Field(default="N/A")
    weight: float = Field(default=0)
    volume: float = Field(default=0)
    value: float = Field(default=0)
    insurance: str = Field(default="N/A")




