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
- **LLM:** OpenAI GPT-4o-mini

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

### 1. Create Retell AI Account
1. Sign up at https://app.retellai.com
2. Navigate to the Agents section

### 2. Create an Agent
1. Click "Create Agent"
2. Choose "Custom LLM" (Retell LLM)
3. Configure basic settings:
   - Agent Name: "Logistics Dispatch Agent"
   - Voice: Choose a natural-sounding voice
   - Language: English (US)

### 3. Configure Webhook
1. In your agent settings, go to "Webhooks"
2. Set webhook URL to: `https://your-domain.com/webhooks/retell` (use ngrok for local development)
3. Copy the webhook secret
4. Add it to your `.env` file as `RETELL_WEBHOOK_SECRET`

### 4. Get API Credentials
1. Go to API Keys section in Retell dashboard
2. Copy your API key → Add to `.env` as `RETELL_API_KEY`
3. Copy your Agent ID → Add to `.env` as `RETELL_AGENT_ID`

### 5. Phone Number (Optional - for phone calls)
1. Go to Phone Numbers section
2. Purchase/verify a phone number
3. Add it to `.env` as `RETELL_FROM_NUMBER` (E.164 format, e.g., +14157774444)
4. **Note:** For non-USA users, use web calls instead (no phone number needed)

## Local Development Setup

### Prerequisites
- Node.js 18+
- Python 3.11+
- Supabase account (https://app.supabase.com)
- Retell AI account (https://app.retellai.com)
- OpenAI API key (https://platform.openai.com)

### Environment Setup

1. **Copy environment template:**
```bash
cp .env.example .env
```

2. **Fill in your API keys and configuration in `.env`:**
   - Retell AI credentials (from setup above)
   - OpenAI API key
   - Supabase credentials (get these from Database Setup below)
   - Webhook URL (get this from Webhook Setup below)

### Database Setup

1. Create a new Supabase project at https://app.supabase.com
2. Go to SQL Editor in Supabase dashboard
3. Copy and paste the contents of `supabase/schema.sql`
4. Run the SQL to create all tables
5. Copy your Supabase credentials to `.env`:
   - `SUPABASE_URL` (from Project Settings → API)
   - `SUPABASE_ANON_KEY` (from Project Settings → API)
   - `SUPABASE_SERVICE_ROLE_KEY` (from Project Settings → API → service_role key)

### Webhook Setup (Local Development)

For local development, use ngrok to expose your backend:

```bash
# Install ngrok: https://ngrok.com/download
ngrok http 8000

# Copy the https URL (e.g., https://abc123.ngrok.io)
# Add it to Retell webhook settings as: https://abc123.ngrok.io/webhooks/retell
# Update BACKEND_URL in .env to match (e.g., BACKEND_URL=https://abc123.ngrok.io)
```

**Note:** You'll need to run ngrok before starting the backend server so that the webhook URL is available when Retell sends events.

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

The API will be available at `http://localhost:8000`. API documentation at `http://localhost:8000/docs`.

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

## Testing

### Web Calls

1. Start both backend and frontend servers
2. Navigate to "Configuration" page
3. Configure your agent prompts and voice settings
4. Click "Save & Sync to Retell"
5. Go to "Test Calls" page
6. Select "Web Call" option
7. Enter driver name and load number
8. Click "Start Test Call"
9. A browser-based call will start - speak into your microphone
10. After call ends, view structured results on the same page

### Phone Calls

1. Ensure `RETELL_FROM_NUMBER` is set in `.env`
2. Follow steps 1-5 from web calls above
3. Select "Phone Call" option
4. Enter driver name, phone number (E.164 format), and load number
5. Click "Start Test Call"
6. The agent will call the provided phone number
7. View results after call completes


## Design Decisions

### Singleton Pattern via Factory Functions

**Decision:** Used factory functions (`get_retell_service()`, `get_openai_service()`) with module-level singleton instances instead of global variables.

**Rationale:**
- Lazy initialization: Services created only when first requested
- Thread-safe: Module-level variables safe in FastAPI's async context
- Testable: Factory functions can be overridden in tests
- FastAPI integration: Works seamlessly with `Depends()` for dependency injection

### FastAPI Dependency Injection

**Decision:** Consistently used `Depends()` for all dependencies (database, services, settings) rather than importing directly.

**Rationale:**
- Testability: Can mock dependencies in tests by overriding `Depends()`
- Explicit dependencies: Makes function signatures clear about requirements
- Lifecycle management: FastAPI manages dependency lifecycle automatically
- Consistency: Uniform pattern across all endpoints

### Pydantic Models for Type Safety

**Decision:** All API inputs/outputs use Pydantic models that mirror the database schema exactly.

**Rationale:**
- Type safety: Compile-time validation catches errors early
- Auto documentation: FastAPI generates OpenAPI/Swagger docs from models
- Schema consistency: Models enforce API contracts match database structure
- Field validation: Built-in validators (e.g., `Field(ge=0.0, le=1.0)` for interruption sensitivity)

### Router Composition Pattern

**Decision:** Separated API routes (`/api/*`) from webhook routes (`/webhooks/*`) using `APIRouter` composition.

**Rationale:**
- Separation of concerns: Webhooks have different auth requirements (signature verification)
- Clear URLs: `/api/configs` vs `/webhooks/retell` indicates different purposes
- Modularity: Each router can be developed/tested independently

### LRU Cache for Settings

**Decision:** Used `@lru_cache` decorator for `get_settings()` and `get_supabase_client()` instead of module-level variables.

**Rationale:**
- Lazy loading: Settings loaded only when first accessed
- Testability: Cache can be cleared between tests
- Performance: Avoids re-parsing environment variables on every access

### Constants Centralization

**Decision:** Centralized all magic strings and configuration values in `constants.py` using `FrozenSet` for immutable collections.

**Rationale:**
- Single source of truth: Changing a constant updates all usages
- Type safety: `FrozenSet` prevents accidental mutations
- Consistency: Prevents typos and ensures same values used everywhere

### React Query Hooks Pattern

**Decision:** Custom hooks (`useConfigs`, `useCalls`) with React Query instead of direct API calls in components.

**Rationale:**
- Separation of concerns: Components don't handle data fetching logic
- Caching: React Query handles caching, invalidation, refetching automatically
- Query key factory: Centralized query keys (`configKeys`, `callKeys`) prevent cache collisions
- Reusability: Same hook used across multiple components

### Centralized API Client

**Decision:** Single axios instance with interceptors for all API calls instead of fetch calls scattered across components.

**Rationale:**
- Error handling: Centralized error transformation (axios errors → user-friendly messages)
- Configuration: Base URL, headers, timeout configured once
- Type safety: Typed API methods ensure request/response types match


## AI Usage Disclosure

See [AI_USAGE.md](./docs/AI_USAGE.md) for detailed breakdown of AI tools used in development.

## Demo

[Optional: Add Loom video link here demonstrating the application in action]

## Future Improvements

Potential enhancements for production use:
- Real-time transcript streaming during active calls
- Call recording playback
- Multi-tenant support with user authentication
- Analytics dashboard (call success rates, duration trends)
- Warm transfer to human dispatcher
- Advanced voice settings (voice selection, custom pronunciations)
- Full Retell agent management via UI (create/update/delete agents)
