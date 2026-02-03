from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-= PRODUCTS =-=-=-=-=-=-=-=-=-=-=-=-=-=-=
class ProductCreate(BaseModel): # json schema for products
    name: str
    ean13: str = Field(min_length=13, max_length=13, pattern="^[0-9]{13}$")
    quantity: int = 0
    alert_threshold: int = 0

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-= MOVEMENTS =-=-=-=-=-=-=-=-=-=-=-=-=-=-=
class MovementCreate(BaseModel):
    type: Literal["in", "out"]
    quantity: int = Field(ge=0)
    date: Optional[datetime] = None
    reason: Optional[str] = None
