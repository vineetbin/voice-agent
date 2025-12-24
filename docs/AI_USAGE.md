# AI Usage Disclosure

This document details the AI tools and assistants used during the development of this project.

## Tools Used

### Cursor AI (Primary)
- **Purpose:** Code generation, debugging, and pair programming
- **Usage:** 
  - Initial project scaffolding and structure
  - React component development
  - FastAPI endpoint implementation
  - Database schema design
  - Type definitions and interfaces
  - Most code was AI-generated with manual review and refinement

### ChatGPT / Claude (Secondary)
- **Purpose:** Architecture decisions, documentation drafting, debugging assistance
- **Usage:**
  - Design pattern discussions (service layer, dependency injection)
  - README.md content structure
  - Prompt engineering for system prompts
  - Testing strategy planning

## What Was AI-Generated vs Manually Written

### AI-Generated (with manual edits and review)

**Frontend:**
- `frontend/src/pages/*.tsx` - All page components (ConfigurationPage, CallsPage, DashboardPage)
- `frontend/src/components/ui/*.tsx` - UI component library (Button, Card, Input, etc.)
- `frontend/src/hooks/*.ts` - Custom React hooks (useConfigs, useCalls, useRetellWebCall)
- `frontend/src/services/api.ts` - API client implementation
- `frontend/src/types/index.ts` - TypeScript type definitions

**Backend:**
- `backend/app/api/*.py` - All API endpoint implementations
- `backend/app/webhooks/*.py` - Webhook handlers
- `backend/app/services/*.py` - Service layer (retell.py, openai_service.py, post_processing.py, fallback_extraction.py)
- `backend/app/models/schemas.py` - Pydantic models
- `backend/app/core/*.py` - Core utilities (config.py, database.py, constants.py, state_machine.py)
- `backend/app/main.py` - FastAPI application setup

**Infrastructure:**
- `supabase/schema.sql` - Database schema
- `.env.example` - Environment variable template
- `README.md` - Documentation (structure and content)

## Verification

All AI-generated code was:
- ✅ Reviewed for correctness
- ✅ Tested for functionality
- ✅ Checked for security issues (no hardcoded secrets, proper validation)
- ✅ Verified against requirements
- ✅ Refactored for consistency and code quality
- ✅ Documented with clear comments and docstrings

## Code Quality Practices

- **Modularization:** Clear separation of concerns (API routes, services, models)
- **Type Safety:** Comprehensive TypeScript types and Pydantic models
- **Error Handling:** Graceful degradation and user-friendly error messages
- **Consistency:** Consistent naming conventions, file structure, and patterns
- **Documentation:** Docstrings, comments, and README documentation
