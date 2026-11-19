import json
from datetime import datetime
from typing import List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator


class CropBase(BaseModel):
    name_en: str = Field(..., description="English name e.g., Maize")
    name_rw: str = Field(..., description="Kinyarwanda name e.g., Ibigori")
    scientific_name: Optional[str] = Field(None, description="Botanical/scientific name")
    category: Optional[str] = Field("CEREAL", description="CEREAL, TUBER, LEGUME, FRUIT, VEGETABLE, CASH_CROP")
    description: Optional[str] = None
    common_pests: Optional[Union[List[str], str]] = None
    is_active: bool = True

    @field_validator("common_pests", mode="before")
    def parse_common_pests(cls, val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return [val]
        return val


class CropCreate(CropBase):
    pass


class CropResponse(CropBase):
    id: int
    created_at: datetime
    common_pests: Optional[List[str]] = []

    model_config = ConfigDict(from_attributes=True)
