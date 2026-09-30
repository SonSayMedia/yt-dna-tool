"""Luu/doc 'ho so khuon kenh' (Title DNA), 'ho so DNA anh', 'da dung', 'da quet'.

An toan: ghi nguyen tu (temp + os.replace), khoa luong (RLock) cho read-modify-write,
va tu phuc hoi khi file JSON bi hong (sao luu .bak roi tra ve mac dinh).
"""
import json
import os
import tempfile
import threading
from datetime import datetime

from .config import root_dir

_PATH = os.path.join(root_dir(), "profiles.json")
_DNA_PATH = os.path.join(root_dir(), "dna_profiles.json")
_USED_PATH = os.path.join(root_dir(), "used.json")
_SEEN_PATH = os.path.join(root_dir(), "seen.json")

_LOCK = threading.RLock()


def norm_kw(k):
    """Chuan hoa tu khoa lam pham vi loai trung (thuong, gom khoang trang)."""
    return " ".join((k or "").strip().lower().split())


def _read_json(path, default):
    with _LOCK:
        if not os.path.exists(path):
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError, ValueError):
            # File hong -> sao luu de khoi phuc tay, tra ve mac dinh de khong sap chuong trinh
            try:
                os.replace(path, path + ".bak")
            except OSError:
                pass
            return default


def _write_json(path, data):
    with _LOCK:
        folder = os.path.dirname(path) or "."
        fd, tmp = tempfile.mkstemp(dir=folder, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)  # nguyen tu tren cung o dia
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise


# ---------------- Khuon tieu de (Title DNA) ----------------

def list_profiles():
    return _read_json(_PATH, [])


def get_profile(name):
    for p in list_profiles():
        if p.get("name") == name:
            return p
    return None


def save_profile(name, channel_url, profile, sample_titles):
    with _LOCK:
        items = [p for p in list_profiles() if p.get("name") != name]
        items.append({
            "name": name,
            "channel_url": channel_url,
            "profile": profile,
            "sample_titles": sample_titles,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        })
        _write_json(_PATH, items)
        return items


def delete_profile(name):
    with _LOCK:
        items = [p for p in list_profiles() if p.get("name") != name]
        _write_json(_PATH, items)
        return items


# ---------------- Image DNA (Khoi C) ----------------

def list_dna(dna_type=None):
    items = _read_json(_DNA_PATH, [])
    for it in items:
        if isinstance(it, dict):
            it.setdefault("type", "ai")  # ho so cu (co ca thumb+noi dung) mac dinh la AI
    if dna_type:
        items = [it for it in items if it.get("type") == dna_type]
    return items


def get_dna(name, dna_type=None):
    for p in list_dna(dna_type):
        if p.get("name") == name:
            return p
    return None


def save_dna(name, dna, dna_type="ai"):
    with _LOCK:
        # du an AI va Ban Content doc lap -> chi ghi de khi TRUNG CA ten LAN loai
        items = [p for p in _read_json(_DNA_PATH, [])
                 if not (p.get("name") == name and p.get("type", "ai") == dna_type)]
        items.append({
            "name": name,
            "dna": dna,
            "type": dna_type,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        })
        _write_json(_DNA_PATH, items)
        return items


def delete_dna(name, dna_type=None):
    with _LOCK:
        items = [p for p in _read_json(_DNA_PATH, [])
                 if not (p.get("name") == name and (dna_type is None or p.get("type", "ai") == dna_type))]
        _write_json(_DNA_PATH, items)
        return items


# ---------------- "Da dung" (loai cung) - theo tung tu khoa ----------------

def used_list():
    return _read_json(_USED_PATH, [])


def used_ids_for(keyword):
    kn = norm_kw(keyword)
    return {e["video_id"] for e in used_list() if e.get("keyword_norm") == kn}


def used_add(entry):
    with _LOCK:
        kn = norm_kw(entry.get("keyword", ""))
        vid = entry["video_id"]
        items = used_list()
        for e in items:
            if e.get("keyword_norm") == kn and e.get("video_id") == vid:
                e["tieu_de_final"] = entry.get("tieu_de_final", e.get("tieu_de_final", ""))
                _write_json(_USED_PATH, items)
                return items
        items.append({
            "keyword_norm": kn,
            "keyword": entry.get("keyword", ""),
            "video_id": vid,
            "title_goc": entry.get("title_goc", ""),
            "tieu_de_final": entry.get("tieu_de_final", ""),
            "channel": entry.get("channel", ""),
            "views": entry.get("views", 0),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        })
        _write_json(_USED_PATH, items)
        return items


def used_delete(keyword, video_id):
    with _LOCK:
        kn = norm_kw(keyword)
        items = [e for e in used_list()
                 if not (e.get("keyword_norm") == kn and e.get("video_id") == video_id)]
        _write_json(_USED_PATH, items)
        return items


# ---------------- "Da quet" (loai mem, tuy chon) - theo tung tu khoa ----------------

def seen_ids_for(keyword):
    return set(_read_json(_SEEN_PATH, {}).get(norm_kw(keyword), []))


def seen_add(keyword, video_ids):
    with _LOCK:
        d = _read_json(_SEEN_PATH, {})
        kn = norm_kw(keyword)
        cur = set(d.get(kn, []))
        cur |= set(video_ids)
        d[kn] = sorted(cur)
        _write_json(_SEEN_PATH, d)


def seen_clear(keyword):
    with _LOCK:
        d = _read_json(_SEEN_PATH, {})
        d.pop(norm_kw(keyword), None)
        _write_json(_SEEN_PATH, d)


# ---------------- Lich su VIET LAI tieu de (tra cuu lai sau) ----------------

_HIST_PATH = os.path.join(root_dir(), "title_history.json")
_HIST_MAX = 800  # gioi han so ban ghi giu lai (moi nhat), tranh phinh vo han


def title_hist_list():
    return _read_json(_HIST_PATH, [])


def title_hist_add(entries):
    """Them nhieu ban ghi (moi tieu de = 1 ban ghi). Tu cat bot khi qua nhieu."""
    if not entries:
        return title_hist_list()
    with _LOCK:
        items = title_hist_list()
        base = datetime.now()
        stamp = base.isoformat(timespec="seconds")
        prefix = base.strftime("%Y%m%d%H%M%S%f")
        for i, e in enumerate(entries):
            rec = dict(e)
            rec["id"] = prefix + "-" + str(i)
            rec.setdefault("created_at", stamp)
            items.append(rec)
        if len(items) > _HIST_MAX:
            items = items[-_HIST_MAX:]
        _write_json(_HIST_PATH, items)
        return items


def title_hist_delete(entry_id):
    with _LOCK:
        items = [e for e in title_hist_list() if e.get("id") != entry_id]
        _write_json(_HIST_PATH, items)
        return items


def title_hist_clear():
    with _LOCK:
        _write_json(_HIST_PATH, [])
        return []
