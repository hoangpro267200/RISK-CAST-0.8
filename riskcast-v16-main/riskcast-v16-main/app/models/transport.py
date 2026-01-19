from datetime import datetime
from typing import List, Optional
from pydantic import Field
from .base import BaseSchema


class RouteLeg(BaseSchema):
    legNumber: int = Field(default=1, ge=1)
    fromPort: str = Field(default="N/A")
    toPort: str = Field(default="N/A")
    mode: str = Field(default="Unknown")
    eta: Optional[datetime] = None
    status: str = Field(default="Pending")


class Transport(BaseSchema):
    mode: str = Field(default="Unknown")
    incoterm: str = Field(default="N/A")
    origin: str = Field(default="N/A")
    destination: str = Field(default="N/A")
    eta: Optional[datetime] = None
    legs: List[RouteLeg] = Field(default_factory=list)




