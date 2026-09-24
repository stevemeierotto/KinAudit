FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV BACKEND_HOST=0.0.0.0
ENV BACKEND_PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host ${BACKEND_HOST} --port ${BACKEND_PORT}"]
