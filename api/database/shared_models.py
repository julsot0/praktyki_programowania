from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid

class ImageURL(BaseModel):
    url: str
    callback_url: Optional[str] = None

class ImageTask(BaseModel):
    task_id: str = str(uuid.uuid4())
    image_url: str
    created_at: datetime = datetime.now()
    status: str = "pending"
    result: Optional[int] = None
    error: Optional[str] = None