from __future__ import annotations

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from redis import Redis
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage

from src.agents.agent import build_llm, run_agent_turn, run_workflow
from src.data.mock_patients import get_patient

from .config import APISettings
from .conversation_store import RedisConversationStore, serialize_history
from .redis_state import RedisStateStore
from .schemas import AnalyzeRequest, AnalyzeResponse, ChatResponse, ConversationSnapshot, ErrorResponse, ChatRequest

logger = logging.getLogger("vinmec.lumina.api")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _log_json(event: str, **fields: Any) -> None:
    payload: dict[str, Any] = {
        "timestamp": _now_utc().isoformat(),
        "event": event,
        **fields,
    }
    logger.info(json.dumps(payload, ensure_ascii=True))


@asynccontextmanager
async def _lifespan(_: FastAPI):
    settings = APISettings.from_env()
    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    redis_state = RedisStateStore(redis_client)
    conversation_store = RedisConversationStore(redis_client=redis_client, ttl_seconds=settings.conversation_ttl_seconds)

    app.state.settings = settings
    app.state.redis_client = redis_client
    app.state.redis_state = redis_state
    app.state.conversation_store = conversation_store
    app.state.ready = False
    app.state.shutting_down = False
    app.state.active_requests = 0
    app.state.ready = bool(settings.api_keys) and redis_state.ping()
    _log_json(
        "startup_complete",
        api_key_users=len(settings.api_keys),
        redis_ready=app.state.ready,
        redis_url=settings.redis_url,
    )
    try:
        yield
    finally:
        app.state.shutting_down = True
        deadline = time.time() + settings.shutdown_grace_seconds
        while app.state.active_requests > 0 and time.time() < deadline:
            await asyncio.sleep(0.1)
        try:
            redis_client.close()
        except Exception:
            pass
        app.state.ready = False
        _log_json("shutdown_complete", active_requests=app.state.active_requests)


app = FastAPI(
    title="Vinmec Lumina API",
    version="1.2.0",
    description="REST API for lab analysis and follow-up chat.",
    lifespan=_lifespan,
)

_SEVERITY_LABEL_VI = {
    "NORMAL": "Binh thuong",
    "WATCH": "Theo doi",
    "SEE_DOCTOR": "Gap bac si",
    "CRITICAL": "Khan cap",
}


def _estimate_chat_cost_usd(request_text: str, response_text: str) -> float:
    settings = app.state.settings
    # Approximate token count from characters to keep cost checks lightweight.
    in_tokens = max(1, int(len(request_text) / 4))
    out_tokens = max(1, int(len(response_text) / 4))
    in_cost = (in_tokens / 1000.0) * settings.input_cost_per_1k_usd
    out_cost = (out_tokens / 1000.0) * settings.output_cost_per_1k_usd
    return round(max(0.001, in_cost + out_cost), 6)


def _auth_and_limits(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    if request.app.state.shutting_down:
        raise HTTPException(status_code=503, detail="Service is shutting down")

    if not request.app.state.redis_state.ping():
        raise HTTPException(status_code=503, detail="Redis is unavailable")

    settings: APISettings = request.app.state.settings
    api_keys: dict[str, str] = settings.api_keys
    if not api_keys:
        raise HTTPException(status_code=503, detail="API key authentication is not configured")

    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key")

    user_id = next((u for u, k in api_keys.items() if k == x_api_key), None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid API key")

    allowed, remaining = request.app.state.redis_state.check_rate_limit(user_id, settings.rate_limit_per_minute)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} requests per minute per user",
        )

    estimated = settings.default_estimated_request_cost_usd
    if not request.app.state.redis_state.can_spend(user_id, estimated, settings.monthly_cost_limit_usd):
        raise HTTPException(status_code=402, detail="Monthly cost limit reached")

    request.state.user_id = user_id
    request.state.rate_limit_remaining = remaining
    return user_id


def _build_context_prompt(patient: Any, result: dict[str, Any]) -> str:
    lab_lines = "\n".join(
        f"  - {r.test_name}: {r.value} {r.unit} [{r.flag.value if hasattr(r.flag, 'value') else r.flag}]"
        for r in patient.lab_results
    )
    abnormal = [e for e in (result.get("explanations") or []) if e.get("severity") != "NORMAL"]
    abnormal_str = (
        ", ".join(f"{e['test_name']} ({_SEVERITY_LABEL_VI.get(e['severity'], e['severity'])})" for e in abnormal)
        or "Khong co chi so bat thuong"
    )
    overall = _SEVERITY_LABEL_VI.get(result.get("overall_severity", "NORMAL"), "Binh thuong")

    return (
        "Ban la Vinmec Lumina - tro ly giai thich ket qua xet nghiem cua Vinmec.\n"
        "Chi giai thich dua tren ket qua xet nghiem hien co; khong bia them thong tin.\n"
        "KHONG chan doan benh cu the, KHONG tu van thuoc hoac lieu dung.\n"
        "Dung tieng Viet de hieu, ngan gon, than thien, va khuyen benh nhan tham khao bac si khi can.\n"
        f"Benh nhan: Ten={patient.name}, Tuoi={patient.age}, Gioi tinh={patient.sex}, Tien su={', '.join(patient.conditions)}\n"
        f"Ngay xet nghiem: {patient.test_date}\n"
        f"Ket qua:\n{lab_lines}\n"
        f"Danh gia he thong: Muc do tong quat={overall}; Chi so can chu y={abnormal_str}; Tom tat={result.get('summary', '')}"
    )


def _ensure_conversation(
    *,
    conversation_id: str | None,
    patient_id: str | None,
    workflow_result: dict[str, Any] | None,
    llm_provider: str,
) -> tuple[str, list[AnyMessage]]:
    store: RedisConversationStore = app.state.conversation_store
    if conversation_id:
        existing = store.get(conversation_id)
        if not existing:
            raise HTTPException(status_code=404, detail="conversation_id not found")
        return existing.id, existing.history

    if not patient_id:
        raise HTTPException(status_code=400, detail="patient_id is required when creating a new conversation")

    try:
        patient = get_patient(patient_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"patient_id not found: {patient_id}") from exc

    result = workflow_result or run_workflow(patient_id=patient_id, llm_provider=llm_provider)
    system_prompt = _build_context_prompt(patient, result)
    conversation = store.create(
        history=[SystemMessage(content=system_prompt)],
        metadata={"patient_id": patient_id, "llm_provider": llm_provider},
    )
    return conversation.id, conversation.history


def _chunk_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return "".join(parts)
    return str(content or "")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "vinmec-lumina-api"}


@app.get("/ready")
def readiness(request: Request) -> JSONResponse:
    settings: APISettings = request.app.state.settings
    redis_ready = request.app.state.redis_state.ping()
    is_ready = bool(request.app.state.ready) and not bool(request.app.state.shutting_down) and bool(settings.api_keys) and redis_ready
    payload = {
        "status": "ready" if is_ready else "not_ready",
        "ready": is_ready,
        "shutting_down": bool(request.app.state.shutting_down),
        "api_key_users": len(settings.api_keys),
        "redis_ready": redis_ready,
    }
    return JSONResponse(content=payload, status_code=200 if is_ready else 503)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    start = time.perf_counter()
    request.app.state.active_requests += 1
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        user_id = getattr(request.state, "user_id", "anonymous")
        _log_json(
            "request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            client_ip=request.client.host if request.client else "unknown",
        )
        request.app.state.active_requests = max(0, request.app.state.active_requests - 1)


@app.post("/api/v1/analyze", response_model=AnalyzeResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def analyze(request: AnalyzeRequest, user_id: str = Depends(_auth_and_limits)) -> AnalyzeResponse:
    if request.initial_state is None and request.patient_id is None:
        raise HTTPException(status_code=400, detail="Provide either patient_id or initial_state")

    try:
        result = run_workflow(
            patient_id=request.patient_id,
            initial_state=request.initial_state,
            llm_provider=request.llm_provider,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"patient_id not found: {request.patient_id}") from exc

    conversation_id: str | None = None
    if request.create_conversation and request.patient_id:
        patient = get_patient(request.patient_id)
        system_prompt = _build_context_prompt(patient, result)
        conversation = app.state.conversation_store.create(
            history=[SystemMessage(content=system_prompt)],
            metadata={"patient_id": request.patient_id, "llm_provider": request.llm_provider},
        )
        conversation_id = conversation.id

    app.state.redis_state.add_cost(user_id, app.state.settings.analyze_cost_usd)

    return AnalyzeResponse(result=result, conversation_id=conversation_id)


@app.post("/api/v1/chat", response_model=ChatResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def chat(request: ChatRequest, user_id: str = Depends(_auth_and_limits)) -> ChatResponse:
    conversation_id, history = _ensure_conversation(
        conversation_id=request.conversation_id,
        patient_id=request.patient_id,
        workflow_result=request.workflow_result,
        llm_provider=request.llm_provider,
    )

    try:
        updated = run_agent_turn(request.message, history, provider=request.llm_provider)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    stored = app.state.conversation_store.set_history(conversation_id, updated)
    if not stored:
        raise HTTPException(status_code=404, detail="conversation_id not found")

    reply = ""
    for msg in reversed(updated):
        if isinstance(msg, AIMessage):
            reply = str(msg.content)
            break

    chat_cost_usd = _estimate_chat_cost_usd(request.message, reply)
    if not app.state.redis_state.can_spend(user_id, chat_cost_usd, app.state.settings.monthly_cost_limit_usd):
        raise HTTPException(status_code=402, detail="Monthly cost limit reached")

    app.state.redis_state.add_cost(user_id, chat_cost_usd)

    return ChatResponse(
        conversation_id=conversation_id,
        reply=reply,
        history=serialize_history(stored.history),
    )


@app.post("/api/v1/chat/stream", responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def chat_stream(request: ChatRequest, user_id: str = Depends(_auth_and_limits)) -> StreamingResponse:
    conversation_id, history = _ensure_conversation(
        conversation_id=request.conversation_id,
        patient_id=request.patient_id,
        workflow_result=request.workflow_result,
        llm_provider=request.llm_provider,
    )

    llm = build_llm(provider=request.llm_provider)
    messages = history + [HumanMessage(content=request.message)]

    def event_stream():
        full_text = ""
        if llm is None:
            payload = {
                "type": "error",
                "message": "LLM provider is not configured. Check API keys.",
            }
            yield f"data: {json.dumps(payload, ensure_ascii=True)}\\n\\n"
            return

        try:
            for chunk in llm.stream(messages):
                delta = _chunk_text(getattr(chunk, "content", ""))
                if not delta:
                    continue
                full_text += delta
                payload = {"type": "token", "content": delta}
                yield f"data: {json.dumps(payload, ensure_ascii=True)}\\n\\n"
        except Exception:
            # Fallback to a normal invoke when provider does not support stream.
            response = llm.invoke(messages)
            full_text = _chunk_text(getattr(response, "content", ""))
            payload = {"type": "token", "content": full_text}
            yield f"data: {json.dumps(payload, ensure_ascii=True)}\\n\\n"

        updated = messages + [AIMessage(content=full_text)]
        app.state.conversation_store.set_history(conversation_id, updated)
        chat_cost_usd = _estimate_chat_cost_usd(request.message, full_text)
        if not app.state.redis_state.can_spend(user_id, chat_cost_usd, app.state.settings.monthly_cost_limit_usd):
            stop_payload = {"type": "error", "message": "Monthly cost limit reached"}
            yield f"data: {json.dumps(stop_payload, ensure_ascii=True)}\\n\\n"
            return
        app.state.redis_state.add_cost(user_id, chat_cost_usd)
        done_payload = {"type": "done", "conversation_id": conversation_id}
        yield f"data: {json.dumps(done_payload, ensure_ascii=True)}\\n\\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/v1/conversations/{conversation_id}", response_model=ConversationSnapshot, responses={404: {"model": ErrorResponse}})
def get_conversation(conversation_id: str, _: str = Depends(_auth_and_limits)) -> ConversationSnapshot:
    conv = app.state.conversation_store.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="conversation_id not found")
    return ConversationSnapshot(conversation_id=conversation_id, history=serialize_history(conv.history))
