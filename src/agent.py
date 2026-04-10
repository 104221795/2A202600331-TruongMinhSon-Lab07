# from typing import Callable

# from .store import EmbeddingStore


# class KnowledgeBaseAgent:
#     """
#     An agent that answers questions using a vector knowledge base.

#     Retrieval-augmented generation (RAG) pattern:
#         1. Retrieve top-k relevant chunks from the store.
#         2. Build a prompt with the chunks as context.
#         3. Call the LLM to generate an answer.
#     """

#     def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
#         # TODO: store references to store and llm_fn
#         pass

#     def answer(self, question: str, top_k: int = 3) -> str:
#         # TODO: retrieve chunks, build prompt, call llm_fn
#         raise NotImplementedError("Implement KnowledgeBaseAgent.answer")
from typing import Callable
from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        """
        Initialize the agent.
        
        :param store: The EmbeddingStore containing your chunked data.
        :param llm_fn: A function that takes a string prompt and returns a string response.
        """
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        """
        Processes a question by retrieving context and generating a response.
        """
        # 1. RETRIEVAL
        # The store.search method returns a list of dicts.
        # Based on the test suite, these dicts contain a 'content' key.
        results = self.store.search(question, top_k=top_k)
        
        if not results:
            return "I'm sorry, I couldn't find any relevant information in my knowledge base to answer that."

        # FIX: Changed res["text"] to res["content"] to avoid KeyError
        context_parts = [res["content"] for res in results]
        context_block = "\n---\n".join(context_parts)

        # 2. PROMPT AUGMENTATION
        # We wrap the user's question with the retrieved context.
        # Note: Keeping the indentation clean in the f-string prevents 
        # extra leading spaces in the prompt sent to the LLM.
        prompt = (
            f"You are a helpful assistant. Use the provided context to answer the user's question.\n"
            f"If the answer is not contained within the context, say that you don't know.\n\n"
            f"CONTEXT:\n{context_block}\n\n"
            f"USER QUESTION: {question}\n\n"
            f"FINAL ANSWER:"
        )

        # 3. GENERATION
        # Send the augmented prompt to the LLM
        response = self.llm_fn(prompt)
        
        return response.strip()