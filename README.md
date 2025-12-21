# AI Voice Agent

A web application that enables non-technical administrators to configure, test, and analyze AI-powered voice calls for logistics dispatch operations.

## Overview

This application provides a simple and intuitive UI for three core administrative functions:
- **Configuring** the voice agent's prompts and conversation logic
- **Triggering** test calls to drivers with context (name, phone, load number)
- **Analyzing** structured results extracted from call transcripts

The system handles two primary scenarios:
1. **Dispatch Check-in** — Routine driver status updates (in-transit, arrived, delayed)
2. **Emergency Protocol** — Dynamic response to emergencies with immediate escalation

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│    Backend      │────▶│   Supabase      │
│  React + Vite   │     │    FastAPI      │     │   PostgreSQL    │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │ Retell   │ │ OpenAI   │ │ Webhook  │
              │   AI     │ │ GPT-4    │ │ Handler  │
              └──────────┘ └──────────┘ └──────────┘
```

### Tech Stack
- **Frontend:** React + TypeScript + Vite + TailwindCSS
- **Backend:** FastAPI + Python 3.11+
- **Database:** Supabase (PostgreSQL)
- **Voice AI:** Retell AI
- **LLM:** OpenAI GPT-4

### Project Structure

```
├── frontend/                 # React + TypeScript + Vite
│   └── src/
│       ├── components/       # Reusable UI components
│       ├── pages/            # Dashboard, Config, Results
│       ├── hooks/            # Custom React hooks
│       ├── services/         # API client
│       └── types/            # TypeScript interfaces
│
├── backend/                  # FastAPI + Python
│   └── app/
│       ├── api/              # REST endpoints
│       ├── webhooks/         # Retell webhook handlers
│       ├── services/         # Business logic, OpenAI
│       ├── models/           # Pydantic models
│       └── core/             # Config, state machine
│
├── supabase/                 # Database schema
│   └── schema.sql
│
└── docs/                     # Documentation
    └── AI_USAGE.md
```

## Retell AI Setup

[TODO: Add step-by-step Retell agent creation and configuration]

1. Create account at https://app.retellai.com
2. Create a new agent
3. Configure webhook URL
4. Copy API key and Agent ID to `.env`

## Local Development Setup

### Prerequisites
- Node.js 18+
- Python 3.11+
- Supabase account (https://app.supabase.com)
- Retell AI account (https://app.retellai.com)
- OpenAI API key (https://platform.openai.com)

### Environment Setup

```bash
# Copy environment template
cp .env.example .env
# Fill in your API keys and configuration
```

### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Database Setup

1. Create a new Supabase project
2. Go to SQL Editor in Supabase dashboard
3. Run the contents of `supabase/schema.sql`

## Testing

### Simulated Calls

[TODO: How to test without real calls using CALL_MODE=simulated]

### Real Calls (Web Calls for non-USA)

[TODO: Instructions for Retell web calls integration]

For users outside the USA, use Retell's Web Call feature instead of phone calls.

## Design Decisions

[TODO: Key architectural choices and tradeoffs]

## AI Usage Disclosure

See [AI_USAGE.md](./docs/AI_USAGE.md) for detailed breakdown of AI tools used in development.

## Demo

[TODO: Add Loom video link]

## Future Improvements

[TODO: List of potential enhancements]
