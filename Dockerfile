FROM python:3.13-slim

# Copy uv binaries from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set version environment variables
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_SUPABASE_MCP_SERVER=0.1.0 \
    SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0

# Set working directory
WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml smithery.yaml README.md ./
COPY supabase_mcp/ ./supabase_mcp/

# Upgrade pip, install pipx, and install project dependencies using uv
RUN pip install --upgrade pip && \
    pip install pipx && \
    uv pip install --no-cache-dir --system .

ENTRYPOINT ["uv", "run", "supabase_mcp/main.py"]