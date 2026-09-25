"""
scripts/es_healthcheck.py
Health check utility to verify that Elasticsearch is running and contains indexed documents.
"""
from elasticsearch import Elasticsearch

ES_HOST = "http://localhost:9200"
ALIAS_NAME = "bis_standards_active"


def check_health():
    print(f"Pinging Elasticsearch at {ES_HOST} ...")
    try:
        es = Elasticsearch(ES_HOST)
        if not es.ping():
            print("FAILURE: Elasticsearch did not respond to ping. Is Docker running?")
            return False

        info = es.info()
        print("--------------------------------------------------")
        print(f" SUCCESS: Elasticsearch cluster is ONLINE!")
        print(f" Cluster Name : {info.get('cluster_name')}")
        print(f" ES Version   : {info.get('version', {}).get('number')}")

        if es.indices.exists_alias(name=ALIAS_NAME):
            count = es.count(index=ALIAS_NAME)["count"]
            print(f" Active Alias : '{ALIAS_NAME}' -> {count} documents indexed")
        else:
            print(f" WARNING     : Alias '{ALIAS_NAME}' not found. Run index_elasticsearch.py.")
        print("--------------------------------------------------")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False


if __name__ == "__main__":
    check_health()
