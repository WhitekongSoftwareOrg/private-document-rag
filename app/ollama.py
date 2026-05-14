import httpx


class OllamaService:
    def __init__(self, *, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate_answer(self, question: str, contexts: list[dict]) -> str:
        prompt = self.build_prompt(question, contexts)
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"].strip()

    def build_prompt(self, question: str, contexts: list[dict]) -> str:
        context_block = "\n\n".join(
            f"[{index}] {item['file_name']} | chunk {item['chunk_index']}\n{item['text']}"
            for index, item in enumerate(contexts, start=1)
        )
        return (
            "You are a private document assistant. "
            "Answer using only the retrieved context. "
            "If the answer is not in the context, say so clearly. "
            "Cite the chunk numbers you used.\n\n"
            f"Question:\n{question}\n\n"
            f"Context:\n{context_block}"
        )
