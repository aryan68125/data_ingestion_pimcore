import requests


def test_excel_ingestion_smoke():
    response = requests.post(
        "http://localhost:8000/api/ingest",
        json={
            "file_type": "excel",
            "file_path": "tests/excel/resources/sample.xlsx",
            "chunk_size_by_records": 5,
            "callback_url": "http://localhost:9000/callback"
        }
    )

    assert response.status_code == 200
    body = response.json()
    assert "ingestion_id" in body
