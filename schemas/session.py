# schemas/session.py
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class SessionCreate(BaseModel):
    title: Optional[str] = None

class SessionOut(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime