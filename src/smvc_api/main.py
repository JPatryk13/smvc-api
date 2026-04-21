"""FastAPI entrypoint: health, user sync, admin pipeline (bridge plan)."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from smvc_api.auth.deps import require_admin_api_key, require_user_bearer_token
from smvc_api.config import get_settings
from smvc_api.logging_config import configure_logging
from smvc_api.models.pipeline import AdminPipelineRunRequest, PipelineSummary


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    yield


app = FastAPI(title="smvc-api", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/sync", dependencies=[Depends(require_user_bearer_token)])
def user_sync() -> PipelineSummary:
    return PipelineSummary()


@app.post("/admin/v1/pipeline/run", dependencies=[Depends(require_admin_api_key)])
def admin_pipeline_run(_body: AdminPipelineRunRequest) -> PipelineSummary:
    return PipelineSummary()
