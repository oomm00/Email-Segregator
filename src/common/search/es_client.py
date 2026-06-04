import logging
from typing import Any, Optional

from elasticsearch import AsyncElasticsearch

from src.common.config import settings

logger = logging.getLogger(__name__)

INDEX_EMAILS = "shipping_emails"


class ESClient:
    def __init__(self) -> None:
        self.client: Optional[AsyncElasticsearch] = None

    async def ensure_connected(self) -> AsyncElasticsearch:
        if self.client is None:
            hosts = settings.elasticsearch_hosts.split(",")
            self.client = AsyncElasticsearch(hosts=hosts, verify_certs=settings.elasticsearch_verify_certs)
        return self.client

    async def ensure_index(self, index: str = INDEX_EMAILS) -> None:
        es = await self.ensure_connected()
        exists = await es.indices.exists(index=index)
        if not exists:
            await es.indices.create(index=index, body={
                "settings": {"number_of_shards": 1, "number_of_replicas": 0},
                "mappings": {
                    "properties": {
                        "email_id": {"type": "keyword"},
                        "message_id": {"type": "keyword"},
                        "subject": {"type": "text"},
                        "sender": {"type": "keyword"},
                        "recipients": {"type": "keyword"},
                        "body_text": {"type": "text"},
                        "received_at": {"type": "date"},
                        "source": {"type": "keyword"},
                        "status": {"type": "keyword"},
                        "attachments": {"type": "nested"},
                    }
                },
            })
            logger.info("created es index", index=index)

    async def index_doc(self, index: str, doc_id: str, body: dict[str, Any]) -> None:
        es = await self.ensure_connected()
        await es.index(index=index, id=doc_id, body=body, refresh="wait_for")

    async def search(self, index: str, query: dict[str, Any], size: int = 20, offset: int = 0) -> dict[str, Any]:
        es = await self.ensure_connected()
        result = await es.search(index=index, body={"query": query, "from": offset, "size": size})
        return result.body

    async def close(self) -> None:
        if self.client:
            await self.client.close()
            self.client = None


es_client = ESClient()


async def index_email(email_data: dict[str, Any]) -> None:
    await es_client.ensure_index(INDEX_EMAILS)
    await es_client.index_doc(INDEX_EMAILS, str(email_data["email_id"]), email_data)


async def search_emails(query: str, size: int = 20, offset: int = 0) -> list[dict[str, Any]]:
    es = await es_client.ensure_connected()
    body = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["subject", "body_text", "sender", "recipients"],
            }
        }
    }
    result = await es.search(index=INDEX_EMAILS, body={**body, "from": offset, "size": size})
    return [hit["_source"] for hit in result["hits"]["hits"]]
