import pandas as pd

class JsonIngestionService:
    def read(self, file_path: str) -> list[dict]:
        """
        Reads a JSON file and returns list of records
        """
        df = pd.read_json(file_path)

        # Convert DataFrame → list of dicts
        return df.to_dict(orient="records")
