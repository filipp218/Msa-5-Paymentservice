import logging
import uuid

from pyzeebe import ZeebeTaskRouter

router = ZeebeTaskRouter()
logger = logging.getLogger("payment-orchestrator")


def _log(handler: str, **fields) -> None:
    details = " ".join(f"{key}={value}" for key, value in fields.items())
    logger.info("[HANDLER] %s %s", handler, details)


@router.task(task_type="create-payment", variables_to_fetch=["amount", "fraudDecision"])
async def create_payment(amount: int = 0, fraudDecision: str = "allow") -> dict:
    payment_id = str(uuid.uuid4())
    _log("CREATE_PAYMENT", paymentId=payment_id, amount=amount, fraudDecision=fraudDecision)
    return {"paymentId": payment_id}


@router.task(task_type="debit-user-account", variables_to_fetch=["paymentId", "amount"])
async def debit_user_account(paymentId: str = "", amount: int = 0) -> dict:
    _log("DEBIT_USER_ACCOUNT", paymentId=paymentId, amount=amount)
    return {}


@router.task(
    task_type="request-fraud-check",
    variables_to_fetch=["paymentId", "fraudDecision"],
)
async def request_fraud_check(paymentId: str = "", fraudDecision: str = "allow") -> dict:
    _log("REQUEST_FRAUD_CHECK", paymentId=paymentId, scenario=fraudDecision)
    return {"fraudDecision": fraudDecision}


@router.task(
    task_type="manual-review-wait",
    variables_to_fetch=["paymentId", "manualDecision"],
)
async def manual_review_wait(paymentId: str = "", manualDecision: str = "approved") -> dict:
    _log(
        "MANUAL_REVIEW_WAIT",
        paymentId=paymentId,
        manualDecision=manualDecision,
        note="operator decision emulated",
    )
    return {"manualDecision": manualDecision}


@router.task(
    task_type="transfer-to-counterparty",
    variables_to_fetch=["paymentId", "amount", "simulateTransferFailure"],
)
async def transfer_to_counterparty(
    paymentId: str = "",
    amount: int = 0,
    simulateTransferFailure: bool = False,
) -> dict:
    transfer_failed = bool(simulateTransferFailure)
    _log(
        "TRANSFER_TO_COUNTERPARTY",
        paymentId=paymentId,
        amount=amount,
        transferFailed=transfer_failed,
    )
    return {"transferFailed": transfer_failed, "notifySecurity": False}


@router.task(task_type="complete-payment", variables_to_fetch=["paymentId"])
async def complete_payment(paymentId: str = "") -> dict:
    _log("COMPLETE_PAYMENT", paymentId=paymentId, pivot="irreversible")
    return {}


@router.task(task_type="notify-client", variables_to_fetch=["paymentId"])
async def notify_client(paymentId: str = "") -> dict:
    _log("NOTIFY_CLIENT", paymentId=paymentId)
    return {}


@router.task(task_type="notify-security", variables_to_fetch=["paymentId"])
async def notify_security(paymentId: str = "") -> dict:
    _log("NOTIFY_SECURITY", paymentId=paymentId)
    return {}


@router.task(task_type="refund-user-account", variables_to_fetch=["paymentId", "amount"])
async def refund_user_account(paymentId: str = "", amount: int = 0) -> dict:
    _log("REFUND_USER_ACCOUNT", paymentId=paymentId, amount=amount)
    return {}


@router.task(task_type="cancel-payment", variables_to_fetch=["paymentId"])
async def cancel_payment(paymentId: str = "") -> dict:
    _log("CANCEL_PAYMENT", paymentId=paymentId)
    return {}


@router.task(task_type="reverse-transfer", variables_to_fetch=["paymentId", "amount"])
async def reverse_transfer(paymentId: str = "", amount: int = 0) -> dict:
    _log("REVERSE_TRANSFER", paymentId=paymentId, amount=amount)
    return {}
