#!/usr/bin/env python3
"""Hybrid RAG engine: BM25 + dense retrieval + cross-encoder reranking."""

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from types import SimpleNamespace


load_dotenv()


class HybridRAG:
    def __init__(self, docs_dir: Path, persist_dir: Path, top_k: int = 5, rerank_top_k: int = 3,
                 *, embeddings=None, reranker=None, retriever=None, llm=None):
        if top_k <= 0 or rerank_top_k <= 0:
            raise ValueError("retrieval limits must be positive")
        self.docs_dir = docs_dir
        self.persist_dir = persist_dir
        self.top_k = top_k
        self.rerank_top_k = rerank_top_k
        self.llm = llm
        if embeddings is None and retriever is None:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        if reranker is None:
            from sentence_transformers import CrossEncoder
            reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.embeddings = embeddings
        self.reranker = reranker
        self.qa = SimpleNamespace(retriever=retriever) if retriever is not None else self._build_qa()

    def _load_documents(self) -> List[Document]:
        from langchain_community.document_loaders import DirectoryLoader, TextLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        loader = DirectoryLoader(str(self.docs_dir), glob="*.txt", loader_cls=TextLoader)
        documents = loader.load()
        if not documents:
            raise ValueError(f"No text documents found in {self.docs_dir}")
        splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
        return splitter.split_documents(documents)

    def _build_qa(self):
        from langchain_community.retrievers import BM25Retriever
        from langchain_community.vectorstores import Chroma
        from langchain_classic.retrievers import EnsembleRetriever
        if self.persist_dir.exists():
            vectorstore = Chroma(
                persist_directory=str(self.persist_dir),
                embedding_function=self.embeddings,
            )
            chunks = self._load_documents()
        else:
            chunks = self._load_documents()
            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=str(self.persist_dir),
            )

        bm25_retriever = BM25Retriever.from_documents(chunks, k=self.top_k)
        dense_retriever = vectorstore.as_retriever(search_kwargs={"k": self.top_k})

        ensemble = EnsembleRetriever(
            retrievers=[bm25_retriever, dense_retriever],
            weights=[0.4, 0.6],
        )

        return SimpleNamespace(retriever=ensemble)

    def _get_llm(self):
        if self.llm is not None:
            return self.llm
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        if api_key:
            return ChatOpenAI(model=model, api_key=api_key, base_url=base_url, temperature=0.2)
        print("OPENAI_API_KEY not set; falling back to local Ollama (llama3.1)")
        return ChatOpenAI(
            model=os.getenv("OLLAMA_MODEL", "llama3.1"),
            openai_api_key="ollama",
            openai_api_base=os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1"),
            temperature=0.2,
        )

    def rerank(self, query: str, docs: List[Document]) -> List[Document]:
        if not docs:
            return docs
        pairs = [[query, doc.page_content] for doc in docs]
        scores = self.reranker.predict(pairs)
        scored = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored[: self.rerank_top_k]]

    def ask(self, question: str):
        if not question.strip():
            raise ValueError("Question must not be empty")
        # Get candidates from hybrid retriever
        candidate_docs = self.qa.retriever.invoke(question)
        ranked_docs = self.rerank(question, candidate_docs)
        if not ranked_docs:
            raise ValueError("No source documents were retrieved")

        # Build a temporary QA chain with reranked documents
        llm = self._get_llm()
        context = "\n\n".join([d.page_content for d in ranked_docs])
        prompt = (
            "Use the following context to answer the question.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )
        answer = llm.invoke(prompt).content
        return {"result": answer, "source_documents": ranked_docs}
