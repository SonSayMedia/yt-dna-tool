"""
Khoi E: Chay HANG LOAT (dung chung 1 hang doi, chay LUAN PHIEN tung viec).

2 loai viec (kind), deu: items = {title, dna_name}; moi tieu de -> 1 prompt tra ve UI:
- "aititles" : tab Tieu de (Prompt Thumbnail). Dung DNA store 'ai'.
- "bctitles" : tab Ban Content. Dung DNA store 'ban_content'.

Chung: worker chay NEN (1 luc 1 viec vi 9router local 1 request/lan),
tam dung / tiep tuc / dung, thanh %.
"""
import threading
from datetime import datetime

from . import image_dna, store

_LK = threading.RLock()
_job = None                 # dict trang thai me hien tai (hoac None)
_thread = None              # luong worker
_pause = threading.Event()  # set = dang tam dung
_stop = threading.Event()   # set = yeu cau dung han


# --------------------------- xu ly tung viec ---------------------------

def _do_bctitles(it):
    dna = None
    if it.get("dna_name"):
        d = store.get_dna(it["dna_name"], "ban_content")
        if d:
            dna = d["dna"].get("thumbnail_dna")
    r = image_dna.thumbnail_prompts_bancontent(it["title"], dna)
    best = r.get("de_xuat_tot_nhat") or {}
    pos = best.get("vi_tri", "")
    prompts = r.get("prompts") or []
    chosen = ""
    for p in prompts:
        if p.get("vi_tri") == pos:
            chosen = p.get("prompt_en", "")
            break
    if not chosen and prompts:
        chosen = prompts[0].get("prompt_en", "")
        pos = prompts[0].get("vi_tri", "")
    with _LK:
        it["prompt"] = chosen
        it["best_pos"] = pos
        it["ly_do"] = best.get("ly_do", "")
        it["chu_the"] = r.get("chu_the_chinh", "")


def _do_aititles(it):
    """Tab AI: 1 tieu de -> 1 prompt thumbnail theo DNA phong cach (store 'ai')."""
    dna = None
    if it.get("dna_name"):
        d = store.get_dna(it["dna_name"], "ai")
        if d:
            dna = d["dna"].get("thumbnail_dna")
    r = image_dna.thumbnail_prompt_from_dna(it["title"], dna)
    with _LK:
        it["prompt"] = r.get("thumbnail_prompt_en", "")
        it["text_tren_thumb"] = r.get("text_tren_thumb", "")
        it["ngon_ngu"] = r.get("ngon_ngu_tieu_de", "")
        it["chu_the"] = r.get("chu_the_chinh", "")


# --------------------------- vong lap worker ---------------------------

def _worker():
    global _job
    with _LK:
        kind = _job["kind"]
        items = _job["items"]

    for it in items:
        if _stop.is_set():
            break
        while _pause.is_set() and not _stop.is_set():
            _stop.wait(0.3)
        if _stop.is_set():
            break

        with _LK:
            _job["status"] = "running"

        with _LK:
            it["state"] = "running"
            it["error"] = ""
        try:
            if kind == "aititles":
                _do_aititles(it)
            else:
                _do_bctitles(it)
            with _LK:
                it["state"] = "done"
        except Exception as e:  # noqa - 1 viec loi khong lam sap ca me
            with _LK:
                it["state"] = "error"
                it["error"] = str(e)

    with _LK:
        if _job is not None:
            _job["status"] = "stopped" if _stop.is_set() else "done"
            _job["finished_at"] = datetime.now().isoformat(timespec="seconds")


# --------------------------- API cho route ---------------------------

def is_running():
    with _LK:
        return _job is not None and _job.get("status") in ("running", "paused", "stopping")


def start(kind, items, folder=None, out_dir=None, motion=True):
    """Tao me moi + chay worker nen. Loi neu dang co me chay do."""
    global _job, _thread
    if is_running():
        raise RuntimeError("Dang co mot me chay. Hay dung (hoac cho xong) truoc khi chay me moi.")
    kind = kind or "aititles"
    if kind not in ("bctitles", "aititles"):
        raise RuntimeError("Loai viec khong hop le.")
    if not items:
        raise RuntimeError("Khong co viec nao de chay.")

    norm = []
    for it in items:  # bctitles / aititles: title + dna_name -> prompt
        title = (it.get("title") or "").strip()
        if not title:
            continue
        norm.append({
            "title": title,
            "dna_name": (it.get("dna_name") or "").strip(),
            "state": "pending", "error": "",
            "prompt": "", "best_pos": "", "ly_do": "", "chu_the": "",
            "text_tren_thumb": "", "ngon_ngu": "",
        })
    if not norm:
        raise RuntimeError("Khong co viec hop le de chay.")

    _pause.clear()
    _stop.clear()
    with _LK:
        _job = {
            "id": datetime.now().strftime("%Y%m%d-%H%M%S"),
            "kind": kind,
            "folder": folder or "",
            "out_dir": out_dir or "",
            "motion": bool(motion),
            "status": "running",
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "finished_at": "",
            "items": norm,
        }
    _thread = threading.Thread(target=_worker, daemon=True)
    _thread.start()
    return snapshot()


def pause():
    with _LK:
        if _job and _job.get("status") == "running":
            _pause.set()
            _job["status"] = "paused"
    return snapshot()


def resume():
    with _LK:
        if _job and _job.get("status") == "paused":
            _pause.clear()
            _job["status"] = "running"
    return snapshot()


def stop():
    _stop.set()
    _pause.clear()
    with _LK:
        if _job and _job.get("status") in ("running", "paused"):
            _job["status"] = "stopping"
    return snapshot()


def snapshot():
    with _LK:
        if _job is None:
            return {"status": "idle", "kind": "", "items": [], "total": 0, "done": 0,
                    "error": 0, "skipped": 0, "pending": 0, "running": 0, "finished": 0,
                    "cur": -1, "pct": 0}
        items = _job["items"]
        cnt = {"done": 0, "error": 0, "skipped": 0, "pending": 0, "running": 0}
        cur = -1
        for i, it in enumerate(items):
            cnt[it["state"]] = cnt.get(it["state"], 0) + 1
            if it["state"] == "running":
                cur = i
        total = len(items)
        finished = cnt["done"] + cnt["error"] + cnt["skipped"]
        return {
            "id": _job["id"],
            "kind": _job["kind"],
            "status": _job["status"],
            "folder": _job["folder"],
            "out_dir": _job["out_dir"],
            "motion": _job["motion"],
            "started_at": _job.get("started_at", ""),
            "finished_at": _job.get("finished_at", ""),
            "total": total,
            "finished": finished,
            "cur": cur,
            "pct": int(finished * 100 / total) if total else 0,
            "items": [dict(it) for it in items],
            **cnt,
        }
