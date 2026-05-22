from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit

import requests


DEFAULT_DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_NATIVE_KIMI_URL = (
    "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
)

_LEGACY_MODEL_ALIASES = {
    "kimi-2.5": "kimi/kimi-k2.5",
    "kimi-k2.5": "kimi/kimi-k2.5",
    "kimi-2.6": "kimi/kimi-k2.6",
    "kimi-k2.6": "kimi/kimi-k2.6",
}


def normalize_kimi_model(model: Optional[str]) -> str:
    raw_model = (model or "kimi-2.5").strip()
    return _LEGACY_MODEL_ALIASES.get(raw_model.lower(), raw_model)


def build_kimi_request_config(
    api_url: Optional[str],
    base_url: Optional[str],
    model: Optional[str],
) -> Dict[str, str]:
    normalized_model = normalize_kimi_model(model)
    resolved_api_url = (api_url or DEFAULT_NATIVE_KIMI_URL).strip()

    if _should_use_compatible_mode(resolved_api_url, normalized_model):
        compatible_base = _resolve_compatible_base_url(resolved_api_url, base_url)
        return {
            "api_style": "openai_compatible",
            "url": f"{compatible_base}/chat/completions",
            "model": normalized_model,
        }

    return {
        "api_style": "dashscope_native",
        "url": resolved_api_url,
        "model": _strip_provider_prefix(normalized_model),
    }


def build_kimi_payload(
    api_style: str,
    model: str,
    messages: List[Dict[str, Any]],
    temperature: float,
    max_tokens: Optional[int] = None,
    stream: bool = False,
) -> Dict[str, Any]:
    if api_style == "openai_compatible":
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        return payload

    parameters: Dict[str, Any] = {
        "result_format": "message",
        "temperature": temperature,
    }
    if max_tokens is not None:
        parameters["max_tokens"] = max_tokens
    if stream:
        parameters["incremental_output"] = True

    return {
        "model": _strip_provider_prefix(model),
        "input": {"messages": messages},
        "parameters": parameters,
    }


def extract_kimi_response_content(result: Dict[str, Any]) -> Optional[str]:
    choice = _extract_first_choice(result)
    if not choice:
        return None

    message = choice.get("message", {})
    content = message.get("content")
    if isinstance(content, str):
        return content
    return None


def extract_kimi_stream_content(chunk: Dict[str, Any]) -> Optional[str]:
    choice = _extract_first_choice(chunk)
    if not choice:
        return None

    delta = choice.get("delta", {})
    delta_content = delta.get("content")
    if isinstance(delta_content, str):
        return delta_content

    message = choice.get("message", {})
    content = message.get("content")
    if isinstance(content, str):
        return content

    return None


def post_kimi_request(
    url: str,
    *,
    headers: Dict[str, str],
    json: Dict[str, Any],
    timeout: Any,
) -> requests.Response:
    """Post to DashScope/Kimi without inheriting shell proxy variables."""
    with requests.Session() as session:
        session.trust_env = False
        return session.post(url, headers=headers, json=json, timeout=timeout)


def _should_use_compatible_mode(api_url: str, model: str) -> bool:
    if "/compatible-mode/" in api_url or api_url.rstrip("/").endswith("/chat/completions"):
        return True

    return model in {"kimi/kimi-k2.5", "kimi/kimi-k2.6"}


def _resolve_compatible_base_url(api_url: str, base_url: Optional[str]) -> str:
    if base_url:
        return base_url.rstrip("/")

    parsed = urlsplit(api_url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}/compatible-mode/v1"

    return DEFAULT_DASHSCOPE_BASE_URL


def _strip_provider_prefix(model: str) -> str:
    if "/" in model:
        return model.split("/", 1)[1]
    return model


def _extract_first_choice(result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    choices = result.get("choices")
    if isinstance(choices, list) and choices:
        return choices[0]

    output = result.get("output", {})
    output_choices = output.get("choices")
    if isinstance(output_choices, list) and output_choices:
        return output_choices[0]

    return None
