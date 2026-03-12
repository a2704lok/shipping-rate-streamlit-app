FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Ensure Python can find the src package
ENV PYTHONPATH=/app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code
COPY ./src ./src

# Copy the entrypoint script
COPY ./scripts/entrypoint.sh .

# Make the entrypoint script executable
RUN chmod +x entrypoint.sh

# Expose the port the app runs on
EXPOSE 8501

# Command to run the application
CMD ["./entrypoint.sh"]