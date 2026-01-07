import pandas as pd
import fsspec
from typing import List, Dict, Tuple

class JsonIngestionService:
    # This method is capable of reading multiple files from the folder [with read pagination]
    def read_paginated(self,path:str, page:int, page_size:int) -> Tuple[List[Dict],int, List[pd.DataFrame]]:
        """
        Stream JSON files from a file or dictonary and return : 
        - Paginated records 
        - Total row counts
        """
        fs, _, paths = fsspec.get_fs_token_paths(path)

        offset = (page - 1) * page_size
        limit = page_size

        # page records
        collected : List[Dict] = []
        # Ro-level dataframes for memory calculations
        collected_dfs: List[pd.DataFrame] = []
        # global row counter
        current_index = 0
        # count all rows access all files
        total_rows = 0

        # find all the files in a directory via looping
        for base_path in paths:
            files = (
                fs.glob(f"{base_path.rstrip('/')}/**/*.json")
                if fs.isdir(base_path)
                else [base_path]
            )

            for file in files:
                # read each file inside the current directory
                with fs.open(file,'r') as f:
                    df = pd.read_json(f,orient="records",dtype=False)

                # record level streaming loop
                records = df.to_dict(orient="records")

                for idx, record in enumerate(records):
                    # always count total rows
                    total_rows += 1
                    
                    # Skip until offset
                    if current_index < offset:
                        current_index += 1
                        continue 

                    # Collect page data 
                    if len(collected) < limit:
                        collected.append(record)
                        collected_dfs.append(df.iloc[[idx]])
                        current_index += 1
                    else:
                        # page is full --> stop early
                        return collected, total_rows, collected_dfs                   
        return collected, total_rows, collected_dfs
