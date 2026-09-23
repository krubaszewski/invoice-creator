from __future__ import annotations

import sys
import random
import re
import string
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

CITY = "Wrocław"

SELLER_NAME = "TEST PANELU TCK"
SELLER_ADDRESS = "ul. Racławicka 4"
SELLER_POSTAL = "50-540"
SELLER_NIP = "PL1233254123"

BUYER_NAME = "KKT PAULINA BILSKA-MAREK"
BUYER_ADDRESS = "ul. Geodezyjna 21"
BUYER_POSTAL = "51-180"
BUYER_NIP = "PL8981919102"

BANK_NAME = "ING Bank Śląski"
ACCOUNT_PLN = "46249083316355081367879111"
ACCOUNT_EUR = "14109000047954000000046296"

SERVICE_NAME = "Usługa transportowa"
UNIT_NAME = "Fracht"

INVOICE_FOOTER_NUM = "Nasz numer: ZK 00432/07/2024 Zlecenie: 043188PIŃCZÓW/S/2024"
INVOICE_FOOTER_SHIP = "Załadunek: FR 62330 Isbergues(2024-07-30)  Rozładunek: PL 41-103 Siemianowice Śląskie(2024-08-05)"

# ZLECENIE
Z_RECIPIENT = "TC SOFT"
Z_RECIPIENT_ADDR = "PL50540 Wrocław"
Z_SENDER = "KKT PAULINA BILSKA-MAREK"
Z_SENDER_ADDR = "PL51180 Wrocław"
Z_PERSON = "Test Testerowy"

Z_TRUCK = "SB2224L"
Z_TRAILER = "SB4014P"
Z_DRIVER = "Janusz Zarazik"
Z_DRIVER_PHONE = "669-399-349"
Z_CARRIAGE = "Plandeka"
Z_ID_DOC = "ATM 670198"

Z_LOAD_DATE = "27.11.2019"
Z_LOAD_COMPANY = "ZBYSZKO Bojanowicz Sp. z o.o."
Z_LOAD_ADDR = "ul. Kościelna 85 A, PL26800 Białobrzegi"
Z_LOAD_GOODS = "7 miejsc paletowych 120x100x255"
Z_LOAD_PALLET = "7 x Miejsce paletowe"
Z_LOAD_ADR = "Nie"

Z_UNLOAD_DATE = "28.11.2019"
Z_UNLOAD_COMPANY = "Plastipak"
Z_UNLOAD_ADDR = "ul. Turyńska 80, PL43100 Tychy"
Z_UNLOAD_GOODS = "7 miejsc paletowych 120x100x255"
Z_UNLOAD_PALLET = "7 x Miejsce paletowe"
Z_UNLOAD_ADR = "Nie"

Z_ADDRESS_CORRESP = '"SAFE WAY TRANSPORT" UL. KS.SYCZEWSKIEGO 8 LOKAL 311, 15-139 BIAŁYSTOK'
Z_PAYMENT_TERM_TEXT = "45 dni od otrzymania faktury i dokumentów"
Z_FREIGHT = "2,00 PLN"

# configurable options
PAYMENT_TERMS = {
    "7 dni": 7,
    "14 dni": 14,
    "30 dni": 30,
    "45 dni": 45,
    "60 dni": 60,
    "90 dni": 90,
}

def _app_dir() -> Path:
    if getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent

INVOICE_TYPES = ["MIKRO", "WINDYKACJA", "POZYCZKA"]
CURRENCIES = ["PLN", "EUR", "RON"]

SETTINGS_DIR = Path.home() / ".invoice_creator"
SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = SETTINGS_DIR / ".last_folder"
DEFAULT_PARTNERS_FILE = SETTINGS_DIR / ".default_partners"

FONT_DIR = _app_dir() / "resources" / "fonts"
PROJECT_DIR = _app_dir()

def calc_vat(gross: Decimal) -> tuple[Decimal, Decimal, Decimal]:
    """Return (netto, vat, brutto) for a gross amount, 23 % VAT."""
    netto = (gross / Decimal("1.23")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    vat = (gross - netto).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return netto, vat, gross


def fmt_pln(value: Decimal) -> str:
    """Polish number formatting: space thousands, comma decimals."""
    s = format(value, ".2f")
    int_part, dec_part = s.split(".")
    int_part = int_part[::-1]
    chunks = [int_part[i : i + 3] for i in range(0, len(int_part), 3)]
    int_part = " ".join(chunks)[::-1]
    return f"{int_part},{dec_part}"


def invoice_number(d: date, combotype: str, seq: str = "") -> str:
    base = f"{d.day:02d}_{d.month:02d}_{d.year % 100:02d}"
    if seq:
        base = f"{base}_{seq}"
    return f"{base}_{combotype}"


def invoice_filename(d: date, combotype: str, seq: str = "") -> str:
    base = f"{d.day:02d}{d.month:02d}{d.year}"
    if seq:
        base = f"{base}_{seq}"
    return f"{base}_{combotype}"


def payment_deadline(d: date, days: int) -> date:
    return d + timedelta(days=days)


def parse_days(label: str) -> int:
    """Extract days from a label like 'Przelej 30 dni'."""
    return int(label.split()[0])

def invoice_currency(vatLabel: str, currency: str) -> str:
    """Return the vabel like 'VAT PLN' or 'VAT EUR' based on the currency."""
    return f"{vatLabel} {currency}"

def generate_random_id():
    part1_chars = string.ascii_uppercase + string.digits
    part1 = ''.join(random.choices(part1_chars, k=12))

    part2 = ''.join(random.choices(string.digits, k=2))
    
    return f"{part1}-{part2}"

def ksef_invoice_number(d: date) -> str:
    return f"{d.year:04d}{d.month:02d}{d.day:02d}"


def strip_country_code(nip: str) -> str:
    """Strip a leading 2-3 letter country code (e.g. 'PL', 'DE') from a NIP/VAT number."""
    nip = (nip or "").strip()
    return re.sub(r"^[A-Za-z]{2,3}(?=\d)", "", nip)


@dataclass
class InvoiceData:
    date: date
    combotype: str
    days: int
    currency: str
    gross: Decimal
    seller_name: str = SELLER_NAME
    seller_address: str = SELLER_ADDRESS
    seller_postal: str = SELLER_POSTAL
    seller_nip: str = SELLER_NIP
    buyer_name: str = BUYER_NAME
    buyer_address: str = BUYER_ADDRESS
    buyer_postal: str = BUYER_POSTAL
    buyer_nip: str = BUYER_NIP
    order_seller_name: str = Z_RECIPIENT
    order_seller_postal: str = Z_RECIPIENT_ADDR
    order_buyer_name: str = Z_SENDER
    order_buyer_postal: str = Z_SENDER_ADDR
    netto: Decimal = None
    vat: Decimal = None
    brutto: Decimal = None
    created_at: datetime = field(default_factory=datetime.now)


    def __post_init__(self) -> None:
        n, v, b = calc_vat(self.gross)
        self.netto = n
        self.vat = v
        self.brutto = b

    @property
    def seller_nip_stripped(self) -> str:
        return strip_country_code(self.seller_nip)

    @property
    def buyer_nip_stripped(self) -> str:
        return strip_country_code(self.buyer_nip)

    @property
    def sequence(self) -> str:
        """Creation-time-based suffix (HHMMSS) so multiple invoices generated
        on the same day can still be distinguished and ordered."""
        return self.created_at.strftime("%H%M%S")

    @property
    def number(self) -> str:
        return invoice_number(self.date, self.combotype, self.sequence)

    @property
    def filename(self) -> str:
        return invoice_filename(self.date, self.combotype, self.sequence)

    @property
    def deadline(self) -> date:
        return payment_deadline(self.date, self.days)

    @property
    def date_iso(self) -> str:
        return self.date.isoformat()

    @property
    def date_dmy(self) -> str:
        return f"{self.date.day:02d}.{self.date.month:02d}.{self.date.year}"