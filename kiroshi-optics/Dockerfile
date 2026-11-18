FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libglib2.0-0 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY kiroshi-optics/requirements-web.txt .
RUN python -m pip install --no-cache-dir -r requirements-web.txt

COPY kiroshi-optics/ .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn interfaces.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
