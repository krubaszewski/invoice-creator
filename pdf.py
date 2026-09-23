from __future__ import annotations

import math
from fpdf import FPDF
from models import (
    FONT_DIR, CITY,
    BANK_NAME, ACCOUNT_PLN, ACCOUNT_EUR,
    SERVICE_NAME, UNIT_NAME,
    INVOICE_FOOTER_NUM, INVOICE_FOOTER_SHIP,
    Z_PERSON,
    Z_TRUCK, Z_TRAILER, Z_DRIVER, Z_DRIVER_PHONE, Z_CARRIAGE, Z_ID_DOC,
    Z_LOAD_DATE, Z_LOAD_COMPANY, Z_LOAD_ADDR, Z_LOAD_GOODS, Z_LOAD_PALLET, Z_LOAD_ADR,
    Z_UNLOAD_DATE, Z_UNLOAD_COMPANY, Z_UNLOAD_ADDR, Z_UNLOAD_GOODS, Z_UNLOAD_PALLET, Z_UNLOAD_ADR,
    Z_ADDRESS_CORRESP, Z_PAYMENT_TERM_TEXT, Z_FREIGHT,
    fmt_pln, invoice_currency, generate_random_id, ksef_invoice_number
)

FONT = "DejaVu"

def _new_pdf() -> FPDF:
    pdf = FPDF(unit="pt", format="A4")
    pdf.add_font(FONT, "", str(FONT_DIR / "DejaVuSans.ttf"))
    pdf.add_font(FONT, "B", str(FONT_DIR / "DejaVuSans-Bold.ttf"))
    pdf.set_auto_page_break(auto=False)
    return pdf


def _text(pdf, x, y, txt, style="", size=10, align="L"):
    pdf.set_xy(x, y)
    pdf.set_font(FONT, style, size)
    pdf.cell(0, 0, str(txt), align=align)


def _text_wrapped(pdf, x, y, txt, style="", size=10, threshold=40):
    pdf.set_font(FONT, style, size)
    lines = max(1, math.ceil(len(txt) / threshold))
    line_height = size * 1.5
    for i, line in enumerate([txt[j:j + threshold] for j in range(0, len(txt), threshold)]):
        pdf.set_xy(x, y + i * line_height)
        pdf.cell(0, 0, str(line))
    return y + (lines - 1) * line_height


# ── Adjusted Table Grid ──
COLS = [
    ("Lp", 30, 20, "C"),
    ("Nazwa wyrobu, usługi", 50, 100, "L"),
    ("Jm", 150, 40, "C"),
    ("Ilość", 190, 30, "C"),                 
    ("Cena netto", 220, 75, "R"),            
    ("Wartość netto", 295, 75, "R"),
    ("VAT %", 370, 40, "C"),
    ("VAT", 410, 65, "R"),                   
    ("Wartość brutto", 475, 90, "R"),
]


def generate_invoice(data, path: str) -> str:
    pdf = _new_pdf()
    pdf.alias_nb_pages()
    pdf.add_page()
    d = data.date
    ksef_date = ksef_invoice_number(d)
    number = data.number
    random_ksef_id = generate_random_id()
    ksef_number = f"{data.seller_nip_stripped}-{ksef_date}-{random_ksef_id}"
    deadline = data.deadline
    currency = data.currency

    # Top Right Date
    pdf.set_xy(30, 40)
    pdf.set_font(FONT, "", 10)
    pdf.cell(535, 10, f"{CITY}, {data.date_iso}", align="R")

    # Titles (moved lower)
    _text(pdf, 30, 75, "FAKTURA TESTOWA", style="", size=22)
    
    # Centered Invoice Number
    _text(pdf, 0, 100, f"FAKTURA VAT NR: {number}", style="B", size=14, align="C")
    _text(pdf, 0, 116, f"Numer KSEF: {ksef_number}", size=10, align="C")

    # Sprzedawca / Nabywca Table
    pdf.rect(30, 125, 267.5, 15)
    pdf.rect(297.5, 125, 267.5, 15)
    seller_lines = max(1, math.ceil(len(data.seller_name) / 40))
    buyer_lines = max(1, math.ceil(len(data.buyer_name) / 40))
    seller_box_h = max(50, seller_lines * 13.5 + 14 + 12 + 12)
    buyer_box_h = max(50, buyer_lines * 13.5 + 14 + 12 + 12)
    box_top = 140

    pdf.rect(30, box_top, 267.5, seller_box_h)
    pdf.rect(297.5, box_top, 267.5, buyer_box_h)

    _text(pdf, 35, 135, "Sprzedawca:", style="B", size=9)
    _text(pdf, 302.5, 135, "Nabywca:", style="B", size=9)

    seller_name_y = _text_wrapped(pdf, 35, 152, data.seller_name, style="B", size=9, threshold=40)
    _text(pdf, 35, seller_name_y + 14, f"Adres: {data.seller_address}, {data.seller_postal}", size=8.5)
    _text(pdf, 35, seller_name_y + 28, f"NIP: {data.seller_nip}", size=8.5)

    buyer_name_y = _text_wrapped(pdf, 302.5, 152, data.buyer_name, style="B", size=9, threshold=40)
    _text(pdf, 302.5, buyer_name_y + 14, f"Adres: {data.buyer_address}, {data.buyer_postal}", size=8.5)
    _text(pdf, 302.5, buyer_name_y + 28, f"NIP: {data.buyer_nip}", size=8.5)

    # Content starts below the tallest name block
    content_y = max(seller_name_y, buyer_name_y) + 28 + 20

    # Detail rows
    _detail(pdf, content_y, "Data dostawy towaru / wykonania usługi:", data.date_iso)
    _detail(pdf, content_y + 15, "Termin płatności:", deadline.isoformat())
    _detail(pdf, content_y + 30, "Sposób zapłaty:", f"Przelew {data.days} dni")
    _detail(pdf, content_y + 45, "Nazwa banku:", BANK_NAME)
    _detail(pdf, content_y + 60, "Numer rachunku PLN:", ACCOUNT_PLN)
    _detail(pdf, content_y + 75, "Numer rachunku EUR:", ACCOUNT_EUR)

    # Main Items Table
    table_y = content_y + 100
    row_h = 18

    # Header Row
    pdf.set_font(FONT, "B", 8)
    for label, x, w, align in COLS:
        pdf.rect(x, table_y, w, row_h)
        pdf.set_xy(x, table_y)
        if label == "VAT":
            pdf.cell(w, row_h, invoice_currency(label, currency), align=align)
        else: 
            pdf.cell(w, row_h, label, align=align)
        
    # Data Row
    data_y = table_y + row_h
    pdf.set_font(FONT, "", 9)
    cells = [
        ("1", COLS[0][1], COLS[0][2], "C"),
        (SERVICE_NAME, COLS[1][1], COLS[1][2], "L"),
        (UNIT_NAME, COLS[2][1], COLS[2][2], "C"),
        ("1", COLS[3][1], COLS[3][2], "C"),
        (fmt_pln(data.netto), COLS[4][1], COLS[4][2], "R"),
        (fmt_pln(data.netto), COLS[5][1], COLS[5][2], "R"),
        ("23", COLS[6][1], COLS[6][2], "C"),
        (fmt_pln(data.vat), COLS[7][1], COLS[7][2], "R"),
        (fmt_pln(data.brutto), COLS[8][1], COLS[8][2], "R"),
    ]

    for text, x, w, align in cells:
        pdf.rect(x, data_y, w, row_h)
        pdf.set_xy(x + (2 if align == "L" else 0), data_y) 
        pdf.cell(w - (4 if align in ["L", "R"] else 0), row_h, str(text), align=align)

    # ── Updated Summary Row (Aligned with new columns) ──
    summary_y = data_y + row_h
    
    # Text "Razem:"
    pdf.rect(220, summary_y, 75, row_h)
    pdf.set_xy(220, summary_y)
    pdf.set_font(FONT, "B", 9)
    pdf.cell(71, row_h, "Razem:", align="R")

    # Netto Total
    pdf.rect(295, summary_y, 75, row_h)
    pdf.set_xy(295, summary_y)
    pdf.cell(71, row_h, fmt_pln(data.netto), align="R")

    # VAT % (Empty box for structural continuity)
    pdf.rect(370, summary_y, 40, row_h)

    # VAT Total
    pdf.rect(410, summary_y, 65, row_h)
    pdf.set_xy(410, summary_y)
    pdf.cell(61, row_h, fmt_pln(data.vat), align="R")

    # Brutto Total
    pdf.rect(475, summary_y, 90, row_h)
    pdf.set_xy(475, summary_y)
    pdf.cell(86, row_h, fmt_pln(data.brutto), align="R")

    # Footer Info
    footer_y = summary_y + 35
    pdf.set_font(FONT, "", 8.5)
    pdf.set_xy(30, footer_y)
    pdf.multi_cell(535, 11, f"{INVOICE_FOOTER_NUM} ZL_{number}")
    pdf.set_xy(30, pdf.y + 2)
    pdf.multi_cell(535, 11, INVOICE_FOOTER_SHIP)

    # "Do zapłaty" block
    do_y = pdf.y + 25
    _text(pdf, 30, do_y, "Do zapłaty:", style="B", size=11)
    _text(pdf, 30, do_y + 16, f"{fmt_pln(data.brutto)} {currency}", style="B", size=11)

    pdf.output(path)
    return path


def _detail(pdf, y, label, value):
    _text(pdf, 30, y, label, size=9.5)
    _text(pdf, 260, y, value, size=9.5)

# ── ZLECENIE (transport order) ────────────────────────────────────

def generate_order(data, path: str) -> str:
    pdf = _new_pdf()
    pdf.alias_nb_pages()
    pdf.add_page()
    d = data.date
    number = data.number

    # City and Date
    pdf.set_xy(30, 30)
    pdf.set_font(FONT, "", 10)
    pdf.cell(535, 10, f"{CITY}, {data.date_dmy}", align="R")

    # "Odbiorca / Sprzedawca" 4-Row Table
    x_left = 30
    x_right = 297.5
    w_box = 267.5

    # Row 1 (Titles)
    pdf.rect(x_left, 50, w_box, 15)
    pdf.rect(x_right, 50, w_box, 15)
    _text(pdf, x_left + 5, 59, "Odbiorca", style="B", size=9)
    _text(pdf, x_right + 5, 59, "Sprzedawca", style="B", size=9)

    # Row 2 (Company Details)
    seller_lines = max(1, math.ceil(len(data.order_seller_name) / 45))
    buyer_lines = max(1, math.ceil(len(data.order_buyer_name) / 45))
    seller_box_h = max(45, seller_lines * 12 + 14 + 12 + 10)
    buyer_box_h = max(45, buyer_lines * 12 + 14 + 12 + 10)
    row2_top = 65
    row3_top = row2_top + seller_box_h + 5  # gap between boxes and row 3

    pdf.rect(x_left, row2_top, w_box, seller_box_h)
    pdf.rect(x_right, row2_top, w_box, buyer_box_h)

    seller_name_y = _text_wrapped(pdf, x_left + 5, 75, data.order_seller_name, style="B", size=8, threshold=45)
    _text(pdf, x_left + 5, seller_name_y + 12, f"{data.seller_address}, {data.order_seller_postal}", size=8)
    _text(pdf, x_left + 5, seller_name_y + 24, f"NIP: {data.seller_nip_stripped}", size=8)
    _text(pdf, x_left + 120, seller_name_y + 24, f"VAT Eu: {data.seller_nip}", size=8)

    buyer_name_y = _text_wrapped(pdf, x_right + 5, 75, data.order_buyer_name, style="B", size=8, threshold=45)
    _text(pdf, x_right + 5, buyer_name_y + 12, f"{data.buyer_address}, {data.order_buyer_postal}", size=8)
    _text(pdf, x_right + 5, buyer_name_y + 24, f"NIP: {data.buyer_nip_stripped}", size=8)
    _text(pdf, x_right + 120, buyer_name_y + 24, f"VAT Eu: {data.buyer_nip}", size=8)

    # Row 3 (Employee Name)
    pdf.rect(x_left, row3_top, w_box, 15)
    pdf.rect(x_right, row3_top, w_box, 15)
    _text(pdf, x_left + 5, row3_top + 9, Z_PERSON, style="B", size=8)

    # Row 4 (Contact Info)
    row4_top = row3_top + 15
    pdf.rect(x_left, row4_top, w_box, 45)
    pdf.rect(x_right, row4_top, w_box, 45)

    labels = ["Telefon:", "Telefon komórkowy:", "Fax:", "E-mail:"]
    for i, lbl in enumerate(labels):
        _text(pdf, x_left + 5, row4_top + 10 + (i * 10), lbl, size=8)
        _text(pdf, x_right + 5, row4_top + 10 + (i * 10), lbl, size=8)

    # Content below the contact info boxes
    order_content_y = row4_top + 45 + 20

    # Centered Order Number
    _text(pdf, 0, order_content_y, "Zlecenie transportowe numer:", style="B", size=13, align="C")
    _text(pdf, 0, order_content_y + 15, f"ZL_{number}", style="B", size=13, align="C")

    # Route Header
    _text(pdf, 30, order_content_y + 32, "dane dotyczące trasy (załadunki, rozładunki):", size=8)

    # Załadunek / Rozładunek Tables
    _draw_point(pdf, order_content_y + 50, "Załadunek 1", Z_LOAD_DATE, Z_LOAD_COMPANY, Z_LOAD_ADDR, Z_LOAD_GOODS, Z_LOAD_PALLET, Z_LOAD_ADR)
    _draw_point(pdf, order_content_y + 50 + 98 + 2, "Rozładunek 1", Z_UNLOAD_DATE, Z_UNLOAD_COMPANY, Z_UNLOAD_ADDR, Z_UNLOAD_GOODS, Z_UNLOAD_PALLET, Z_UNLOAD_ADR)

    # Driver & Truck Info
    y_info = order_content_y + 50 + 98 + 2 + 98 + 20
    _text(pdf, 30, y_info, "Ciągnik:", style="B", size=8)
    _text(pdf, 110, y_info, Z_TRUCK, size=8)
    
    _text(pdf, 270, y_info, "Kierowca:", style="B", size=8)
    _text(pdf, 370, y_info, Z_DRIVER, size=8)

    _text(pdf, 30, y_info + 15, "Naczepa:", style="B", size=8)
    _text(pdf, 110, y_info + 15, Z_TRAILER, size=8)
    
    _text(pdf, 270, y_info + 15, "Nr telefonu:", style="B", size=8)
    _text(pdf, 370, y_info + 15, Z_DRIVER_PHONE, size=8)

    _text(pdf, 30, y_info + 30, "Typ:", style="B", size=8)
    _text(pdf, 110, y_info + 30, Z_CARRIAGE, size=8)
    
    _text(pdf, 270, y_info + 30, "Nr dok. tożsamości:", style="B", size=8)
    _text(pdf, 370, y_info + 30, Z_ID_DOC, size=8)

    # Payment & Freight
    y_pay = order_content_y + 50 + 98 + 2 + 98 + 20 + 60
    _text(pdf, 30, y_pay, "Termin płatności:", style="B", size=9)
    _text(pdf, 120, y_pay, Z_PAYMENT_TERM_TEXT, size=9)
    _text(pdf, 380, y_pay, "Fracht (netto):", style="B", size=10)
    _text(pdf, 465, y_pay, Z_FREIGHT, size=10)

    # Bottom Address & Terms
    y_cor = order_content_y + 50 + 98 + 2 + 98 + 20 + 60 + 35
    _text(pdf, 30, y_cor, "ADRES DO KORESPONDENCJI:", style="B", size=10)
    _text(pdf, 30, y_cor + 15, Z_ADDRESS_CORRESP, size=10)

    y_war = order_content_y + 50 + 98 + 2 + 98 + 20 + 60 + 35 + 30
    _text(pdf, 30, y_war, "WARUNKI PŁATNOŚCI", style="B", size=11)
    _text(pdf, 30, y_war + 15, "Kwota netto płatna w PLN według kursu średniego ogłoszonego przez NBP z dnia załadunku.", size=9)

    pdf.output(path)
    return path


def _draw_point(pdf, y, title, date, company, addr, goods, pallet, adr):
    # Row 1: Title and Date
    pdf.rect(30, y, 535, 18)
    _text(pdf, 35, y + 12, title, style="B", size=10)
    _text(pdf, 150, y + 12, date, style="B", size=10)

    # Row 2: Content Details
    h = 80 
    pdf.rect(30, y + 18, 535, h)
    dy = y + 18
    
    # Texts shifted up inside the box
    _text(pdf, 35, dy + 14, company, style="B", size=9)
    _text(pdf, 35, dy + 27, addr, size=8)
    _text(pdf, 35, dy + 41, "Numer referencyjny:", style="B", size=8)
    
    # Indented fields
    _text(pdf, 60, dy + 54, f"Ładunek: {goods} (Wymiana - Miejsce paletowe: NIE)", size=8)
    _text(pdf, 60, dy + 67, f"Ilość: {pallet}", size=8)
    
    # Right-aligned fields
    _text(pdf, 380, dy + 67, "4 400,0 [kg]", size=8)
    _text(pdf, 470, dy + 54, f"ADR: {adr}", size=8)