import json
import threading
from collections.abc import Callable, Iterator, Mapping, Sequence
from urllib.parse import urlparse

import requests


def stream_chat(
    base_url: str,
    messages: Sequence[Mapping[str, str]],
    *,
    api_key: str = "",
    parameters: Mapping[str, object] | None = None,
    cancel_event: threading.Event | None = None,
    response_callback: Callable[[requests.Response], None] | None = None,
) -> Iterator[tuple[str, str]]:
    parsed_url = urlparse(base_url)
    if parsed_url.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("Fuserio only connects to a model server on this computer.")

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload: dict[str, object] = {
        "messages": list(messages),
        "stream": True,
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 2048,
    }
    if parameters:
        payload.update(parameters)

    response = requests.post(
        f"{base_url.rstrip('/')}/v1/chat/completions",
        headers=headers,
        json=payload,
        stream=True,
        timeout=(5, 300),
    )
    if response_callback:
        response_callback(response)
    try:
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            if cancel_event and cancel_event.is_set():
                break
            if not line:
                continue
            if isinstance(line, bytes):
                line = line.decode("utf-8", errors="replace")
            if not line.startswith("data:"):
                continue

            data = line[5:].strip()
            if data == "[DONE]":
                break

            chunk = json.loads(data)
            if "error" in chunk:
                raise RuntimeError(str(chunk["error"]))
            choices = chunk.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            reasoning = delta.get("reasoning_content") or delta.get("reasoning") or ""
            content = delta.get("content") or ""
            if reasoning or content:
                yield str(reasoning), str(content)
    finally:
        response.close()