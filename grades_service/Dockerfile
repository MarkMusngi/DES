FROM python:3.11-slim

# Install dependencies needed for psycopg2 (PostgreSQL adapter)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements from root and install
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

# Copy generated gRPC stubs from root
COPY generated /app/generated 

# Copy the main service file from its specific folder
COPY grades_service/grpc_grades_server.py .

# Set Environment variables 
ENV POSTGRES_HOST=postgres_db
ENV AUTH_GRPC_HOST=auth_service:50051 

EXPOSE 50054
CMD ["python", "grpc_grades_server.py"]