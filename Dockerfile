# Stage 1: Alpine base
FROM python:3.13-alpine as base

RUN apk add --no-cache --virtual .build-deps gcc musl-dev && \
    adduser -D appuser && \
    mkdir -p /app /app/otp_cache && \
    chown -R appuser:appuser /app && \
    chmod -R 777 /app/otp_cache

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/home/appuser/.local/bin:$PATH" \
    DISKCACHE_DIR="/app/otp_cache"

# Stage 2: Builder (unchanged)
FROM base as builder
USER appuser
RUN mkdir -p /home/appuser/.local
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 3: Final Image
FROM base as final
COPY --from=builder /home/appuser/.local /home/appuser/.local
COPY . .   
# NOSONAR: Safe due to strict .dockerignore

# Environment config (updated)
ENV ENVIRONMENT=development \
    FLASK_APP=app.py \
    FLASK_DEBUG=0  

# Final setup
USER appuser
VOLUME /app/otp_cache

# Run Flask dev server directly
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5000"]
