import sys
import logging
import requests
import signal
import time
from environs import Env
from prometheus_client import start_http_server, Gauge, Counter

REQUESTS_TOTAL = Counter("oncall_web_probe_requests_total", "Total HTTP requests to /healthcheck")
REQUESTS_SUCCESS = Counter("oncall_web_probe_requests_success_total", "Successful HTTP requests (status 200)")
PROBE_HEALTHY = Gauge("oncall_web_probe_healthy", "1 if last probe was successful")

env = Env()
env.read_env()

class Config:
    oncall_exporter_api_url = env("ONCALL_EXPORTER_API_URL", "http://oncall:8080")
    oncall_exporter_scrape_interval = env.int("ONCALL_EXPORTER_SCRAPE_INTERVAL", 30)
    oncall_exporter_log_level = env.log_level("ONCALL_EXPORTER_LOG_LEVEL", logging.INFO)
    oncall_exporter_metrics_port = env.int("ONCALL_EXPORTER_METRICS_PORT", 9081)

def setup_logging(config: Config):
    logging.basicConfig(
        stream=sys.stdout,
        level=config.oncall_exporter_log_level,
        format="%(asctime)s %(levelname)s:%(message)s"
    )

def probe(config: Config):
    REQUESTS_TOTAL.inc()
    try:
        resp = requests.get(f"{config.oncall_exporter_api_url}/healthcheck", timeout=10)
        if resp.status_code == 200:
            REQUESTS_SUCCESS.inc()
            PROBE_HEALTHY.set(1)
        else:
            PROBE_HEALTHY.set(0)
    except Exception as e:
        logging.error(f"Probe failed: {e}")
        PROBE_HEALTHY.set(0)

def main():
    config = Config()
    setup_logging(config)
    start_http_server(config.oncall_exporter_metrics_port)
    logging.info(f"Starting prober on {config.oncall_exporter_api_url}, metrics on port {config.oncall_exporter_metrics_port}")
    while True:
        probe(config)
        time.sleep(config.oncall_exporter_scrape_interval)

def terminate(signal, frame):
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, terminate)
    main()