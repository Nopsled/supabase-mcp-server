FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_SUPABASE_MCP_SERVER=0.1.0
ENV SETUPTOOLS_SCM_PRETEND_VERSION=0.1.0


# Set working directory
WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY smithery.yaml .
COPY supabase_mcp/ ./supabase_mcp/
COPY README.md .

# Upgrade pip and install pipx
RUN pip install --upgrade pip
RUN pip install pipx

# Add pipx binary directory to PATH
ENV PATH="/root/.local/bin:$PATH"

# Install project dependencies using uv
RUN uv pip install --no-cache-dir --system .


# Expose any ports needed (if applicable)
# This MCP server communicates via stdin/stdout according to smithery.yaml

# Set the entrypoint to the command that Smithery expects
ENTRYPOINT ["uv", "run", "supabase_mcp/main.py"]