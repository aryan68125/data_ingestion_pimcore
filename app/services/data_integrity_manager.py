"""
This file is responsible for making sure that pim-core callback url gets the exactly the same chunk with zero data loss
[PREVENTS]
- Partial trasmission of chunks over the network
- Proxy/body truncation 
- Corrupted JSON
- Duplicate chunk retry
- Out-of-order chunk
"""
import hashlib
import orjson
from typing import List, Dict, Any

# ort json parser
from app.utils.json_decimal_encoder import orjson_default

CANONICAL_OPTS = orjson.OPT_SORT_KEYS

class ChunkIntegrityManager:
    @staticmethod
    def canonical_dumps(obj) -> bytes:
        return orjson.dumps(
            obj,
            option=CANONICAL_OPTS,
            default=orjson_default
        )
    
    @staticmethod
    def compute_checksum(records: List[Dict[str, Any]]) -> str:
        """
        Computes deterministic checksum for a chunk.
        """
        payload_bytes = ChunkIntegrityManager.canonical_dumps(records)
        return hashlib.sha256(payload_bytes).hexdigest()

    @staticmethod
    def build_chunk_id(ingestion_id: str, chunk_number: int) -> str:
        """
        Unique identity for a chunk.
        """
        return f"{ingestion_id}:{chunk_number}"
