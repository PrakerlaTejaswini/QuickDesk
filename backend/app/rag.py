from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_huggingface import HuggingFaceEmbeddings

from langchain_community.vectorstores import FAISS

from .config import settings


KB_DIR = Path(__file__).parent / "kb"


class RAGEngine:

    def __init__(self):

        self.documents = []

        self.vectorstore = None

        self._load_knowledge_base()

    def _load_knowledge_base(self):

        for file_path in KB_DIR.glob("*.md"):

            text = file_path.read_text(
                encoding="utf-8"
            )

            self.documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": file_path.name
                    }
                )
            )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=80
        )

        chunks = splitter.split_documents(
            self.documents
        )

        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        self.vectorstore = FAISS.from_documents(
            chunks,
            embeddings
        )

    def search(
        self,
        query: str,
        k: int = 3
    ):

        if not self.vectorstore:
            return []

        return self.vectorstore.similarity_search(
            query,
            k=k
        )

    def generate_draft(
        self,
        title: str,
        description: str
    ):

        docs = self.search(
            f"{title} {description}",
            k=3
        )

        if not docs:

            return {
                "draft": (
                    "I could not find a relevant "
                    "knowledge base article for this request. "
                    "An agent should review the ticket manually."
                ),
                "citations": []
            }

        context = "\n\n".join(
            doc.page_content
            for doc in docs
        )

        citations = list(
            dict.fromkeys(
                doc.metadata.get("source")
                for doc in docs
            )
        )

        if not settings.GROQ_API_KEY:

            return {
                "draft": (
                    "Thanks for reporting this issue. "
                    "Please review the relevant internal "
                    "knowledge-base guidance and contact "
                    "the appropriate support team if the "
                    "issue continues."
                ),
                "citations": citations
            }

        try:

            from groq import Groq

            client = Groq(
                api_key=settings.GROQ_API_KEY
            )

            prompt = f"""
You are an internal helpdesk assistant.

Answer the employee's ticket using ONLY
the supplied knowledge base.

If the knowledge base does not contain enough
information, explicitly say that the knowledge
base does not contain enough information.

Do not invent policies.

Ticket:
Title: {title}
Description: {description}

Knowledge Base:
{context}

Write a concise professional response
that an agent can review and send.
"""

            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2
            )

            draft = (
                response
                .choices[0]
                .message
                .content
            )

            return {
                "draft": draft,
                "citations": citations
            }

        except Exception:

            return {
                "draft": (
                    "The AI service is currently unavailable. "
                    "Please review the knowledge-base article "
                    "manually before responding."
                ),
                "citations": citations
            }


rag_engine = RAGEngine()