"""
Cau noi toi 'bo nao AI' (Gemini Flash qua 9router).
Gia dinh 9router theo chuan OpenAI-compatible: POST {base_url}/chat/completions.
Neu 9router dung duong dan khac, chi can sua ham _endpoint() ben duoi.
"""
import base64
import json
import re

import requests

from .config import load_config

_TIMEOUT = 120


def _endpoint():
    cfg = load_config()
    base = cfg["llm_base_url"].rstrip("/")
    # cho phep khai bao base co hoac khong co '/v1'
    return base + "/chat/completions"


def _headers():
    cfg = load_config()
    return {
        "Authorization": "Bearer " + cfg["llm_api_key"],
        "Content-Type": "application/json",
    }


def _post(payload):
    resp = requests.post(_endpoint(), headers=_headers(), json=payload, timeout=_TIMEOUT)
    # 9router khong khai bao charset -> requests mac dinh Latin-1 -> vo dau tieng Viet.
    # Ep UTF-8 de doc dung.
    resp.encoding = "utf-8"
    if resp.status_code >= 400:
        raise RuntimeError(
            "Loi goi AI ({}): {}".format(resp.status_code, resp.text[:500])
        )
    ctype = resp.headers.get("content-type", "")
    text = resp.text
    # 9router tra ve kieu streaming (SSE) -> ghep cac chunk lai
    if "text/event-stream" in ctype or text.lstrip().startswith("data:"):
        return _parse_sse(text)
    # JSON thuong
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise RuntimeError("AI tra ve khong dung dinh dang: " + json.dumps(data)[:500])


def _parse_sse(text):
    """Ghep noi dung tu luong SSE 'data: {...}' thanh 1 chuoi hoan chinh."""
    parts = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        chunk = line[len("data:"):].strip()
        if not chunk or chunk == "[DONE]":
            continue
        try:
            obj = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        choices = obj.get("choices") or []
        if not choices:
            continue
        ch = choices[0]
        content = (ch.get("delta") or {}).get("content")
        if content is None:
            content = (ch.get("message") or {}).get("content")
        if content:
            parts.append(content)
    result = "".join(parts)
    if not result.strip():
        raise RuntimeError("AI tra ve rong (khong co noi dung trong luong SSE).")
    return result


def _pick_model(cfg, vision_images, role):
    """Chon model theo TAC VU: vision hoac role='analyze' -> slot PHAN TICH & NHIN ANH;
    con lai (role='create') -> slot SANG TAO. Thieu slot -> fallback llm_model (tuong thich nguoc)."""
    base = cfg.get("llm_model") or ""
    analyze = (cfg.get("model_analyze") or "").strip() or (cfg.get("llm_vision_model") or "").strip() or base
    create = (cfg.get("model_create") or "").strip() or base
    return analyze if (vision_images or role == "analyze") else create


def chat(system, user, temperature=0.7, vision_images=None, role="create"):
    """Goi AI. role='analyze' (phan tich/nhin anh) hoac 'create' (sang tao tieu de/prompt).
    vision_images = list bytes anh (neu can nhin anh)."""
    cfg = load_config()
    model = _pick_model(cfg, vision_images, role)

    if vision_images:
        content = [{"type": "text", "text": user}]
        for img in vision_images:
            b64 = base64.b64encode(img).decode("ascii")
            content.append({
                "type": "image_url",
                "image_url": {"url": "data:image/jpeg;base64," + b64},
            })
        user_msg = {"role": "user", "content": content}
    else:
        user_msg = {"role": "user", "content": user}

    payload = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            user_msg,
        ],
    }
    # Che do suy luan (Thinking) tuy chon — 9router nhan 'reasoning_effort'. Auto/rong = khong gui.
    reasoning = str(cfg.get("llm_reasoning", "") or "").strip().lower()
    if reasoning and reasoning != "auto":
        payload["reasoning_effort"] = reasoning
    return _post(payload)


def ping():
    """Goi 1 lenh nho de kiem tra 9router + key co hoat dong khong."""
    return chat("Ban la bo kiem tra ket noi.", "Tra loi dung 2 ky tu: OK", temperature=0)


def chat_json(system, user, temperature=0.4, vision_images=None, role="create"):
    """Nhu chat() nhung ep tra ve JSON va tu parse (chiu duoc code-fence)."""
    system_json = system + (
        "\n\nQUAN TRONG: Chi tra ve JSON hop le thuan tuy, khong kem giai thich, "
        "khong bao boc trong ```."
    )
    raw = chat(system_json, user, temperature=temperature, vision_images=vision_images, role=role)
    return _extract_json(raw)


def _extract_json(text):
    text = text.strip()
    # go bo code fence neu co
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    # thu parse truc tiep
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # thu tim khoi { ... } hoac [ ... ] dai nhat
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                continue
    raise RuntimeError("Khong doc duoc JSON tu AI. Noi dung:\n" + text[:800])
