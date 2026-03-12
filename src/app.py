"""RFP Column Mapping - Map shipper RFP columns to target schema with confidence scores."""

import json
import os
import pandas as pd
import streamlit as st
from pydantic import ValidationError

from src.models.pydantic_models import (
    ColumnMappingRequest,
    ColumnMappingResponse,
    TARGET_SCHEMA_FIELDS,
)
from src.services.mapper import map_columns

st.set_page_config(page_title="RFP Column Mapper", layout="wide")

# Sidebar: API key for LLM fallback
with st.sidebar:
    st.header("LLM Fallback")
    st.caption("Optional. Used when embedding confidence < 70%")
    llm_provider = st.selectbox(
        "Provider",
        options=["Groq (free)", "OpenAI"],
        key="llm_provider",
    )
    api_key = st.text_input(
        "API Key",
        type="password",
        placeholder="gsk_... or sk-...",
        key="api_key",
    )
    if api_key:
        env_key = "GROQ_API_KEY" if "Groq" in llm_provider else "OPENAI_API_KEY"
        os.environ[env_key] = api_key
        st.success("API key set for this session")

st.title("RFP Column Mapping")
st.markdown(
    "Map arbitrary shipper RFP column headers to the internal target schema. "
    "Provide input columns as JSON and receive mapped columns with confidence scores."
)

st.subheader("Target schema")
st.code(", ".join(TARGET_SCHEMA_FIELDS), language=None)
st.caption(
    "Mapping uses embeddings first; LLM fallback when confidence < 70%. "
    "Provide API key in sidebar or set GROQ_API_KEY / OPENAI_API_KEY in .env."
)

# Input section
st.header("Input")
input_help = """
Provide your input columns as JSON. Supported formats:

**Option 1 - Array of column names:**
```json
["Orig Port", "Destination", "20GP", "40HQ Rate", "ETD", "Transit (days)", "Currency"]
```

**Option 2 - Object with columns key:**
```json
{"columns": ["POL", "POD", "Rate_20", "Rate_40HC", "Departure", "T/T", "Curr"]}
```
"""
with st.expander("Input format help", expanded=False):
    st.markdown(input_help)

input_json = st.text_area(
    "Input columns (JSON)",
    placeholder='["Orig Port", "Destination", "20GP", "40HQ Rate", "ETD", "Transit (days)", "Currency"]',
    height=120,
)

if st.button("Map Columns", type="primary"):
    if not input_json.strip():
        st.error("Please enter JSON input.")
    else:
        try:
            parsed = json.loads(input_json)
            # Handle both array and object formats
            if isinstance(parsed, list):
                columns = parsed
            elif isinstance(parsed, dict) and "columns" in parsed:
                columns = parsed["columns"]
            else:
                st.error("Invalid format. Use an array of column names or {\"columns\": [...]}")
                st.stop()

            # Validate with Pydantic
            request = ColumnMappingRequest(columns=columns)

            # Run mapping
            response: ColumnMappingResponse = map_columns(request)

            st.success("Mapping complete.")

            # Output section
            st.header("Output")

            # Output as JSON
            output_data = {
                "mappings": [
                    {
                        "target_field": m.target_field,
                        "mapped_input_column": m.mapped_input_column,
                        "confidence_score": m.confidence_score,
                        "source": m.source,
                        "embedding_confidence": m.embedding_confidence,
                        "llm_confidence": m.llm_confidence,
                    }
                    for m in response.mappings
                ],
                "unmapped_columns": response.unmapped_columns,
            }
            output_json = json.dumps(output_data, indent=2)

            st.text_area("Mapped output (JSON)", value=output_json, height=400)

            # Summary table
            st.subheader("Mapping summary")
            summary_data = []
            for m in response.mappings:
                row = {
                    "Target field": m.target_field,
                    "Mapped from": m.mapped_input_column or "—",
                    "Confidence": f"{m.confidence_score:.0%}",
                    "Source": m.source or "—",
                }
                if m.embedding_confidence is not None:
                    row["Embedding"] = f"{m.embedding_confidence:.0%}"
                if m.llm_confidence is not None:
                    row["LLM"] = f"{m.llm_confidence:.0%}"
                summary_data.append(row)
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

            if response.unmapped_columns:
                st.warning(f"Unmapped columns: {', '.join(response.unmapped_columns)}")

        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")
        except ValidationError as e:
            st.error(f"Validation error: {e}")
