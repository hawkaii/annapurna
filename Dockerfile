# Use official Python image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Install uv (Python package manager)
RUN pip install --upgrade pip && pip install uv

# Set workdir
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies using uv
RUN uv venv && uv sync

# Activate venv for all future RUN/CMD
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Expose port 8086 for Railway
EXPOSE 8086

# Start the server (runs your script directly)
CMD [".venv/bin/python", "mcp-bearer-token/mcp_starter.py"]
