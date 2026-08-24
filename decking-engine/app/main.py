from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.services.telemetry import telemetry_simulator


@asynccontextmanager
async def lifespan(app: FastAPI):
    telemetry_simulator.start()
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
