FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_server.py .
COPY app.py .
COPY "7_2자주 틀리는 말01.json" ./

EXPOSE 8080

CMD ["python", "app.py"]