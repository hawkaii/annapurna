# Use official Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libffi-dev && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package manager)
RUN pip install --no-cache-dir uv

# Set workdir
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN uv venv && uv sync

# Activate venv for all future RUN/CMD
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Expose the port the app runs on
EXPOSE 8086

# Set environment variables for production (Railway injects these)
# ENV AUTH_TOKEN=your_token_here
# ENV MY_NUMBER=your_number_here

# Default command to run the server
CMD ["python", "mcp-bearer-token/mcp_starter.py"]
