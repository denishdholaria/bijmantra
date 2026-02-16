"""Mock BrAPI server used by compliance and integration tests."""

from __future__ import annotations

from fastapi import FastAPI


app = FastAPI(title="BrAPI Mock Server", version="2.1")


def _ok(result):
    return {
        "metadata": {
            "pagination": {"currentPage": 0, "pageSize": 1000, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Success", "messageType": "INFO"}],
            "datafiles": [],
        },
        "result": result,
    }


@app.get("/brapi/v2/serverinfo")
def serverinfo():
    return _ok(
        {
            "serverName": "Mock BrAPI",
            "organizationName": "Bijmantra Test Harness",
            "calls": [
                {"service": "serverinfo", "method": "GET", "contentTypes": ["application/json"]},
                {"service": "programs", "method": "GET", "contentTypes": ["application/json"]},
                {"service": "studies", "method": "GET", "contentTypes": ["application/json"]},
            ],
        }
    )


@app.get("/brapi/v2/programs")
def programs():
    return _ok({"data": [{"programDbId": "P-1", "programName": "Mock Program"}]})


@app.get("/brapi/v2/studies")
def studies():
    return _ok({"data": [{"studyDbId": "S-1", "studyName": "Mock Study"}]})
