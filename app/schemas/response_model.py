from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional 

class IngestResponse(BaseModel):
    status: int
    error: Optional[str] = None
    rows: int = 0
    data: List[Dict[str, Any]] = Field(default_factory=list)
