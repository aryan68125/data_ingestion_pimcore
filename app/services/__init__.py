from app.services.excel_reader import ExcelIngestionService
from app.services.memory_monitoring import DataFrameMemoryService
from app.services.json_reader import JsonIngestionService
class IngestionController:
    def __init__(self):
        self.json_ingestion_service = JsonIngestionService()
        self.excel_ingestion_service = ExcelIngestionService()
        self.memory_service = DataFrameMemoryService()
