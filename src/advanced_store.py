from src.store import EmbeddingStore

class ParentChildStore(EmbeddingStore):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Nơi lưu trữ nội dung đầy đủ của các Điều luật (Large Chunks)
        self.parent_vault = {}

    def add_parent_child_docs(self, parent_map: dict, child_docs: list):
        """
        parent_map: { 'parent_id': 'nội dung đầy đủ' }
        child_docs: Danh sách các Document nhỏ để tạo embedding
        """
        self.parent_vault.update(parent_map)
        self.add_documents(child_docs)

    def search_expanded(self, query: str, top_k: int = 3):
        child_results = self.search(query, top_k=top_k)

        expanded_results = []
        seen_parents = set()

        for res in child_results:
            p_id = res["metadata"].get("parent_id")

            if p_id and p_id in self.parent_vault:
                if p_id not in seen_parents:
                    new_res = res.copy()
                    new_res["parent_content"] = self.parent_vault[p_id]
                    new_res["matched_child"] = res["content"]
                    new_res["is_parent"] = True

                    expanded_results.append(new_res)
                    seen_parents.add(p_id)
            else:
                new_res = res.copy()
                new_res["is_parent"] = False
                expanded_results.append(new_res)

        return expanded_results