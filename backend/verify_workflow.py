"""Exercise the offline HTTP workflow with isolated storage."""
import json
import os
import tempfile
from pathlib import Path


def main():
    with tempfile.TemporaryDirectory(prefix="analyst-smoke-") as directory:
        root = Path(directory)
        os.environ.update(AI_PROVIDER="offline", DATABASE_URL=f"sqlite+aiosqlite:///{root / 'test.db'}",
                          DATA_DIR=str(root), UPLOAD_DIR=str(root / "uploads"), DUCKDB_DIR=str(root / "duckdb"))
        from fastapi.testclient import TestClient
        from app.main import app
        from app.tools.duckdb_tool import duckdb_tool
        with TestClient(app) as client:
            csv = b"category,revenue\nA,10\nA,20\nB,40\nB,5\n"
            uploaded = client.post("/api/v1/datasets/upload", files={"file": ("sales.csv", csv, "text/csv")})
            assert uploaded.status_code == 200, uploaded.text
            dataset = uploaded.json()
            did = dataset["id"]
            session = client.post("/api/v1/analyst/sessions", params={"dataset_id": did})
            assert session.status_code == 200, session.text
            sid = session.json()["id"]
            params = {"dataset_id": did, "session_id": sid, "query": "Compare total revenue by category"}
            response = client.get("/api/v1/analyst/stream", params=params)
            assert response.status_code == 200, response.text
            events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
            assert any(e.get("event") == "workflow_finished" for e in events), events
            history = client.get(f"/api/v1/analyst/sessions/{sid}")
            assert history.status_code == 200, history.text
            assert len(history.json()["messages"]) == 2, history.text
            missing = client.get("/api/v1/analyst/stream", params={**params, "session_id": "missing"})
            assert missing.status_code == 404, missing.text
            other = client.post("/api/v1/datasets/upload", files={"file": ("other.csv", csv, "text/csv")})
            assert other.status_code == 200, other.text
            mismatch = client.get("/api/v1/analyst/stream", params={**params, "dataset_id": other.json()["id"]})
            assert mismatch.status_code == 400, mismatch.text
            print("PASS: upload, offline analysis stream, saved history, session validation")
        # DuckDB owns file handles until explicitly closed on Windows.
        if hasattr(duckdb_tool, "conn"):
            duckdb_tool.conn.close()


if __name__ == "__main__":
    main()
