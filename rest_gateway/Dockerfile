FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

COPY generated /app/generated 

COPY rest_gateway/rest_gateway.py .

EXPOSE 5001
CMD ["python", "rest_gateway.py"]