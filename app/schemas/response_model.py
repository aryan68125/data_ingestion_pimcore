from pydantic import BaseModel, Field
from typing import List, Dict, Any

class IngestResponse(BaseModel):
    rows: int  = Field(default=0)
    data: List[Dict[str, Any]] = Field(default=[])
