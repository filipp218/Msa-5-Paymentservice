import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel, Field
from pyzeebe import ZeebeClient, ZeebeWorker, create_insecure_channel

from workers import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("payment-orchestrator")

ZEEBE_ADDRESS = os.getenv("ZEEBE_ADDRESS", "localhost:26500")
PROCESS_ID = "PaymentSagaProcess"


class StartPaymentRequest(BaseModel):
    fraudDecision: str = Field(default="allow", pattern="^(allow|deny|manual)$")
    manualDecision: str = Field(default="approved", pattern="^(approved|denied)$")
    amount: int = Field(default=1000, ge=1)
    simulateTransferFailure: bool = False


class StartPaymentResponse(BaseModel):
    processInstanceKey: int
    fraudDecision: str
    manualDecision: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Connecting to Zeebe at %s", ZEEBE_ADDRESS)
    channel = create_insecure_channel(ZEEBE_ADDRESS)
    worker = ZeebeWorker(channel)
    worker.include_router(router)
    app.state.zeebe_client = ZeebeClient(channel)

    worker_task = asyncio.create_task(worker.work())
    logger.info("Zeebe worker started")

    yield

    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    logger.info("Zeebe worker stopped")


app = FastAPI(title="OrchestrPay Payment Orchestrator", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/payments/start", response_model=StartPaymentResponse)
async def start_payment(request: StartPaymentRequest) -> StartPaymentResponse:
    notify_security = request.fraudDecision == "deny" or (
        request.fraudDecision == "manual" and request.manualDecision == "denied"
    )
    variables = {
        "fraudDecision": request.fraudDecision,
        "manualDecision": request.manualDecision,
        "amount": request.amount,
        "transferFailed": False,
        "notifySecurity": notify_security,
        "simulateTransferFailure": request.simulateTransferFailure,
    }
    logger.info("Starting process %s with variables %s", PROCESS_ID, variables)

    client: ZeebeClient = app.state.zeebe_client
    result = await client.run_process(
        bpmn_process_id=PROCESS_ID,
        variables=variables,
    )

    return StartPaymentResponse(
        processInstanceKey=result.process_instance_key,
        fraudDecision=request.fraudDecision,
        manualDecision=request.manualDecision,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=False)
