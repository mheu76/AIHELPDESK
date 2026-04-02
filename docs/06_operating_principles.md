# 06. Operating Principles

This document records the current operating assumptions for the system.

## Scope

The product is focused on internal IT helpdesk workflows:

- employee support chat
- internal knowledge base search
- ticket escalation and handling
- admin operations

Out-of-scope requests should not be treated as supported product requirements unless explicitly added.

## Retrieval and Response

1. User sends a chat message
2. Backend loads runtime settings from `system_settings`
3. If `rag_enabled=true`, KB search runs
4. If ChromaDB is available, vector search is used
5. Otherwise, fallback DB text matching is used
6. LLM response is generated with runtime `llm_model`, `llm_temperature`, and `max_tokens`

## Ticket Escalation

Ticket creation is currently user-initiated from chat sessions.

Current behavior:

- summarize the chat session
- categorize the issue
- create a sequential ticket number
- allow IT/admin follow-up through comments and status changes

Automatic ticket creation from failed AI resolution is not implemented yet.

## Admin Settings

Admin settings are now persistent:

- stored in `system_settings`
- applied to new runtime requests
- used by `get_llm()` and chat processing

## Operational Constraints

- Password hashing is still temporary and must be replaced before production use
- SSE chat streaming is not available
- Production monitoring and CI are not set up yet
