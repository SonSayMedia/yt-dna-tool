"""Nap cau hinh tu config.json (nam cung thu muc goc du an)."""
import json
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONFIG_PATH = os.path.join(_ROOT, "config.json")

_cache = None


def load_config():
    global _cache
    if _cache is not None:
        return _cache
    if not os.path.exists(_CONFIG_PATH):
        raise RuntimeError(
            "Chua co file config.json. Hay copy 'config.example.json' thanh 'config.json' "
            "va dien API key vao."
        )
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    required = ["llm_base_url", "llm_api_key", "llm_model", "youtube_api_key"]
    missing = [k for k in required if not data.get(k) or str(data[k]).startswith("DAN_")]
    if missing:
        raise RuntimeError(
            "config.json thieu hoac chua dien: " + ", ".join(missing)
        )

    # vision model mac dinh = model chu neu khong khai bao rieng
    if not data.get("llm_vision_model"):
        data["llm_vision_model"] = data["llm_model"]

    _cache = data
    return data


def root_dir():
    return _ROOT


def raw_config():
    """Doc config.json tho (khong kiem tra). Neu chua co, lay tu file mau."""
    path = _CONFIG_PATH
    if not os.path.exists(path):
        path = os.path.join(_ROOT, "config.example.json")
        if not os.path.exists(path):
            return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_config(updates):
    """Ghi (merge) cac gia tri vao config.json roi xoa cache. Bo qua gia tri rong."""
    global _cache
    data = raw_config()
    for k, v in updates.items():
        if v is not None and str(v).strip() != "":
            data[k] = v.strip() if isinstance(v, str) else v
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    _cache = None
    return data


def key_is_set(key_name):
    v = raw_config().get(key_name, "")
    return bool(v) and not str(v).startswith("DAN_")
