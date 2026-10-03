"""
Khoi C: Nhin anh thumbnail + anh noi dung -> rut ra DNA phong cach.
Dung Gemini vision qua llm.chat(..., vision_images=...).
"""
from . import llm


def analyze_thumbnails(images):
    """
    Nhin BO SUU TAP thumbnail (20 video nhieu view nhat cua kenh) -> DNA thumbnail SAU.
    Tra ve dict thumbnail_dna. images = list bytes.
    """
    if not images:
        return {}
    system = (
        "Ban la giam doc nghe thuat thumbnail YouTube trieu view. "
        "Ban duoc xem BO SUU TAP thumbnail cua nhung video NHIEU VIEW NHAT cua 1 kenh. "
        "Hay phan tich CHUYEN SAU de rut ra 'DNA thumbnail' — cong thuc thi giac chung "
        "khien kenh nay hut click. Nhin ca bo de tim diem LAP LAI / DONG NHAT.\n"
        "QUY TAC CHU (FONT) — BAT BUOC, KHONG DUOC PHA:\n"
        "- Font phai CHOT DUY NHAT 1 kieu. TUYET DOI KHONG dung 'hoac' / 'hay' / 'tuong tu X hoac Y'. "
        "Neu phan van, chon 1 font pho bien GAN NHAT roi CHOT (vd chi 'Georgia', khong phai 'Georgia hoac Garamond').\n"
        "- MOI truong ve chu deu phai co GIA TRI CU THE, khong de trong, khong ghi 'khong ro'. "
        "Neu khong co vien thi ghi ro 'chu phang, khong vien'; khong co hieu ung thi ghi 'khong hieu ung'.\n"
        "- Muc tieu: chu tren MOI thumbnail phai giong het nhau 100% de dong nhat ca kenh. "
        "Ta font phai du chi tiet de tai tao Y HET moi lan (kieu chu, do dam, IN HOA/thuong, mau + HEX, vien, hieu ung).\n"
        "QUY TAC NHAN VAT (CHARACTER DNA) — chi ap dung khi kenh CO 1 kieu nhan vat/thiet ke lap lai xuyen suot "
        "(vd nhan vat hoat hinh ve tay, nguoi que, linh vat, avatar minh hoa...), KHONG ap dung cho anh chup "
        "nguoi that thay doi moi video:\n"
        "- Neu CO: phai mo ta dau/mat, toc, trang phuc, ty le dau-than THANH 1 CONG THUC cu the, tai tao duoc "
        "Y HET moi lan (khong chung chung kieu 'nhan vat hoat hinh vui ve'). Rieng bieu cam phai tach thanh "
        "CONG THUC RIENG cho tung nhom cam xuc pho bien (vd vui/hai long, boi roi/ngac nhien, gian du/cuc doan) "
        "vi bieu cam la phan SE DOI theo tung tieu de, chi dau/toc/trang phuc la phan CO DINH.\n"
        "- Neu KHONG (anh chup nguoi that, khong co thiet ke nhan vat lap lai, hoac kenh khong co nhan vat) "
        "thi ghi ro 'co_nhan_vat_co_dinh': false va de khoa_nhan_vat_en la chuoi RONG.\n"
        "Cac muc con lai (chu the, boi canh, anh sang...) hay mo ta DAY DU, CU THE, tranh so sai chung chung."
    )
    user = (
        "Day la cac thumbnail nhieu view nhat cua 1 kenh. Tra ve JSON dung cau truc "
        "(mo ta bang TIENG VIET CO DAU; rieng style_prompt_en bang TIENG ANH):\n"
        "{\n"
        '  "bo_cuc_chung": "layout tong the lap lai: vi tri chu the, vi tri chu, khoang trong",\n'
        '  "chu_the_chinh": {\n'
        '    "la_gi": "chu the chinh la gi (mat nguoi / dia danh-canh vat / vat the / nhan vat...)",\n'
        '    "ty_le_chiem": "chiem khoang bao nhieu % khung hinh (vd: ~40%, chiem gan het khung, nho ~15%...)",\n'
        '    "vi_tri": "vi tri chu the: trai/giua/phai + tren/giua/duoi, thuoc 1/3 nao"\n'
        "  },\n"
        '  "bang_mau": ["mau chu dao 1", "mau 2", ...],\n'
        '  "text_tren_thumb": {\n'
        '    "co_chu": "kenh CO dat chu tren thumbnail hay khong (co/khong)",\n'
        '    "font": "1 FONT DUY NHAT, cu the (vd: \'classic thin serif Georgia\' hoac \'bold condensed sans-serif IN HOA\'). CAM ghi \'hoac\'/\'tuong tu\'.",\n'
        '    "mau_chu": "mau chu + ma HEX (vd: trang #FFFFFF)",\n'
        '    "vien_chu": "neu CO vien: ghi mau + do day px (vd \'vien den ~5px\'); neu KHONG: ghi \'chu phang, khong vien\'",\n'
        '    "hieu_ung": "bong do / glow / gradient / 3D (ghi ro); neu khong co: ghi \'khong hieu ung\'",\n'
        '    "vi_tri": "vi tri & do lon chu tren thumb",\n'
        '    "quan_he_voi_tieu_de": "chu tren thumb bo tro / nhac lai / khac han tieu de ra sao"\n'
        "  },\n"
        '  "khoa_chu_en": "MOT cau TIENG ANH KHOA CUNG kieu chu (CHI style, KHONG kem noi dung chu cu the), de chen Y NGUYEN vao moi prompt — vd: \'in EXACTLY classic thin elegant serif (Georgia), pure white #FFFFFF, flat clean lettering, no outline, no drop shadow — identical channel typography on every thumbnail\'. Phai chi tiet, DUY NHAT, khong \'hoac\'. Neu kenh KHONG dat chu thi de chuoi RONG.",\n'
        '  "nhan_vat_dna": {\n'
        '    "co_nhan_vat_co_dinh": true/false (kenh co 1 kieu nhan vat/thiet ke lap lai xuyen suot hay khong — anh chup nguoi that thay doi tung video thi de false),\n'
        '    "dau_mat": "hinh dang dau, mau/kieu nen mat (co to mau da hay de trang...), mat/mui/mieng ve nhu the nao",\n'
        '    "toc": "mau toc CU THE, kieu toc, do dai (1 kieu CO DINH, khong \'hoac\')",\n'
        '    "trang_phuc": "trang phuc/phu kien co dinh lap lai qua cac video",\n'
        '    "ty_le_dau_than": "ty le dau so voi than nguoi (vd dau to ~1:3.5 than, hay ty le nguoi that binh thuong)",\n'
        '    "cong_thuc_bieu_cam": {"vui_hai_long": "mat-may-mieng ve the nao", "boi_roi_ngac_nhien": "...", "gian_du_cuc_doan": "..."}\n'
        "  },\n"
        '  "khoa_nhan_vat_en": "1 doan TIENG ANH KHOA CUNG thiet ke nhan vat co dinh (dau/toc/trang phuc/ty le), KHONG kem hanh dong hay bieu cam cu the (bieu cam se do tung prompt tu quyet dinh theo tieu de), de chen Y NGUYEN vao moi prompt — vd: \'the same recurring character: round blank-white head with no skin shading, messy dark-brown spiky hair (4-6 tufts), draped brown fur pelt over one shoulder, thin black stick-figure limbs, head roughly 1:3.5 of body height — identical character design on every thumbnail\'. Neu kenh KHONG co nhan vat co dinh lap lai thi de chuoi RONG.",\n'
        '  "khoa_bo_cuc_en": "1 doan TIENG ANH mo ta BO CUC CO DINH lap lai cua kenh (ty le %, vi tri chu the, mau nen, khung/vien, vi tri & do lon banner chu) de tai tao MOI thumbnail GIONG BO CUC nay. Phan CO DINH (mau, bo cuc, ty le, khung) ghi CU THE. Phan THAY DOI theo tung video thi de PLACEHOLDER trong ngoac vuong kep: [[SUBJECT]]=chu the chinh, [[EMOTION]]=bieu cam neu co mat nguoi, [[SYMBOL]]=bieu tuong dai dien noi dung neu co, [[HOOK]]=cum chu tren thumb, [[FONT]]=kieu chu (de NGUYEN chu [[FONT]]), [[SCENE]]=THE GIOI/BOI CANH cua canh (noi/thoi diem xay ra — doi theo noi dung tung video). BAT BUOC co [[HOOK]] va [[FONT]] neu kenh co chu, va it nhat 1 placeholder chu the ([[SUBJECT]]) va [[SCENE]]. QUAN TRONG: phan CO DINH chi ghi bo cuc/ty le/mau/phong cach ve — TUYET DOI KHONG ghi cung the gioi/thoi dai/dia diem dac trung cua kenh (vd prehistoric, cave, medieval, office) vao phan co dinh; nhung thu do phai nam trong [[SCENE]] hoac [[SUBJECT]]. Chi dung placeholder cho phan THAT SU doi. Vd: \'Flat editorial illustration, 16:9, deep navy background, olive-green borders; on the LEFT a glowing pale-blue [[SYMBOL]] with a tiny lone silhouette; on the RIGHT a close-up of [[SUBJECT]] filling ~55% width, terracotta-red skin, an expression of [[EMOTION]]; a solid black top banner with the text \\"[[HOOK]]\\" [[FONT]]\'.",\n'
        '  "cam_giac_nguoi_xem": "cam xuc / cam giac ma thumbnail tao ra cho nguoi xem",\n'
        '  "do_dong_nhat": "muc do dong nhat giua cac thumbnail (cao/vua/thap) + yeu to lap lai tao nhan dien kenh",\n'
        '  "boi_canh": {\n'
        '    "tien_canh": "tien canh thuong co gi",\n'
        '    "trung_canh": "trung canh / chu the chinh",\n'
        '    "hau_canh": "hau canh / nen"\n'
        "  },\n"
        '  "bo_cuc_vang": "cach ap dung quy tac 1/3 hoac ti le vang - chu the/diem nhan dat o dau",\n'
        '  "anh_sang": "kieu anh sang, do tuong phan",\n'
        '  "style_prompt_en": "1 doan TIENG ANH tong hop phong cach de tao thumbnail moi dung chat kenh"\n'
        "}"
    )
    return llm.chat_json(system, user, temperature=0.3, vision_images=list(images))


def analyze_content(images):
    """
    Nhin cac ANH NOI DUNG (khung hinh minh hoa trong video) -> DNA SAU.
    Trong tam: bo cuc, do don gian, luong text, va vai tro MINH HOA cho loi noi.
    images = list bytes.
    """
    if not images:
        return {}
    system = (
        "Ban la giam doc nghe thuat phim hoat hinh / explainer YouTube. "
        "Ban duoc xem cac khung hinh MINH HOA ben trong video cua 1 kenh. "
        "Loai anh nay thuong: DON GIAN, IT/KHONG chu, va chi de MINH HOA cho loi noi (narration). "
        "Hay phan tich CHUYEN SAU ve BO CUC va phong cach de tai tao duoc anh minh hoa GIONG HET "
        "tren nen tang tao anh (Google Flow). Nhin ca bo de tim diem LAP LAI / DONG NHAT."
    )
    user = (
        "Tra ve JSON dung cau truc (mo ta bang TIENG VIET CO DAU; style_prompt_en bang TIENG ANH):\n"
        "{\n"
        '  "phong_cach_ve": "chat lieu/phong cach: 2D hand-drawn cartoon, nguoi que (stick figure), '
        'flat illustration, 3D, whiteboard, anh that... (cang cu the cang tot)",\n'
        '  "do_don_gian": "muc do don gian (rat toi gian / vua / chi tiet) + so luong yeu to moi khung",\n'
        '  "bo_cuc": "bo cuc/layout: chu the dat o dau, khoang trong, diem nhan, quy tac 1/3 neu co",\n'
        '  "bang_mau": ["mau chu dao..."],\n'
        '  "chu_the": "chu the thuong xuat hien (nguoi que, vat the don gian, so do, canh vat...)",\n'
        '  "text_trong_anh": "luong chu/nhan trong anh (khong co / rat it / thinh thoang co nhan) va cach dung",\n'
        '  "vai_tro_minh_hoa": "anh minh hoa cho loi noi the nao (minh hoa truc tiep dieu dang noi / an du / bieu tuong)",\n'
        '  "nen": "kieu nen (trang tron / gradient don gian / canh...)",\n'
        '  "cam_xuc": "khong khi / cam xuc",\n'
        '  "style_prompt_en": "1 doan TIENG ANH tong hop: nhan manh SIMPLE, minimalist, MINIMAL or NO text, '
        'clean composition, illustrating the narration - de gan vao moi prompt anh noi dung"\n'
        "}"
    )
    return llm.chat_json(system, user, temperature=0.3, vision_images=list(images))


def analyze_images(thumbnail_images, content_images):
    """
    Gop: DNA thumbnail (sau) + DNA anh noi dung.
    Tra ve dict {thumbnail_dna, content_dna}. Ben nao khong co anh -> {}.
    """
    if not thumbnail_images and not content_images:
        raise RuntimeError("Chua co anh nao de phan tich.")
    return {
        "thumbnail_dna": analyze_thumbnails(thumbnail_images),
        "content_dna": analyze_content(content_images),
    }


def thumbnail_prompt_from_reference(title, image_bytes):
    """
    Nhin 1 thumbnail GOC (da nhieu view) + 1 tieu de MOI -> sinh prompt thumbnail moi:
    giu tuong dong mau sac/goc do/bo cuc/chu the, nhung bo tro hoan hao cho tieu de.
    """
    system = (
        "Ban la giam doc nghe thuat thiet ke thumbnail YouTube trieu view. "
        "Ban duoc dua 1 THUMBNAIL GOC (video da rat nhieu view) va 1 TIEU DE MOI. "
        "Nhiem vu: tao prompt tao 1 thumbnail MOI vua GIU su tuong dong voi thumbnail goc "
        "(bang mau chu dao, goc do/goc may, bo cuc-layout, loai chu the), "
        "vua BO TRO HOAN HAO cho tieu de moi: truyen tai dung cam xuc & thong diep cua tieu de, "
        "KHONG lap lai y het chu trong tieu de, va CHUA khoang trong (negative space) dung cho "
        "viec chen chu tieu de sau. Bieu cam/chu the phai danh dung tu huyet cam xuc cua tieu de."
    )
    user = (
        "TIEU DE MOI: " + title + "\n\n"
        "Hay tra ve JSON dung cau truc:\n"
        "{\n"
        '  "phan_tich_goc": {\n'
        '    "mau_sac": "bang mau chu dao cua thumbnail goc",\n'
        '    "goc_do": "goc may/goc nhin",\n'
        '    "bo_cuc": "cach sap xep chu the, khoang trong, diem nhan",\n'
        '    "chu_the": "chu the chinh la gi",\n'
        '    "cam_xuc": "cam xuc chu dao"\n'
        "  },\n"
        '  "thumbnail_prompt_en": "prompt TIENG ANH chi tiet cho Google Flow: giu bang mau, goc do, '
        'bo cuc cua thumbnail goc; nhung chu the & bieu cam duoc chinh de bo tro cho tieu de moi; '
        'chua khoang trong ro rang de chen chu tieu de"\n'
        "}\n"
        "Cac truong trong phan_tich_goc viet bang TIENG VIET CO DAU. thumbnail_prompt_en viet TIENG ANH."
    )
    return llm.chat_json(system, user, temperature=0.6, vision_images=[image_bytes])


# Quy tac chon SO LUONG nhan vat/chu the & HANH DONG theo LOAI tieu de (niche-agnostic:
# dua tren cau truc ngu nghia cua cau hoi, khong dua tren chu de cu the).
CAST_ACTION_GRAMMAR = (
    "QUY TAC CHON SO LUONG CHU THE & HANH DONG THEO LOAI TIEU DE (Cast & Action Grammar) — "
    "XAC DINH tieu de thuoc loai nao TRUOC, roi moi chon so luong nhan vat/chu the va hanh dong:\n"
    "1. Tieu de hoi ve DAC DIEM/BAN CHAT ca nhan (vd 'Why X la Y nhat', 'X co dac diem gi') "
    "-> 1 CHU THE DUY NHAT, hanh dong/bieu cam CUC DOAN de minh hoa dac diem do.\n"
    "2. Tieu de hoi ve QUA TRINH/PHAT MINH co HE QUA (vd 'X vo tinh tao ra Y the nao') "
    "-> 1 chu the chinh CAM/THE HIEN vat-ket qua + co the them nhom nho PHAN UNG doi lap phia sau.\n"
    "3. Tieu de hoi ve GIAI PHAP/SINH TON xoay quanh 1 VAT THE trung tam (vd 'X song sot qua Y bang cach nao') "
    "-> nhom nho 2-3 chu the THU NHO lai, VAT THE-giai phap chiem PHAN LON khung, to hon chu the.\n"
    "4. Tieu de hoi ve CHIU DUNG/CHO DOI (vd 'X lam gi khi Y xay ra') "
    "-> nhom nho 2-3 chu the, tu the tinh/bat dong, bieu cam met moi/cho doi.\n"
    "5. Tieu de hoi ve HANH TRINH/DI CHUYEN (vd 'X di chuyen/du hanh the nao') "
    "-> nhom nho 2-3 (kieu gia dinh/doi nhom), xep hang noi duoi, tu the dang di.\n"
    "6. Tieu de hoi ve SO SANH/PHAN LOAI (vd 'Vi sao chi con X', 'X nao la...') "
    "-> NHIEU chu the dai dien (4 tro len), dan hang de doi chieu truc quan.\n"
    "7. Tieu de hoi ve HOAT DONG NHOM/XA HOI (vd 'X bat dau lam Y cung nhau tu khi nao') "
    "-> nhom 3-4 chu the quay quan quanh 1 hanh dong chung.\n"
    "8. Tieu de hoi ve HIEN TUONG/PATTERN lap lai o NHIEU NOI/NHIEU LAN (vd '...O KHAP NOI', '...MOI LUC') "
    "-> 1 chu the chinh + THEM 1 lop hinh anh the hien su lap lai (vd ban sao/silhouette mo dan o hau canh, "
    "hoac icon/ban do nho danh dau nhieu vi tri).\n"
    "Neu tieu de khong khop ro loai nao, chon phuong an GAN NHAT va uu tien it chu the (de chu the du LON, "
    "ro net khi thu nho thumbnail)."
)


def _character_lock_block(thumbnail_dna):
    """Khoi khoa THIET KE NHAN VAT co dinh (dau/toc/trang phuc/ty le) -> chen y nguyen moi lan
    de nhan vat khong bi troi qua tung thumbnail. Rong neu kenh khong co nhan vat co dinh lap lai."""
    if not thumbnail_dna:
        return ""
    lock = (thumbnail_dna.get("khoa_nhan_vat_en") or "").strip()
    if lock:
        return lock
    nv = thumbnail_dna.get("nhan_vat_dna") or {}
    if not nv or not nv.get("co_nhan_vat_co_dinh"):
        return ""
    parts = []
    if nv.get("dau_mat"):
        parts.append(str(nv["dau_mat"]))
    if nv.get("toc"):
        parts.append("hair: " + str(nv["toc"]))
    if nv.get("trang_phuc"):
        parts.append("outfit: " + str(nv["trang_phuc"]))
    if nv.get("ty_le_dau_than"):
        parts.append("proportions: " + str(nv["ty_le_dau_than"]))
    if not parts:
        return ""
    return ("the same recurring character design, identical on every thumbnail: " + "; ".join(parts))


def _font_lock_block(thumbnail_dna):
    """Khoi lenh CHU CO DINH (chen y nguyen moi lan) -> chu dong nhat 100% ca kenh.
    Uu tien 'khoa_chu_en' da phan tich san; neu chua co thi ghep tu text_tren_thumb.
    Tra ve chuoi rong neu kenh khong dat chu."""
    if not thumbnail_dna:
        return ""
    lock = (thumbnail_dna.get("khoa_chu_en") or "").strip()
    if lock:
        return lock
    t = thumbnail_dna.get("text_tren_thumb") or {}
    if str(t.get("co_chu", "")).strip().lower().startswith("khong"):
        return ""
    parts = []
    if t.get("font"):
        parts.append("font: " + str(t["font"]))
    if t.get("mau_chu"):
        parts.append("color " + str(t["mau_chu"]))
    if t.get("vien_chu"):
        parts.append(str(t["vien_chu"]))
    if t.get("hieu_ung"):
        parts.append(str(t["hieu_ung"]))
    if not parts:
        return ""
    return ("rendered in EXACTLY this fixed channel typography, identical on every thumbnail: "
            + "; ".join(parts))


def _strip_font_position(font_lock):
    """Bo cum chi VI TRI chu (vd 'centered at the very top') khoi khoa font de khong de len bo cuc tham chieu.
    Chi dung khi ve lai theo bo cuc thumbnail doi thu; kieu chu/mau/vien giu nguyen."""
    import re
    s = re.sub(r",?\s*(?:(?:horizontally\s+)?cent(?:ered|red)\s+)?(?:at|in|on)\s+the\s+(?:very\s+)?"
               r"(?:top|bottom|upper|lower)(?:[\s-](?:center|centre|left|right|third|part|area))?"
               r"(?:\s+of\s+the\s+(?:frame|image|canvas|thumbnail))?", "", font_lock or "", flags=re.I)
    return s


def _richness_hint_block(thumbnail_dna):
    """Gom CONG THUC BIEU CAM (mat-may-mieng theo tung nhom cam xuc) + BOI CANH trung/tien/hau canh
    tu DNA thanh 1 doan THAM KHAO de lam giau noi dung o trong (bieu cam cu the hon, co nhan vat phu/
    dong vat/dam lua neu kenh von hay co) - KHONG dung de doi bo cuc/ty le/mau/font/nhan vat da khoa,
    chi lam giau NOI DUNG BEN TRONG cac o co san. Rong neu DNA khong co du lieu."""
    if not thumbnail_dna:
        return ""
    import json
    parts = []
    ct = (thumbnail_dna.get("nhan_vat_dna") or {}).get("cong_thuc_bieu_cam") or {}
    if ct:
        parts.append(
            "CONG THUC BIEU CAM cua kenh theo tung nhom cam xuc (chon nhom GAN NHAT voi tieu de, "
            "mo ta CU THE mat-may-mieng dung theo cong thuc nay khi dien o bieu cam, TUYET DOI KHONG "
            "dung 1 tinh tu chung chung nhu 'ngac nhien' hay 'to mo' - phai ta RO mat/may/mieng the nao): "
            + json.dumps(ct, ensure_ascii=False)
        )
    bc = thumbnail_dna.get("boi_canh") or {}
    bc_bits = [k + ": " + str(v) for k, v in
               [("tien canh", bc.get("tien_canh")), ("trung canh", bc.get("trung_canh")),
                ("hau canh", bc.get("hau_canh"))] if v]
    if bc_bits:
        parts.append(
            "CAU TRUC CHIEU SAU thuong dung cua kenh (CHI tham khao CACH to chuc tien/trung/hau canh de anh khong "
            "don dieu/trong trai; TUYET DOI KHONG sao chep NOI DUNG hay THE GIOI cu the cua kenh nay — vat the & "
            "the gioi phai theo TIEU DE): " + "; ".join(bc_bits) + ". "
            "Neu hop ly voi tieu de, hay THEM 1-2 chi tiet phu THEO TIEU DE (nhan vat phu/dong vat/vat dung...) "
            "vao noi dung mo ta cac o co san (KHONG tao them o moi, KHONG doi bo cuc/ty le/mau/font/thiet ke "
            "nhan vat chinh da khoa) de bo cuc co chieu sau, tranh chi co 1 nhan vat trong khung trong."
        )
    if not parts:
        return ""
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# BOC TACH TIEU DE CHO THUMBNAIL (theo CONG THUC tieu de cua nguoi dung)
#   Tach:    van de | khoang trong to mo | boi canh | tu huyet
#   Suy ra:  chu the <- van de ; hanh dong/bieu tuong <- to mo ; cam xuc <- tu huyet ; the gioi canh <- boi canh
# Nguoi dung duyet/sua 8 truong nay truoc khi sinh prompt.
# ---------------------------------------------------------------------------
BREAK_KEYS = ("van_de", "to_mo", "boi_canh", "tu_huyet", "chu_the", "hanh_dong", "cam_xuc", "the_gioi_canh", "hook")
BREAK_EXTRA_KEYS = ("y_tuong_goc", "bo_cuc_tham_chieu", "hook_goc", "hook_ly_do", "hook_nguon", "chu_doi_thu")

# Quy tac HOOK (chu tren thumbnail): phai BO TRO / LIEN QUAN TRUC TIEP voi tieu de, khong bia chi tiet moi.
# (Loi that: tieu de "...Discovered SILK [The Bizarre ACCIDENT]" nhung hook "DROPPED IN TEA?" - bia chi tiet 'tra'.)
HOOK_RULE = (
    "HOOK = cum 2-4 tu IN HOA, viet bang NGON NGU CUA TIEU DE, BO TRO tieu de: chon 1 TU KHOA / cai TO MO dang NAM TRONG "
    "tieu de roi dong khung lai (cau hoi / canh bao / nhan manh) de tang to mo. HOOK va tieu de phai LIEN QUAN TRUC TIEP: "
    "nguoi xem doc ca hai phai thay chung noi CUNG MOT chuyen. TUYET DOI KHONG them su kien/vat/chi tiet/dia danh MOI "
    "khong co trong tieu de (vd tieu de khong nhac 'tra' thi hook khong duoc noi 'tra'), KHONG tiet lo dap an cua tieu de. "
    "Duoc lap lai 1 tu khoa cua tieu de nhung doi cach goi (vd tieu de '...Bizarre ACCIDENT' -> hook 'WHAT ACCIDENT?' hoac "
    "'PURE ACCIDENT?'; KHONG chep nguyen ca cum tieu de)."
)


def _hook_grounded(title, goc):
    """`goc` = tu khoa/cum cua TIEU DE ma hook dua vao. Dat khi it nhat 1 tu (>=3 chu cai, hoac 1 ky tu CJK) cua `goc`
    nam that su trong tieu de. Chong truong hop hook bia chi tiet khong co trong tieu de."""
    g, t = _unaccent(goc), _unaccent(title)
    if not g or not t:
        return False
    if g in t:
        return True
    twords = set(t.replace("-", " ").split())
    for w in g.replace("-", " ").split():
        w = w.strip(".,!?:;\"'()[]{}")
        if _script_flags(w) & {"cjk", "thai"}:
            if any(ch in t for ch in w):
                return True
        elif len(w) >= 3 and (w in twords or any(w in tw or tw in w for tw in twords if len(tw) >= 4)):
            return True
    return False
TU_HUYET_LABELS = ("Sợ hãi", "Tò mò", "Tham lam", "Cảnh giác")


def _unaccent(s):
    import unicodedata
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d").replace("Đ", "D").lower().strip()


def _norm_tu_huyet(v):
    k = _unaccent(str(v or ""))
    for label in TU_HUYET_LABELS:
        if _unaccent(label) in k:
            return label
    return "Tò mò"


def _empty_breakdown():
    b = {k: "" for k in BREAK_KEYS}
    b["tu_huyet"] = "Tò mò"
    b["ngon_ngu_tieu_de"] = ""
    return b


# ---- Tieng Viet CO DAU 100% cho cac o boc tach (nguoi dung doc de kiem tra) ----
VN_DIACRITIC_RULE = (
    "\nQUY TẮC NGÔN NGỮ (BẮT BUỘC): MỌI ô mô tả (vấn đề, khoảng trống tò mò, bối cảnh, chủ thể, hành động, cảm xúc, "
    "thế giới cảnh, ý tưởng, bố cục) PHẢI viết bằng TIẾNG VIỆT CÓ DẤU đầy đủ (ví dụ: “người tiền sử tìm kiếm khoái cảm”). "
    "TUYỆT ĐỐI KHÔNG viết tiếng Việt không dấu (kiểu “nguoi tien su”), KHÔNG viết tiếng Anh hay tiếng của tiêu đề "
    "trong các ô này — dù tiêu đề gốc viết bằng ngôn ngữ nào, các ô vẫn là TIẾNG VIỆT CÓ DẤU."
)
VN_TEXT_KEYS = ("van_de", "to_mo", "boi_canh", "chu_the", "hanh_dong", "cam_xuc", "the_gioi_canh",
                "y_tuong_goc", "bo_cuc_tham_chieu", "hook_ly_do")
_VN_MARKS = set("àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ")


def _lacks_vn_diacritics(text):
    """True neu o dai >= 8 chu cai ma KHONG co ky tu tieng Viet co dau nao (tieng Viet khong dau hoac tieng Anh)."""
    t = (text or "").strip()
    if sum(1 for c in t if c.isalpha()) < 8:
        return False
    return not any(c in _VN_MARKS for c in t.lower())


def _fix_vn_diacritics(bks, keys=None):
    """Quet cac o boc tach: o nao thieu dau -> nho AI viet lai thanh tieng Viet CO DAU (toi da 2 luot).
    Sua truc tiep tren list dict `bks`; loi mang/AI thi giu nguyen (khong lam hong ca loat)."""
    import json
    keys = tuple(keys or VN_TEXT_KEYS)
    for _ in range(2):
        bad = []
        for i, b in enumerate(bks):
            for k in keys:
                if _lacks_vn_diacritics(b.get(k)):
                    bad.append({"id": "%d|%s" % (i, k), "text": b[k]})
        if not bad:
            return bks
        system = (
            "Bạn là biên tập viên tiếng Việt. Nhận danh sách đoạn văn ngắn đang bị viết KHÔNG DẤU hoặc bằng ngôn ngữ khác. "
            "Hãy viết lại MỖI đoạn thành TIẾNG VIỆT CÓ DẤU đầy đủ, giữ nguyên ý (nếu là tiếng Anh/ngôn ngữ khác thì DỊCH sang "
            "tiếng Việt có dấu). Ngắn gọn như bản gốc. KHÔNG thêm ý mới."
        )
        user = ("Danh sách (JSON):\n" + json.dumps(bad, ensure_ascii=False) +
                '\n\nTrả về JSON là MỘT MẢNG, mỗi phần tử {"id": "...", "text": "..."} giữ nguyên id.')
        try:
            res = llm.chat_json(system, user, temperature=0.1, role="analyze")
        except Exception:
            return bks
        if isinstance(res, dict):
            for key in ("items", "data", "result"):
                if isinstance(res.get(key), list):
                    res = res[key]
                    break
        if not isinstance(res, list):
            return bks
        for r in res:
            if not isinstance(r, dict):
                continue
            try:
                i_s, k = str(r.get("id", "")).split("|", 1)
                i = int(i_s)
            except ValueError:
                continue
            new = str(r.get("text") or "").strip()
            if 0 <= i < len(bks) and k in keys and new and not _lacks_vn_diacritics(new):
                bks[i][k] = new
    return bks


def decompose_titles_for_thumb(titles, thumbnail_dna=None):
    """Boc tach danh sach tieu de theo cong thuc cua nguoi dung roi suy ra hinh thumbnail.
    Tra ve list dict (cung thu tu `titles`), moi dict co cac khoa BREAK_KEYS (+ ngon_ngu_tieu_de)."""
    import json
    char_lock = _character_lock_block(thumbnail_dna)
    system = (
        "Ban la giam doc sang tao thumbnail YouTube. Voi MOI tieu de, hay BOC TACH theo CONG THUC cua nguoi dung "
        "roi SUY RA hinh anh thumbnail.\n"
        "CONG THUC BOC TACH:\n"
        "(1) VAN DE = tu khoa/van de chinh ma khan gia dang go tim.\n"
        "(2) KHOANG TRONG TO MO = 'luoi cau' cam xuc / noi dau / dieu chua biet khien nguoi ta phai bam vao.\n"
        "(3) BOI CANH = cum dong goi/the loai/con so/do tin cay (de RONG neu tieu de khong co).\n"
        "(4) TU HUYET = DUNG 1 trong: So hai, To mo, Tham lam (ket qua de dang), Canh giac.\n"
        "SUY RA HINH (nhin thay duoc, ve duoc):\n"
        "- CHU THE <- van de: ai/cai gi la TRUNG TAM cua hinh.\n"
        "- HANH DONG hoac BIEU TUONG <- khoang trong to mo: dieu gi dang xay ra / vat gi gay to mo (cu the, khong chung chung).\n"
        "- CAM XUC <- tu huyet: ta CU THE mat-may-mieng cua nhan vat, TUYET DOI KHONG dung tinh tu chung chung "
        "nhu 'ngac nhien'/'to mo'.\n"
        "- THE GIOI CANH <- boi canh: noi/thoi diem xay ra, BAM DUNG NOI DUNG TIEU DE (tieu de hien dai thi canh hien dai; "
        "tieu de lich su thi canh lich su). KHONG mac dinh the gioi dac trung cua kenh.\n"
        "- HOOK (chu tren thumbnail) <- khoang trong to mo: " + HOOK_RULE + "\n"
        "Moi truong viet NGAN GON (toi da ~14 tu), de doc nhanh, KHONG van hoc thuat, KHONG tom tat dai dong. "
        "RIENG truong `hook` viet bang NGON NGU CUA TIEU DE (khong dich), con `hook_goc` chep NGUYEN tu/cum co that trong tieu de."
        + VN_DIACRITIC_RULE
        + ("\nKENH CO NHAN VAT CO DINH (thiet ke da khoa, KHONG ta lai dau/toc/trang phuc): " + char_lock
           + "\n=> truong chu_the BAT BUOC bat dau bang cum “Nhân vật cố định của kênh” + no dang lam/tuong tac voi gi "
             "(KHONG doi thanh nghe nghiep/nhan vat khac)."
           if char_lock else "")
    )
    schema = (
        "Tra ve JSON la MOT MANG, moi phan tu dung cau truc (giu nguyen index):\n"
        '{"index": 0, "ngon_ngu_tieu_de": "ten ngon ngu cua tieu de, vd Spanish",\n'
        ' "van_de": "...", "to_mo": "...", "boi_canh": "...", "tu_huyet": "So hai|To mo|Tham lam|Canh giac",\n'
        ' "chu_the": "...", "hanh_dong": "...", "cam_xuc": "...", "the_gioi_canh": "...",\n'
        ' "hook": "2-4 tu IN HOA, NGON NGU CUA TIEU DE", "hook_goc": "tu/cum CO THAT trong tieu de ma hook dua vao",\n'
        ' "hook_ly_do": "1 cau TIENG VIET CO DAU: hook bo tro tieu de the nao"}'
    )
    out = [None] * len(titles)
    BATCH = 8
    for start in range(0, len(titles), BATCH):
        chunk = titles[start:start + BATCH]
        items = [{"index": start + j, "title": t} for j, t in enumerate(chunk)]
        user = "Danh sach tieu de (JSON):\n" + json.dumps(items, ensure_ascii=False) + "\n\n" + schema
        try:
            res = llm.chat_json(system, user, temperature=0.4, role="analyze")
        except Exception:
            res = []
        if isinstance(res, dict):
            for key in ("items", "data", "result", "titles"):
                if isinstance(res.get(key), list):
                    res = res[key]
                    break
        if isinstance(res, list):
            for pos, r in enumerate(res):
                if not isinstance(r, dict):
                    continue
                try:
                    idx = int(r.get("index", start + pos))
                except (TypeError, ValueError):
                    idx = start + pos
                if 0 <= idx < len(titles):
                    out[idx] = r
    bks = [_clean_breakdown(out[i] or {}) for i in range(len(titles))]
    for b in bks:
        if b.get("hook"):
            b["hook_nguon"] = "tu_tao"
    _regen_ungrounded_hooks(titles, bks)
    return _fix_vn_diacritics(bks)


def _clean_breakdown(r):
    """Chuan hoa 1 ket qua boc tach tu LLM thanh dict day du BREAK_KEYS
    (+ ngon_ngu_tieu_de; y_tuong_goc, bo_cuc_tham_chieu khi lay y tuong tu thumbnail doi thu)."""
    b = _empty_breakdown()
    for k in BREAK_KEYS:
        if k != "tu_huyet":
            b[k] = str(r.get(k) or "").strip()
    b["tu_huyet"] = _norm_tu_huyet(r.get("tu_huyet"))
    b["ngon_ngu_tieu_de"] = str(r.get("ngon_ngu_tieu_de") or "").strip()
    for k in BREAK_EXTRA_KEYS:
        if r.get(k):
            b[k] = str(r.get(k)).strip()
    return b


def _regen_ungrounded_hooks(titles, bks):
    """Hook nao khong bam tu khoa trong TIEU DE (hook_goc khong nam trong tieu de) -> yeu cau AI viet lai 1 lan.
    Sua truc tiep tren `bks`; loi AI thi giu nguyen."""
    import json
    bad = [i for i, b in enumerate(bks) if b.get("hook") and not _hook_grounded(titles[i], b.get("hook_goc"))]
    if not bad:
        return bks
    system = (
        "Bạn là giám đốc sáng tạo thumbnail YouTube. Với mỗi tiêu đề, hãy viết lại HOOK (chữ trên thumbnail) cho đúng quy tắc, "
        "vì hook cũ KHÔNG bám tiêu đề (bịa chi tiết không có trong tiêu đề).\nQUY TẮC HOOK:\n" + HOOK_RULE +
        "\nTrường hook_goc = từ/cụm CÓ THẬT trong tiêu đề mà hook dựa vào (chép nguyên từ tiêu đề). "
        "hook_ly_do viết TIẾNG VIỆT CÓ DẤU, 1 câu ngắn: hook bổ trợ tiêu đề thế nào."
    )
    items = [{"index": i, "title": titles[i], "to_mo": bks[i].get("to_mo", ""), "hook_cu_sai": bks[i].get("hook", "")}
             for i in bad]
    user = ("Danh sách (JSON):\n" + json.dumps(items, ensure_ascii=False) +
            '\n\nTrả về JSON là MỘT MẢNG, mỗi phần tử {"index": n, "hook": "...", "hook_goc": "...", "hook_ly_do": "..."}.')
    try:
        res = llm.chat_json(system, user, temperature=0.5, role="analyze")
    except Exception:
        return bks
    if isinstance(res, dict):
        for key in ("items", "data", "result"):
            if isinstance(res.get(key), list):
                res = res[key]
                break
    if not isinstance(res, list):
        return bks
    for r in res:
        if not isinstance(r, dict):
            continue
        try:
            i = int(r.get("index"))
        except (TypeError, ValueError):
            continue
        h, g = str(r.get("hook") or "").strip(), str(r.get("hook_goc") or "").strip()
        if i in bad and h and _hook_grounded(titles[i], g):
            bks[i]["hook"], bks[i]["hook_goc"] = h, g
            bks[i]["hook_ly_do"] = str(r.get("hook_ly_do") or "").strip()
    return bks


def read_competitor_pair(image_bytes, title_goc):
    """NHIN thumbnail doi thu + TIEU DE GOC cua ho -> hieu 'cap' anh/chu/tieu de dang hua dieu gi, de TAI TAO TIEU DE
    moi van LIEN QUAN & BO TRO voi anh + chu do. Tra ve {chu_tren_thumb, hinh_hua, cap_bo_tro}
    (hinh_hua, cap_bo_tro = TIENG VIET CO DAU; chu_tren_thumb = nguyen van, de rong neu khong co chu)."""
    system = (
        "Bạn là chuyên gia thumbnail & tiêu đề YouTube. Bạn xem THUMBNAIL của một video đối thủ nhiều view cùng TIÊU ĐỀ GỐC "
        "của nó. Hãy hiểu CẶP (ảnh + chữ trên ảnh + tiêu đề) đang HỨA điều gì với người xem và chúng BỔ TRỢ nhau ra sao.\n"
        "Trả về JSON: {\"chu_tren_thumb\": \"chữ in trên ảnh, chép CHÍNH XÁC nguyên văn (để rỗng nếu không có chữ)\", "
        "\"hinh_hua\": \"1 câu: ảnh cho người xem thấy/gợi điều gì (chủ thể, hành động, biểu tượng gây tò mò)\", "
        "\"cap_bo_tro\": \"1 câu: chữ trên ảnh + ảnh bổ trợ tiêu đề gốc thế nào (khoảng trống tò mò chung của cả cặp)\"}\n"
        "hinh_hua và cap_bo_tro viết TIẾNG VIỆT CÓ DẤU đầy đủ, ngắn gọn (tối đa ~25 từ mỗi câu). "
        "Không mô tả khuôn mặt người thật."
    )
    r = llm.chat_json(system, "TIÊU ĐỀ GỐC: " + str(title_goc or ""), temperature=0.2, vision_images=[image_bytes])
    r = r if isinstance(r, dict) else {}
    out = {"chu_tren_thumb": str(r.get("chu_tren_thumb") or "").strip(),
           "hinh_hua": str(r.get("hinh_hua") or "").strip(),
           "cap_bo_tro": str(r.get("cap_bo_tro") or "").strip()}
    return _fix_vn_diacritics([out], keys=("hinh_hua", "cap_bo_tro"))[0]


def breakdown_from_reference_thumb(image_bytes, new_title, thumbnail_dna=None):
    """NHIN thumbnail cua DOI THU (da nhieu view) -> rut BO CUC + Y TUONG -> ve lai cho TIEU DE MOI:
    dien san cac o boc tach (nguoi dung duyet/sua roi moi sinh prompt).
    BAM theo BO CUC cua anh doi thu (vi tri/ty le chu the, vat phu, vung chu, goc may, lop chieu sau) nhung NOI DUNG
    theo tu khoa/van de cua TIEU DE MOI; phong cach/mau/font/nhan vat theo DNA kenh nguoi dung (ap o buoc sinh prompt).
    KHONG chep chu, nhan vat, tac pham, logo, guong mat nguoi that cua doi thu."""
    char_lock = _character_lock_block(thumbnail_dna)
    system = (
        "Ban la giam doc sang tao thumbnail YouTube. Ban duoc xem THUMBNAIL CUA DOI THU (video da nhieu view) va 1 "
        "TIEU DE MOI cua nguoi dung. Nhiem vu: VE LAI thumbnail do cho TIEU DE MOI, theo 2 nguyen tac:\n"
        "(A) BAM BO CUC cua thumbnail doi thu: chu the dat o dau va chiem bao nhieu % khung, vat/nhan vat phu o dau, "
        "vung chu (tren/duoi/trai/phai), goc may (can canh/trung canh/toan canh), co bao nhieu lop tien/trung/hau canh, "
        "huong nhin/huong hanh dong. Mo ta BO CUC nay vao truong bo_cuc_tham_chieu (CHI bo cuc: khong tai mau sac, "
        "khong tai phong cach ve).\n"
        "(B) NOI DUNG theo TIEU DE MOI (tu khoa, van de, boi canh cua tieu de moi) - KHONG ve lai noi dung cu cua doi thu. "
        "Dat chu the/vat/hanh dong cua tieu de moi vao DUNG VI TRI & TY LE cua bo cuc tham chieu.\n"
        "Phong cach ve/mau/font/nhan vat se duoc ap SAU theo DNA kenh nguoi dung - ban chi quyet dinh BO CUC va NOI DUNG.\n"
        "CONG THUC: tach TIEU DE MOI thanh VAN DE / KHOANG TRONG TO MO / BOI CANH / TU HUYET (So hai|To mo|Tham lam|Canh giac), "
        "roi SUY RA HINH: CHU THE <- van de; HANH DONG hoac BIEU TUONG <- khoang trong to mo; CAM XUC <- tu huyet "
        "(ta CU THE mat-may-mieng, khong dung tinh tu chung chung); THE GIOI CANH <- boi canh cua TIEU DE MOI. "
        "Trong chu_the / hanh_dong / the_gioi_canh, GHI RO vi tri & ty le theo bo cuc tham chieu "
        "(vd 'o ben trai, chiem khoang 40% khung').\n"
        "Neu thumbnail doi thu khong lien quan tieu de moi, van lay BO CUC cua no nhung noi dung bam tieu de moi.\n"
        "CHU TREN THUMBNAIL DOI THU (HOOK): doc CHINH XAC chu in tren anh (chu_doi_thu; de rong neu khong co chu). "
        "Neu chu do LIEN QUAN va BO TRO duoc cho TIEU DE MOI (cung noi mot chuyen, khong bia chi tiet khong co trong "
        "tieu de moi) thi DUNG LUON lam `hook` (neu khac ngon ngu tieu de moi thi DICH sang NGON NGU CUA TIEU DE MOI), "
        "chu_doi_thu_dung_duoc=true, hook_nguon=\"doi_thu\". Neu KHONG hop thi TU TAO hook moi dung quy tac sau, "
        "chu_doi_thu_dung_duoc=false, hook_nguon=\"tu_tao\". QUY TAC HOOK: " + HOOK_RULE + "\n"
        "AN TOAN (BAT BUOC): chu tren anh doi thu CHI duoc dung cho truong `hook`, KHONG mo ta chu vao cac o khac. "
        "TUYET DOI KHONG: dung lai nhan vat, tac pham, logo, thiet ke rieng cua doi thu; mo ta guong mat hay dac diem "
        "nhan vat cua NGUOI THAT (neu anh co nguoi that thi doi thanh nhan vat cua kenh nguoi dung hoac mot nhan vat chung chung).\n"
        "Moi truong viet NGAN GON (toi da ~25 tu cho bo_cuc_tham_chieu, ~16 tu cho cac truong khac), de doc nhanh."
        + VN_DIACRITIC_RULE
        + ("\nKENH NGUOI DUNG CO NHAN VAT CO DINH (thiet ke da khoa, KHONG ta lai): " + char_lock
           + "\n=> chu_the BAT BUOC bat dau bang cum “Nhân vật cố định của kênh” (KHONG doi thanh nghe nghiep/nhan vat khac "
             "nhu nha khoa hoc, bac si...) + vi tri/ty le theo bo cuc tham chieu + no dang lam/tuong tac voi gi." if char_lock else "")
    )
    user = (
        "TIEU DE MOI: " + new_title + "\n\n"
        "Tra ve JSON dung cau truc:\n"
        '{"y_tuong_goc": "Y TUONG hinh anh cua thumbnail doi thu va vi sao hut click (1 cau ngan)",\n'
        ' "bo_cuc_tham_chieu": "BO CUC cua thumbnail doi thu: vi tri & ty le chu the, vat phu, vung chu, goc may, lop chieu sau",\n'
        ' "ngon_ngu_tieu_de": "ten ngon ngu cua tieu de moi, vd Spanish",\n'
        ' "van_de": "...", "to_mo": "...", "boi_canh": "...", "tu_huyet": "So hai|To mo|Tham lam|Canh giac",\n'
        ' "chu_the": "...", "hanh_dong": "...", "cam_xuc": "...", "the_gioi_canh": "...",\n'
        ' "chu_doi_thu": "chu in tren thumbnail doi thu (nguyen van, de rong neu khong co)",\n'
        ' "chu_doi_thu_dung_duoc": true/false, "hook_nguon": "doi_thu|tu_tao",\n'
        ' "hook": "2-4 tu IN HOA, NGON NGU CUA TIEU DE MOI", "hook_goc": "tu/cum CO THAT trong tieu de moi ma hook dua vao",\n'
        ' "hook_ly_do": "1 cau TIENG VIET CO DAU: hook bo tro tieu de moi the nao"}'
    )
    r = llm.chat_json(system, user, temperature=0.5, vision_images=[image_bytes])
    bk = _clean_breakdown(r if isinstance(r, dict) else {})
    if bk.get("hook_nguon") not in ("doi_thu", "tu_tao"):
        bk["hook_nguon"] = "tu_tao"
    # hook phai bam TIEU DE MOI; hook lay tu doi thu thi hook_goc cung phai nam trong tieu de moi
    hook_truoc = bk.get("hook")
    _regen_ungrounded_hooks([new_title], [bk])
    if bk.get("hook") != hook_truoc or not _hook_grounded(new_title, bk.get("hook_goc")):
        bk["hook_nguon"] = "tu_tao"      # da phai viet lai (hook doi thu khong bam tieu de moi)
    return _fix_vn_diacritics([bk])[0]


# Quy tac THE GIOI CANH: bam NOI DUNG TIEU DE, chi giu phong cach/mau/bo cuc/font/nhan vat co dinh cua kenh.
WORLD_RULE = (
    "THE GIOI/BOI CANH cua canh (nen, dia diem, thoi diem, vat dung xung quanh) PHAI THEO NOI DUNG TIEU DE — "
    "tieu de hien dai thi canh hien dai, tieu de lich su thi canh lich su. TUYET DOI KHONG mac dinh the gioi dac trung "
    "cua kenh (vd hang dong tien su). CHI GIU tu kenh: phong cach ve, bang mau, anh sang, bo cuc da khoa, font chu "
    "va thiet ke nhan vat co dinh."
)


def _breakdown_block(bk):
    """Khoi 'PHAN TICH DA DUOC NGUOI DUNG DUYET' chen vao prompt sinh thumbnail (rong neu khong co)."""
    if not bk:
        return ""
    g = lambda k: (str(bk.get(k) or "").strip() or "(de trong - AI tu quyet)")
    layout = str(bk.get("bo_cuc_tham_chieu") or "").strip()
    layout_line = (
        "BO CUC THAM CHIEU (lay tu thumbnail doi thu da nhieu view; nguoi dung muon VE LAI theo dung bo cuc nay): %s\n"
        "=> Moi o noi dung (chu the, vat, bieu tuong, nen) phai dat dung VI TRI & TY LE theo bo cuc tren; "
        "NOI DUNG van la cua tieu de moi; phong cach/mau/font/nhan vat van theo DNA kenh.\n" % layout
        if layout else "")
    hook = str(bk.get("hook") or "").strip()
    hook_line = (
        "CHU TREN THUMBNAIL (o HOOK) DA DUOC NGUOI DUNG DUYET: \"%s\" => o HOOK PHAI la CHINH XAC cum nay "
        "(giu nguyen ngon ngu & chu cai, KHONG doi, KHONG dich lai, KHONG them bot).\n" % hook
        if hook else "")
    return layout_line + hook_line + (
        "PHAN TICH TIEU DE DA DUOC NGUOI DUNG DUYET - BAT BUOC BAM SAT, KHONG tu y doi y:\n"
        "- Van de: %s\n- Khoang trong to mo: %s\n- Boi canh: %s\n- Tu huyet: %s\n"
        "=> HINH CAN VE:\n- Chu the: %s\n- Hanh dong/Bieu tuong: %s\n- Cam xuc nhan vat: %s\n- The gioi canh: %s\n"
        "CACH DIEN CAC O: o chu the/vat/su viec (SUBJECT/FACE/OBJECT...) <- Chu the + Hanh dong; "
        "o bieu tuong/hanh dong (SYMBOL/ACTION/...) <- Hanh dong/Bieu tuong; "
        "o bieu cam (EMOTION) <- Cam xuc nhan vat (ta CU THE mat-may-mieng); "
        "o nen/canh (SCENE/BACKGROUND/...) <- The gioi canh. "
        "Neu template DA CO SAN nhan vat co dinh thi o SUBJECT/OBJECT la vat/su viec ma nhan vat dang tuong tac "
        "(rut tu Chu the + Hanh dong). Gia tri o trong viet TIENG ANH, cu the; HOOK van viet theo ngon ngu tieu de "
        "va BO TRO tieu de.\n"
    ) % (g("van_de"), g("to_mo"), g("boi_canh"), g("tu_huyet"),
         g("chu_the"), g("hanh_dong"), g("cam_xuc"), g("the_gioi_canh"))


def _neutralize_world(comp):
    """Viet lai MAU BO CUC CU: thay the gioi/thoi dai/dia diem cu the cua kenh (vd 'prehistoric', 'cave')
    bang o trong [[SCENE]], giu NGUYEN moi thu khac. Tra ve None neu ket qua khong an toan."""
    import re
    ph = lambda s: set(re.findall(r"\[\[[A-Za-z_]+\]\]", s))
    system = (
        "Ban la bien tap vien prompt thumbnail. Ban nhan 1 TEMPLATE bo cuc co dinh (tieng Anh) co cac o trong dang [[X]]. "
        "Nhiem vu: viet lai TEMPLATE sao cho THE GIOI/BOI CANH/THOI DAI/DIA DIEM cu the cua kenh "
        "(vd 'prehistoric', 'primitive landscape', 'cave background', 'medieval', 'office') KHONG con bi ghi cung — "
        "thay phan mo ta nen/canh do bang MOT o trong [[SCENE]] (vd '... set in [[SCENE]], drawn in the same flat hand-drawn style ...'). "
        "Bo cac tinh tu thoi dai gan voi nhan vat (vd 'prehistoric stickman' -> 'stickman'): thiet ke nhan vat da khoa rieng. "
        "GIU NGUYEN 100% con lai: bo cuc, vi tri, ty le, mau, phong cach ve, banner chu va MOI o trong [[...]] da co "
        "(dac biet [[HOOK]], [[FONT]]). KHONG them chi tiet moi."
    )
    user = ('TEMPLATE:\n' + comp + '\n\nTra ve JSON: {"template": "<template da viet lai, co [[SCENE]]>"}')
    r = llm.chat_json(system, user, temperature=0.2, role="analyze")
    new = str((r or {}).get("template") or "").strip()
    if not new or "[[SCENE]]" not in new:
        return None
    if not ph(comp) <= ph(new):
        return None
    if not (0.6 <= len(new) / max(1, len(comp)) <= 1.7):
        return None
    return new


def _adapt_template_layout(comp, ref_layout):
    """Viet lai MAU BO CUC khoa cua kenh sao cho cach SAP XEP (vi tri/ty le chu the, vat phu, vung chu, goc may, lop
    chieu sau) theo BO CUC THAM CHIEU (tieng Viet, lay tu thumbnail doi thu). Giu NGUYEN phong cach ve, bang mau, anh sang,
    kieu chu/banner, nhan vat khoa va MOI o [[...]]. Tra ve None neu ket qua khong an toan."""
    import re
    ph = lambda s: set(re.findall(r"\[\[[A-Za-z_]+\]\]", s))
    system = (
        "Bạn là biên tập viên prompt thumbnail. Bạn nhận 1 TEMPLATE bố cục cố định (tiếng Anh, có các ô trống [[X]]) và 1 "
        "BỐ CỤC THAM CHIẾU (tiếng Việt, lấy từ thumbnail đối thủ). Hãy viết lại TEMPLATE (tiếng Anh) sao cho CÁCH SẮP XẾP — "
        "vị trí & tỷ lệ chủ thể, vật phụ, vùng đặt chữ, góc máy, số lớp tiền/trung/hậu cảnh — ĐÚNG THEO BỐ CỤC THAM CHIẾU. "
        "GIỮ NGUYÊN 100%: phong cách vẽ, bảng màu, ánh sáng, kiểu chữ/banner (nội dung ô [[FONT]], [[HOOK]]), thiết kế nhân vật "
        "cố định và MỌI ô trống [[...]] đã có. KHÔNG thêm màu/phong cách/nhân vật/chữ của thumbnail đối thủ. "
        "Chỉ đổi phần bố trí không gian cho khớp bố cục tham chiếu."
    )
    user = ("TEMPLATE:\n" + comp + "\n\nBỐ CỤC THAM CHIẾU:\n" + ref_layout +
            '\n\nTrả về JSON: {"template": "<template đã viết lại>"}')
    r = llm.chat_json(system, user, temperature=0.2, role="analyze")
    new = str((r or {}).get("template") or "").strip()
    if not new or not ph(comp) <= ph(new):
        return None
    if not (0.6 <= len(new) / max(1, len(comp)) <= 1.8):
        return None
    return new


def ensure_scene_slot(dna_name):
    """Tra ve thumbnail_dna (dict) cua DNA 'ai'. Mau bo cuc CU chua co [[SCENE]] thi tu nang cap 1 lan va luu lai
    (giu ban goc o khoa_bo_cuc_goc_en) de canh BAM NOI DUNG TIEU DE thay vi bi dong dinh the gioi cua kenh."""
    from . import store
    d = store.get_dna(dna_name, "ai")
    if not d:
        return None
    dna = d["dna"]
    t = dna.get("thumbnail_dna") or {}
    comp = (t.get("khoa_bo_cuc_en") or "").strip()
    if comp and "[[SCENE]]" not in comp and not t.get("khoa_bo_cuc_scene_checked"):
        try:
            new = _neutralize_world(comp)
        except Exception:
            return t   # loi tam thoi (vd 9router tat) -> khong danh dau da kiem, de lan sau thu lai
        t["khoa_bo_cuc_scene_checked"] = True
        if new:
            t["khoa_bo_cuc_goc_en"] = comp
            t["khoa_bo_cuc_en"] = new
        dna["thumbnail_dna"] = t
        store.save_dna(dna_name, dna, "ai")
    return t


def _script_flags(text):
    """Cac he chu KHONG-Latin co mat trong text (cyrillic/cjk/hangul/thai/arabic/devanagari/greek)."""
    flags = set()
    for ch in text or "":
        o = ord(ch)
        if 0x0400 <= o <= 0x04FF:
            flags.add("cyrillic")
        elif 0x3040 <= o <= 0x30FF or 0x4E00 <= o <= 0x9FFF:
            flags.add("cjk")
        elif 0xAC00 <= o <= 0xD7AF or 0x1100 <= o <= 0x11FF:
            flags.add("hangul")
        elif 0x0E00 <= o <= 0x0E7F:
            flags.add("thai")
        elif 0x0600 <= o <= 0x06FF:
            flags.add("arabic")
        elif 0x0900 <= o <= 0x097F:
            flags.add("devanagari")
        elif 0x0370 <= o <= 0x03FF:
            flags.add("greek")
    return flags


def _hook_matches_title_script(title, hook):
    """Tieu de dung chu khong-Latin (Nga/Nhat/Han/Thai...) thi HOOK cung phai co chu do.
    Tieu de chu Latin (es/en/vi/pt/fr...) khong kiem duoc bang ky tu -> tin vao model."""
    ts = _script_flags(title)
    if not ts or not hook:
        return True
    return bool(ts & _script_flags(hook))


def _hook_lang_retry_note(title):
    return ("\nLUU Y QUAN TRONG: lan truoc chu HOOK SAI ngon ngu. HOOK PHAI viet bang CHINH NGON NGU va BANG CHU CAI "
            "cua tieu de ('" + title + "'), TUYET DOI KHONG dich sang tieng Anh.")


def _prompt_locked_composition(title, comp_lock, font_lock, char_lock="", richness_hint="", breakdown=None):
    """DNA co 'khoa_bo_cuc_en' (template bo cuc CO DINH + placeholder [[X]]) ->
    dien MOI o trong theo tieu de (linh hoat, khong cung so o). [[FONT]] = khoa chu.
    Bo cuc/ty le/mau giu nguyen moi thumb; chu the/bieu tuong/hook bam tieu de.
    char_lock (neu co) = thiet ke nhan vat co dinh, duoc CHEN Y NGUYEN vao cuoi prompt
    (khong de LLM tu ve lai dau/toc/trang phuc).
    richness_hint (neu co) = cong thuc bieu cam + boi canh tien/trung/hau canh tu DNA, giup dien
    noi dung cac o TRONG (bieu cam cu the, co nhan vat phu) thay vi chung chung/don dieu."""
    import re
    slots = [s for s in dict.fromkeys(re.findall(r"\[\[([A-Za-z_]+)\]\]", comp_lock))
             if s.upper() != "FONT"]
    if not slots:  # template khong co o trong -> tra thang (van khoa font + nhan vat)
        p = comp_lock.replace("[[FONT]]", font_lock or "")
        if char_lock:
            p = p + " " + char_lock
        return {"phan_tich_tieu_de": "", "chu_the_chinh": "", "boi_canh_de_xuat": "",
                "text_tren_thumb": "", "thumbnail_prompt_en": p,
                "khoa_chu_en": font_lock, "khoa_nhan_vat_en": char_lock, "khoa_bo_cuc": True}
    def _slot_line(s):
        u = s.upper()
        if u == "HOOK":  # chu TREN THUMB: cung ngon ngu voi tieu de (KHONG ep tieng Anh)
            return ('  "%s": "cum 2-4 tu IN HOA viet bang NGON NGU CUA TIEU DE (dung ngon ngu o truong ngon_ngu_tieu_de, '
                    'KHONG dich sang tieng Anh), BO TRO va LIEN QUAN TRUC TIEP tieu de: dua vao 1 tu khoa/cai to mo CO TRONG '
                    'tieu de, KHONG bia chi tiet moi",' % s)
        if u == "SCENE":  # the gioi canh: BAM NOI DUNG TIEU DE
            return ('  "%s": "gia tri TIENG ANH: THE GIOI/BOI CANH BAM NOI DUNG TIEU DE (khong mac dinh the gioi cua kenh), '
                    'cu the nhung ngan",' % s)
        extra = " - MO TA CU THE, khong dung tinh tu chung chung" if u == "EMOTION" else ""
        return '  "%s": "gia tri TIENG ANH, hop tieu de%s",' % (s, extra)

    slot_lines = ('  "ngon_ngu_tieu_de": "ten ngon ngu cua TIEU DE (vd Spanish, English, Vietnamese, Japanese)",\n'
                  + "\n".join(_slot_line(s) for s in slots))
    hook_key = next((s for s in slots if s.upper() == "HOOK"), None)
    system = (
        "Ban la giam doc nghe thuat thumbnail YouTube trieu view. "
        "BO CUC, TY LE, MAU va FONT da KHOA CUNG (khong duoc doi). Viec cua ban: doc TIEU DE "
        "roi dien cac O TRONG sao cho HOP tieu de, hut click, dung tam ly nguoi xem. "
        "Bieu tuong/chu the/bieu cam PHAI BIEN THIEN RO RET theo TUNG tieu de (KHONG dung mac dinh "
        "cung 1 kieu chu the/hanh dong cho moi bai, du template bo cuc giong nhau).\n"
        "NGUYEN TAC BO TRO (1+1=3): thumbnail va TIEU DE la 1 CAP, khong phai 1 ban sao cua nhau. "
        "Hinh anh (chu the/bieu tuong/hanh dong) TRUYEN CAM XUC va goi mo 1 GOC RIENG cua tieu de "
        "(vd chi tiet gay to mo, hau qua chua noi, phan ung cua nhan vat), tieu de van giu vai tro cung "
        "cap boi canh/tu khoa chinh. TUYET DOI KHONG ve lai dung nghia den cua tieu de — muc tieu la nguoi xem "
        "doc tieu de + nhin hinh se TO MO HON la chi doc rieng tieu de.\n"
        + HOOK_RULE + "\n"
        + CAST_ACTION_GRAMMAR + "\n" + WORLD_RULE
        + ("\nTHIET KE NHAN VAT (dau/toc/trang phuc) DA KHOA CUNG, se duoc chen tu dong vao cuoi prompt — "
           "KHONG mo ta lai dau/toc/trang phuc trong cac o trong, chi dien HANH DONG/TU THE/BIEU CAM cua "
           "nhan vat do sao cho hop tieu de.\n" if char_lock else "")
        + ("\n" + richness_hint + "\n" if richness_hint else "")
    )
    user = (
        "TIEU DE: " + title + "\n\n"
        + (_breakdown_block(breakdown) + "\n" if breakdown else "")
        + "TEMPLATE BO CUC (chi de tham chieu, KHONG sua):\n" + comp_lock + "\n\n"
        "Dien cac o trong. Tra ve JSON dung cau truc:\n{\n" + slot_lines + "\n"
        '  "phan_tich_tieu_de": "tieu de noi ve gi (TIENG VIET)",\n'
        '  "chu_the_chinh": "chu the + bieu tuong (TIENG VIET)",\n'
        '  "boi_canh_de_xuat": "y nghia hinh anh theo tieu de (TIENG VIET)"\n'
        "}\n"
        "Cac o trong viet TIENG ANH, RIENG o HOOK viet bang ngon ngu cua TIEU DE; 3 field cuoi viet TIENG VIET CO DAU."
    )
    r = llm.chat_json(system, user, temperature=0.6)
    approved_hook = str((breakdown or {}).get("hook") or "").strip()
    if hook_key and approved_hook:      # nguoi dung da duyet/sua hook o buoc boc tach -> dung CHINH XAC, khong de AI doi
        r[hook_key] = approved_hook
    elif hook_key and not _hook_matches_title_script(title, str(r.get(hook_key) or "")):
        r = llm.chat_json(system, user + _hook_lang_retry_note(title), temperature=0.6)
    p = comp_lock
    hook = ""
    for s in slots:
        val = str(r.get(s) or "").strip()
        if s.upper() == "HOOK":
            hook = val
        p = p.replace("[[" + s + "]]", val or s.lower().replace("_", " "))
    p = p.replace("[[FONT]]", font_lock or "")
    p = p.replace(" in in ", " in ")   # mau "in [[FONT]]" + khoa font bat dau bang "in EXACTLY" -> bo "in" thua
    if char_lock:
        p = p + " " + char_lock
    return {
        "phan_tich_tieu_de": r.get("phan_tich_tieu_de", ""),
        "chu_the_chinh": r.get("chu_the_chinh", ""),
        "boi_canh_de_xuat": r.get("boi_canh_de_xuat", ""),
        "text_tren_thumb": hook,
        "ngon_ngu_tieu_de": str(r.get("ngon_ngu_tieu_de") or "").strip(),
        "thumbnail_prompt_en": p,
        "khoa_chu_en": font_lock,
        "khoa_nhan_vat_en": char_lock,
        "khoa_bo_cuc": True,
    }


def thumbnail_prompt_from_dna(title, thumbnail_dna, breakdown=None):
    """
    Nhap 1 tieu de + DNA thumb -> tai tao thumbnail dung phong cach kenh.
    CHU (font/mau/vien/hieu ung) = KHOA CUNG, chen Y NGUYEN tu DNA (khong cho model che lai)
    => dong nhat 100%. CHU THE + BOI CANH + CUM HOOK = model tu suy luan tot nhat theo tieu de.
    Neu DNA co 'khoa_bo_cuc_en' -> KHOA CA BO CUC (chi dien slot theo tieu de).
    """
    import json
    font_lock = _font_lock_block(thumbnail_dna)
    char_lock = _character_lock_block(thumbnail_dna)
    richness_hint = _richness_hint_block(thumbnail_dna)
    comp_lock = (thumbnail_dna.get("khoa_bo_cuc_en") or "").strip() if thumbnail_dna else ""
    if comp_lock:
        ref_layout = str((breakdown or {}).get("bo_cuc_tham_chieu") or "").strip()
        if ref_layout:   # ve lai theo BO CUC thumbnail doi thu: chinh cach sap xep trong mau khoa (loi -> giu mau goc)
            try:
                comp_lock = _adapt_template_layout(comp_lock, ref_layout) or comp_lock
            except Exception:
                pass
            font_lock = _strip_font_position(font_lock)   # khoa font van giu kieu chu, bo cau "o chinh giua phia tren"
        return _prompt_locked_composition(title, comp_lock, font_lock, char_lock, richness_hint, breakdown)
    dna_full = json.dumps(thumbnail_dna, ensure_ascii=False, indent=2) if thumbnail_dna else "(chua co DNA)"
    co_chu = bool(font_lock)

    system = (
        "Ban la giam doc nghe thuat thumbnail YouTube trieu view. Ban co DNA 1 kenh va 1 TIEU DE moi.\n"
        "TACH BACH TUYET DOI 2 phan:\n"
        "1) PHONG CACH BAT BIEN (giu Y NGUYEN tu DNA): bang mau, anh sang, bo cuc & bo cuc vang, "
        "ty le %/vi tri chu the, do dong nhat. Ap dung Y HET cho moi thumbnail.\n"
        "2) NOI DUNG SANG TAO (tu suy luan theo TIEU DE): chu the cu the, boi canh, cum HOOK. "
        "TUYET DOI KHONG copy y nguyen boi canh vi du trong DNA.\n"
        "CHU (font/mau/vien/hieu ung): DA KHOA CUNG, se chen tu dong. "
        "=> BAN KHONG DUOC mo ta lai font/mau/vien cua chu. Chi dat dung cho chu bang placeholder [[FONT]].\n"
        + ("THIET KE NHAN VAT (dau/toc/trang phuc/ty le) CUNG DA KHOA CUNG, se chen tu dong vao cuoi prompt. "
           "=> BAN KHONG DUOC mo ta lai dau/toc/trang phuc nhan vat; CHI mo ta HANH DONG/TU THE/BIEU CAM cua "
           "nhan vat do sao cho hop tieu de.\n" if char_lock else "")
        + "Hay SUY NGHI KY nhu 1 chuyen gia: boc tach tieu de -> chon PHUONG AN chu the + boi canh MANH NHAT "
        "(hut click, dung tam ly nguoi xem, hop chu de) -> viet 1 CUM HOOK. " + HOOK_RULE + "\n"
        + CAST_ACTION_GRAMMAR + "\n"
        + "BIEU CAM: neu DNA co 'nhan_vat_dna.cong_thuc_bieu_cam', BAT BUOC dung dung CONG THUC do (mo ta CU THE "
        "mat/may/mieng theo nhom cam xuc GAN NHAT voi tieu de), TUYET DOI KHONG dung 1 tinh tu chung chung nhu "
        "'ngac nhien'/'to mo'.\n"
        "CHIEU SAU BO CUC: neu DNA co 'boi_canh.trung_canh' nhac toi nhan vat phu/dong vat/dam lua, hay CAN NHAC "
        "them 1-2 chi tiet phu do vao boi canh (khi hop tieu de) de anh co chieu sau, tranh chi co 1 chu the "
        "don doc giua khung hinh trong.\n"
        + ("Kenh NAY CO dat chu.\n" if co_chu
           else "Kenh nay KHONG dat chu -> chua khoang trong sach, KHONG dung [[FONT]].\n")
    )
    hook_line = ('  "ngon_ngu_tieu_de": "ten ngon ngu cua TIEU DE (vd Spanish, English, Vietnamese, Japanese)",\n'
                 '  "text_tren_thumb": "cum HOOK 2-4 tu IN HOA, BO TRO va LIEN QUAN TRUC TIEP tieu de (dua vao tu khoa '
                 'CO TRONG tieu de, khong bia chi tiet moi), viet bang NGON NGU CUA TIEU DE (khong dich sang tieng Anh)",\n'
                 if co_chu else '  "text_tren_thumb": "",\n')
    prompt_hint = (
        'prompt TIENG ANH: chu the + boi canh (theo tieu de) + bang mau/anh sang/bo cuc/ty le %/vi tri theo DNA. '
        'Cho chu: viet chinh xac the title text \\"[[HOOK]]\\" [[FONT]] (GIU NGUYEN 2 chuoi [[HOOK]] va [[FONT]], '
        'KHONG tu ta font, KHONG tu viet hook vao prompt).'
        if co_chu else
        'prompt TIENG ANH: chu the + boi canh (theo tieu de) + bang mau/anh sang/bo cuc/ty le %/vi tri theo DNA. '
        'Chua khoang trong sach cho chu, KHONG them chu.'
    )
    user = (
        "DNA PHONG CACH (CHI lay STYLE mau/anh sang/bo cuc/ty le; KHONG copy boi canh vi du; KHONG tu ta font):\n"
        + dna_full + "\n\n"
        + WORLD_RULE + "\n\n"
        "TIEU DE MOI: " + title + "\n\n"
        + (_breakdown_block(breakdown) + "\n" if breakdown else "")
        + "Tra ve JSON dung cau truc:\n"
        "{\n"
        '  "phan_tich_tieu_de": "tieu de dang noi ve van de/chu de gi",\n'
        '  "chu_the_chinh": "chu the cu the suy ra tu tieu de (kem ty le % va vi tri theo DNA)",\n'
        '  "boi_canh_de_xuat": "boi canh (tien/trung/hau canh) PHU HOP tieu de - khong copy DNA",\n'
        + hook_line +
        '  "thumbnail_prompt_en": "' + prompt_hint + '"\n'
        "}\n"
        "phan_tich_tieu_de, chu_the_chinh, boi_canh_de_xuat viet TIENG VIET CO DAU. "
        "text_tren_thumb viet bang NGON NGU CUA TIEU DE. "
        "thumbnail_prompt_en viet TIENG ANH."
    )
    result = llm.chat_json(system, user, temperature=0.6)
    approved_hook = str((breakdown or {}).get("hook") or "").strip()
    if co_chu and approved_hook:        # hook da duyet o buoc boc tach -> dung CHINH XAC
        result["text_tren_thumb"] = approved_hook
    elif co_chu and not _hook_matches_title_script(title, str(result.get("text_tren_thumb") or "")):
        result = llm.chat_json(system, user + _hook_lang_retry_note(title), temperature=0.6)

    # CHEN khoi chu KHOA CUNG y nguyen -> chu giong het moi lan (khong phu thuoc model che lai)
    p = result.get("thumbnail_prompt_en", "") or ""
    hook = (result.get("text_tren_thumb") or "").strip()
    if co_chu:
        p = p.replace("[[HOOK]]", hook)  # hook dung ngon ngu tieu de, do Python chen (khong de model tu dich)
        if "[[FONT]]" in p:
            p = p.replace("[[FONT]]", font_lock)
        else:
            p = (p + ' The title text "' + hook + '" ' + font_lock + ".") if hook else (p + " " + font_lock + ".")
    else:
        p = p.replace("[[FONT]]", "").strip()
    # CHEN khoi thiet ke nhan vat KHOA CUNG y nguyen -> nhan vat khong troi qua tung thumbnail
    if char_lock:
        p = p + " " + char_lock
    result["thumbnail_prompt_en"] = p
    result["khoa_chu_en"] = font_lock
    result["khoa_nhan_vat_en"] = char_lock
    return result


def decompose_title(title, thumbnail_dna=None):
    """
    Buoc BOC TACH tieu de (tieng Viet) de nguoi dung DOC va SUA truoc khi tao prompt.
    Tra ve {phan_tich_tieu_de, giai_thich, chu_the_chinh, boi_canh_de_xuat}.
    """
    import json
    hint = ""
    if thumbnail_dna:
        hint = ("Phong cach kenh (tham khao de chon LOAI chu the phu hop): "
                + json.dumps(thumbnail_dna, ensure_ascii=False)[:1500] + "\n\n")
    system = (
        "Ban la chuyen gia thiet ke thumbnail YouTube. Hay BOC TACH 1 tieu de video de chuan bi lam thumbnail. "
        "Muc tieu: xac dinh ro CHU THE hinh anh va BOI CANH xung quanh phu hop nhat voi tieu de, "
        "trinh bay de nguoi dung DOC va SUA duoc truoc khi tao prompt."
    )
    user = (
        hint +
        "TIEU DE: " + title + "\n\n"
        "Tra ve JSON, TAT CA cac truong viet bang TIENG VIET CO DAU:\n"
        "{\n"
        '  "phan_tich_tieu_de": "tieu de dang noi ve van de/chu de gi",\n'
        '  "giai_thich": "giai thich cach boc tach: dau la tu khoa/van de chinh, dau la yeu to gay to mo/cam xuc",\n'
        '  "chu_the_chinh": "chu the hinh anh nen la gi (cu the, hop tieu de) - se hien lon tren thumbnail",\n'
        '  "boi_canh_de_xuat": "boi canh xung quanh (tien/trung/hau canh) phu hop tieu de"\n'
        "}"
    )
    return llm.chat_json(system, user, temperature=0.5)


# Kien thuc bo cuc dien anh "vang" - nap vao he thong
CINE_COMPOSITION = (
    "KIEN THUC BO CUC DIEN ANH VANG (ap dung nghiem tuc):\n"
    "1. Quy tac 1/3 (rule of thirds): chia khung thanh luoi 3x3; dat chu the & duong chan troi doc theo "
    "cac duong 1/3; dat DIEM NHAN o giao diem 1/3 (power points), khong dat chinh giua tru khi co chu dich.\n"
    "2. Duong dan (leading lines): dung con duong/dong song/song nui/bo bien/hang rao... dan mat nguoi xem "
    "vao chu the chinh.\n"
    "3. Chieu sau 3 lop: foreground - midground - background ro rang de tao khong gian dien anh.\n"
    "4. Ti le vang / golden spiral: bo cuc cuon dan vao diem manh; can bang thi giac.\n"
    "5. Negative space: chua khoang trong thoang, sach o phia DOI DIEN chu the.\n"
    "6. Framing (khung trong khung), depth of field (xoa phong nhe lam noi chu the), headroom hop ly, "
    "anh sang tao khoi (rim light / god rays) chuan phim tai lieu dien anh."
)


def thumbnail_prompts_bancontent(title, thumbnail_dna, chu_the=None, boi_canh=None):
    """
    Ban Content: tu 1 tieu de + DNA -> 3 PHIEN BAN prompt (chu the lech TRAI / PHAI / GIUA)
    de con nguoi duyet. Chu the >70%, bo cuc dien anh vang, KHONG co chu (user tu them Photoshop).
    chu_the / boi_canh: neu nguoi dung da sua o buoc boc tach thi truyen vao de dung dung.
    """
    import json
    dna_full = json.dumps(thumbnail_dna, ensure_ascii=False, indent=2) if thumbnail_dna else "(chua co DNA)"
    char_lock = _character_lock_block(thumbnail_dna)
    override = ""
    if (chu_the and chu_the.strip()) or (boi_canh and boi_canh.strip()):
        override = "\nNGUOI DUNG DA CHINH SUA (BAT BUOC dung DUNG cai nay lam chu the/boi canh):\n"
        if chu_the and chu_the.strip():
            override += "- Chu the: " + chu_the.strip() + "\n"
        if boi_canh and boi_canh.strip():
            override += "- Boi canh: " + boi_canh.strip() + "\n"
    system = (
        "Ban la dao dien hinh anh / giam doc nghe thuat thumbnail YouTube trieu view. "
        "Ban co DNA phong cach cua 1 kenh va 1 TIEU DE moi.\n"
        "NGUYEN TAC: DNA la CONG THUC PHONG CACH BAT BIEN (phong cach anh, bang mau, anh sang, chieu sau, "
        "chat dien anh). CHU THE + BOI CANH cu the PHAI suy ra tu TIEU DE (KHONG copy boi canh vi du trong DNA).\n"
        + CINE_COMPOSITION + "\n"
        + CAST_ACTION_GRAMMAR + "\n"
        + ("THIET KE NHAN VAT (dau/toc/trang phuc) DA KHOA CUNG, se duoc chen tu dong vao cuoi moi prompt — "
           "KHONG mo ta lai dau/toc/trang phuc trong prompt_en, chi mo ta HANH DONG/TU THE/BIEU CAM.\n"
           if char_lock else "")
        + "YEU CAU DAC BIET:\n"
        "- Chu the chinh chiem ~70-80% khung hinh (chiem PHAN LON), du LON & TUONG PHAN cao de "
        "nhin RO chu the ngay ca khi thumbnail bi thu nho con 25%.\n"
        "- TUYET DOI KHONG co CHU / TEXT / chu cai / watermark / logo trong anh. Nguoi dung se TU THEM chu "
        "bang Photoshop, nen chi chua KHOANG TRONG SACH (clean negative space) o phia DOI DIEN chu the.\n"
        "- Tao DUNG 3 PHIEN BAN prompt khac nhau ve VI TRI chu the: TRAI (khoang trong ben phai), "
        "PHAI (khoang trong ben trai), GIUA (khoang trong phia tren hoac duoi). Ca 3 cung chu the & boi canh, "
        "chi khac vi tri & bo cuc de con nguoi chon.\n"
        "MUC TIEU CUOI CUNG: thumbnail + TIEU DE phai BO TRO NHAU thanh 1 CAP HOAN HAO tang ty le click (CTR). "
        "Hinh KHONG lap lai chu trong tieu de (hinh truyen cam xuc & chu the, tieu de giu hook/to mo). "
        "Sau khi ra 3 phuong an, hay TU SUY LUAN chon phuong an TOT NHAT dua tren: (a) cam xuc & hook cua tieu de; "
        "(b) chu viet se dat o phia DOI DIEN chu the - phuong an nao cho vung dat chu dep & tuong phan tot nhat; "
        "(c) bo cuc nao dan mat manh nhat: nhin HINH -> doc CHU -> CLICK."
    )
    user = (
        "DNA PHONG CACH (CHI lay STYLE, KHONG copy boi canh vi du):\n" + dna_full + "\n\n"
        "TIEU DE MOI: " + title + "\n" + override + "\n"
        "Tra ve JSON dung cau truc:\n"
        "{\n"
        '  "phan_tich_tieu_de": "tieu de noi ve van de/chu de gi",\n'
        '  "chu_the_chinh": "chu the cu the suy ra tu tieu de (~70-80% khung)",\n'
        '  "boi_canh_de_xuat": "boi canh (tien/trung/hau canh) phu hop tieu de",\n'
        '  "prompts": [\n'
        '    {"vi_tri": "Trái", "prompt_en": "chu the ~65% lech TRAI theo quy tac 1/3, leading lines, chieu sau 3 lop, khoang trong PHAI"},\n'
        '    {"vi_tri": "Phải", "prompt_en": "chu the ~65% lech PHAI, khoang trong TRAI"},\n'
        '    {"vi_tri": "Giữa", "prompt_en": "chu the ~65% O GIUA, can doi, khoang trong tren/duoi"}\n'
        "  ],\n"
        '  "de_xuat_tot_nhat": {"vi_tri": "Trái|Phải|Giữa", "ly_do": "vi sao phuong an nay bo tro tieu de tot nhat de tang CTR"}\n'
        "}\n"
        "phan_tich_tieu_de, chu_the_chinh, boi_canh_de_xuat, de_xuat_tot_nhat.ly_do viet TIENG VIET CO DAU. "
        "Cac prompt_en viet TIENG ANH, bam bang mau/anh sang/chat dien anh cua DNA, "
        "va MOI prompt PHAI ket thuc bang cum: 'no text, no letters, no watermark, clean negative space'."
    )
    result = llm.chat_json(system, user, temperature=0.75)
    # CHEN khoi thiet ke nhan vat KHOA CUNG y nguyen vao CA 3 phuong an -> nhan vat dong nhat du chon vi tri nao
    if char_lock and isinstance(result.get("prompts"), list):
        for item in result["prompts"]:
            if isinstance(item, dict) and item.get("prompt_en"):
                item["prompt_en"] = item["prompt_en"] + " " + char_lock
    result["khoa_nhan_vat_en"] = char_lock
    return result
