#!/bin/bash

# This script serves as the entry point for the Docker container.

# Set environment variables from the .env file
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Add project root to Python path so `src` module can be imported
export PYTHONPATH=/app:${PYTHONPATH}

# Run the Streamlit application
streamlit run src/app.py --server.port 8501 --server.address 0.0.0.0 --logger.level info