"""
Khoi C (nhanh 3b): dan link video -> lay thumbnail + cat ~N khung hinh noi dung.
Dung yt-dlp de tai ban do phan giai thap, ffmpeg de cat khung.
"""
import glob
import os
import re
import subprocess
import tempfile

import requests

from . import youtube

_YT_ID = [
    r"[?&]v=([\w-]{11})",
    r"youtu\.be/([\w-]{11})",
    r"/shorts/([\w-]{11})",
    r"/embed/([\w-]{11})",
]


def extract_video_id(url):
    for p in _YT_ID:
        m = re.search(p, url)
        if m:
            return m.group(1)
    s = url.strip()
    if re.fullmatch(r"[\w-]{11}", s):
        return s
    raise RuntimeError("Khong nhan dang duoc video id tu link: " + url)


def fetch_thumbnail_bytes(video_id):
    """Lay anh thumbnail (bytes) + tieu de qua YouTube API. Can youtube_api_key."""
    try:
        details = youtube.get_videos_details([video_id])
    except Exception:
        return None, ""
    if not details:
        return None, ""
    v = details[0]
    url = v.get("thumbnail")
    title = v.get("title", "")
    if not url:
        return None, title
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            return r.content, title
    except Exception:
        pass
    return None, title


def download_low_res(url, workdir):
    """Tai ban do phan giai thap nhat vao workdir. Tra ve (path, duration_giay)."""
    import yt_dlp  # import tre de app van chay du chua cai

    out = os.path.join(workdir, "video.%(ext)s")
    # Chi can hinh de cat khung (khong can tieng) -> uu tien luong video-only nho.
    # Chuoi fallback rong de "chong truot" voi moi loai video.
    opts = {
        "format": "worstvideo[height>=240]/worstvideo/worst/best[height<=480]/best",
        "outtmpl": out,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "noprogress": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    files = glob.glob(os.path.join(workdir, "video.*"))
    if not files:
        raise RuntimeError("Tai video that bai (yt-dlp khong tao ra file).")
    return files[0], int(info.get("duration") or 0)


def sample_frames(video_path, duration, n, workdir):
    """Cat n khung hinh deu nhau (tranh 2 dau video). Tra ve list bytes JPEG."""
    if duration <= 0:
        duration = 60
    frames = []
    for i in range(n):
        t = duration * (i + 0.5) / n
        outp = os.path.join(workdir, "f{}.jpg".format(i))
        cmd = ["ffmpeg", "-ss", str(round(t, 2)), "-i", video_path,
               "-frames:v", "1", "-q:v", "3", "-y", outp]
        subprocess.run(cmd, capture_output=True)
        if os.path.exists(outp):
            with open(outp, "rb") as fh:
                frames.append(fh.read())
    return frames


def frames_from_video_url(url, n=10):
    """Tra ve (thumbnail_bytes_list, content_frames_bytes_list, title)."""
    vid = extract_video_id(url)
    thumb_bytes, title = fetch_thumbnail_bytes(vid)
    with tempfile.TemporaryDirectory() as wd:
        path, dur = download_low_res(url, wd)
        frames = sample_frames(path, dur, n=n, workdir=wd)
    thumbs = [thumb_bytes] if thumb_bytes else []
    return thumbs, frames, title


def is_channel_url(url):
    """Phan biet link KENH (@handle, /channel, /c, /user) voi link VIDEO."""
    s = (url or "").lower()
    if "watch?v=" in s or "youtu.be/" in s or "/shorts/" in s or "/embed/" in s:
        return False
    if "@" in s or "/channel/" in s or "/c/" in s or "/user/" in s:
        return True
    return False


def _download_image(url):
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200 and r.content:
            return r.content
    except Exception:
        pass
    return None


def dna_inputs_from_channel(channel_url, n_frames=12, top_videos=20):
    """
    Tu link KENH: lay thumbnail cua ~8 video top (hoc phong cach thumbnail)
    + cat khung hinh tu video top 1 (hoc phong cach anh noi dung).
    Tra ve (thumbnail_bytes_list, content_frames_list, label).
    """
    vids = youtube.get_channel_top_videos(channel_url, count=top_videos)
    if not vids:
        raise RuntimeError("Khong lay duoc video nao tu kenh nay.")
    thumbs = []
    for v in vids:
        b = _download_image(v.get("thumbnail", ""))
        if b:
            thumbs.append(b)
    contents = []
    try:
        with tempfile.TemporaryDirectory() as wd:
            path, dur = download_low_res(vids[0]["url"], wd)
            contents = sample_frames(path, dur, n=n_frames, workdir=wd)
    except Exception:
        contents = []  # khong cat duoc khung thi van co thumbnail de phan tich
    label = "Kênh: " + (vids[0].get("channelTitle") or channel_url)
    return thumbs, contents, label


def dna_inputs_from_url(url, n_frames=10):
    """Nhan link KENH hoac link VIDEO -> (thumbs, contents, label)."""
    if is_channel_url(url):
        return dna_inputs_from_channel(url, n_frames=n_frames)
    return frames_from_video_url(url, n=n_frames)


def thumbnails_only_from_url(url, top_videos=20):
    """
    CHI lay thumbnail (cho kenh Ban Content): khong tai video, khong cat khung.
    Kenh -> thumbnail cua ~10 video top. Video -> thumbnail cua video do.
    Tra ve (thumbnail_bytes_list, [], label).
    """
    if is_channel_url(url):
        vids = youtube.get_channel_top_videos(url, count=top_videos)
        if not vids:
            raise RuntimeError("Khong lay duoc video nao tu kenh nay.")
        thumbs = []
        for v in vids:
            b = _download_image(v.get("thumbnail", ""))
            if b:
                thumbs.append(b)
        label = "Kênh: " + (vids[0].get("channelTitle") or url)
        return thumbs, [], label
    # link video don le
    vid = extract_video_id(url)
    tb, title = fetch_thumbnail_bytes(vid)
    return ([tb] if tb else []), [], (title or url)


def ffmpeg_available():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True)
        return True
    except Exception:
        return False
