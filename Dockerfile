FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy \
    aiosqlite pydantic requests websockets \
    scikit-learn numpy pandas \
    psycopg2-binary redis prometheus-fastapi-instrumentator

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]