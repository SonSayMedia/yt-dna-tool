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
        '  "khoa_bo_cuc_en": "1 doan TIENG ANH mo ta BO CUC CO DINH lap lai cua kenh (ty le %, vi tri chu the, mau nen, khung/vien, vi tri & do lon banner chu) de tai tao MOI thumbnail GIONG BO CUC nay. Phan CO DINH (mau, bo cuc, ty le, khung) ghi CU THE. Phan THAY DOI theo tung video thi de PLACEHOLDER trong ngoac vuong kep: [[SUBJECT]]=chu the chinh, [[EMOTION]]=bieu cam neu co mat nguoi, [[SYMBOL]]=bieu tuong dai dien noi dung neu co, [[HOOK]]=cum chu tren thumb, [[FONT]]=kieu chu (de NGUYEN chu [[FONT]]). BAT BUOC co [[HOOK]] va [[FONT]] neu kenh co chu, va it nhat 1 placeholder chu the ([[SUBJECT]]). Chi dung placeholder cho phan THAT SU doi. Vd: \'Flat editorial illustration, 16:9, deep navy background, olive-green borders; on the LEFT a glowing pale-blue [[SYMBOL]] with a tiny lone silhouette; on the RIGHT a close-up of [[SUBJECT]] filling ~55% width, terracotta-red skin, an expression of [[EMOTION]]; a solid black top banner with the text \\"[[HOOK]]\\" [[FONT]]\'.",\n'
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
            "Kenh nay THUONG CO chi tiet phu de anh khong bi don dieu/trong trai: " + "; ".join(bc_bits) + ". "
            "Neu hop ly voi tieu de, hay THEM 1-2 chi tiet phu (nhan vat phu/dong vat/dam lua/vat dung...) "
            "vao noi dung mo ta cac o co san (KHONG tao them o moi, KHONG doi bo cuc/ty le/mau/font/thiet ke "
            "nhan vat chinh da khoa) de bo cuc co chieu sau, tranh chi co 1 nhan vat trong khung trong."
        )
    if not parts:
        return ""
    return "\n".join(parts)


def _prompt_locked_composition(title, comp_lock, font_lock, char_lock="", richness_hint=""):
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
    slot_lines = "\n".join(
        '  "%s": "gia tri TIENG ANH, hop tieu de%s",' % (
            s, " - cum 2-4 tu IN HOA, BO TRO tieu de (tao khoang trong to mo RIENG), "
               "TUYET DOI KHONG lap lai nguyen tu/cum tu da co san trong tieu de"
            if s.upper() == "HOOK"
            else " - MO TA CU THE, khong dung tinh tu chung chung" if s.upper() == "EMOTION"
            else "")
        for s in slots)
    system = (
        "Ban la giam doc nghe thuat thumbnail YouTube trieu view. "
        "BO CUC, TY LE, MAU va FONT da KHOA CUNG (khong duoc doi). Viec cua ban: doc TIEU DE "
        "roi dien cac O TRONG sao cho HOP tieu de, hut click, dung tam ly nguoi xem. "
        "Bieu tuong/chu the/bieu cam PHAI BIEN THIEN RO RET theo TUNG tieu de (KHONG dung mac dinh "
        "cung 1 kieu chu the/hanh dong cho moi bai, du template bo cuc giong nhau).\n"
        "NGUYEN TAC BO TRO (1+1=3): thumbnail va TIEU DE la 1 CAP, khong phai 1 ban sao cua nhau. "
        "Hinh anh (chu the/bieu tuong/hanh dong) TRUYEN CAM XUC va goi mo 1 GOC RIENG cua tieu de "
        "(vd chi tiet gay to mo, hau qua chua noi, phan ung cua nhan vat), tieu de van giu vai tro cung "
        "cap boi canh/tu khoa chinh. TUYET DOI KHONG ve lai dung nghia den cua tieu de va KHONG de HOOK "
        "nhac lai nguyen van chu trong tieu de — muc tieu la nguoi xem doc tieu de + nhin hinh se TO MO "
        "HON la chi doc rieng tieu de.\n"
        + CAST_ACTION_GRAMMAR
        + ("\nTHIET KE NHAN VAT (dau/toc/trang phuc) DA KHOA CUNG, se duoc chen tu dong vao cuoi prompt — "
           "KHONG mo ta lai dau/toc/trang phuc trong cac o trong, chi dien HANH DONG/TU THE/BIEU CAM cua "
           "nhan vat do sao cho hop tieu de.\n" if char_lock else "")
        + ("\n" + richness_hint + "\n" if richness_hint else "")
    )
    user = (
        "TIEU DE: " + title + "\n\n"
        "TEMPLATE BO CUC (chi de tham chieu, KHONG sua):\n" + comp_lock + "\n\n"
        "Dien cac o trong. Tra ve JSON dung cau truc:\n{\n" + slot_lines + "\n"
        '  "phan_tich_tieu_de": "tieu de noi ve gi (TIENG VIET)",\n'
        '  "chu_the_chinh": "chu the + bieu tuong (TIENG VIET)",\n'
        '  "boi_canh_de_xuat": "y nghia hinh anh theo tieu de (TIENG VIET)"\n'
        "}\n"
        "Cac o trong viet TIENG ANH; 3 field cuoi viet TIENG VIET CO DAU."
    )
    r = llm.chat_json(system, user, temperature=0.6)
    p = comp_lock
    hook = ""
    for s in slots:
        val = str(r.get(s) or "").strip()
        if s.upper() == "HOOK":
            hook = val
        p = p.replace("[[" + s + "]]", val or s.lower().replace("_", " "))
    p = p.replace("[[FONT]]", font_lock or "")
    if char_lock:
        p = p + " " + char_lock
    return {
        "phan_tich_tieu_de": r.get("phan_tich_tieu_de", ""),
        "chu_the_chinh": r.get("chu_the_chinh", ""),
        "boi_canh_de_xuat": r.get("boi_canh_de_xuat", ""),
        "text_tren_thumb": hook,
        "thumbnail_prompt_en": p,
        "khoa_chu_en": font_lock,
        "khoa_nhan_vat_en": char_lock,
        "khoa_bo_cuc": True,
    }


def thumbnail_prompt_from_dna(title, thumbnail_dna):
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
        return _prompt_locked_composition(title, comp_lock, font_lock, char_lock, richness_hint)
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
        "(hut click, dung tam ly nguoi xem, hop chu de) -> viet 1 CUM HOOK 2-4 tu IN HOA sac ben, "
        "bo tro (khong lap y het) tieu de.\n"
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
    hook_line = ('  "text_tren_thumb": "cum HOOK 2-4 tu IN HOA suy ra tu tieu de",\n'
                 if co_chu else '  "text_tren_thumb": "",\n')
    prompt_hint = (
        'prompt TIENG ANH: chu the + boi canh (theo tieu de) + bang mau/anh sang/bo cuc/ty le %/vi tri theo DNA. '
        'Cho chu: viet chinh xac the title text \\"<HOOK>\\" [[FONT]] (GIU NGUYEN chuoi [[FONT]], KHONG tu ta font).'
        if co_chu else
        'prompt TIENG ANH: chu the + boi canh (theo tieu de) + bang mau/anh sang/bo cuc/ty le %/vi tri theo DNA. '
        'Chua khoang trong sach cho chu, KHONG them chu.'
    )
    user = (
        "DNA PHONG CACH (CHI lay STYLE mau/anh sang/bo cuc/ty le; KHONG copy boi canh vi du; KHONG tu ta font):\n"
        + dna_full + "\n\n"
        "TIEU DE MOI: " + title + "\n\n"
        "Tra ve JSON dung cau truc:\n"
        "{\n"
        '  "phan_tich_tieu_de": "tieu de dang noi ve van de/chu de gi",\n'
        '  "chu_the_chinh": "chu the cu the suy ra tu tieu de (kem ty le % va vi tri theo DNA)",\n'
        '  "boi_canh_de_xuat": "boi canh (tien/trung/hau canh) PHU HOP tieu de - khong copy DNA",\n'
        + hook_line +
        '  "thumbnail_prompt_en": "' + prompt_hint + '"\n'
        "}\n"
        "phan_tich_tieu_de, chu_the_chinh, boi_canh_de_xuat, text_tren_thumb viet TIENG VIET CO DAU. "
        "thumbnail_prompt_en viet TIENG ANH."
    )
    result = llm.chat_json(system, user, temperature=0.6)

    # CHEN khoi chu KHOA CUNG y nguyen -> chu giong het moi lan (khong phu thuoc model che lai)
    p = result.get("thumbnail_prompt_en", "") or ""
    if co_chu:
        if "[[FONT]]" in p:
            p = p.replace("[[FONT]]", font_lock)
        else:
            hook = (result.get("text_tren_thumb") or "").strip()
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
