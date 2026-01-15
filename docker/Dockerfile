FROM python:3.11-slim-bookworm

# Install uv
RUN pip install -U pip && pip install uv

# Set working directory
WORKDIR /app

# Copy application files
COPY pyproject.toml uv.lock ./
COPY src ./src
COPY html-template ./html-template
COPY config.yaml ./
COPY docker/entrypoint.sh ./

# Install dependencies and make entrypoint executable
RUN uv sync --frozen && chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
