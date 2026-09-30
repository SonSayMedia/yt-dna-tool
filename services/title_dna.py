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


def analyze_channel(titles):
    system = (
        "Ban la chuyen gia phan tich tieu de YouTube. "
        "Dua tren cong thuc duoi day, hay boc tach cac tieu de mau cua MOT kenh "
        "va rut ra 'khuon dat tieu de' dac trung cua kenh do (Title DNA).\n" + KHUNG_CONG_THUC
        + "\nCac truong mo ta (vi_tri_tu_khoa, kieu_in_hoa, giong_dieu, ghi_chu, tu_huyet_chu_dao) "
        "viet bang TIENG VIET CO DAU day du."
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
        '  "ghi_chu": "nhung dac diem rieng khac khien tieu de kenh nay hut view"\n'
        "}\n\n"
        "Cac tieu de:\n" + "\n".join("- " + t for t in titles)
    )
    return llm.chat_json(system, user, temperature=0.3, role="analyze")


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
    }.get(output_language, output_language)


def scan_decompose_recreate(videos, profile, output_language):
    """
    videos: list dict co 'title','views','url','channelTitle'
    profile: khuon kenh (dict tu analyze_channel) hoac None (dung cong thuc chung)
    output_language: 'vi' | 'en' | ... (ngon ngu tieu de tai tao)
    Voi MOI tieu de goc -> tao 1 tieu de tai tao HAY NHAT (tu chon khung xuong tot nhat).
    Tra ve 'khung_index' (0-based, hoac -1 neu khong theo khung nao) de nut 'Tao lai' xoay vong.
    """
    import json

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
        items = [{"index": start + j, "title": v["title"]} for j, v in enumerate(chunk)]
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
        })
    return out


def recreate_one(title_goc, profile, output_language, khung_index):
    """
    Tao lai 1 tieu de theo 1 KHUNG XUONG cu the (cho nut 'Tao lai' xoay vong).
    khung_index: so thu tu khung (0-based). Neu khong hop le / khong co khuon -> cong thuc chung.
    Tra ve {tieu_de_tai_tao, so_ky_tu, dich_viet, khung_index}.
    """
    import json
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
        + "\nTIEU DE TAI TAO viet bang: " + lang
        + "\nBAT BUOC: IN HOA TOAN BO 1-2 tu khoa cam xuc/van de manh nhat de tao diem nhan. "
        "TUYET DOI KHONG in hoa toan bo ca tieu de."
    )
    user = (
        'Tieu de goc: "' + title_goc + '"\n\n'
        'Tra ve JSON: {"tieu_de_tai_tao": "...", "so_ky_tu": <do dai>, '
        '"dich_viet": "ban dich TIENG VIET CO DAU (neu da tieng Viet thi y nguyen)"}'
    )
    try:
        r = llm.chat_json(system, user, temperature=0.85)
    except Exception:
        r = {}
    t = (r.get("tieu_de_tai_tao") or "").strip()
    return {
        "tieu_de_tai_tao": t,
        "so_ky_tu": r.get("so_ky_tu", len(t)),
        "dich_viet": r.get("dich_viet", ""),
        "khung_index": khung_index,
    }
