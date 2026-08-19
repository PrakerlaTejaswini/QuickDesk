# QuickDesk – AI-Assisted Helpdesk

QuickDesk is an AI-assisted internal helpdesk application where employees can raise support tickets and agents can manage and resolve them. AI suggests ticket category and priority and generates knowledge-base-grounded replies using RAG, while the agent remains in control of the final response.

## Features

- JWT authentication with Employee and Agent roles
- bcrypt password hashing
- Employee ticket creation and ticket tracking
- AI-based category and priority suggestion
- Agent dashboard with search and filters
- LangChain RAG-based AI reply generation
- FAISS vector database
- Knowledge-base citations
- Agent override audit logs
- Real-time updates using WebSockets
- Agent metrics dashboard

## Tech Stack

- **Frontend:** React + TypeScript
- **Backend:** Python + FastAPI
- **Database:** PostgreSQL
- **LLM:** Groq
- **RAG:** LangChain + FAISS
- **Embeddings:** all-MiniLM-L6-v2
- **Authentication:** JWT + bcrypt
- **Real-time:** WebSockets

## Architecture

```text
Employee / Agent
       ↓
React + TypeScript
       ↓
FastAPI
   ┌───┴──────────────┐
   ↓                  ↓
PostgreSQL        AI Services
                      ↓
                Groq + LangChain
                      ↓
                    FAISS
                      ↓
              Knowledge Base
