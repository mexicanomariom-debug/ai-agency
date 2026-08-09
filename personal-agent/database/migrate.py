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
    "digest_enabled": "BOOLEAN DEFAULT 1",
    "digest_hour": "INTEGER DEFAULT 8",
    "digest_last_sent": "VARCHAR(10)",
    "pulse_enabled": "BOOLEAN DEFAULT 1",
    "pulse_last_hour": "VARCHAR(13)",
    "ambient_enabled": "BOOLEAN DEFAULT 1",
    "night_enabled": "BOOLEAN DEFAULT 1",
    "night_hour": "INTEGER DEFAULT 21",
    "night_last_sent": "VARCHAR(10)",
    "traffic_enabled": "BOOLEAN DEFAULT 0",
    "traffic_origin": "TEXT",
    "traffic_destination": "TEXT",
    "traffic_threshold_min": "INTEGER DEFAULT 15",
    "traffic_check_start": "VARCHAR(5)",
    "traffic_check_end": "VARCHAR(5)",
    "traffic_last_alert": "VARCHAR(16)",
    "traffic_provider": "VARCHAR(16)",
    "traffic_mode": "VARCHAR(16)",
}

TASK_COLUMNS = {
    "notify_phone": "BOOLEAN DEFAULT 0",
    "google_event_id": "VARCHAR(255)",
    "recurrence_rule": "VARCHAR(32)",
}

RECON_SOURCE_COLUMNS = {
    "filter_query": "TEXT",
    "keywords": "TEXT",
    "last_seen_item_ids": "TEXT",
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

            if "recon_sources" not in tables:
                sync_conn.execute(
                    text(
                        """
                        CREATE TABLE recon_sources (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                            source_type VARCHAR(32) NOT NULL,
                            url_or_handle TEXT NOT NULL,
                            label VARCHAR(255),
                            enabled BOOLEAN DEFAULT 1,
                            verify_enabled BOOLEAN DEFAULT 1,
                            check_interval_min INTEGER DEFAULT 60,
                            last_checked_at DATETIME,
                            last_content_hash VARCHAR(64),
                            last_preview TEXT,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                        """
                    )
                )
                sync_conn.execute(text("CREATE INDEX ix_recon_sources_user_id ON recon_sources (user_id)"))
                logger.info("Created table recon_sources")

            if "recon_events" not in tables:
                sync_conn.execute(
                    text(
                        """
                        CREATE TABLE recon_events (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            source_id INTEGER NOT NULL REFERENCES recon_sources(id) ON DELETE CASCADE,
                            detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            title VARCHAR(500),
                            excerpt TEXT,
                            verdict VARCHAR(32),
                            confidence REAL,
                            summary TEXT,
                            notified BOOLEAN DEFAULT 0
                        )
                        """
                    )
                )
                sync_conn.execute(text("CREATE INDEX ix_recon_events_source_id ON recon_events (source_id)"))
                logger.info("Created table recon_events")

            if "recon_sources" in tables:
                existing = {c["name"] for c in inspector.get_columns("recon_sources")}
                for name, ddl in RECON_SOURCE_COLUMNS.items():
                    if name not in existing:
                        sync_conn.execute(text(f"ALTER TABLE recon_sources ADD COLUMN {name} {ddl}"))
                        logger.info("Added column recon_sources.%s", name)

        await conn.run_sync(_migrate)
