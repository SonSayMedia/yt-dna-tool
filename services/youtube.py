"""
Goi YouTube Data API v3 qua REST (chi can requests, khong can thu vien google).
Chi phi quota: search.list = 100 diem/lan, videos.list & channels.list = 1 diem/lan.
"""
import json
import re
from datetime import datetime, timedelta, timezone

import requests

from .config import load_config

_BASE = "https://www.googleapis.com/youtube/v3"
_TIMEOUT = 30


def _key():
    return load_config()["youtube_api_key"]


def _get(path, params):
    params = dict(params)
    params["key"] = _key()
    resp = requests.get(_BASE + "/" + path, params=params, timeout=_TIMEOUT)
    if resp.status_code >= 400:
        raise RuntimeError(
            "Loi YouTube API ({}): {}".format(resp.status_code, resp.text[:400])
        )
    return resp.json()


def ping():
    """Goi 1 endpoint re (1 quota) de kiem tra key YouTube co hop le khong."""
    data = _get("i18nLanguages", {"part": "snippet", "hl": "en"})
    return len(data.get("items", []))


def suggest(keyword, hl="vi"):
    """
    Lay goi y tu khoa THAT cua YouTube (giong thanh tim kiem) qua endpoint autocomplete.
    Khong ton quota API. Neu loi thi tra ve rong (khong lam gay chuong trinh).
    """
    if not keyword or not keyword.strip():
        return []
    try:
        r = requests.get(
            "https://suggestqueries.google.com/complete/search",
            params={"client": "firefox", "ds": "yt", "q": keyword, "hl": hl},
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        r.encoding = "utf-8"
        data = json.loads(r.text)  # dang: ["q", ["goi y 1", "goi y 2", ...]]
        if isinstance(data, list) and len(data) >= 2 and isinstance(data[1], list):
            return [s for s in data[1] if isinstance(s, str)][:8]
    except Exception:
        pass
    return []


def suggest_expand(keyword, hl="vi", max_results=60):
    """
    Khai thac NHIEU y tuong tu khoa lien quan (kieu nghien cuu tu khoa):
    ghep tu khoa goc voi a-z va cac tu hoi roi hoi bo goi y cua YouTube, gom lai.
    Mien phi (khong ton quota API).
    """
    import concurrent.futures

    keyword = (keyword or "").strip()
    if not keyword:
        return []

    letters = list("abcdefghijklmnopqrstuvwxyz")
    if hl == "vi":
        mods = ["cách", "tại sao", "làm sao", "là gì", "có nên", "khi nào",
                "ở đâu", "cho người mới", "thực chiến", "ví dụ"]
    else:
        mods = ["how", "why", "what", "best", "for", "without",
                "vs", "explained", "tips", "guide"]

    queries = [keyword]
    queries += [keyword + " " + c for c in letters]
    queries += [keyword + " " + m for m in mods]
    queries += [m + " " + keyword for m in mods]

    out, seen = [], set()
    seed = keyword.lower()

    def fetch(q):
        return suggest(q, hl)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        for res in ex.map(fetch, queries):
            for s in res:
                key = s.strip().lower()
                if key and key != seed and key not in seen:
                    seen.add(key)
                    out.append(s.strip())
    return out[:max_results]


# ---------- phat hien thi truong theo ngon ngu dau vao ----------

def detect_market(keyword):
    """Doan (relevance_language, region_code) tu ngon ngu cua tu khoa."""
    text = keyword or ""
    # tieng Viet (co dau dac trung)
    if re.search(r"[ăâđêôơưĂÂĐÊÔƠƯáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]", text):
        return ("vi", "VN")
    # CJK
    if re.search(r"[一-鿿]", text):
        return ("zh", "CN")
    if re.search(r"[぀-ヿ]", text):
        return ("ja", "JP")
    if re.search(r"[가-힯]", text):
        return ("ko", "KR")
    if re.search(r"[฀-๿]", text):
        return ("th", "TH")
    # mac dinh: tieng Anh / My
    return ("en", "US")


def window_to_published_after(window):
    """window: '48h','1m','3m','6m','1y','2y','3y' -> chuoi RFC3339 (publishedAfter)."""
    now = datetime.now(timezone.utc)
    mapping_days = {
        "48h": 2,
        "1m": 30,
        "3m": 90,
        "6m": 180,
        "1y": 365,
        "2y": 730,
        "3y": 1095,
    }
    days = mapping_days.get(window, 365)
    after = now - timedelta(days=days)
    return after.strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------- nhan dien Short vs Video dai ----------

_ISO_DUR = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")


def _duration_to_sec(iso):
    """ISO 8601 (vd 'PT3M45S') -> so giay. Tra 0 neu khong doc duoc."""
    m = _ISO_DUR.fullmatch(iso or "")
    if not m:
        return 0
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + s


def _is_short_by_url(video_id):
    """
    Nhan dien Short chinh xac: mo 'youtube.com/shorts/<id>'.
    - 200  -> DUNG la Short (video doc).
    - 3xx  -> chuyen huong sang /watch => video DAI (khong phai short).
    - None -> khong xac dinh (loi mang) => nguoi goi tu quyet theo duration.
    """
    try:
        r = requests.head(
            "https://www.youtube.com/shorts/" + video_id,
            allow_redirects=False, timeout=8,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        if r.status_code == 200:
            return True
        if 300 <= r.status_code < 400:
            return False
    except Exception:
        pass
    return None


def classify_shorts(videos):
    """
    Gan v['is_short'] = True/False cho tung video.
    Toi uu: duration > 180s => chac chan video DAI (Short toi da 3 phut) -> khoi goi HTTP.
    Con lai (<=180s) -> kiem tra URL /shorts/ song song. Loi mang -> fallback: <=60s = short.
    """
    import concurrent.futures
    todo = []
    for v in videos:
        d = v.get("duration_sec", 0) or 0
        if d > 180:
            v["is_short"] = False
        else:
            todo.append(v)

    def work(v):
        r = _is_short_by_url(v["id"])
        if r is None:
            r = (v.get("duration_sec", 0) or 0) <= 60
        v["is_short"] = bool(r)

    if todo:
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
            list(ex.map(work, todo))
    return videos


# ---------- tim kiem video theo tu khoa ----------

def search_and_rank(keyword, window="1y", count=10, region_code=None,
                    relevance_language=None, want_pool=50, exclude_ids=None, emulate=True,
                    video_type="both"):
    """
    Tim video theo tu khoa, lay thong ke that, xep theo TONG VIEW giam dan.
    emulate=True: tron ung vien tu 2 bang xep hang cua YouTube -> 'relevance'
    (giong thanh tim kiem) + 'viewCount' (nhieu view) roi xep lai theo view.
    exclude_ids = tap ID can loai (da dung / da quet).
    """
    exclude_ids = exclude_ids or set()
    if region_code is None or relevance_language is None:
        rl, rc = detect_market(keyword)
        relevance_language = relevance_language or rl
        region_code = region_code or rc

    base = {
        "part": "snippet",
        "q": keyword,
        "type": "video",
        "maxResults": 50,
        "publishedAfter": window_to_published_after(window),
        "regionCode": region_code,
        "relevanceLanguage": relevance_language,
    }
    orders = ["relevance", "viewCount"] if emulate else ["viewCount"]
    ids, seen = [], set()
    for od in orders:
        params = dict(base)
        params["order"] = od
        data = _get("search", params)
        for it in data.get("items", []):
            vid = it.get("id", {}).get("videoId")
            if vid and vid not in seen:
                seen.add(vid)
                ids.append(vid)
    if not ids:
        return []
    videos = get_videos_details(ids)
    if exclude_ids:
        videos = [v for v in videos if v["id"] not in exclude_ids]
    videos.sort(key=lambda v: v["views"], reverse=True)

    if video_type in ("long", "short"):
        want_short = (video_type == "short")
        pool = videos[:50]  # chi phan loai top-50 theo view (gioi han so HTTP -> nhanh hon)
        classify_shorts(pool)
        picked = [v for v in pool if v.get("is_short") == want_short]
        return picked[:count]

    # 'both': khong loc; chi phan loai top-N de hien nhan Dai/Short (nhe)
    top = videos[:count]
    classify_shorts(top)
    return top


def get_videos_details(video_ids):
    """Lay tieu de, view, ngay dang, kenh, thumbnail cho danh sach id."""
    out = []
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i + 50]
        data = _get("videos", {
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(chunk),
        })
        for it in data.get("items", []):
            sn = it.get("snippet", {})
            st = it.get("statistics", {})
            cd = it.get("contentDetails", {})
            thumbs = sn.get("thumbnails", {})
            thumb = (thumbs.get("high") or thumbs.get("medium") or thumbs.get("default") or {}).get("url", "")
            out.append({
                "id": it["id"],
                "title": sn.get("title", ""),
                "views": int(st.get("viewCount", 0)),
                "publishedAt": sn.get("publishedAt", ""),
                "channelTitle": sn.get("channelTitle", ""),
                "thumbnail": thumb,
                "url": "https://www.youtube.com/watch?v=" + it["id"],
                "duration_sec": _duration_to_sec(cd.get("duration", "")),
            })
    return out


_VIDEO_ID = re.compile(r"(?:v=|/shorts/|youtu\.be/|/embed/|/live/|/v/)([\w-]{11})")


def extract_video_id(url):
    """Lay videoId (11 ky tu) tu link YouTube nhieu dinh dang. None neu khong phai link video."""
    if not url:
        return None
    m = _VIDEO_ID.search(url)
    return m.group(1) if m else None


# ---------- phan tich kenh ----------

def resolve_channel_id(channel_url_or_handle):
    """Chap nhan link kenh nhieu dinh dang -> channelId (UC...)."""
    s = channel_url_or_handle.strip()

    m = re.search(r"/channel/(UC[\w-]+)", s)
    if m:
        return m.group(1)

    # @handle (trong link hoac go truc tiep)
    m = re.search(r"@([\w.\-]+)", s)
    if m:
        data = _get("channels", {"part": "id", "forHandle": "@" + m.group(1)})
        items = data.get("items", [])
        if items:
            return items[0]["id"]

    # /user/Name
    m = re.search(r"/user/([\w.\-]+)", s)
    if m:
        data = _get("channels", {"part": "id", "forUsername": m.group(1)})
        items = data.get("items", [])
        if items:
            return items[0]["id"]

    # /c/Name hoac ten tuy y -> tim kiem kenh
    name = s
    m = re.search(r"/c/([\w.\-]+)", s)
    if m:
        name = m.group(1)
    data = _get("search", {"part": "snippet", "q": name, "type": "channel", "maxResults": 1})
    items = data.get("items", [])
    if items:
        return items[0]["id"]["channelId"]

    raise RuntimeError("Khong tim duoc kenh tu: " + channel_url_or_handle)


def get_channel_top_videos(channel_url, count=20):
    """Lay 'count' video nhieu view nhat cua kenh (co tieu de + thumbnail)."""
    channel_id = resolve_channel_id(channel_url)
    data = _get("search", {
        "part": "snippet",
        "channelId": channel_id,
        "type": "video",
        "order": "viewCount",
        "maxResults": min(count, 50),
    })
    ids = [it["id"]["videoId"] for it in data.get("items", []) if it.get("id", {}).get("videoId")]
    videos = get_videos_details(ids)
    videos.sort(key=lambda v: v["views"], reverse=True)
    return videos[:count]
