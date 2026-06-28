from __future__ import annotations

import secrets
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles


ROOT_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT_DIR / "static"
APP_VERSION = "1.0.1"

MODEL_ENDPOINTS = [
    {
        "id": "vercel-openai",
        "name": "OpenAI API",
        "base_url": "https://api.openai.com/v1",
        "chat_url": "https://api.openai.com/v1/chat/completions",
        "env_key": "OPENAI_API_KEY",
        "category": "api",
        "endpoint_kind": "openai-compatible",
        "preview_selectable": True,
        "models": [
            "gpt-4o-mini",
            "gpt-4.1-mini",
            "gpt-4.1",
        ],
    },
    {
        "id": "vercel-deepseek",
        "name": "DeepSeek API",
        "base_url": "https://api.deepseek.com/v1",
        "chat_url": "https://api.deepseek.com/v1/chat/completions",
        "env_key": "DEEPSEEK_API_KEY",
        "category": "api",
        "endpoint_kind": "openai-compatible",
        "preview_selectable": True,
        "models": [
            "deepseek-chat",
            "deepseek-reasoner",
        ],
    },
    {
        "id": "vercel-ollama",
        "name": "Ollama (local)",
        "base_url": "http://127.0.0.1:11434/v1",
        "chat_url": "http://127.0.0.1:11434/v1/chat/completions",
        "env_key": "",
        "category": "local",
        "endpoint_kind": "ollama",
        "preview_selectable": True,
        "models": [
            "llama3.1",
            "qwen2.5",
            "deepseek-r1",
        ],
        "local_only": True,
    },
    {
        "id": "vercel-lmstudio",
        "name": "LM Studio (local)",
        "base_url": "http://127.0.0.1:1234/v1",
        "chat_url": "http://127.0.0.1:1234/v1/chat/completions",
        "env_key": "",
        "category": "local",
        "endpoint_kind": "lm-studio",
        "preview_selectable": True,
        "models": [
            "local-model",
        ],
        "local_only": True,
    },
]

ADMIN_PRIVILEGES = {
    "can_use_agent": True,
    "can_use_browser": True,
    "can_use_bash": True,
    "can_use_documents": True,
    "can_use_research": True,
    "max_messages_per_day": 0,
    "allowed_models": [],
    "allowed_models_restricted": False,
    "block_all_models": False,
}

app = FastAPI(
    title="OrionX",
    version=APP_VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _html_page(filename: str) -> HTMLResponse:
    path = STATIC_DIR / filename
    if not path.exists():
        return HTMLResponse("OrionX page not found.", status_code=404)

    nonce = secrets.token_urlsafe(16)
    html = path.read_text(encoding="utf-8").replace("{{CSP_NONCE}}", nonce)
    return HTMLResponse(
        html,
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        },
    )


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "app": "OrionX",
        "deployment": "vercel",
    }


@app.get("/api/version")
async def version() -> dict[str, str]:
    return {"version": APP_VERSION}


@app.get("/api/runtime")
async def runtime() -> dict[str, object]:
    return {
        "deployment": "vercel",
        "backend": "static-preview",
        "local_backend_required": True,
        "available_model_catalog": True,
        "message": "Vercel can show configured cloud models. Run OrionX locally for local Ollama/LM Studio, tools, memory, and full model routing APIs.",
    }


@app.get("/api/auth/status")
async def auth_status() -> dict[str, object]:
    return {
        "authenticated": True,
        "configured": True,
        "username": "admin",
        "is_admin": True,
        "signup_enabled": False,
        "privileges": ADMIN_PRIVILEGES,
    }


@app.get("/api/auth/features")
async def auth_features() -> dict[str, bool]:
    return {
        "web_search": True,
        "deep_research": True,
        "document_editor": True,
        "gallery": True,
    }


@app.get("/api/auth/settings")
async def auth_settings() -> dict[str, object]:
    return {
        "share_defaults_with_users": False,
        "tts_enabled": False,
        "tts_provider": "disabled",
        "image_gen_enabled": False,
    }


@app.get("/api/auth/policy")
async def auth_policy() -> dict[str, object]:
    return {
        "password_min_length": 8,
        "password_requires_letter": False,
        "password_requires_number": False,
        "password_requires_symbol": False,
    }


def _endpoint_enabled(endpoint: dict[str, object]) -> bool:
    env_key = str(endpoint.get("env_key") or "")
    if endpoint.get("local_only"):
        return False
    return bool(env_key and os.getenv(env_key))


def _model_item(endpoint: dict[str, object]) -> dict[str, object]:
    models = list(endpoint["models"])
    enabled = _endpoint_enabled(endpoint)
    selectable = bool(endpoint.get("preview_selectable"))
    return {
        "host": "vercel",
        "port": 0,
        "url": endpoint["chat_url"],
        "models": models,
        "models_display": [model.split("/")[-1] for model in models],
        "models_extra": [],
        "models_extra_display": [],
        "endpoint_id": endpoint["id"],
        "endpoint_name": endpoint["name"],
        "category": endpoint["category"],
        "endpoint_kind": endpoint["endpoint_kind"],
        "model_type": "llm",
        "offline": bool(not enabled and not selectable),
        "selectable": selectable,
        "configured": enabled,
        "configuration_required": not enabled,
    }


@app.get("/api/models")
async def models() -> dict[str, object]:
    return {
        "hosts": [],
        "items": [_model_item(endpoint) for endpoint in MODEL_ENDPOINTS],
    }


@app.get("/api/default-chat")
async def default_chat() -> dict[str, object]:
    for endpoint in MODEL_ENDPOINTS:
        models = list(endpoint.get("models") or [])
        if models:
            return {
                "endpoint_url": endpoint["chat_url"],
                "endpoint_id": endpoint["id"],
                "endpoint_name": endpoint["name"],
                "model": models[0],
                "configured": _endpoint_enabled(endpoint),
                "configuration_required": not _endpoint_enabled(endpoint),
            }
    return {"endpoint_url": "", "endpoint_id": "", "model": ""}


@app.get("/api/model-endpoints")
async def model_endpoints() -> list[dict[str, object]]:
    endpoints = []
    for endpoint in MODEL_ENDPOINTS:
        enabled = _endpoint_enabled(endpoint)
        endpoints.append(
            {
                "id": endpoint["id"],
                "name": endpoint["name"],
                "base_url": endpoint["base_url"],
                "has_key": bool(endpoint.get("env_key") and os.getenv(str(endpoint["env_key"]))),
                "is_enabled": enabled,
                "models": endpoint["models"],
                "pinned_models": endpoint["models"],
                "hidden_count": 0,
                "online": enabled,
                "status": "online" if enabled else "configuration_required",
                "ping_error": None if enabled else "Add the matching provider key in Vercel environment variables or run OrionX locally.",
                "model_type": "llm",
                "supports_tools": None,
                "endpoint_kind": endpoint["endpoint_kind"],
                "category": endpoint["category"],
                "model_refresh_mode": "manual",
                "model_refresh_interval": None,
                "model_refresh_timeout": None,
            }
        )
    return endpoints


@app.get("/api/model-endpoints/probe-local")
async def probe_local_model_endpoints() -> dict[str, object]:
    return {
        "ok": False,
        "endpoints": [],
        "message": "Local Ollama and LM Studio endpoints are available only when OrionX runs on the same machine as those servers.",
    }


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def api_unavailable(path: str, request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "error": "This Vercel deployment serves the OrionX web UI preview.",
            "path": f"/api/{path}",
            "method": request.method,
            "local_backend_required": True,
        },
        status_code=501,
    )


@app.get("/login")
async def login() -> HTMLResponse:
    return _html_page("login.html")


@app.get("/{path:path}")
async def spa(path: str) -> HTMLResponse:
    page = "backgrounds.html" if path == "backgrounds" else "index.html"
    return _html_page(page)
