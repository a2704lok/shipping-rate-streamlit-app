"""LLM fallback when embedding confidence is below threshold."""

import os
import json
import re
from typing import List, Optional, Tuple

# Context for LLM: target schema and mapping task
LLM_CONTEXT = """
You are a logistics data mapping assistant. Map RFP (Request for Proposal) column headers 
from shippers to a standardized internal schema for freight forwarding.

TARGET SCHEMA (map each to exactly one input column or null if none matches):
- origin_port: Port of origin/loading (POL, orig port, load port, from)
- destination_port: Port of destination/discharge (POD, dest port, discharge port, to)
- container_type_20gp_rate: 20GP / 20ft container rate
- container_type_40hq_rate: 40HQ / 40HC container rate
- estimated_time_of_departure: ETD, sailing date, departure date
- transit_time_days: Transit time, T/T, duration in days
- currency: Currency code (USD, EUR, etc.)

RULES:
- Each target field maps to at most ONE input column
- Return null for target fields with no matching input column
- Assign confidence 0.0-1.0; use higher scores for clearer matches
- Output valid JSON only, no markdown or extra text
"""


def _get_llm_client():
    """
    Get LLM client. Supports Groq (free tier) or OpenAI.
    Priority: GROQ_API_KEY > OPENAI_API_KEY
    """
    from openai import OpenAI
    groq_key = os.getenv("GROQ_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    if groq_key:
        return OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
    if openai_key:
        return OpenAI(api_key=openai_key)
    raise ValueError(
        "Set GROQ_API_KEY (free: console.groq.com) or OPENAI_API_KEY for LLM fallback"
    )


def _get_llm_model() -> str:
    """Model to use: Groq models for Groq, else OpenAI default."""
    if os.getenv("GROQ_API_KEY"):
        return os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def llm_map_column(
    target_field: str,
    input_columns: List[str],
    target_descriptions: dict,
) -> Tuple[Optional[str], float]:
    """
    Use LLM to map a single target field to the best input column.
    Returns (mapped_column, confidence).
    """
    client = _get_llm_client()
    schema_desc = target_descriptions.get(
        target_field,
        target_field.replace("_", " ")
    )
    prompt = f"""{LLM_CONTEXT}

INPUT COLUMNS: {json.dumps(input_columns)}

Map target field "{target_field}" ({schema_desc}) to one of the input columns.
Return JSON: {{"mapped_column": "column_name_or_null", "confidence": 0.0-1.0}}
"""
    response = client.chat.completions.create(
        model=_get_llm_model(),
        messages=[
            {"role": "system", "content": "You return only valid JSON. No explanations."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    text = response.choices[0].message.content.strip()
    # Extract JSON (handle markdown code blocks)
    json_match = re.search(r"\{[^{}]*\}", text)
    if json_match:
        data = json.loads(json_match.group())
        mapped = data.get("mapped_column")
        conf = float(data.get("confidence", 0.5))
        if mapped and mapped.lower() in ("null", "none", ""):
            mapped = None
        if mapped and mapped not in input_columns:
            # Fuzzy match: try case-insensitive
            for col in input_columns:
                if col.lower() == str(mapped).lower():
                    mapped = col
                    break
        return (mapped, min(1.0, max(0.0, conf)))
    return (None, 0.0)
