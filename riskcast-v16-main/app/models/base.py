from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        str_strip_whitespace = True
        populate_by_name = True
        extra = "forbid"


class TimeStampedSchema(BaseSchema):
    updatedAt: Optional[datetime] = None




