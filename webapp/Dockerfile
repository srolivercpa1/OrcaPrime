FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements-server.txt requirements-web.txt ./
RUN pip install --no-cache-dir -r requirements-web.txt && useradd --uid 10001 --create-home orcaprime
COPY webapp ./webapp
COPY assets/brand.png ./assets/brand.png
COPY orcaprime/__init__.py orcaprime/stock_categories.py ./orcaprime/
RUN mkdir -p /data/backup && chown -R orcaprime:orcaprime /data
USER orcaprime
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "webapp.server:application", "--factory", "--host", "0.0.0.0", "--port", "8080", "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*"]
