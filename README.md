# RFP Column Mapper

Map arbitrary shipper RFP column headers to a standardized internal schema with embedding-based matching and LLM fallback.

## Features

- **Embedding-based mapping** (sentence-transformers)
- **LLM fallback** when confidence < 70% (Groq or OpenAI)
- **Pydantic validation** for input/output
- **Streamlit UI** with optional API key input
- **Docker** support

## Quick Start

### Run locally

```bash
pip install -r requirements.txt
streamlit run src/app.py
```

### Run with Docker


docker compose -f docker-compose.app.yml up -d
# Open http://localhost:8501
```

## Configuration

- **LLM fallback**: Set `GROQ_API_KEY` or `OPENAI_API_KEY` in `.env` or use the sidebar
- **Threshold**: Override with `CONFIDENCE_THRESHOLD` (default 0.70)

## License

MIT License. See [LICENSE](LICENSE).

<img width="1470" height="881" alt="RFP column_ norm" src="https://github.com/user-attachments/assets/5fb6226e-63dc-415e-84ed-c1c99b5b8831" />

<img width="1150" height="738" alt="mapping output" src="https://github.com/user-attachments/assets/044c76c1-28fe-4da0-ac1d-9cba5bc2e101" />

