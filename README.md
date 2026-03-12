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

```bash
docker compose -f docker-compose.app.yml up -d
# Open http://localhost:8501
```

## Configuration

- **LLM fallback**: Set `GROQ_API_KEY` or `OPENAI_API_KEY` in `.env` or use the sidebar
- **Threshold**: Override with `CONFIDENCE_THRESHOLD` (default 0.70)

## License

MIT License. See [LICENSE](LICENSE).
