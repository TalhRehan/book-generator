"""Supabase data-access helpers and shared client initialization."""

from supabase import create_client, Client
from fastapi_service.core.config import settings
from typing import Any

_client: Client | None = None


def get_client() -> Client:
    """Get client."""
    global _client
    if _client is None:
        _client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    return _client


def insert(table: str, data: dict) -> dict:
    """Insert."""
    response = get_client().table(table).insert(data).execute()
    return response.data[0] if response.data else {}


def fetch_one(table: str, filters: dict) -> dict | None:
    """Fetch one."""
    response = (
        get_client()
        .table(table)
        .select("*")
        .match(filters)   
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def fetch_many(
    table: str,
    filters: dict | None = None,
    order_by: str | None = None
) -> list:
    """Fetch many."""
    query = get_client().table(table).select("*")

    if filters:
        query = query.match(filters)  

    if order_by:
        query = query.order(order_by)

    response = query.execute()
    return response.data if response.data else []


def update(table: str, filters: dict, data: dict) -> dict:
    """Update."""
    response = (
        get_client()
        .table(table)
        .update(data)
        .match(filters)   
        .execute()
    )
    return response.data[0] if response.data else {}
