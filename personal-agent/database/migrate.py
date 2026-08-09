from __future__ import annotations

import logging

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)

USER_COLUMNS = {
    "phone_number": "VARCHAR(32)",
    "google_refresh_token": "TEXT",
    "google_calendar_enabled": "BOOLEAN DEFAULT 0",
    "translate_target_lang": "VARCHAR(8) DEFAULT 'en'",
}

TASK_COLUMNS = {
    "notify_phone": "BOOLEAN DEFAULT 0",
    "google_event_id": "VARCHAR(255)",
}


async def migrate(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        def _migrate(sync_conn) -> None:
            inspector = inspect(sync_conn)
            tables = inspector.get_table_names()

            if "users" in tables:
                existing = {c["name"] for c in inspector.get_columns("users")}
                for name, ddl in USER_COLUMNS.items():
                    if name not in existing:
                        sync_conn.execute(text(f"ALTER TABLE users ADD COLUMN {name} {ddl}"))
                        logger.info("Added column users.%s", name)

            if "tasks" in tables:
                existing = {c["name"] for c in inspector.get_columns("tasks")}
                for name, ddl in TASK_COLUMNS.items():
                    if name not in existing:
                        sync_conn.execute(text(f"ALTER TABLE tasks ADD COLUMN {name} {ddl}"))
                        logger.info("Added column tasks.%s", name)

        await conn.run_sync(_migrate)
