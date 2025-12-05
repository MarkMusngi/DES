FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

COPY generated /app/generated 

COPY enrollment_service/grpc_enrollment_server.py .
 
ENV POSTGRES_HOST=postgres_db
ENV AUTH_GRPC_HOST=auth_service:50051 

EXPOSE 50053
CMD ["python", "grpc_enrollment_server.py"]