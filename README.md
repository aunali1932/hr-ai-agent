# HR AI Agent MVP

An intelligent HR assistant built with FastAPI, React, LangGraph, and Google Gemini. The agent can answer questions about company HR policies using RAG (Retrieval Augmented Generation) and process leave requests through natural conversation.

## Architecture Overview

```
┌─────────────┐
│   React     │
│  Frontend   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   FastAPI   │
│   Backend   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  LangGraph  │
│ Orchestrator│
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
   ▼       ▼
┌─────┐ ┌──────────┐
│ RAG │ │  Tool    │
│     │ │ Calling  │
└──┬──┘ └────┬─────┘
   │         │
   ▼         ▼
┌──────┐ ┌──────────┐
│Qdrant│ │PostgreSQL│
└──────┘ └──────────┘
```

## Features

- **Policy Q&A**: Ask questions about HR policies using RAG with Qdrant vector database
- **Leave Request Processing**: Create leave requests through natural conversation using LangGraph tool calling
- **Role-Based Access**: Separate interfaces for HR and employees
- **HR Dashboard**: View and approve/reject leave requests
- **Intent Classification**: Automatically routes queries to appropriate handlers

## Tech Stack

### Backend
- **FastAPI**: Python web framework
- **LangGraph**: Stateful workflow orchestration
- **Google Gemini**: LLM for chat and embeddings
- **Qdrant**: Vector database for RAG
- **PostgreSQL**: Relational database
- **Alembic**: Database migrations
- **SQLAlchemy**: ORM

### Frontend
- **React**: UI framework
- **Tailwind CSS**: Styling
- **Vite**: Build tool
- **React Router**: Routing
- **Axios**: HTTP client

## Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 12+
- Qdrant (can run embedded or as a service)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/aunali1932/hr-ai-agent
cd hr-ai-agent
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp env.example .env
# Edit .env and fill in all required variables:
# - DATABASE_URL (PostgreSQL connection string)
# - GEMINI_API_KEY (from Google AI Studio: https://makersuite.google.com/app/apikey)
# - SECRET_KEY (generate using: python -c "import secrets; print(secrets.token_urlsafe(32))")
# - QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION_NAME
# - ALGORITHM (default: HS256)
# - CORS_ORIGINS (comma-separated list of allowed origins)

# Set up Alembic migrations (see backend/ALEMBIC_SETUP.md for detailed guide)
# Step 1: Create the database
# psql -U postgres -c "CREATE DATABASE hr_ai_agent;" or through pg admin


# Step 2: Apply the migration
alembic upgrade head

# Seed sample users
python -m app.seeds.seed_users

# Initialize Qdrant and ingest policies
python -c "from app.services.rag_service import ingest_policy_documents; ingest_policy_documents()"

# Start the server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 4. Qdrant Setup

#### Option 1: Embedded Mode (Local Development)
Qdrant will run embedded in the Python process. No additional setup needed.

#### Option 2: Qdrant Cloud (Recommended)
Just paste your Qdrant Cloud host and API key in the env

## Default Test Credentials

- **HR User**: 
  - Email: `hr@company.com`
  - Password: `hr123456`

- **Employee Users**:
  - Email: `john.employee@company.com` or `jane.employee@company.com`
  - Password: `employee123`

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login with email/password
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/logout` - Logout

### Chat
- `POST /api/chat` - Send message to HR agent
  - Request: `{ "message": "string", "session_id": "uuid?", "user_id": "int" }`
  - Response: `{ "response": "string", "intent": "string", "data": {...}, "session_id": "uuid" }`

### HR Requests
- `GET /api/requests` - Get current user's requests
- `GET /api/requests/all` - Get all requests (HR only)
- `PATCH /api/requests/{id}/approve` - Approve request (HR only)
- `PATCH /api/requests/{id}/reject` - Reject request (HR only)

## LangGraph Workflow

The chat system uses LangGraph for orchestration:

1. **Intent Classifier Node**: Classifies user message as `policy_question` or `leave_request`
2. **Policy Q&A Node**: Uses RAG to retrieve relevant policy chunks and generate answer
3. **Leave Request Tool Node**: Extracts leave details and creates request in database

### State Flow

```python
ChatState {
    message: str
    user_id: int
    intent: Optional[str]  # "policy_question" or "leave_request"
    context: Optional[str]  # RAG context for policy questions
    tool_result: Optional[dict]  # Result from leave request tool
    response: str  # Final response to user
}
```

## Sample Queries

### Policy Questions
- "What is the work from home policy?"
- "How many sick days do I get per year?"
- "What are the benefits?"
- "Tell me about the leave policy"

### Leave Requests
- "I need to take leave tomorrow"
- "Apply for annual leave from January 1st to January 5th"
- "I need a sick day on Friday"
- "Request 2 days of leave next week"

## Project Structure

```
hr-ai-agent/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── graphs/       # LangGraph workflows
│   │   │   ├── nodes/    # Graph nodes
│   │   │   └── tools/    # LangGraph tools
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   ├── data/         # HR policy documents
│   │   └── seeds/        # Database seeds
│   ├── alembic/          # Database migrations
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/   # React components
    │   ├── services/     # API clients
    │   └── context/      # React context
    └── package.json
```

## Assumptions and Design Decisions


1. **Policy Format**: Plain text (.txt) files for simplicity
2. **Roles**: Two roles only - "HR" and "employee"
3. **Request Approval**: Manual approval by HR users via dashboard
4. **No Email Notifications**: Approval status visible only in UI for this assesment

## Future Enhancements

- OAuth/SSO integration (Google, Microsoft)
- Email notifications for request status changes
- Real-time updates using WebSockets
- Advanced analytics dashboard (leave trends, policy usage)
- Multi-language support
- Voice input/output for accessibility
- Export reports (PDF, Excel)
- Multi-tenancy for different companies

## Troubleshooting

### Qdrant Connection Issues
- Ensure Qdrant is running on the configured host/port
- Check `QDRANT_HOST` and `QDRANT_PORT` in `.env`

### Database Connection Issues
- Verify PostgreSQL is running
- Check `DATABASE_URL` in `.env`
- Ensure database exists: `CREATE DATABASE hr_ai_agent;`

### Gemini API Issues
- Verify `GEMINI_API_KEY` is set correctly
- Check API quota/limits in Google AI Studio

### Frontend Not Connecting
- Ensure backend is running on port 8000
- Check CORS settings in `backend/app/config.py`
- Verify proxy settings in `frontend/vite.config.js`

## License

This project is for assessment purposes.



