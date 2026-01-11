FROM python:3.11-slim-trixie

# Install dependencies and clean up in one layer to reduce image size
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -U pip && pip install uv

# Set working directory
WORKDIR /app

# Copy application files
COPY pyproject.toml uv.lock ./
COPY src ./src
COPY html-template ./html-template
COPY config.yaml ./
COPY entrypoint.sh ./

# Install dependencies and make entrypoint executable
RUN uv sync --frozen && chmod +x entrypoint.sh

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["./entrypoint.sh"]
