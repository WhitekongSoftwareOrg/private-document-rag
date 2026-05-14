from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.http import models


class VectorStore:
    def __init__(self, *, path: str, collection_name: str, vector_size: int) -> None:
        self.client = QdrantClient(path=path)
        self.collection_name = collection_name
        self._ensure_collection(vector_size)

    def _ensure_collection(self, vector_size: int) -> None:
        collections = self.client.get_collections().collections
        if any(collection.name == self.collection_name for collection in collections):
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )

    def upsert_chunks(self, items: list[dict]) -> None:
        points = [
            models.PointStruct(
                id=str(uuid4()),
                vector=item["vector"],
                payload=item["payload"],
            )
            for item in items
        ]
        self.client.upsert(collection_name=self.collection_name, points=points, wait=True)

    def search(self, query_vector: list[float], top_k: int) -> list[models.ScoredPoint]:
        if hasattr(self.client, "query_points"):
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k,
                with_payload=True,
            )
            return list(response.points)

        return self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
        )
