import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import UserEvent
from app.models.enums import EventType


class EventService:
    """Fire-and-forget immutable event recording.
    
    Every service that records a user action calls emit().
    Events are never modified or deleted.
    Phase 5 behavioral learning consumes these events retroactively.
    """

    @staticmethod
    async def emit(
        db: AsyncSession,
        user_id: uuid.UUID,
        event_type: EventType,
        entity_type: str,
        entity_id: uuid.UUID,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UserEvent:
        """Record an immutable behavioral event.
        
        Args:
            db: Database session
            user_id: The user who performed the action
            event_type: Type of event (from EventType enum)
            entity_type: Category of entity ("recipe", "meal", "ingredient", etc.)
            entity_id: UUID of the entity involved
            metadata: Optional JSON payload with event-specific data
            
        Returns:
            The created UserEvent
        """
        event = UserEvent(
            user_id=user_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_=metadata,
        )
        db.add(event)
        await db.flush()
        return event

    @staticmethod
    async def get_user_events(
        db: AsyncSession,
        user_id: uuid.UUID,
        event_types: Optional[List[EventType]] = None,
        entity_type: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[UserEvent]:
        """Query events for a user with optional filters.
        
        Args:
            db: Database session
            user_id: The user to query events for
            event_types: Optional filter by event type(s)
            entity_type: Optional filter by entity type
            since: Optional filter for events after this datetime
            limit: Max number of events to return (default 100)
            
        Returns:
            List of matching UserEvent records, newest first
        """
        stmt = (
            select(UserEvent)
            .where(UserEvent.user_id == user_id)
            .order_by(UserEvent.created_at.desc())
            .limit(limit)
        )
        
        if event_types:
            stmt = stmt.where(UserEvent.event_type.in_(event_types))
        if entity_type:
            stmt = stmt.where(UserEvent.entity_type == entity_type)
        if since:
            stmt = stmt.where(UserEvent.created_at >= since)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def count_user_events(
        db: AsyncSession,
        user_id: uuid.UUID,
        event_type: EventType,
        entity_type: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> int:
        """Count events for a user by type. Useful for behavioral thresholds."""
        from sqlalchemy import func as sa_func
        stmt = (
            select(sa_func.count())
            .select_from(UserEvent)
            .where(
                UserEvent.user_id == user_id,
                UserEvent.event_type == event_type,
            )
        )
        if entity_type:
            stmt = stmt.where(UserEvent.entity_type == entity_type)
        if since:
            stmt = stmt.where(UserEvent.created_at >= since)
        
        result = await db.execute(stmt)
        return result.scalar_one()
