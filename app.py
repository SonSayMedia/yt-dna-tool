"""
YT DNA Tool - phan mem localhost.
Chay: python app.py  ->  mo http://127.0.0.1:5000
"""
import os
import traceback

from flask import Flask, jsonify, request, send_from_directory

from services import batch, image_dna, media, store, title_dna, youtube

app = Flask(__name__, static_folder="static", static_url_path="")
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0  # khong cache file tinh (index.html)


@app.after_request
def _no_cache(resp):
    """Ep trinh duyet LUON nap ban moi nhat -> chi can F5 (khoi Ctrl+F5 / tat mo lai)."""
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


def _err(e):
    return jsonify({"ok": False, "error": _scrub(str(e)), "trace": _scrub(traceback.format_exc()[-1500:])}), 400


def _scrub(text):
    """Xoa moi key that ra khoi thong bao (khong bao gio lo key)."""
    from services import config as cfg
    try:
        d = cfg.raw_config()
    except Exception:
        return text
    for k in ("llm_api_key", "youtube_api_key"):
        v = d.get(k, "")
        if v and not str(v).startswith("DAN_") and len(str(v)) >= 6:
            text = text.replace(str(v), "***")
    return text


def _short(text, n=240):
    text = _scrub(str(text)).strip().replace("\n", " ")
    return text[:n]


# ---------------- Khoi A: phan tich kenh -> khuon ----------------

@app.route("/api/analyze-channel", methods=["POST"])
def api_analyze_channel():
    try:
        data = request.get_json(force=True)
        channel_url = data["channel_url"].strip()
        name = (data.get("name") or "").strip() or channel_url

        videos = youtube.get_channel_top_videos(channel_url, count=20)
        if not videos:
            raise RuntimeError("Khong lay duoc video nao tu kenh nay.")
        titles = [v["title"] for v in videos]
        profile = title_dna.analyze_channel(titles)
        store.save_profile(name, channel_url, profile, titles)
        return jsonify({"ok": True, "name": name, "profile": profile, "sample_titles": titles})
    except Exception as e:  # noqa
        return _err(e)


def _profile_with_keywords(profile_name):
    """Tra ve dict khuon (hoac None). Khuon CU chua co 'tu_khoa_chien_thang' thi tu rut 1 lan
    tu sample_titles roi luu lai (lan sau khong ton them 1 luot goi AI)."""
    if not profile_name:
        return None
    p = store.get_profile(profile_name)
    if not p:
        return None
    prof = p["profile"]
    if not prof.get("tu_khoa_chien_thang") and p.get("sample_titles"):
        try:
            kws = title_dna.extract_channel_keywords(p["sample_titles"])
            if kws:
                prof["tu_khoa_chien_thang"] = kws
                store.save_profile(p["name"], p.get("channel_url", ""), prof, p["sample_titles"])
        except Exception:
            pass  # khong rut duoc -> van chay, chi thieu rang buoc tu khoa kenh
    return prof


@app.route("/api/profiles", methods=["GET"])
def api_profiles():
    return jsonify({"ok": True, "profiles": store.list_profiles()})


@app.route("/api/profiles/delete", methods=["POST"])
def api_delete_profile():
    try:
        name = request.get_json(force=True)["name"]
        store.delete_profile(name)
        return jsonify({"ok": True})
    except Exception as e:  # noqa
        return _err(e)


# ---------------- Khoi B: quet tu khoa + tai tao ----------------

def _attach_thumb_context(videos):
    """Che do 'tieu de BAM THEO thumbnail doi thu': voi moi video co anh, AI NHIN thumbnail + tieu de goc
    (3 luong song song) roi gan v['thumb_ctx']. Video nao loi/khong co anh thi bo qua (van tai tao binh thuong).
    Tra ve (so video doc duoc, so video loi)."""
    import requests as _rq
    from concurrent.futures import ThreadPoolExecutor

    def one(v):
        url = (v.get("thumbnail") or "").strip()
        if not url.startswith(("http://", "https://")):
            return None
        try:
            rimg = _rq.get(url, timeout=30)
            if rimg.status_code != 200 or not rimg.content:
                return False
            v["thumb_ctx"] = image_dna.read_competitor_pair(rimg.content, v.get("title", ""))
            return True
        except Exception:  # noqa
            return False

    with ThreadPoolExecutor(max_workers=3) as ex:
        res = list(ex.map(one, videos))
    return sum(1 for r in res if r is True), sum(1 for r in res if r is False)


@app.route("/api/scan", methods=["POST"])
def api_scan():
    try:
        data = request.get_json(force=True)
        keyword = data["keyword"].strip()
        mode = data.get("mode", "normal")          # 'normal' | 'trend48h'
        window = data.get("window", "1y")           # 3m/6m/1y/2y/3y
        count = int(data.get("count", 10))
        video_type = data.get("video_type", "both")   # 'both' | 'long' | 'short'
        output_language = data.get("output_language", "vi")
        profile_name = data.get("profile_name") or None
        # cho phep ep thi truong; mac dinh auto theo ngon ngu tu khoa
        region_code = data.get("region_code") or None
        relevance_language = data.get("relevance_language") or None

        hide_used = data.get("hide_used", True)
        hide_seen = data.get("hide_seen", False)

        if mode == "trend48h":
            window = "48h"
            if not data.get("count"):
                count = 10

        # Tu sua chinh ta tu khoa (YouTube API khong tu sua)
        original_keyword = keyword
        corrected_flag = False
        if data.get("autocorrect", True) and keyword:
            keyword, corrected_flag = title_dna.correct_keyword(keyword)

        # Loai trung theo TUNG TU KHOA
        exclude = set()
        used_all = store.used_ids_for(keyword)   # video da danh dau "Su dung" (de bao so luong dang an + danh dau trong bang)
        if hide_used:
            exclude |= used_all
        if hide_seen:
            exclude |= store.seen_ids_for(keyword)

        market = youtube.detect_market(keyword)
        market_obj = {"relevance_language": market[0], "region_code": market[1]}

        videos = youtube.search_and_rank(
            keyword, window=window, count=count,
            region_code=region_code, relevance_language=relevance_language,
            exclude_ids=exclude, video_type=video_type,
        )
        if not videos:
            if video_type == "long":
                note = "Khong tim thay VIDEO DAI moi cho tu khoa nay (thu 'Ca hai' hoac doi tu khoa)."
            elif video_type == "short":
                note = "Khong tim thay VIDEO SHORT moi cho tu khoa nay (thu 'Ca hai' hoac doi tu khoa)."
            elif exclude:
                note = "Khong con video moi cho tu khoa nay (da an video da dung/da quet)."
            else:
                note = "Khong tim thay video phu hop (thu doi tu khoa hoac noi rong moc thoi gian)."
            return jsonify({"ok": True, "rows": [], "note": note, "keyword": keyword,
                            "original_keyword": original_keyword, "corrected": corrected_flag,
                            "market": market_obj, "mode": mode, "window": window,
                            "used_count": len(used_all), "hide_used": bool(hide_used)})

        # Ghi nhan cac video vua hien = "da quet" cho tu khoa nay
        store.seen_add(keyword, [v["id"] for v in videos])

        profile = _profile_with_keywords(profile_name)

        thumb_note = ""
        if data.get("thumb_aware"):
            n_ok, n_bad = _attach_thumb_context(videos)
            thumb_note = "Tiêu đề bám thumbnail đối thủ: đọc được %d ảnh%s." % (
                n_ok, (", %d ảnh lỗi (các dòng đó tái tạo bình thường)" % n_bad) if n_bad else "")

        # O Quet tu khoa: tu khoa anh go de quet CHINH LA tu khoa chinh cua tieu de moi
        rows = title_dna.scan_decompose_recreate(videos, profile, output_language, main_keyword=keyword)
        for r in rows:
            r["da_dung"] = r.get("video_id") in used_all   # chi co y nghia khi KHONG an video da dung
        return jsonify({
            "ok": True,
            "thumb_note": thumb_note,
            "rows": rows,
            "used_count": len(used_all),
            "keyword": keyword,
            "original_keyword": original_keyword,
            "corrected": corrected_flag,
            "hide_used": bool(hide_used),
            "hide_seen": bool(hide_seen),
            "market": market_obj,
            "mode": mode,
            "window": window,
            "khuon": profile,            # cau truc khuon dang ap dung (None neu cong thuc chung)
            "khuon_name": profile_name,
        })
    except Exception as e:  # noqa
        return _err(e)


@app.route("/api/rewrite-titles", methods=["POST"])
def api_rewrite_titles():
    """Viet lai tieu de BAT KY (nhap tay hoac dan link video) theo khuon DNA kenh."""
    try:
        data = request.get_json(force=True)
        raw = data.get("inputs") or []
        if isinstance(raw, str):
            raw = raw.splitlines()
        inputs = [s.strip() for s in raw if s and s.strip()]
        if not inputs:
            raise RuntimeError("Chua nhap tieu de hoac link nao.")
        output_language = data.get("output_language", "vi")
        profile_name = data.get("profile_name") or None
        main_keyword = (data.get("main_keyword") or "").strip() or None  # None = AI tu chon tung tieu de

        # Tach link (lay tieu de goc that) vs tieu de nhap tay
        url_ids = {}
        for i, s in enumerate(inputs):
            if "youtu" in s.lower():
                vid = youtube.extract_video_id(s)
                if vid:
                    url_ids[i] = vid
        details = {}
        if url_ids:
            got = youtube.get_videos_details(list(dict.fromkeys(url_ids.values())))
            details = {v["id"]: v for v in got}

        videos, notes = [], []
        for i, s in enumerate(inputs):
            if i in url_ids:
                d = details.get(url_ids[i])
                if d:
                    videos.append(d)
                else:
                    notes.append("Link khong lay duoc tieu de (video an/xoa?): " + s[:50])
            else:
                videos.append({"id": "", "title": s, "views": 0, "url": "",
                               "thumbnail": "", "channelTitle": "", "duration_sec": 0})
        if not videos:
            return jsonify({"ok": True, "rows": [], "note": "; ".join(notes) or "Khong co tieu de hop le."})

        profile = _profile_with_keywords(profile_name)

        if data.get("thumb_aware"):   # chi video dan LINK moi co thumbnail
            n_ok, n_bad = _attach_thumb_context(videos)
            notes.append("Tiêu đề bám thumbnail đối thủ: đọc được %d ảnh%s." % (
                n_ok, (", %d ảnh lỗi" % n_bad) if n_bad else ""))

        rows = title_dna.scan_decompose_recreate(videos, profile, output_language, main_keyword=main_keyword)

        # Tu luu vao LICH SU viet lai (that bai khong lam sap viec chinh)
        try:
            hist = []
            for r in rows:
                if not r.get("tieu_de_tai_tao"):
                    continue
                hist.append({
                    "khuon_name": profile_name or "",
                    "lang": output_language,
                    "title_goc": r.get("title_goc", ""),
                    "tu_khoa_chinh": r.get("tu_khoa_chinh", ""),
                    "tieu_de_tai_tao": r.get("tieu_de_tai_tao", ""),
                    "dich_viet": r.get("dich_viet", ""),
                    "so_ky_tu": r.get("so_ky_tu", 0),
                    "ly_do": r.get("ly_do_tai_tao", ""),
                    "khung_index": r.get("khung_index", -1),
                })
            store.title_hist_add(hist)
        except Exception:
            pass

        return jsonify({"ok": True, "rows": rows, "note": "; ".join(notes),
                        "khuon": profile, "khuon_name": profile_name})
    except Exception as e:  # noqa
        return _err(e)


@app.route("/api/title-history", methods=["GET"])
def api_title_history():
    return jsonify({"ok": True, "history": store.title_hist_list()})


@app.route("/api/title-history/delete", methods=["POST"])
def api_title_history_delete():
    try:
        data = request.get_json(force=True)
        store.title_hist_delete((data.get("id") or "").strip())
        return jsonify({"ok": True})
    except Exception as e:  # noqa
        return _err(e)


@app.route("/api/title-history/clear", methods=["POST"])
def api_title_history_clear():
    store.title_hist_clear()
    return jsonify({"ok": True})


@app.route("/api/recreate-one", methods=["POST"])
def api_recreate_one():
    """Tao lai 1 tieu de theo 1 khung xuong cu the (nut 'Tao lai' xoay vong)."""
    try:
        data = request.get_json(force=True)
        title_goc = (data.get("title_goc") or "").strip()
        if not title_goc:
            raise RuntimeError("Thieu tieu de goc.")
        output_language = data.get("output_language", "vi")
        try:
            khung_index = int(data.get("khung_index", -1))
        except (TypeError, ValueError):
            khung_index = -1
        profile_name = data.get("profile_name") or None
        profile = _profile_with_keywords(profile_name)
        main_keyword = (data.get("main_keyword") or "").strip() or None
        tc = data.get("thumb_ctx") if isinstance(data.get("thumb_ctx"), dict) else None   # che do bam thumbnail doi thu
        out = title_dna.recreate_one(title_goc, profile, output_language, khung_index,
                                     main_keyword=main_keyword, thumb_ctx=tc)
        return jsonify({"ok": True, **out})
    except Exception as e:  # noqa
        return _err(e)


# ---------------- "Da dung" / loai trung ----------------

@app.route("/api/use-title", methods=["POST"])
def api_use_title():
    try:
        data = request.get_json(force=True)
        store.used_add({
            "keyword": data["keyword"],
            "video_id": data["video_id"],
            "title_goc": data.get("title_goc", ""),
            "tieu_de_final": data.get("tieu_de_final", ""),
            "channel": data.get("channel", ""),
            "views": data.get("views", 0),
        })
        return jsonify({"ok": True})
    except Exception as e:  # noqa
        return _err(e)


@app.route("/api/used", methods=["GET"])
def api_used_list():
    return jsonify({"ok": True, "used": store.used_list()})


@app.route("/api/used/delete", methods=["POST"])
def api_used_delete():
    try:
        data = request.get_json(force=True)
        store.used_delete(data["keyword"], data["video_id"])
        return jsonify({"ok": True})
    except Exception as e:  # noqa
        return _err(e)


@app.route("/api/seen/clear", methods=["POST"])
def api_seen_clear():
    try:
        store.seen_clear(request.get_json(force=True)["keyword"])
        return jsonify({"ok": True})
    except Exception as e:  # noqa
        return _err(e)


@app.route("/api/thumb-prompt", methods=["POST"])
def api_thumb_prompt():
    try:
        import requests as _rq
        data = request.get_json(force=True)
        title = (data.get("title") or "").strip()
        thumb_url = (data.get("thumbnail_url") or "").strip()
        if not title:
            raise RuntimeError("Thieu tieu de.")
        if not thumb_url:
            raise RuntimeError("Thieu anh thumbnail goc cua video.")
        rimg = _rq.get(thumb_url, timeout=30)
        if rimg.status_code != 200 or not rimg.content:
            raise RuntimeError("Khong tai duoc thumbnail goc.")
        result = image_dna.thumbnail_prompt_from_reference(title, rimg.content)
        return jsonify({"ok": True, **result})
    except Exception as e:  # noqa
        return _err(e)


# ---------------- Khoi C: DNA anh (tu anh tai len) ----------------

@app.route("/api/image-dna", methods=["POST"])
def api_image_dna():
    try:
        name = (request.form.get("name") or "").strip()
        dna_type = (request.form.get("type") or "ai").strip()
        if not name:
            raise RuntimeError("Hay dat ten cho du an.")
        thumbs = [f.read() for f in request.files.getlist("thumbnails") if f.filename]
        contents = [f.read() for f in request.files.getlist("contents") if f.filename]
        if dna_type == "ban_content":
            if not thumbs:
                raise RuntimeError("Hay tai len it nhat 1 anh thumbnail.")
            dna = image_dna.analyze_images(thumbs, [])
        else:
            if not thumbs and not contents:
                raise RuntimeError("Hay tai len it nhat 1 anh (thumbnail hoac noi dung).")
            dna = image_dna.analyze_images(thumbs, contents)
        store.save_dna(name, dna, dna_type=dna_type)
        return jsonify({"ok": True, "name": name, "dna": dna, "type": dna_type})
    except Exception as e:  # noqa
        return _err(e)


@app.route("/api/video-dna", methods=["POST"])
def api_video_dna():
    try:
        data = request.get_json(force=True)
        url = data["video_url"].strip()
        name = (data.get("name") or "").strip()
        dna_type = (data.get("type") or "ai").strip()
        if not name:
            raise RuntimeError("Hay dat ten cho du an.")
        # CHI lay THUMBNAIL (khong tai video, khong cat khung): DNA "anh noi dung" khong con duoc dung
        # (da bo SRT->prompt) nen bo di cho nhanh (~3s thay vi ~46s) va khoi can ffmpeg/yt-dlp.
        thumbs, frames, title = media.thumbnails_only_from_url(url)
        if not thumbs:
            raise RuntimeError("Khong lay duoc anh nao tu link nay.")
        dna = image_dna.analyze_images(thumbs, frames)
        store.save_dna(name, dna, dna_type=dna_type)
        return jsonify({
            "ok": True, "name": name, "dna": dna, "type": dna_type,
            "video_title": title, "frames_count": len(frames),
            "thumbs_count": len(thumbs), "has_thumbnail": bool(thumbs),
        })
    except Exception as e:  # noqa
        return _err(e)


@app.route("/api/dna", methods=["GET"])
def api_dna_list():
    t = request.args.get("type") or None
    return jsonify({"ok": True, "dna": store.list_dna(t)})


@app.route("/api/projects", methods=["GET"])
def api_projects():
    """Gop 'du an' theo ten: moi du an co the co khuon tieu de va/hoac DNA anh."""
    profs = {p["name"]: p for p in store.list_profiles()}
    dnas = {d["name"]: d for d in store.list_dna()}
    names = sorted(set(profs) | set(dnas), key=lambda s: s.lower())
    projects = []
    for nm in names:
        projects.append({
            "name": nm,
            "has_khuon": nm in profs,
            "has_dna": nm in dnas,
            "channel_url": profs.get(nm, {}).get("channel_url", ""),
        })
    return jsonify({"ok": True, "projects": projects})


@app.route("/api/dna/delete", methods=["POST"])
def api_dna_delete():
    try:
        data = request.get_json(force=True)
        store.delete_dna(data["name"], data.get("type"))
        return jsonify({"ok": True})
    except Exception as e:  # noqa
        return _err(e)


def _bc_thumb_dna(name):
    if name:
        p = store.get_dna(name, "ban_content")
        if p:
            return p["dna"].get("thumbnail_dna")
    return None


@app.route("/api/decompose-title", methods=["POST"])
def api_decompose_title():
    """Buoc boc tach tieu de (tieng Viet) de nguoi dung doc & sua."""
    try:
        data = request.get_json(force=True)
        title = (data.get("title") or "").strip()
        if not title:
            raise RuntimeError("Hay nhap tieu de.")
        thumb_dna = _bc_thumb_dna((data.get("name") or "").strip())
        return jsonify({"ok": True, **image_dna.decompose_title(title, thumb_dna)})
    except Exception as e:  # noqa
        return _err(e)


@app.route("/api/thumb-from-title", methods=["POST"])
def api_thumb_from_title():
    """Ban Content Buoc 2: tieu de (+ chu the/boi canh da sua) -> 3 prompt thumbnail."""
    try:
        data = request.get_json(force=True)
        title = (data.get("title") or "").strip()
        if not title:
            raise RuntimeError("Hay nhap tieu de.")
        thumb_dna = _bc_thumb_dna((data.get("name") or "").strip())
        result = image_dna.thumbnail_prompts_bancontent(
            title, thumb_dna,
            chu_the=data.get("chu_the"), boi_canh=data.get("boi_canh"),
        )
        return jsonify({"ok": True, **result})
    except Exception as e:  # noqa
        return _err(e)


@app.route("/api/thumb-breakdown", methods=["POST"])
def api_thumb_breakdown():
    """Buoc 1 cua tao thumbnail: BOC TACH tieu de theo cong thuc (van de / to mo / boi canh / tu huyet)
    roi suy ra hinh (chu the / hanh dong / cam xuc / the gioi canh). Nguoi dung duyet/sua truoc khi sinh prompt."""
    try:
        data = request.get_json(force=True)
        titles = [str(t).strip() for t in (data.get("titles") or []) if str(t).strip()]
        if not titles:
            raise RuntimeError("Hay nhap it nhat 1 tieu de.")
        if len(titles) > 60:
            raise RuntimeError("Toi da 60 tieu de moi lan boc tach.")
        thumb_dna = None
        name = (data.get("name") or "").strip()
        if name:
            d = store.get_dna(name, "ai")
            if d:
                thumb_dna = d["dna"].get("thumbnail_dna")
        bks = image_dna.decompose_titles_for_thumb(titles, thumb_dna)
        return jsonify({"ok": True, "items": [{"title": t, "breakdown": b} for t, b in zip(titles, bks)]})
    except Exception as e:  # noqa
        return _err(e)


@app.route("/api/thumb-breakdown-ref", methods=["POST"])
def api_thumb_breakdown_ref():
    """Tai tao thumbnail DOI THU theo DNA kenh minh: NHIN anh thumbnail doi thu, rut Y TUONG hinh anh,
    dien san o boc tach cho TIEU DE MOI. Nguoi dung duyet/sua roi moi sinh prompt (theo khoa font/bo cuc/nhan vat cua minh).
    Nhan items=[{title, thumbnail_url}]; loi 1 anh -> roi ve boc tach theo tieu de (co ghi chu), khong lam hong ca loat."""
    try:
        import requests as _rq
        from concurrent.futures import ThreadPoolExecutor
        data = request.get_json(force=True)
        items = [it for it in (data.get("items") or []) if isinstance(it, dict) and str(it.get("title") or "").strip()]
        if not items:
            raise RuntimeError("Hay chon it nhat 1 tieu de.")
        if len(items) > 30:
            raise RuntimeError("Toi da 30 thumbnail moi lan (moi anh la 1 luot AI nhin anh).")
        thumb_dna = None
        name = (data.get("name") or "").strip()
        if name:
            d = store.get_dna(name, "ai")
            if d:
                thumb_dna = d["dna"].get("thumbnail_dna")

        def one(it):
            title = str(it["title"]).strip()
            url = str(it.get("thumbnail_url") or "").strip()
            note = ""
            try:
                if not url.startswith(("http://", "https://")):
                    raise RuntimeError("Dong nay khong co anh thumbnail doi thu.")
                rimg = _rq.get(url, timeout=30)
                if rimg.status_code != 200 or not rimg.content:
                    raise RuntimeError("Khong tai duoc thumbnail doi thu.")
                bk = image_dna.breakdown_from_reference_thumb(rimg.content, title, thumb_dna)
                return {"title": title, "breakdown": bk, "from_ref": True}
            except Exception as e:  # noqa
                note = _short(e, 200)
            try:
                bk = image_dna.decompose_titles_for_thumb([title], thumb_dna)[0]
            except Exception as e2:  # noqa
                return {"title": title, "breakdown": None, "error": _short(e2, 200)}
            return {"title": title, "breakdown": bk, "from_ref": False, "note": note}

        with ThreadPoolExecutor(max_workers=3) as ex:
            out = list(ex.map(one, items))
        return jsonify({"ok": True, "items": out})
    except Exception as e:  # noqa
        return _err(e)


@app.route("/api/ai-thumb-from-title", methods=["POST"])
def api_ai_thumb_from_title():
    """Tab AI: tieu de -> 1 prompt thumbnail (AI style, CO CHU) theo DNA du an AI."""
    try:
        data = request.get_json(force=True)
        title = (data.get("title") or "").strip()
        if not title:
            raise RuntimeError("Hay nhap tieu de.")
        thumb_dna = None
        name = (data.get("name") or "").strip()
        if name:
            thumb_dna = image_dna.ensure_scene_slot(name)   # mau bo cuc cu -> tu nang cap o [[SCENE]] (1 lan)
        bk = data.get("breakdown") if isinstance(data.get("breakdown"), dict) else None
        result = image_dna.thumbnail_prompt_from_dna(title, thumb_dna, breakdown=bk)
        return jsonify({"ok": True, **result})
    except Exception as e:  # noqa
        return _err(e)


# ---------------- Chay HANG LOAT (aititles / bctitles) ----------------

def _scrub_batch(snap):
    """Xoa key that khoi moi thong bao loi truoc khi tra ve UI."""
    for it in snap.get("items", []):
        if it.get("error"):
            it["error"] = _short(it["error"], 300)
    return snap


@app.route("/api/batch/start", methods=["POST"])
def api_batch_start():
    try:
        data = request.get_json(force=True)
        snap = batch.start(data.get("kind", "aititles"), data.get("items", []))
        return jsonify({"ok": True, **_scrub_batch(snap)})
    except Exception as e:  # noqa
        return _err(e)


@app.route("/api/batch/status", methods=["GET"])
def api_batch_status():
    return jsonify({"ok": True, **_scrub_batch(batch.snapshot())})


@app.route("/api/batch/pause", methods=["POST"])
def api_batch_pause():
    return jsonify({"ok": True, **_scrub_batch(batch.pause())})


@app.route("/api/batch/resume", methods=["POST"])
def api_batch_resume():
    return jsonify({"ok": True, **_scrub_batch(batch.resume())})


@app.route("/api/batch/stop", methods=["POST"])
def api_batch_stop():
    return jsonify({"ok": True, **_scrub_batch(batch.stop())})


# ---------------- Cai dat: nhap key ngay tren giao dien ----------------

@app.route("/api/config", methods=["GET"])
def api_get_config():
    from services import config as cfg
    d = cfg.raw_config()

    def isset(k):
        v = d.get(k, "")
        return bool(v) and not str(v).startswith("DAN_")

    def hint(k):
        v = str(d.get(k, ""))
        if not v or v.startswith("DAN_"):
            return ""
        return "…" + v[-4:] if len(v) >= 4 else "••••"

    return jsonify({
        "ok": True,
        "llm_base_url": d.get("llm_base_url", ""),
        "llm_model": d.get("llm_model", ""),
        "model_analyze": d.get("model_analyze", "") or d.get("llm_model", ""),
        "model_create": d.get("model_create", "") or d.get("llm_model", ""),
        "llm_reasoning": d.get("llm_reasoning", "auto"),
        "has_llm_key": isset("llm_api_key"),
        "has_youtube_key": isset("youtube_api_key"),
        "llm_key_hint": hint("llm_api_key"),
        "youtube_key_hint": hint("youtube_api_key"),
        "ready": isset("llm_api_key") and isset("youtube_api_key"),
        "sheet_url": d.get("sheet_url", ""),
        "sheet_auto": bool(d.get("sheet_auto", False)),
    })


@app.route("/api/config", methods=["POST"])
def api_set_config():
    try:
        from services import config as cfg
        data = request.get_json(force=True)
        updates = {}
        for k in ("llm_api_key", "youtube_api_key", "llm_model", "llm_base_url", "sheet_url",
                  "llm_reasoning", "model_analyze", "model_create"):
            if k in data and str(data[k]).strip() != "":
                updates[k] = str(data[k]).strip()
        if "sheet_auto" in data:
            updates["sheet_auto"] = bool(data["sheet_auto"])
        # llm_model (truong bat buoc) = model sang tao -> config luon hop le + lam fallback
        if updates.get("model_create"):
            updates["llm_model"] = updates["model_create"]
        cfg.update_config(updates)
        return jsonify({"ok": True})
    except Exception as e:  # noqa
        return _err(e)


@app.route("/api/sheet/append", methods=["POST"])
def api_sheet_append():
    """Day cac dong len Google Sheet qua 'cong' Apps Script (URL luu trong config: sheet_url)."""
    try:
        import json as _json
        import requests
        from services import config as cfg
        data = request.get_json(force=True)
        rows = data.get("rows") or []
        url = (cfg.raw_config().get("sheet_url") or "").strip()
        if not url:
            raise RuntimeError("Chua cai link Google Sheet o tab Cai dat.")
        if not rows:
            raise RuntimeError("Khong co dong nao de gui.")
        resp = requests.post(
            url, data=_json.dumps({"rows": rows}).encode("utf-8"),
            headers={"Content-Type": "application/json"}, timeout=30,
        )
        body = (resp.text or "")[:300]
        if resp.status_code >= 400:
            raise RuntimeError("Google Sheet tu choi (HTTP %d): %s" % (resp.status_code, body))
        return jsonify({"ok": True, "count": len(rows), "resp": body})
    except Exception as e:  # noqa
        return _err(e)


def _friendly_llm(msg):
    low = msg.lower()
    if "invalid api key" in low or "missing api key" in low or "401" in low:
        return "Key 9router không hợp lệ. Kiểm tra lại key."
    if "refused" in low or "10061" in low or "max retries" in low or "connection" in low:
        return "Không kết nối được 9router — kiểm tra app 9router đã mở và đúng địa chỉ http://127.0.0.1:20128/v1."
    return msg


def _friendly_yt(msg):
    low = msg.lower()
    if "api key not valid" in low or "api_key_invalid" in low:
        return "Key YouTube không hợp lệ. Cần key YouTube Data API v3 (dạng 'AIza...'), KHÔNG phải key 9router."
    if "quota" in low:
        return "Đã hết quota YouTube hôm nay. Thử lại ngày mai."
    if "not been used" in low or "accessnotconfigured" in low or "disabled" in low or "403" in low:
        return "Chưa bật 'YouTube Data API v3' cho key này trong Google Cloud Console."
    return msg


@app.route("/api/check-api", methods=["POST"])
def api_check_api():
    from services import config as cfg
    out = {"llm": {"ok": False, "message": ""}, "youtube": {"ok": False, "message": ""}}

    # --- 9router / Gemini ---
    if not cfg.key_is_set("llm_api_key"):
        out["llm"]["message"] = "Chưa nhập key 9router."
    else:
        try:
            from services import llm
            reply = llm.ping()
            out["llm"] = {"ok": True, "message": "Kết nối OK — model phản hồi: " + _short(reply, 40)}
        except Exception as e:  # noqa
            out["llm"]["message"] = _friendly_llm(_short(e))

    # --- YouTube ---
    if not cfg.key_is_set("youtube_api_key"):
        out["youtube"]["message"] = "Chưa nhập key YouTube."
    else:
        try:
            n = youtube.ping()
            out["youtube"] = {"ok": True, "message": "Kết nối OK."}
        except Exception as e:  # noqa
            out["youtube"]["message"] = _friendly_yt(_short(e))

    return jsonify({"ok": True, **out})


@app.route("/api/suggest", methods=["GET"])
def api_suggest():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"ok": True, "suggestions": []})
    hl = youtube.detect_market(q)[0]
    return jsonify({"ok": True, "suggestions": youtube.suggest(q, hl=hl)})


@app.route("/api/keyword-ideas", methods=["GET"])
def api_keyword_ideas():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"ok": True, "ideas": []})
    hl = youtube.detect_market(q)[0]
    return jsonify({"ok": True, "ideas": youtube.suggest_expand(q, hl=hl)})


@app.route("/api/health")
def health():
    return jsonify({"ok": True})


def _is_port_in_use(port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


if __name__ == "__main__":
    import threading
    import webbrowser

    PORT = int(os.environ.get("YTDNA_PORT", "5000"))
    URL = "http://127.0.0.1:{}".format(PORT)
    # Voi use_reloader, tien trinh con (server that) co WERKZEUG_RUN_MAIN=true.
    reloader_child = os.environ.get("WERKZEUG_RUN_MAIN") == "true"

    if not reloader_child:
        # Neu server da chay (tranh crash "cong dang ban") -> chi mo trinh duyet roi thoat.
        if _is_port_in_use(PORT):
            print("Phan mem dang chay san. Mo trinh duyet: " + URL)
            webbrowser.open(URL)
            raise SystemExit(0)
        print("=" * 60)
        print(" YT DNA Tool dang chay tai:  " + URL)
        print(" Trinh duyet se tu mo. Dong cua so nay de DUNG phan mem.")
        print("=" * 60)
        # Tu mo trinh duyet sau khi server kip khoi dong (tat bang YTDNA_NO_BROWSER=1)
        if os.environ.get("YTDNA_NO_BROWSER") != "1":
            threading.Timer(1.5, lambda: webbrowser.open(URL)).start()

    # threaded=True: thao tac dai khong lam dong bang thao tac khac.
    # use_reloader=True: tu nap lai khi code backend thay doi -> khoi phai restart tay.
    # (YTDNA_NO_RELOAD=1 de tat reloader khi can - chi dung khi test.)
    use_rl = os.environ.get("YTDNA_NO_RELOAD") != "1"
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True, use_reloader=use_rl)
