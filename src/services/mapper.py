"""Column mapping service: embedding-based with LLM fallback when confidence < threshold."""

import os
from typing import List, Optional, Tuple

from src.models.pydantic_models import (
    TARGET_SCHEMA_FIELDS,
    ColumnMappingRequest,
    ColumnMappingResponse,
    FieldMapping,
)

# Confidence threshold below which we call LLM (override via CONFIDENCE_THRESHOLD env)
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.70"))

# Re-export for LLM context
from src.services.embeddings import TARGET_FIELD_DESCRIPTIONS


def _embedding_match(
    target_field: str,
    input_columns: List[str],
    used_columns: set,
) -> Tuple[Optional[str], float]:
    """Use embeddings to find best matching input column. Returns (column, confidence)."""
    try:
        from src.services.embeddings import compute_similarity
    except ImportError:
        return (None, 0.0)

    available = [c for c in input_columns if c not in used_columns]
    if not available:
        return (None, 0.0)

    pairs = compute_similarity(available, target_field)
    if not pairs:
        return (None, 0.0)

    best_col, raw_score = pairs[0]
    # Cosine similarity with normalized embeddings is typically 0-1 for similar text
    confidence = max(0.0, min(1.0, float(raw_score)))
    return (best_col, round(confidence, 3))


def _llm_match(
    target_field: str,
    input_columns: List[str],
    used_columns: set,
) -> Tuple[Optional[str], float]:
    """Use LLM to map when embedding confidence is low. Returns (column, confidence)."""
    try:
        from src.services.llm_fallback import llm_map_column
    except ImportError:
        return (None, 0.0)

    if not (os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")):
        return (None, 0.0)

    available = [c for c in input_columns if c not in used_columns]
    if not available:
        return (None, 0.0)

    mapped, confidence = llm_map_column(
        target_field, available, TARGET_FIELD_DESCRIPTIONS
    )
    if mapped and mapped in available:
        return (mapped, round(confidence, 3))
    return (None, 0.0)


def map_columns(request: ColumnMappingRequest) -> ColumnMappingResponse:
    """
    Map input columns to target schema:
    1. Use embedding similarity first
    2. If best confidence < 70%, fall back to LLM
    """
    input_columns = [c.strip() for c in request.columns if c.strip()]
    used_columns = set()
    mappings = []

    for target_field in TARGET_SCHEMA_FIELDS:
        # Step 1: Try embedding-based match
        mapped_col, confidence = _embedding_match(
            target_field, input_columns, used_columns
        )

        # Step 2: Fall back to LLM if below threshold
        embedding_conf = confidence
        llm_conf: Optional[float] = None
        source = "embedding"
        has_llm = bool(os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY"))
        if confidence < CONFIDENCE_THRESHOLD and has_llm:
            llm_col, llm_conf = _llm_match(
                target_field, input_columns, used_columns
            )
            if llm_col and llm_conf is not None and llm_conf > confidence:
                mapped_col = llm_col
                confidence = llm_conf
                source = "llm"

        if mapped_col and confidence > 0:
            used_columns.add(mapped_col)
            mappings.append(FieldMapping(
                target_field=target_field,
                mapped_input_column=mapped_col,
                confidence_score=confidence,
                source=source,
                embedding_confidence=round(embedding_conf, 3) if embedding_conf > 0 else None,
                llm_confidence=round(llm_conf, 3) if llm_conf is not None and llm_conf > 0 else None,
            ))
        else:
            mappings.append(FieldMapping(
                target_field=target_field,
                mapped_input_column=None,
                confidence_score=0.0,
                source=None,
                embedding_confidence=round(embedding_conf, 3) if embedding_conf > 0 else None,
                llm_confidence=None,
            ))

    unmapped = [c for c in input_columns if c not in used_columns]

    return ColumnMappingResponse(
        mappings=mappings,
        unmapped_columns=unmapped,
    )
