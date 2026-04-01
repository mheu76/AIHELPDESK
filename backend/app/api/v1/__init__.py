"""
API v1 routes.
"""
from fastapi import APIRouter
from app.api.v1 import auth, chat, kb, ticket

api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth.router)
api_router.include_router(chat.router)
api_router.include_router(kb.router)
api_router.include_router(ticket.router)
