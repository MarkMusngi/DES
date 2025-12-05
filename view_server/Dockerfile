FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

COPY view_server/app_view.py .

COPY frontend /app/frontend

ENV REST_GATEWAY_URL=http://rest_gateway:5001/api/v1 

EXPOSE 5000
CMD ["python", "app_view.py"]