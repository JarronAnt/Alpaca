# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml README.md ./
COPY src ./src

# Install dependencies
RUN uv pip install --system -e .

# Create workspace
RUN mkdir -p /workspace
ENV WORKSPACE_ROOT=/workspace

# Run as non-root user
RUN useradd -m -u 1000 alpaca && chown -R alpaca:alpaca /workspace
USER alpaca

ENTRYPOINT ["alpaca"]
CMD ["run", "--interactive"]
