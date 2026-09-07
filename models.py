from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

CITY = "Wrocław"

SELLER_NAME = "TEST PANELU TCK"
SELLER_ADDRESS = "ul. Racławicka 4"
SELLER_POSTAL = "50-540 Wrocław"
SELLER_NIP = ""

BUYER_NAME = "KKT PAULINA BILSKA-MAREK"
BUYER_ADDRESS = "ul. Geodezyjna 21"
BUYER_POSTAL = "51-180 Wrocław"
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
Z_RECIPIENT_ADDR = "ul. Racławicka 4, PL50540 Wrocław, PL"
Z_SENDER = "KKT PAULINA BILSKA-MAREK"
Z_SENDER_ADDR = "ul. Geodezyjna 21, PL51180 Wrocław"
Z_PERSON = "Test Testerowy"

Z_TRUCK = "SB2224L"
Z_TRAILER = "SB4014P"
Z_DRIVER = "Janusz Zarazik"
Z_DRIVER_PHONE = "669-399-349"
Z_CARRIAGE = "Plandeka"
Z_ID_DOC = "ATM 670198"

Z_LOAD_DATE = "27.11.2019"
Z_LOAD_COMPANY = "ZBYSZKO Bojanowicz Sp. z o.o."
Z_LOAD_ADDR = "ul. Kościelna 85 A, PL26800 Białobrzegi, PL"
Z_LOAD_GOODS = "7 miejsc paletowych 120x100x255"
Z_LOAD_PALLET = "7 x Miejsce paletowe"
Z_LOAD_ADR = "Nie"

Z_UNLOAD_DATE = "28.11.2019"
Z_UNLOAD_COMPANY = "Plastipak"
Z_UNLOAD_ADDR = "ul. Turyńska 80, PL43100 Tychy, PL"
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


def invoice_number(d: date, combotype: str) -> str:
    return f"{d.day:02d}_{d.month:02d}_{d.year % 100:02d}_{combotype}"


def invoice_filename(d: date, combotype: str) -> str:
    return f"{d.day:02d}{d.month:02d}{d.year}_{combotype}"


def payment_deadline(d: date, days: int) -> date:
    return d + timedelta(days=days)


def parse_days(label: str) -> int:
    """Extract days from a label like 'Przelej 30 dni'."""
    return int(label.split()[0])

def invoice_currency(vatLabel: str, currency: str) -> str:
    """Return the vabel like 'VAT PLN' or 'VAT EUR' based on the currency."""
    return f"{vatLabel} {currency}"

@dataclass
class InvoiceData:
    date: date
    combotype: str
    days: int
    currency: str
    gross: Decimal
    netto: Decimal = None
    vat: Decimal = None
    brutto: Decimal = None

    def __post_init__(self) -> None:
        n, v, b = calc_vat(self.gross)
        self.netto = n
        self.vat = v
        self.brutto = b

    @property
    def number(self) -> str:
        return invoice_number(self.date, self.combotype)

    @property
    def filename(self) -> str:
        return invoice_filename(self.date, self.combotype)

    @property
    def deadline(self) -> date:
        return payment_deadline(self.date, self.days)

    @property
    def date_iso(self) -> str:
        return self.date.isoformat()

    @property
    def date_dmy(self) -> str:
        return f"{self.date.day:02d}.{self.date.month:02d}.{self.date.year}"