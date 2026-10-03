"""
Khoi A + B: Boc tach tieu de theo cong thuc cua anh, rut khuon kenh (Title DNA),
va tai tao tieu de moi theo khuon.
"""
from . import llm

# ---- Cong thuc boc tach 3 thanh phan + bo quy tac ky thuat (IP cua anh) ----
KHUNG_CONG_THUC = """
CONG THUC BOC TACH 1 TIEU DE = 3 THANH PHAN:
1. Tu khoa cam xuc / VAN DE (Keyword - cho SEO): cum tu chinh khan gia go tim,
   nen nam nua dau tieu de. Vi du: "Cach nhan biet nguoi noi doi", "Thao tung tam ly".
2. Yeu to Tam ly - KHOANG TRONG TO MO / NOI DAU (Click-trigger - cho con nguoi):
   "luoi cau" cam xuc, danh vao 1 trong 4 tu huyet: So hai, To mo, Tham lam (ket qua de dang),
   Canh giac. Vi du: "...Chi Trong 1 Phut", "...Dang Am Tham Huy Hoai Ban", "...Ma Ban Khong He Biet".
3. Cum BOI CANH / DONG GOI (Format/Context): giup dinh hinh the loai/do tin,
   thuong dung so, ngoac vuong [ ], ngoac tron ( ). Vi du: "[Tam ly hoc]", "(Moi 2026)", "5 Dau hieu".

CONG THUC GHEP THAM KHAO: [Boi canh/Con so] + [Tu khoa cam xuc] + [Yeu to Tam ly].

BO QUY TAC KY THUAT (BAT BUOC khi TAI TAO tieu de):
- Tu khoa chinh + yeu to giat gan nhat PHAI nam trong 50 ky tu dau.
- Do dai tong: khong che 65-75 ky tu (tuy ngon ngu).
- Viet Hoa Chu Cai Dau moi tu quan trong; CHI IN HOA TOAN BO 1-2 tu cam xuc manh nhat.
- CAM in hoa toan bo ca tieu de (bi tinh spam).
- Tan dung ky tu suc manh: [ ] ( ) | - de phan tach cho de doc.
"""


# ---------------- Khoi A: rut khuon kenh tu 20 tieu de ----------------

def correct_keyword(keyword):
    """
    Sua loi chinh ta RO RANG cua tu khoa truoc khi quet (API YouTube khong tu sua).
    Giu nguyen ngon ngu & y nghia, khong dich, khong them bot. Tra ve (corrected, changed).
    """
    system = (
        "Ban la bo sua chinh ta cho tu khoa tim kiem YouTube. "
        "CHI sua loi chinh ta/danh may RO RANG. GIU nguyen ngon ngu goc, giu nguyen y nghia, "
        "KHONG dich sang ngon ngu khac, KHONG them hay bot tu, KHONG mo rong. "
        "Neu tu khoa da dung thi giu nguyen."
    )
    user = (
        'Tu khoa: "' + keyword + '"\n'
        'Tra ve JSON: {"corrected": "<tu khoa da sua>", "changed": true/false}'
    )
    try:
        r = llm.chat_json(system, user, temperature=0)
        corrected = (r.get("corrected") or keyword).strip()
        if not corrected:
            return keyword, False
        changed = corrected.strip().lower() != keyword.strip().lower()
        return corrected, changed
    except Exception:
        return keyword, False


def _norm(s):
    return " ".join((s or "").lower().split())


def _clean_kw_list(values, limit=12):
    """Lam sach danh sach tu khoa: bo rong/trung, cat toi da `limit`."""
    out, seen = [], set()
    for k in (values or []):
        s = str(k).strip().strip("\"'")
        key = _norm(s)
        if s and key not in seen:
            seen.add(key)
            out.append(s)
    return out[:limit]


def _channel_keywords(profile):
    return _clean_kw_list((profile or {}).get("tu_khoa_chien_thang"))


def extract_channel_keywords(titles):
    """Rut 'TU KHOA CHIEN THANG' cua kenh tu cac tieu de nhieu view (giu nguyen ngon ngu tieu de)."""
    system = (
        "Ban la chuyen gia SEO YouTube. Tu danh sach tieu de NHIEU VIEW NHAT cua 1 kenh, hay rut ra "
        "'TU KHOA CHIEN THANG' cua kenh: cac cum tu khoa (1-3 tu, la chu de/danh tu) LAP LAI nhieu nhat "
        "va dang dan dat luot xem. BO cac tu chung chung (cach, tai sao, the, how, why, what, ...). "
        "GIU NGUYEN ngon ngu cua tieu de."
    )
    user = (
        "Cac tieu de:\n" + "\n".join("- " + t for t in titles)
        + '\n\nTra ve JSON: {"tu_khoa_chien_thang": ["...", "..."]} (6-12 cum, xep tu quan trong nhat).'
    )
    r = llm.chat_json(system, user, temperature=0.2, role="analyze")
    return _clean_kw_list(r.get("tu_khoa_chien_thang") if isinstance(r, dict) else r)


def analyze_channel(titles):
    system = (
        "Ban la chuyen gia phan tich tieu de YouTube. "
        "Dua tren cong thuc duoi day, hay boc tach cac tieu de mau cua MOT kenh "
        "va rut ra 'khuon dat tieu de' dac trung cua kenh do (Title DNA).\n" + KHUNG_CONG_THUC
        + "\nCac truong mo ta (vi_tri_tu_khoa, kieu_in_hoa, giong_dieu, ghi_chu, tu_huyet_chu_dao) "
        "viet bang TIENG VIET CO DAU day du."
        + "\ntu_khoa_chien_thang = cac cum tu khoa (1-3 tu, la chu de) LAP LAI nhieu nhat o tieu de top view; "
        "bo tu chung chung (cach, tai sao, how, why...); giu NGUYEN ngon ngu cua tieu de."
    )
    user = (
        "Day la cac tieu de nhieu view nhat cua 1 kenh. Hay phan tich va tra ve JSON dung cau truc:\n"
        "{\n"
        '  "do_dai_trung_binh": <so ky tu trung binh>,\n'
        '  "tu_huyet_chu_dao": ["To mo", ...],\n'
        '  "vi_tri_tu_khoa": "mo ta thoi quen dat tu khoa (dau/giua)",\n'
        '  "ky_tu_dac_biet_hay_dung": ["[]", "()", "|", "so", ...],\n'
        '  "kieu_in_hoa": "mo ta thoi quen in hoa",\n'
        '  "giong_dieu": "mo ta chat giong tong the",\n'
        '  "khung_xuong_tieu_de": ["[So] + [Chu de] + [Yeu to tam ly manh]", "..."],\n'
        '  "tu_khoa_chien_thang": ["cum tu khoa 1", "cum tu khoa 2", "... (6-12 cum)"],\n'
        '  "ghi_chu": "nhung dac diem rieng khac khien tieu de kenh nay hut view"\n'
        "}\n\n"
        "Cac tieu de:\n" + "\n".join("- " + t for t in titles)
    )
    profile = llm.chat_json(system, user, temperature=0.3, role="analyze")
    kws = _clean_kw_list(profile.get("tu_khoa_chien_thang")) if isinstance(profile, dict) else []
    if not kws:  # model quen tra truong nay -> rut rieng 1 lan
        try:
            kws = extract_channel_keywords(titles)
        except Exception:
            kws = []
    profile["tu_khoa_chien_thang"] = kws
    return profile


# ---------------- Khoi B: boc tach + tai tao theo khuon ----------------

def _khung_list_of(profile):
    if not profile:
        return []
    kl = profile.get("khung_xuong_tieu_de") or []
    return [str(k).strip() for k in kl if str(k).strip()]


def _lang_name(output_language):
    return {
        "vi": "Tieng Viet", "en": "English", "zh": "Tieng Trung",
        "ja": "Tieng Nhat", "ko": "Tieng Han", "th": "Tieng Thai",
        "es": "Espanol (Tay Ban Nha)",
    }.get(output_language, output_language)


def _keyword_rules(main_keyword, channel_kws, lang):
    """Quy tac TU KHOA (uu tien cao nhat) chen vao prompt tai tao/viet lai tieu de."""
    rules = ["QUY TAC TU KHOA (BAT BUOC, uu tien CAO NHAT):"]
    if main_keyword:
        rules.append(
            '- TU KHOA CHINH = "%s". Tieu de tai tao PHAI chua tu khoa nay trong 50 ky tu DAU. '
            "Neu ngon ngu dau ra (%s) khac ngon ngu cua tu khoa, dung ban dich TU NHIEN cua tu khoa "
            "trong ngon ngu dau ra (giu nguyen neu la ten rieng)." % (main_keyword, lang)
        )
    else:
        rules.append(
            "- Voi MOI tieu de goc, tu chon 1 TU KHOA CHINH (cum 1-3 tu, chu de SEO cua tieu de) va ghi vao "
            "'tu_khoa_chinh'. Tieu de tai tao PHAI chua tu khoa nay trong 50 ky tu DAU."
        )
    rules.append(
        "- TU KHOA LEN VIEW: tim trong TIEU DE GOC (da co nhieu view) cum tu khoa da giup no len view va ghi vao "
        "'tu_khoa_len_view'. Neu con cho (tong <= ~75 ky tu) hay GIU cum do (dich sang ngon ngu dau ra neu can)."
    )
    if channel_kws:
        rules.append(
            "- TU KHOA CHIEN THANG CUA KENH: " + " | ".join(channel_kws) + ". Tieu de tai tao PHAI chua IT NHAT 1 tu khoa "
            "trong danh sach nay (co the trung voi tu khoa chinh; dich sang ngon ngu dau ra neu can). "
            "'tu_khoa_kenh' = CHINH XAC doan chu cua tu khoa kenh NHU XUAT HIEN trong tieu_de_tai_tao "
            "(da dich sang ngon ngu dau ra neu can, copy y nguyen tung ky tu)."
        )
    rules.append(
        "- THU TU UU TIEN khi xung dot: (1) tu khoa chinh trong 50 ky tu dau > (2) it nhat 1 tu khoa chien thang "
        "cua kenh > (3) giu tu khoa len view cua tieu de goc neu con cho. Van PHAI theo KHUNG XUONG + do dai 65-75 ky tu."
    )
    rules.append(
        "- 'tu_khoa_trong_tieu_de' = CHINH XAC doan chu cua TU KHOA CHINH nhu no xuat hien trong tieu_de_tai_tao "
        "(copy y nguyen tung ky tu)."
    )
    return "\n".join(rules)


def _kw_fields(title, main_keyword, r, channel_kws):
    """Kiem tra tieu de da du tu khoa chua. r = dict LLM tra ve (co the rong).
    Tra ve cac truong tu_khoa_* + kw_ok (None neu chua co tieu de)."""
    t = _norm(title)
    typed = (main_keyword or "").strip()
    declared = (r.get("tu_khoa_trong_tieu_de") or "").strip()
    main_decl = (r.get("tu_khoa_chinh") or "").strip()
    kenh_decl = (r.get("tu_khoa_kenh") or "").strip()

    def in_front(k):  # tu khoa co mat va BAT DAU trong 50 ky tu dau
        kn = _norm(k)
        pos = t.find(kn) if kn else -1
        return 0 <= pos < 50

    main_ok = any(in_front(c) for c in (typed, declared) if c)
    kenh_ok = None
    if channel_kws:
        kenh_ok = any(_norm(k) in t for k in channel_kws) or bool(kenh_decl and _norm(kenh_decl) in t)
    shown = declared if (declared and _norm(declared) in t) else (typed or main_decl)
    return {
        "tu_khoa_chinh": shown,
        "tu_khoa_len_view": (r.get("tu_khoa_len_view") or "").strip(),
        "tu_khoa_kenh": kenh_decl,
        "kw_main_ok": main_ok if t else None,
        "kw_kenh_ok": kenh_ok if t else None,
        "kw_ok": (main_ok and kenh_ok is not False) if t else None,
    }


# Che do "TIEU DE BAM THEO THUMBNAIL DOI THU": AI da NHIN thumbnail -> hieu cap (anh + chu + tieu de) dang hua dieu gi.
THUMB_PAIR_RULE = (
    "MOI tieu de goc co the kem THUMBNAIL DOI THU da duoc doc (truong `thumbnail`: chu_tren_anh, hinh_hua, cap_bo_tro). "
    "Hay tai tao tieu de MOI sao cho van LIEN QUAN va BO TRO voi thumbnail do: giu cung LOI HUA / khoang trong to mo ma "
    "anh + chu tren anh dang goi, de nguoi xem thay thumbnail va tieu de moi thi thay chung noi CUNG MOT chuyen. "
    "KHONG chep nguyen van tieu de goc hay chu tren anh; KHONG them chi tiet khong co trong ca tieu de goc lan thumbnail. "
    "Trong ly_do_tai_tao noi ro tieu de moi bam thumbnail the nao."
)


def _thumb_ctx_of(v):
    """Rut {chu_tren_anh, hinh_hua, cap_bo_tro} tu video (da gan 'thumb_ctx'); None neu khong co thong tin."""
    c = (v or {}).get("thumb_ctx") or {}
    d = {"chu_tren_anh": c.get("chu_tren_thumb") or c.get("chu_tren_anh") or "",
         "hinh_hua": c.get("hinh_hua") or "", "cap_bo_tro": c.get("cap_bo_tro") or ""}
    return d if any(d.values()) else None


def scan_decompose_recreate(videos, profile, output_language, main_keyword=None):
    """
    videos: list dict co 'title','views','url','channelTitle'
    profile: khuon kenh (dict tu analyze_channel) hoac None (dung cong thuc chung)
    output_language: 'vi' | 'en' | ... (ngon ngu tieu de tai tao)
    main_keyword: tu khoa chinh BAT BUOC co trong tieu de moi (None = AI tu chon cho tung tieu de)
    Voi MOI tieu de goc -> tao 1 tieu de tai tao HAY NHAT (tu chon khung xuong tot nhat),
    bam tu khoa chinh + tu khoa chien thang cua kenh + giu tu khoa da giup tieu de goc len view.
    Tra ve 'khung_index' (0-based, hoac -1 neu khong theo khung nao) de nut 'Tao lai' xoay vong.
    """
    import json

    main_keyword = (main_keyword or "").strip() or None
    ch_kws = _channel_keywords(profile)
    khung_list = _khung_list_of(profile)

    profile_txt = ""
    if profile:
        profile_txt = (
            "KHUON KENH DICH (phai nan tieu de tai tao theo dung khuon nay):\n"
            + json.dumps(profile, ensure_ascii=False, indent=2) + "\n"
        )

    if khung_list:
        khung_block = (
            "DANH SACH KHUNG XUONG TIEU DE CUA KENH (0-based):\n"
            + "\n".join("  [{}] {}".format(i, k) for i, k in enumerate(khung_list)) + "\n"
        )
        ver_rule = (
            "Voi MOI tieu de goc: CHON 1 KHUNG XUONG HAY NHAT/PHU HOP NHAT trong danh sach tren, "
            "va TAO 1 tieu de tai tao theo khung do (giu nguyen VAN DE + KHOANG TRONG TO MO cua ban goc). "
            "Ghi so thu tu khung da chon (0-based) vao 'khung_index'."
        )
    else:
        khung_block = ""
        ver_rule = "Voi MOI tieu de goc, tao 1 tieu de tai tao HAY NHAT theo cong thuc chung. Dat khung_index = -1."

    lang = _lang_name(output_language)

    system = (
        "Ban la chuyen gia dat tieu de YouTube. Voi moi tieu de goc, hay:\n"
        "1) Boc tach 3 thanh phan (chu de / tu khoa-van de / khoang trong to mo).\n"
        "2) TAI TAO tieu de MOI theo khuon kenh dich, KHONG dung lai toan bo cau goc.\n"
        + ver_rule + "\n"
        "3) GIAI THICH (ly_do_tai_tao): giu lai van de gi, khoang trong to mo gi, bam khung nao, vi sao de hut click.\n"
        + KHUNG_CONG_THUC + "\n" + khung_block + profile_txt
        + "\n" + _keyword_rules(main_keyword, ch_kws, lang)
        + (("\n" + THUMB_PAIR_RULE) if any(_thumb_ctx_of(v) for v in videos) else "")
        + "\nTIEU DE TAI TAO viet bang: " + lang
        + "\nBAT BUOC: IN HOA TOAN BO 1-2 tu khoa cam xuc/van de manh nhat de tao diem nhan "
        "(vi du: THAO TUNG, NOI DOI, HUY HOAI, PHAN BOI, BIEN MAT). TUYET DOI KHONG in hoa toan bo ca tieu de."
        + "\ndich_goc = DICH TIEU DE GOC sang tieng Viet (giup hieu tieu de doi thu)."
        + "\nRIENG cac truong PHAN TICH + DICH (chu_de, tu_khoa_van_de, khoang_trong_to_mo, tu_huyet, "
        "dich_goc, dich_viet, ly_do_tai_tao) PHAI viet bang TIENG VIET CO DAU day du, van phong tu nhien de doc."
    )

    schema = (
        "Tra ve JSON la MOT MANG, moi phan tu dung cau truc:\n"
        "{\n"
        '  "index": <giu nguyen>,\n'
        '  "chu_de": "...",\n'
        '  "tu_khoa_van_de": "...",\n'
        '  "khoang_trong_to_mo": "...",\n'
        '  "tu_huyet": "So hai|To mo|Tham lam|Canh giac",\n'
        '  "khung_index": <so thu tu khung da chon (0-based), hoac -1 neu khong theo khung>,\n'
        '  "dich_goc": "ban dich TIENG VIET CO DAU cua TIEU DE GOC (neu von da tieng Viet thi ghi y nguyen)",\n'
        '  "tu_khoa_len_view": "cum tu khoa trong TIEU DE GOC da giup no len view",\n'
        '  "tu_khoa_chinh": "tu khoa chinh cua tieu de tai tao",\n'
        '  "tu_khoa_trong_tieu_de": "doan chu cua tu khoa chinh NHU XUAT HIEN trong tieu_de_tai_tao",\n'
        '  "tu_khoa_kenh": "doan chu cua tu khoa kenh NHU XUAT HIEN trong tieu_de_tai_tao (da dich neu can; de trong neu khong co danh sach)",\n'
        '  "tieu_de_tai_tao": "...",\n'
        '  "so_ky_tu": <do dai tieu de tai tao>,\n'
        '  "dich_viet": "ban dich TIENG VIET CO DAU cua TIEU DE TAI TAO (neu da tieng Viet thi y nguyen)",\n'
        '  "ly_do_tai_tao": "giai thich bang TIENG VIET CO DAU"\n'
        "}"
    )

    BATCH = 8  # 1 ban/tieu de -> nhanh nhu ban goc
    by_index = {}
    for start in range(0, len(videos), BATCH):
        chunk = videos[start:start + BATCH]
        items = []
        for j, v in enumerate(chunk):
            it = {"index": start + j, "title": v["title"]}
            tc = _thumb_ctx_of(v)
            if tc:
                it["thumbnail"] = tc
            items.append(it)
        user = ("Danh sach tieu de goc (JSON):\n"
                + json.dumps(items, ensure_ascii=False) + "\n\n" + schema)
        try:
            result = llm.chat_json(system, user, temperature=0.7)
        except Exception:
            result = []
        if isinstance(result, dict):
            for key in ("items", "data", "result", "titles"):
                if isinstance(result.get(key), list):
                    result = result[key]
                    break
        if isinstance(result, list):
            for idx2, r in enumerate(result):
                if isinstance(r, dict):
                    by_index[r.get("index", start + idx2)] = r

    def _ki(r):
        try:
            ki = int(r.get("khung_index", -1))
        except (TypeError, ValueError):
            ki = -1
        if not khung_list:
            return -1
        return ki if 0 <= ki < len(khung_list) else 0

    out = []
    for i, v in enumerate(videos):
        r = by_index.get(i, {})
        t = (r.get("tieu_de_tai_tao") or "").strip()
        out.append({
            "rank": i + 1,
            "video_id": v["id"],
            "views": v["views"],
            "title_goc": v["title"],
            "dich_goc": r.get("dich_goc", ""),
            "url": v["url"],
            "thumbnail": v.get("thumbnail", ""),
            "channel": v.get("channelTitle", ""),
            "is_short": v.get("is_short"),
            "duration_sec": v.get("duration_sec", 0),
            "chu_de": r.get("chu_de", ""),
            "tu_khoa_van_de": r.get("tu_khoa_van_de", ""),
            "khoang_trong_to_mo": r.get("khoang_trong_to_mo", ""),
            "tu_huyet": r.get("tu_huyet", ""),
            "khung_index": _ki(r),
            "tieu_de_tai_tao": t,
            "so_ky_tu": r.get("so_ky_tu", len(t)),
            "dich_viet": r.get("dich_viet", ""),
            "ly_do_tai_tao": r.get("ly_do_tai_tao", ""),
            "thumb_ctx": _thumb_ctx_of(v),     # None neu khong bat che do bam thumbnail
            **_kw_fields(t, main_keyword, r, ch_kws),
        })

    # EP tu khoa: dong nao con thieu thi tao lai 1 lan (toi da 8 dong/lan de khong cham)
    fixed = 0
    for row in out:
        if row.get("kw_ok") is False and fixed < 8 and row["title_goc"]:
            fixed += 1
            try:
                fx = recreate_one(row["title_goc"], profile, output_language, row["khung_index"],
                                  main_keyword=main_keyword, attempts=1, thumb_ctx=row.get("thumb_ctx"))
            except Exception:
                continue
            if fx.get("tieu_de_tai_tao") and fx.get("kw_ok"):
                for k in ("tieu_de_tai_tao", "so_ky_tu", "dich_viet", "tu_khoa_chinh", "tu_khoa_len_view",
                          "tu_khoa_kenh", "kw_main_ok", "kw_kenh_ok", "kw_ok"):
                    row[k] = fx.get(k, row.get(k))
                row["ly_do_tai_tao"] = (row.get("ly_do_tai_tao") or "") + " (Đã tự sửa lại để có đủ từ khóa.)"
    return out


def recreate_one(title_goc, profile, output_language, khung_index, main_keyword=None, attempts=2, thumb_ctx=None):
    """
    Tao lai 1 tieu de theo 1 KHUNG XUONG cu the (cho nut 'Tao lai' xoay vong).
    khung_index: so thu tu khung (0-based). Neu khong hop le / khong co khuon -> cong thuc chung.
    main_keyword: tu khoa chinh BAT BUOC (None = AI tu chon). attempts: so lan thu neu thieu tu khoa.
    Tra ve {tieu_de_tai_tao, so_ky_tu, dich_viet, khung_index, tu_khoa_*, kw_ok}.
    """
    import json
    main_keyword = (main_keyword or "").strip() or None
    ch_kws = _channel_keywords(profile)
    khung_list = _khung_list_of(profile)
    lang = _lang_name(output_language)

    if khung_list and isinstance(khung_index, int) and 0 <= khung_index < len(khung_list):
        khung = khung_list[khung_index]
        khung_txt = ("BAM DUNG KHUNG XUONG NAY (bat buoc theo dung cau truc nay):\n  " + khung + "\n")
    else:
        khung = ""
        khung_index = -1
        khung_txt = "Dung cong thuc chung (khong co khung cu the).\n"

    profile_txt = ""
    if profile:
        profile_txt = "KHUON KENH (tham khao phong cach): " + json.dumps(profile, ensure_ascii=False)[:1500] + "\n"

    system = (
        "Ban la chuyen gia dat tieu de YouTube. Tai tao 1 tieu de MOI tu tieu de goc: "
        "GIU nguyen VAN DE + KHOANG TRONG TO MO cua ban goc, KHONG dung lai toan bo cau goc.\n"
        + khung_txt + KHUNG_CONG_THUC + "\n" + profile_txt
        + "\n" + _keyword_rules(main_keyword, ch_kws, lang)
        + (("\n" + THUMB_PAIR_RULE) if thumb_ctx else "")
        + "\nTIEU DE TAI TAO viet bang: " + lang
        + "\nBAT BUOC: IN HOA TOAN BO 1-2 tu khoa cam xuc/van de manh nhat de tao diem nhan. "
        "TUYET DOI KHONG in hoa toan bo ca tieu de."
    )
    user = (
        'Tieu de goc: "' + title_goc + '"\n'
        + (("Thumbnail doi thu (JSON): " + json.dumps(thumb_ctx, ensure_ascii=False) + "\n") if thumb_ctx else "")
        + '\n'
        'Tra ve JSON: {"tu_khoa_len_view": "...", "tu_khoa_chinh": "...", "tu_khoa_trong_tieu_de": "...", '
        '"tu_khoa_kenh": "...", "tieu_de_tai_tao": "...", "so_ky_tu": <do dai>, '
        '"dich_viet": "ban dich TIENG VIET CO DAU (neu da tieng Viet thi y nguyen)"}'
    )
    r, t, kw = {}, "", {}
    for _ in range(max(1, attempts)):
        try:
            r = llm.chat_json(system, user, temperature=0.85)
        except Exception:
            r = {}
        t = (r.get("tieu_de_tai_tao") or "").strip()
        kw = _kw_fields(t, main_keyword, r, ch_kws)
        if kw["kw_ok"] is not False:  # du tu khoa (hoac chua co tieu de) -> dung thu lai
            break
    return {
        "tieu_de_tai_tao": t,
        "so_ky_tu": r.get("so_ky_tu", len(t)),
        "dich_viet": r.get("dich_viet", ""),
        "khung_index": khung_index,
        **kw,
    }
