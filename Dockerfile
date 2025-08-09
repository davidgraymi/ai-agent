FROM alpine:3.20

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Python 3, pip, curl, and git
RUN apk add --no-cache python3 py3-pip curl git

# Set working directory
WORKDIR /app

# Copy application code
COPY pyproject.toml README.md poetry.lock* requirements.txt* ./
COPY src ./src

# Create a venv and install dependencies inside it
RUN python3 -m venv /opt/venv \
    && . /opt/venv/bin/activate \
    && pip install --upgrade pip \
    && if [ -f "requirements.txt" ]; then pip install --no-cache-dir -r requirements.txt; fi \
    && if [ -f "pyproject.toml" ]; then pip install poetry && poetry install; fi

# Make sure the venv is on PATH
ENV PATH="/opt/venv/bin:$PATH"

# Default command (can be overridden)
# RUN pytest --maxfail=1 --disable-warnings -q

# Default entrypoint
ENTRYPOINT ["python", "-m", "src.main"]
