FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg MPLCONFIGDIR=/tmp/matplotlib \
    PREFECT_HOME=/var/lib/prefect PREFECT_SERVER_ANALYTICS_ENABLED=false
WORKDIR /app
COPY requirements-lock.txt ./
RUN pip install --no-cache-dir -r requirements-lock.txt \
    && useradd --uid 10001 --create-home app \
    && mkdir -p /var/lib/prefect /app/outputs/current /app/report/current \
    && chown -R app:app /var/lib/prefect /app/outputs /app/report
COPY --chown=app:app src ./src
COPY --chown=app:app data/telco_churn.csv ./data/telco_churn.csv
COPY --chown=app:app assets ./assets
USER app
CMD ["python", "-m", "src.deploy"]
