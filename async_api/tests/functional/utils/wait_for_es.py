from elasticsearch import Elasticsearch

from tests.functional.settings import test_settings
from tests.functional.utils.backoff import backoff


@backoff()
def wait_for_es(es_client: Elasticsearch) -> bool:
    return es_client.ping()


if __name__ == '__main__':
    es_client = Elasticsearch(hosts=f'http://{test_settings.elastic_host}:{test_settings.elastic_port}')
    wait_for_es(es_client)
