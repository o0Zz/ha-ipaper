FROM ghcr.io/astral-sh/uv:0.9.21 AS uv

# Build stage: resolve dependencies into a virtualenv with uv
FROM python:3.13-alpine AS builder

COPY --from=uv /uv /usr/local/bin/uv

# Compilers for packages without a musllinux wheel (matplotlib on arm64); not shipped in the runtime image
RUN apk add --no-cache build-base pkgconf

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=/usr/local/bin/python3

WORKDIR /app

# Install dependencies first to benefit from layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN uv sync --frozen --no-dev

# Runtime stage: no uv, no pip, no build cache
FROM python:3.13-alpine

# Pick up Alpine security fixes released after the base image, drop pip (unused at runtime)
# libstdc++ is needed by C++ extensions built from source in the build stage
RUN apk upgrade --no-cache \
    && apk add --no-cache libstdc++ \
    && python -m pip uninstall -y pip \
    && rm -rf /root/.cache

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /app/.venv ./.venv
COPY --from=builder /app/src ./src
COPY config.yaml ./
COPY docker/entrypoint.sh ./

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
