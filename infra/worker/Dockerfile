FROM python:3.12-slim

# Install system dependencies for MDB and ODBC
RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    mdbtools \
    odbc-mdbtools \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy source code
COPY src ./src

# Set environment variables for Docker network
ENV POSTGRES_HOST=postgres
ENV POSTGRES_PORT=5432
ENV MDB_DRIVER={MDBTools}
ENV PYTHONPATH=.
ENV IS_DOCKER=true

# Run the application
CMD ["uv", "run", "python", "-m", "src.mdb_sync.main"]
