from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class BaseSchema(BaseModel):
    class Config:
        orm_mode = True
        anystr_strip_whitespace = True
        allow_population_by_field_name = True
        extra = "forbid"


class TimeStampedSchema(BaseSchema):
    updatedAt: Optional[datetime] = None




