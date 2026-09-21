FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY core ./core
COPY rag ./rag
COPY api ./api
COPY web ./web
COPY tests/bills ./tests/bills
COPY tests/expected.json ./tests/expected.json
RUN mkdir -p /app/cache && chmod 777 /app/cache
ENV PYTHONUNBUFFERED=1
EXPOSE 7860
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]
