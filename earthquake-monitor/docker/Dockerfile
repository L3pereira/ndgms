FROM python:3.12.3-slim


WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and project configuration
COPY requirements.txt ./
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Copy alembic configuration and migrations
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Copy scripts
COPY scripts/ ./scripts/

# Copy and make startup script executable
COPY docker/startup.sh ./startup.sh
RUN chmod +x ./startup.sh

# Expose port
EXPOSE 8000

# Run the startup script
CMD ["./startup.sh"]
