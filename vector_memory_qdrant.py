import numpy as np
from typing import List, Dict, Any
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams

class VectorMemoryQdrant:
    """Векторная память на Qdrant для хранения и поиска диалогов."""

    def __init__(self, storage_path: str = "./qdrant_storage"):
        self.client = QdrantClient(path=storage_path)
        self.collection_name = "memory_bridge_dialogs"
        self._ensure_collection_exists()
        self._embedding_model = None
        print(f"[VectorMemory] Инициализирован. Путь: {storage_path}")

    def _ensure_collection_exists(self):
        """Создаёт коллекцию, если её нет."""
        collections = self.client.get_collections().collections
        if not any(c.name == self.collection_name for c in collections):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
            print(f"[VectorMemory] Коллекция создана.")

    def _get_embedding(self, text: str) -> List[float]:
        """Получает эмбеддинг через Sentence Transformers."""
        if self._embedding_model is None:
            from sentence_transformers import SentenceTransformer
            self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        return self._embedding_model.encode(text).tolist()

    def add_memory(self, user_id: str, role: str, text: str):
        """Добавляет реплику в память."""
        if not text.strip():
            return
        try:
            vector = self._get_embedding(text)
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=hash(f"{user_id}{text}") % (2**63),
                        vector=vector,
                        payload={"user_id": user_id, "role": role, "text": text}
                    )
                ]
            )
        except Exception as e:
            print(f"[VectorMemory] Ошибка сохранения: {e}")

    def search_memories(self, user_id: str, query: str, limit: int = 3) -> List[str]:
        """Ищет релевантные воспоминания."""
        if not query.strip():
            return []
        try:
            query_vector = self._get_embedding(query)
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=models.Filter(
                    must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))]
                ),
                limit=limit
            )
            return [point.payload["text"] for point in search_result.points if "text" in point.payload]
        except Exception as e:
            print(f"[VectorMemory] Ошибка поиска: {e}")
            return []