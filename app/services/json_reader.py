import pandas as pd
import fsspec
from typing import List, Dict

class JsonIngestionService:
    # This method is only capable of reading one file at a time [old logic]
    # def read(self, file_path: str) -> list[dict]:
    #     """
    #     Reads a JSON file and returns list of records
    #     """
    #     df = pd.read_json(file_path)

    #     # Convert DataFrame → list of dicts
    #     return df.to_dict(orient="records")
    
    # This method is capable of reading multiple files from the folder [without read pagination]
    def read(self, path:str) -> List[Dict]:
        """
        Read JSON file(s) from a file or directory (local or cloud) and returns combined list of records.
        """
        fs, _, paths = fsspec.get_fs_token_paths(path)
        all_records : list[dict] = []

        for path in paths:
            if fs.isdir(path):
                # Read all JSON files inside this directory
                files = fs.glob(f"{path.rstrip('/')}/**/*.json")
            else:
                files = [path]
            
            for file in files:
                with fs.open(file,"r") as f:
                    df = pd.read_json(f)
                    all_records.extend(df.to_dict(orient="records"))
        if not all_records:
            raise ValueError("No JSON files found in the given path")
        
        return all_records
    

    # This method is capable of reading multiple files from the folder [with read pagination]
    
