import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.services.ml_model import dwell_time_model
from app.services.telemetry import telemetry_simulator

logger = logging.getLogger(__name__)


def _retrain_in_background() -> None:
    """Promotes the model off the synthetic corpus once the gateway answers.

    Runs off the startup path deliberately: the gateway may still be booting,
    and a slot request must never wait on a training round.
    """
    try:
        dwell_time_model.retrain_from_history()
    except Exception as exc:
        logger.warning("Start-up retrain failed, keeping synthetic model: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    telemetry_simulator.start()
    threading.Thread(target=_retrain_in_background, daemon=True, name="model-warmup").start()
    yield
    telemetry_simulator.stop()


app = FastAPI(
    title="Navis-Lite Expert Decking Engine",
    description="Yard slot placement, weight-tier and reefer-routing rules, and telemetry simulation.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
