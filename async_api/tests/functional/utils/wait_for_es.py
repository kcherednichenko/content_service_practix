import os
import time

from elasticsearch import Elasticsearch

from tests.functional.settings import test_settings


if __name__ == '__main__':
    es_client = Elasticsearch(
        hosts=f'http://{test_settings.elastic_host}:{test_settings.elastic_port}',)
    while True:
        if es_client.ping():
            break
        time.sleep(1)
