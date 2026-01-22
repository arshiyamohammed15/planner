# syntax=docker/dockerfile:1

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if needed (e.g., for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . /app

# Expose default app port if desired (FastAPI/uvicorn default 8000)
EXPOSE 8000

# Default command to run the API
CMD ["python", "-m", "uvicorn", "api.planner_api:app", "--host", "0.0.0.0", "--port", "8000"]

