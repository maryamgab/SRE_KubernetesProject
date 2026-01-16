FROM python:3.11-slim

RUN pip install requests prometheus-client environs

COPY prober.py /app/prober.py

CMD ["python", "/app/prober.py"]