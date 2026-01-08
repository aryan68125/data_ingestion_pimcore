import pandas as pd
import ijson
import fsspec
from typing import List, Dict, Tuple, Optional



import httpx
import orjson

class JsonIngestionService:
    # This method is capable of reading multiple files from the folder [with read pagination] [old logic : without the support for chunk_size_by_memory]
    # def read_paginated(self,path:str, page:int, chunk_size_by_records:int) -> Tuple[List[Dict],int, List[pd.DataFrame]]:
    #     """
    #     Stream JSON files from a file or dictonary and return : 
    #     - Paginated records 
    #     - Total row counts
    #     """
    #     fs, _, paths = fsspec.get_fs_token_paths(path)

    #     offset = (page - 1) * chunk_size_by_records
    #     limit = chunk_size_by_records

    #     # page records
    #     collected : List[Dict] = []
    #     # Ro-level dataframes for memory calculations
    #     collected_dfs: List[pd.DataFrame] = []
    #     # global row counter
    #     current_index = 0
    #     # count all rows access all files
    #     total_rows = 0

    #     # find all the files in a directory via looping
    #     for base_path in paths:
    #         files = (
    #             fs.glob(f"{base_path.rstrip('/')}/**/*.json")
    #             if fs.isdir(base_path)
    #             else [base_path]
    #         )

    #         for file in files:
    #             # read each file inside the current directory
    #             with fs.open(file,'r') as f:
    #                 df = pd.read_json(f,orient="records",dtype=False)

    #             # record level streaming loop
    #             records = df.to_dict(orient="records")

    #             for idx, record in enumerate(records):
    #                 # always count total rows
    #                 total_rows += 1
                    
    #                 # Skip until offset
    #                 if current_index < offset:
    #                     current_index += 1
    #                     continue 

    #                 # Collect page data 
    #                 if len(collected) < limit:
    #                     collected.append(record)
    #                     collected_dfs.append(df.iloc[[idx]])
    #                     current_index += 1
    #                 else:
    #                     # page is full --> stop early
    #                     return collected, total_rows, collected_dfs                   
    #     return collected, total_rows, collected_dfs

    # This method is capable of reading multiple files from the folder with read pagination [with chunk_size_by_memory support]
    # [old code remove]
    """
    When chunk_size_by_memory is supplied this method will automatically determine the number of rows each chunk must have 
    """
    # def read_paginated(
    #     self,
    #     path: str,
    #     page: int,
    #     chunk_size_by_records: Optional[int] = None,
    #     chunk_size_by_memory: Optional[int] = None
    # ) -> Tuple[List[Dict], int, List[pd.DataFrame]]:

    #     fs, _, paths = fsspec.get_fs_token_paths(path)

    #     collected: List[Dict] = []
    #     collected_dfs: List[pd.DataFrame] = []

    #     current_index = 0
    #     total_rows = 0
    #     current_memory_bytes = 0

    #     for base_path in paths:
    #         files = (
    #             fs.glob(f"{base_path.rstrip('/')}/**/*.json")
    #             if fs.isdir(base_path)
    #             else [base_path]
    #         )

    #         for file in files:
    #             with fs.open(file, "rb") as f:
    #                 # STREAM objects inside JSON array
    #                 for record in ijson.items(f, "item"):
    #                     total_rows += 1

    #                     # Pagination (record-based)
    #                     if chunk_size_by_records and current_index < (page - 1) * chunk_size_by_records:
    #                         current_index += 1
    #                         continue

    #                     record_df = pd.DataFrame([record])
    #                     record_memory = record_df.memory_usage(deep=True).sum()

    #                     # Stop conditions
    #                     if chunk_size_by_records and len(collected) >= chunk_size_by_records:
    #                         return collected, total_rows, collected_dfs

    #                     if chunk_size_by_memory and current_memory_bytes + record_memory > chunk_size_by_memory:
    #                         return collected, total_rows, collected_dfs

    #                     collected.append(record)
    #                     collected_dfs.append(record_df)
    #                     current_memory_bytes += record_memory
    #                     current_index += 1

    #     return collected, total_rows, collected_dfs


    """
    This method will read json using read stream method
    """
    async def stream_and_push(self, ingestion_id: str, request):
        fs, _, paths = fsspec.get_fs_token_paths(request.file_path)

        chunk = []
        chunk_bytes = 0
        chunk_number = 0
        total_records = 0

        async with httpx.AsyncClient(timeout=60) as client:
            for base_path in paths:
                files = (
                    fs.glob(f"{base_path.rstrip('/')}/**/*.json")
                    if fs.isdir(base_path)
                    else [base_path]
                )

                for file in files:
                    with fs.open(file, "rb") as f:
                        for record in ijson.items(f, "item"):
                            record_bytes = len(orjson.dumps(record, default=orjson_default)

)

                            if self._should_flush(
                                request,
                                chunk,
                                chunk_bytes,
                                record_bytes
                            ):
                                await self._send_chunk(
                                    client,
                                    request.callback_url,
                                    ingestion_id,
                                    chunk_number,
                                    chunk,
                                    False
                                )
                                chunk_number += 1
                                chunk.clear()
                                chunk_bytes = 0

                            chunk.append(record)
                            chunk_bytes += record_bytes
                            total_records += 1

            # Final chunk
            if chunk:
                await self._send_chunk(
                    client,
                    request.callback_url,
                    ingestion_id,
                    chunk_number,
                    chunk,
                    True
                )

            # Completion event
            await client.post(
                request.callback_url,
                json={
                    "ingestion_id": ingestion_id,
                    "status": "COMPLETED",
                    "total_records": total_records
                }
            )

    def _should_flush(self, request, chunk, chunk_bytes, next_record_bytes):
        if request.chunk_size_by_records:
            return len(chunk) >= request.chunk_size_by_records
        return (chunk_bytes + next_record_bytes) > request.chunk_size_by_memory

    async def _send_chunk(
        self,
        client,
        url,
        ingestion_id,
        chunk_number,
        records,
        is_last
    ):
        payload = {
            "ingestion_id": ingestion_id,
            "chunk_number": chunk_number,
            "records": records,
            "is_last": is_last
        }

        for attempt in range(3):
            try:
                resp = await client.post(
                    url,
                    content=orjson.dumps(payload, default=orjson_default),
                    headers={"Content-Type": "application/json"}
                )
                resp.raise_for_status()
                return
            except Exception:
                if attempt == 2:
                    raise

# json decimal encoder
"""
This function allows us to parse the decimal values in json files 
"""
import decimal
def orjson_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)   # OR: return str(obj)
    raise TypeError
