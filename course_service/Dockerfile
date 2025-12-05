FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

COPY generated /app/generated 

COPY course_service/grpc_course_server.py .

ENV POSTGRES_HOST=postgres_db

EXPOSE 50052
CMD ["python", "grpc_course_server.py"]