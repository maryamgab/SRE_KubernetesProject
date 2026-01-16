import sys
import logging
import requests
import signal
import time
from datetime import datetime
from environs import Env
import mysql.connector

env = Env()
env.read_env()

class Config(object):
    prometheus_api_url = env("PROMETHEUS_API_URL", 'http://sage-query.sage.svc:9090')
    scrape_interval = env.int("SCRAPE_INTERVAL", 60)
    log_level = env.log_level("LOG_LEVEL", logging.INFO)
    mysql_host = env("MYSQL_HOST", 'mysql')
    mysql_port = env.int("MYSQL_PORT", 3306)
    mysql_user = env("MYSQL_USER", 'root')
    mysql_password = env("MYSQL_PASS", '1234')
    mysql_db_name = env("MYSQL_DB_NAME", 'sla')

class Mysql:
    def __init__(self, config: Config) -> None:
        logging.info('Connecting db')
        self.connection = mysql.connector.connect(
            host=config.mysql_host,
            user=config.mysql_user,
            passwd=config.mysql_password,
            auth_plugin='mysql_native_password'
        )
        self.table_name = 'indicators'
        logging.info('Starting migration')
        cursor = self.connection.cursor()
        cursor.execute(f'CREATE DATABASE IF NOT EXISTS {config.mysql_db_name}')
        cursor.execute(f'USE {config.mysql_db_name}')
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                datetime datetime not null default NOW(),
                name varchar(255) not null,
                slo float(4) not null,
                value float(4) not null,
                is_bad bool not null default false
            )
        """)
        cursor.execute(f"""
            ALTER TABLE {self.table_name} ADD INDEX (datetime)
        """)
        cursor.execute(f"""
            ALTER TABLE {self.table_name} ADD INDEX (name)
        """)
        self.connection.commit()

    def save_indicator(self, name, slo, value, is_bad=False, time=None):
        cursor = self.connection.cursor()
        sql = f"INSERT INTO {self.table_name} (name, slo, value, is_bad, datetime) VALUES (%s, %s, %s, %s, %s)"
        val = (name, slo, value, int(is_bad), time)
        cursor.execute(sql, val)
        self.connection.commit()

class PrometheusRequest:
    def __init__(self, config: Config) -> None:
        self.prometheus_api_url = config.prometheus_api_url

    def lastValue(self, query, time, default):
        try:
            response = requests.get(
                self.prometheus_api_url + '/api/v1/query',
                params={'query': query, 'time': time},
                timeout=10
            )
            content = response.json()
            if not content or len(content['data']['result']) == 0:
                return default
            return content['data']['result'][0]['value'][1]
        except Exception as error:
            logging.error(error)
            return default

def setup_logging(config: Config):
    logging.basicConfig(
        stream=sys.stdout,
        level=config.log_level,
        format="%(asctime)s %(levelname)s:%(message)s"
    )

def main():
    config = Config()
    setup_logging(config)
    db = Mysql(config)
    prom = PrometheusRequest(config)
    logging.info(f"Starting sla checker")

    while True:
        logging.debug(f"Run prober")
        unixtimestamp = int(time.time())
        date_format = datetime.utcfromtimestamp(unixtimestamp).strftime('%Y-%m-%d %H:%M:%S')

        # Метрика 1: Доступность веб-интерфейса (через создание пользователя)
        # Получаем текущие значения счётчиков
        success = float(prom.lastValue('oncall_web_probe_requests_success_total', unixtimestamp, 0))
        total = float(prom.lastValue('oncall_web_probe_requests_total', unixtimestamp, 0))
        sli = success / total if total > 0 else 1.0
        is_bad = sli < 0.999

        db.save_indicator(
            name='oncall_web_availability_sli',
            slo=0.999,
            value=sli,
            is_bad=is_bad,
            time=date_format
        )

        logging.debug(
            f"Waiting {config.scrape_interval} seconds for next loop")
        time.sleep(config.scrape_interval)

def terminate(signal, frame):
    print("Terminating")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, terminate)
    main()