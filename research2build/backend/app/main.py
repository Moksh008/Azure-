from fastapi import FastAPI
from shared.schemas import HealthResponse

app = FastAPI(title="Research2Build API", version="0.1.0")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="research2build-api")
