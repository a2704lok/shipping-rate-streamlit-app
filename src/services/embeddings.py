"""Embedding-based semantic similarity for column mapping."""

from typing import List, Tuple
import numpy as np

# Target field descriptions for semantic matching
TARGET_FIELD_DESCRIPTIONS = {
    "origin_port": "port of origin, port of loading, POL, origin, load port, from port",
    "destination_port": "port of destination, port of discharge, POD, destination, discharge port, to port",
    "container_type_20gp_rate": "20 foot general purpose container rate, 20GP rate, 20 ft rate, twenty foot rate",
    "container_type_40hq_rate": "40 foot high cube container rate, 40HQ rate, 40HC rate, forty foot rate",
    "estimated_time_of_departure": "estimated time of departure, ETD, sailing date, departure date",
    "transit_time_days": "transit time in days, transit duration, T/T, travel time",
    "currency": "currency code, rate currency, CCY, money type",
}


def _get_encoder():
    """Lazy load encoder to avoid slow startup when not used."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2", device="cpu")


def compute_similarity(input_columns: List[str], target_field: str) -> List[Tuple[str, float]]:
    """
    Compute cosine similarity between input columns and a target field description.
    Returns list of (column, score) sorted by score descending.
    """
    encoder = _get_encoder()
    description = TARGET_FIELD_DESCRIPTIONS.get(
        target_field,
        target_field.replace("_", " ")
    )
    # Encode target description
    target_embedding = encoder.encode([description], normalize_embeddings=True)
    # Encode input columns
    col_embeddings = encoder.encode(input_columns, normalize_embeddings=True)
    # Cosine similarity (already normalized, so dot product = cosine sim)
    scores = np.dot(col_embeddings, target_embedding.T).flatten()
    # Sort by score descending
    pairs = [(col, float(s)) for col, s in zip(input_columns, scores)]
    return sorted(pairs, key=lambda x: x[1], reverse=True)
