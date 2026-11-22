FROM node:24-slim AS web

WORKDIR /web

# NODE_ENV may be "production" in the caller's environment; dev deps are required to build.
ENV NODE_ENV=development

COPY web/package.json web/package-lock.json ./
RUN npm ci --include=dev

COPY web/ ./
RUN npm run build


FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    HF_HOME=/app/storage/model_cache \
    SENTENCE_TRANSFORMERS_HOME=/app/storage/model_cache/sentence-transformers

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=web /web/dist ./web/dist

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
