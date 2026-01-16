FROM python:3.11-slim

RUN pip install requests mysql-connector-python environs

COPY sla.py /app/sla.py

CMD ["python", "/app/sla.py"]