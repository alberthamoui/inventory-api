from pydantic import BaseModel, Field

class ProductCreate(BaseModel): # json schema for products
    name: str
    ean13: str = Field(min_length=13, max_length=13)
    quantity: int = 0
    alert_threshold: int = 0
