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



RAG Flow
Knowledge Base
      ↓
Chunking
      ↓
Embeddings
      ↓
FAISS
      ↓
Relevant Documents
      ↓
Groq LLM
      ↓
AI Draft Reply
      ↓
Agent Review
      ↓
Final Reply
Setup
Backend
cd backend
python -m venv quick
quick\Scripts\activate
pip install -r requirements.txt

Create .env:

DATABASE_URL=postgresql://postgres:password@localhost:5432/quickdesk
SECRET_KEY=your_secret_key
GROQ_API_KEY=your_groq_api_key

Run:

python seed.py
uvicorn app.main:app --reload

Backend: http://127.0.0.1:8000

Frontend
cd frontend
npm install
npm run dev

Frontend: http://localhost:5173

User Roles
Employee
Create tickets
View own tickets
Track ticket status
Agent
View all tickets
Search and filter tickets
Generate AI replies
Override AI suggestions
Reply and resolve tickets
View metrics
Security
JWT authentication
bcrypt password hashing
Backend role-based authorization
API keys stored in .env
.env and virtual environments excluded from Git
Repository

GitHub: https://github.com/PrakerlaTejaswini/QuickDesk

Demo

Add the demo video link here after recording.

Future Improvements
AI confidence score
Automated tests
Docker deployment
Email notifications
Advanced monitoring
