import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class DigitalTwinBase(BaseModel):
    user_id: uuid.UUID
    knowledge_state: Dict[str, Any]
    memory_state: Dict[str, Any]
    practice_state: Dict[str, Any]
    writing_state: Dict[str, Any]
    behaviour_state: Dict[str, Any]
    learning_profile: Dict[str, Any]
    knowledge_readiness: float
    memory_readiness: float
    practice_readiness: float
    writing_readiness: float
    behaviour_readiness: float

class DigitalTwinResponse(DigitalTwinBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class StudentEventPayload(BaseModel):
    event_type: str
    payload: Dict[str, Any]
