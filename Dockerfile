# ---- Base image ----
FROM python:3.11-slim

# ---- Environment variables ----
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ---- Work directory ----
WORKDIR /app

# ---- System dependencies (important for pgvector / builds) ----
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ---- Install Python dependencies ----
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy project ----
COPY . .

# ---- Expose FastAPI port ----
EXPOSE 7860

# ---- Start server ----
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]