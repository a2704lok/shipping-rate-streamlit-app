"""RFP Column Mapping - Map CSV/Excel columns to target schema with confidence scores."""

import io
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
    "Upload a **CSV** or **Excel** file. Column headers are mapped to the internal target schema. "
    "Download the transformed file with mapped columns."
)

st.subheader("Target schema")
st.code(", ".join(TARGET_SCHEMA_FIELDS), language=None)
st.caption(
    "Mapping uses embeddings first; LLM fallback when confidence < 70%. "
    "Provide API key in sidebar for LLM fallback."
)

# Input: File upload - shown prominently at top
st.header("Upload file")
uploaded_file = st.file_uploader(
    "Drop your CSV or Excel file here, or click to browse",
    type=["csv", "xlsx", "xls"],
    help="Supported: .csv, .xlsx, .xls",
)

if uploaded_file is not None:
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded_file)
            input_format = "csv"
        else:
            df = pd.read_excel(uploaded_file)
            input_format = "xlsx"
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    st.success(f"Loaded **{uploaded_file.name}** — {len(df)} rows, {len(df.columns)} columns")
    st.write("**Columns:**", ", ".join(df.columns))
    columns = list(df.columns)

    if st.button("Map Columns", type="primary"):
        if not columns:
            st.error("No columns found in the file.")
        else:
            try:
                request = ColumnMappingRequest(columns=columns)
                response: ColumnMappingResponse = map_columns(request)

                st.success("Mapping complete.")

                # Build rename dict
                rename_map = {}
                for m in response.mappings:
                    if m.mapped_input_column and m.confidence_score > 0:
                        rename_map[m.mapped_input_column] = m.target_field

                df_mapped = df.rename(columns=rename_map)

                st.header("Output")

                # Mapping summary with confidence
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
                    st.warning(
                        f"Unmapped columns (kept as-is): {', '.join(response.unmapped_columns)}"
                    )

                # Download button
                st.subheader("Download mapped file")
                if input_format == "csv":
                    buffer = io.BytesIO()
                    df_mapped.to_csv(buffer, index=False)
                    buffer.seek(0)
                    st.download_button(
                        label="Download CSV",
                        data=buffer,
                        file_name="mapped_output.csv",
                        mime="text/csv",
                    )
                else:
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        df_mapped.to_excel(writer, index=False, sheet_name="Sheet1")
                    buffer.seek(0)
                    st.download_button(
                        label="Download Excel",
                        data=buffer,
                        file_name="mapped_output.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

                with st.expander("Preview mapped data"):
                    st.dataframe(df_mapped.head(20), use_container_width=True)

            except ValidationError as e:
                st.error(f"Validation error: {e}")
else:
    st.info("👆 Upload a CSV or Excel file above to get started.")
