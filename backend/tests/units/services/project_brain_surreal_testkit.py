from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

import httpx

from app.modules.ai.services.project_brain_memory_surreal import ProjectBrainSurrealConnectionConfig


class MockSurrealHttpServer:
    def __init__(self, *, namespace: str, database: str):
        self.namespace = namespace
        self.database = database
        self.tables: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        self.requests: list[httpx.Request] = []
        self.sql_payloads: list[str] = []

    def _statement(self, result: Any) -> httpx.Response:
        return httpx.Response(200, json=[{"status": "OK", "result": result, "time": "1ms"}])

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if request.url.path == "/health":
            return httpx.Response(200)

        if request.url.path == "/sql" and request.method == "POST":
            body = request.content.decode("utf-8")
            self.sql_payloads.append(body)
            statements = [item.strip() for item in body.split(";") if item.strip()]
            return httpx.Response(
                200,
                json=[{"status": "OK", "result": None, "time": "1ms"} for _ in statements],
            )

        if request.headers.get("Surreal-NS") != self.namespace:
            return httpx.Response(400, json={"detail": "bad namespace"})
        if request.headers.get("Surreal-DB") != self.database:
            return httpx.Response(400, json={"detail": "bad database"})

        path_parts = request.url.path.strip("/").split("/")
        if len(path_parts) < 2 or path_parts[0] != "key":
            return httpx.Response(404)

        table = path_parts[1]
        record_id = path_parts[2] if len(path_parts) > 2 else None

        if request.method == "GET":
            if record_id is None:
                return self._statement(list(self.tables[table].values()))
            record = self.tables[table].get(record_id)
            return self._statement([] if record is None else [record])

        if record_id is None:
            return httpx.Response(400, json={"detail": "record id required"})

        body = json.loads(request.content.decode("utf-8") or "{}")
        if request.method == "POST":
            stored = {"id": f"{table}:{record_id}", **body}
            self.tables[table][record_id] = stored
            return self._statement([stored])

        if request.method == "PUT":
            if record_id not in self.tables[table]:
                return httpx.Response(404)
            stored = {"id": f"{table}:{record_id}", **body}
            self.tables[table][record_id] = stored
            return self._statement([stored])

        if request.method == "DELETE":
            removed = self.tables[table].pop(record_id, None)
            return self._statement([] if removed is None else [removed])

        return httpx.Response(405)


def project_brain_surreal_test_config() -> ProjectBrainSurrealConnectionConfig:
    return ProjectBrainSurrealConnectionConfig(
        base_url="http://surreal.test",
        namespace="beingbijmantra",
        database="beingbijmantra_surrealdb",
        username="root",
        password="root",
    )
