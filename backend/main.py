
import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .api.routes import router
from .auth.router import router as auth_router
from .incidents.router import router as incidents_router
from .ml.model_loader import model_manager
from .simulator.network_simulator import simulator

logger = logging.getLogger(__name__)

app = FastAPI(title="AEGIS Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(auth_router)
app.include_router(incidents_router)

@app.on_event("startup")
async def startup_event():
    logger.info("AEGIS backend online — models loading...")
    model_manager.load_models()
    
    logger.info("Starting network simulator...")
    asyncio.create_task(simulator.run())
    
    logger.info("AEGIS backend online — models loaded, simulator running")
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
