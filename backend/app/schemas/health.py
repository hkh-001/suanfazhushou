from pydantic import BaseModel


class HealthData(BaseModel):
    status: str
    service: str
    app_name: str
    environment: str


class HealthResponse(BaseModel):
    data: HealthData
