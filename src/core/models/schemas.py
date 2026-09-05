from pydantic import BaseModel, Field
from typing import Literal

class EmailMetadata(BaseModel):
    category:Literal[
        "invoice",
        "technical_support",
        "sales",
        "complaint",
        "refund",
        "order_tracking",
        "account",
        "inquiry",
        "spam",
        "other"
    ] = Field(description="Phân loại category dựa vào email")
    sentiment:Literal[
        "positive",
        "neutral",
        "negative"
    ] = Field(description="Thái độ thể hiện qua email")
    urgency:Literal[
         "low",
        "medium",
        "high"
    ] = Field(description="Mức độ khẩn cấp của email")
    confidence_score:float = Field(ge=0.0, le=1.0, description="Mức độ tự tin của ai")
