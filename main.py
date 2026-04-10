
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
import google.generativeai as genai

from src.agent import KnowledgeBaseAgent
from src.embeddings import LocalEmbedder
from src.models import Document
from src.store import EmbeddingStore


# ===============================
# Configuration
# ===============================

DATA_FILE = "luat_lao_dong.md"
OUTPUT_FILE = "rag_answers.txt"

TEST_QUERIES = [
    "Bộ luật Lao động năm 2019 (Luật số 45/2019/QH14) chính thức có hiệu lực thi hành kể từ ngày tháng năm nào?",
    "Theo Bộ luật Lao động 2019, hợp đồng lao động được phân loại thành mấy loại chính? Đó là những loại nào?",
    "Quy định pháp luật không cho phép áp dụng thời gian thử việc đối với trường hợp người lao động giao kết loại hợp đồng lao động nào?",
    "Theo quy định, thời gian thử việc tối đa đối với công việc của người quản lý doanh nghiệp là bao nhiêu ngày?",
    "Trong dịp lễ Quốc khánh 02/9, người lao động được nghỉ làm việc và hưởng nguyên lương tổng cộng bao nhiêu ngày?",
    "Người lao động có những quyền cơ bản nào theo Bộ luật Lao động 2019?",
    "Lộ trình điều chỉnh tuổi nghỉ hưu đối với người lao động làm việc trong điều kiện lao động bình thường được thực hiện cho đến khi đạt mức độ tuổi nào đối với nam và nữ?"
]


# ===============================
# Gemini LLM
# ===============================

def init_gemini():

    load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError("Missing GOOGLE_API_KEY")

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel("gemini-2.5-flash-lite")

    return model


def gemini_llm(prompt: str) -> str:

    model = init_gemini()

    response = model.generate_content(prompt)

    return response.text


# ===============================
# Load Document
# ===============================

def load_document(path: str) -> List[Document]:

    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    content = file_path.read_text(encoding="utf-8")

    return [
        Document(
            id="luat_lao_dong_2019",
            content=content,
            metadata={"source": path}
        )
    ]


# ===============================
# Parent-Child Chunking
# ===============================

def parent_child_chunking(doc: Document,
                          parent_size: int = 1200,
                          child_size: int = 300):

    text = doc.content

    parents = []
    children = []

    parent_id = 0

    for i in range(0, len(text), parent_size):

        parent_text = text[i:i + parent_size]

        parent_doc = Document(
            id=f"parent_{parent_id}",
            content=parent_text,
            metadata={"type": "parent"}
        )

        parents.append(parent_doc)

        child_index = 0

        for j in range(0, len(parent_text), child_size):

            child_text = parent_text[j:j + child_size]

            child_doc = Document(
                id=f"child_{parent_id}_{child_index}",
                content=child_text,
                metadata={
                    "type": "child",
                    "parent_id": parent_doc.id
                }
            )

            children.append(child_doc)

            child_index += 1

        parent_id += 1

    return parents, children


# ===============================
# Build Advanced Store
# ===============================

def build_advanced_store():

    print("Loading document...")

    docs = load_document(DATA_FILE)

    print("Creating parent-child chunks...")

    parents, children = parent_child_chunking(docs[0])

    print(f"Parent chunks: {len(parents)}")
    print(f"Child chunks: {len(children)}")

    embedder = LocalEmbedder()

    store = EmbeddingStore(
        collection_name="law_parent_child_store",
        embedding_fn=embedder
    )

    print("Adding child chunks to embedding store...")

    store.add_documents(children)

    parent_lookup = {p.id: p for p in parents}

    return store, parent_lookup


# ===============================
# Parent Retrieval
# ===============================

TOP_K = 5


def print_top_k_results(store, query, top_k=5):

    print("\n=== Top-K Retrieval Results ===")

    results = store.search(query, top_k=top_k)

    for i, r in enumerate(results, start=1):

        score = r["score"]
        source = r["metadata"].get("parent_id", "unknown")

        preview = r["content"][:120].replace("\n", " ")

        print(f"{i}. score={score:.4f} parent={source}")
        print(f"   preview: {preview}...\n")

    return results


# ===============================
# Run RAG QA
# ===============================

def run_queries():

    store, parent_lookup = build_advanced_store()

    print("\n===== Running Queries =====\n")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:

        for q_index, q in enumerate(TEST_QUERIES):

            print("\n===================================")
            print(f"Question {q_index+1}: {q}")

            f.write("\n===================================\n")
            f.write(f"Question {q_index+1}: {q}\n\n")

            results = print_top_k_results(store, q, TOP_K)

            parent_docs = []
            used = set()

            for i, r in enumerate(results, start=1):

                score = r["score"]
                parent_id = r["metadata"].get("parent_id")

                preview = r["content"][:120].replace("\n", " ")
                full_text = r["content"]

                print(f"{i}. score={score:.4f} parent={parent_id}")
                print(f"   preview: {preview}...")
                print("   full text:")
                print(full_text)
                print("-"*50)

                f.write(f"Chunk {i} (score={score:.4f})\n")
                f.write(full_text + "\n\n")

                if parent_id and parent_id not in used:
                    parent_docs.append(parent_lookup[parent_id])
                    used.add(parent_id)

            context = "\n\n".join([d.content for d in parent_docs])

            prompt = f"""
Bạn là trợ lý pháp luật.

Context:
{context}

Question:
{q}

Trả lời ngắn gọn và chính xác.
"""

            answer = gemini_llm(prompt)

            print("\n=== Final Answer ===")
            print(answer)

            f.write("\n=== Final Answer ===\n")
            f.write(answer + "\n")


# ===============================
# Main
# ===============================

def main():

    run_queries()


if __name__ == "__main__":
    main()
