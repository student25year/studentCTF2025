FROM python:3.11-slim-bookworm


ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


RUN apt-get update && \
    apt-get install libmagic1 -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m ctf && \
    mkdir -p /app && \
    chown ctf:ctf /app

WORKDIR /app

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY --chown=ctf . .

USER ctf

ENTRYPOINT ["/entrypoint.sh"]
