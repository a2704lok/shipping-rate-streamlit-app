from pydantic import BaseModel, Field, condecimal
from typing import List, Optional


# Target schema fields for RFP column normalization
TARGET_SCHEMA_FIELDS = [
    "origin_port",
    "destination_port",
    "container_type_20gp_rate",
    "container_type_40hq_rate",
    "estimated_time_of_departure",
    "transit_time_days",
    "currency",
]


# --- Column Mapping Models ---

class ColumnMappingRequest(BaseModel):
    """Input model: columns to be mapped to target schema."""
    columns: List[str] = Field(..., min_length=1, description="List of input column names")


class FieldMapping(BaseModel):
    """Single field mapping with confidence scores."""
    target_field: str
    mapped_input_column: Optional[str] = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    source: Optional[str] = Field(None, description="embedding | llm")
    embedding_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    llm_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class ColumnMappingResponse(BaseModel):
    """Output model: mappings with confidence scores."""
    mappings: List[FieldMapping]
    unmapped_columns: List[str] = Field(default_factory=list)


# --- Legacy models (kept for compatibility) ---

class ShippingRate(BaseModel):
    container_type: str
    rate: condecimal(gt=0)

class ShippingData(BaseModel):
    rates: List[ShippingRate]

class UserInput(BaseModel):
    selected_container_types: List[str]
    min_rate: Optional[condecimal(gt=0)] = None
    max_rate: Optional[condecimal(gt=0)] = None
