FROM python:3.12-slim
WORKDIR /app
COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt && useradd --uid 10001 --create-home app && mkdir /data && chown app:app /data
COPY licensing ./licensing
USER app
EXPOSE 8000
CMD ["uvicorn", "licensing.api:from_env", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log", "--no-proxy-headers"]
