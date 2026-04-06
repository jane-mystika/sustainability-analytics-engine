FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY frontend-streamlit/requirements.txt /tmp/frontend-requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/frontend-requirements.txt

COPY frontend-streamlit /app/frontend-streamlit
COPY database-mysql /app/database-mysql

WORKDIR /app/frontend-streamlit

EXPOSE 8501

CMD [
  "streamlit",
  "run",
  "app.py",
  "--server.address=0.0.0.0",
  "--server.port=8501"
]
