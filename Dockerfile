FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 16163
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "16163"]
