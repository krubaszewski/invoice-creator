from __future__ import annotations

import json
import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from turtle import st

import FreeSimpleGUI as sg
from FreeSimpleGUI import main, window
from models import (
    DEFAULT_PARTNERS_FILE, PAYMENT_TERMS, INVOICE_TYPES, CURRENCIES,
    SELLER_NAME, SELLER_ADDRESS, SELLER_POSTAL, SELLER_NIP,
    BUYER_NAME, BUYER_ADDRESS, BUYER_POSTAL, BUYER_NIP, CITY, Z_RECIPIENT, Z_RECIPIENT_ADDR, Z_SENDER, Z_SENDER_ADDR,
    InvoiceData, parse_days, fmt_pln, SETTINGS_FILE, PROJECT_DIR,
)
from pdf import generate_invoice, generate_order

WINDOW_TITLE = "Invoice and Transport order generator"
_LAST_FOLDER_FILE = SETTINGS_FILE
_LAST_DEFAULT_PARTNERS_FILE = DEFAULT_PARTNERS_FILE

def _today_iso() -> str:
    return datetime.date.today().isoformat()

def _load_last_folder() -> str:
    try:
        return _LAST_FOLDER_FILE.read_text().strip()
    except Exception:
        return ""

def _save_last_folder(path: str) -> None:
    try:
        _LAST_FOLDER_FILE.write_text(path)
    except Exception:
        pass

def _save_default_partners(values: dict) -> None:
    try:
        _LAST_DEFAULT_PARTNERS_FILE.write_text(json.dumps(values))
    except Exception:
        pass

def _load_default_partners(field: str, default: str = "") -> str:
    try:
        data = json.loads(_LAST_DEFAULT_PARTNERS_FILE.read_text())
        for ref, value in data.items():
            if ref == field:
                return value
    except Exception:
        pass
    return default
     
def build_layout() -> list:
    last_folder = _load_last_folder()

    main_screen = [
        [sg.Text("Date (yyyy-mm-dd):"), sg.Input(key="-IN-", default_text=_today_iso(), size=(14, 1), enable_events=True),
         sg.CalendarButton("📅", target="-IN-", format="%Y-%m-%d", close_when_date_chosen=True)],
        [sg.Frame("VAT calculation (23 %)", [
            [sg.Text("Netto:"),       sg.Text(key="-NETTO-",       font=("Helvetica", 14), text_color="blue")],
            [sg.Text("VAT 23 %:"),     sg.Text(key="-VAT-",         font=("Helvetica", 14), text_color="blue")],
            [sg.Text("Brutto:"),       sg.Text(key="-BRUTTO-",     font=("Helvetica", 14), text_color="blue")],
        ], title_color="blue")],
        [sg.Text("Invoice type:"),  sg.Combo(values=INVOICE_TYPES, key="-COMBOTYPE-", size=(14, 1), enable_events=True)],
        [sg.Text("Payment term:"),  sg.Combo(values=list(PAYMENT_TERMS.keys()), key="-COMBO-", size=(16, 1), enable_events=True),
                                        sg.Text(key="-DEADLINE-", font=("Helvetica", 14), text_color="purple")],
        [sg.Text("Currency:"),      sg.Combo(values=CURRENCIES, key="-CURRENCY-", size=(8, 1), enable_events=True)],
        [sg.Text("Gross amount:"),  sg.InputText(key="-GROSS-", size=(15, 1), enable_events=True)],
        [sg.Text("Save PDF to:"), sg.Input(key="-FOLDER-", default_text=last_folder, size=(50, 1), enable_events=True), sg.FolderBrowse("Folder", key="-BROWSE-", target="-FOLDER-")],
        [sg.Button("Generate", key="-GENERATE-", button_color=("white", "green")), sg.Button("Quit", key="-QUIT-")],
        [sg.Multiline(size=(90, 13), key="-OUTPUT-", disabled=True, autoscroll=True, text_color="green")],
    ]

    common_seller_column = [
        [sg.Frame("Sprzedawca", [
            [sg.Input(key="-SELLER_ADDRESS-", default_text=_load_default_partners("-SELLER_ADDRESS-", default=SELLER_ADDRESS), size=(36, 1), enable_events=True)],
            [sg.Text("NIP"), sg.Input(key="-SELLER_NIP-", default_text=_load_default_partners("-SELLER_NIP-", default=SELLER_NIP), size=(37, 1), enable_events=True)],
        ])],
    ]

    common_buyer_column = [
        [sg.Frame("Nabywca", [
            [sg.Input(key="-BUYER_ADDRESS-", default_text=_load_default_partners("-BUYER_ADDRESS-", default=BUYER_ADDRESS), size=(36, 1), enable_events=True)],
            [sg.Text("NIP"), sg.Input(key="-BUYER_NIP-", default_text=_load_default_partners("-BUYER_NIP-", default=BUYER_NIP), size=(37, 1), enable_events=True)],
        ])],
    ]

    invoice_seller_column = [
        [sg.Frame("Sprzedawca", [
            [sg.Input(key="-SELLER_NAME-", default_text=_load_default_partners("-SELLER_NAME-", default=SELLER_NAME), size=(37, 1), enable_events=True)],
            [sg.Input(key="-SELLER_POSTAL-", default_text=_load_default_partners("-SELLER_POSTAL-", default=f"{SELLER_POSTAL} {CITY}"), size=(37, 1), enable_events=True)],
        ])],
    ]
    
    invoice_buyer_column = [
        [sg.Frame("Nabywca", [
            [sg.Input(key="-BUYER_NAME-", default_text=_load_default_partners("-BUYER_NAME-", default=BUYER_NAME), size=(41, 1), enable_events=True)],
            [sg.Input(key="-BUYER_POSTAL-", default_text=_load_default_partners("-BUYER_POSTAL-", default=f"{BUYER_POSTAL} {CITY}"), size=(41, 1), enable_events=True)],
        ])],
    ]

    order_seller_column = [
        [sg.Frame("Sprzedawca", [
            [sg.Input(key="-ORDER_SELLER_NAME-", default_text=_load_default_partners("-ORDER_SELLER_NAME-", default=Z_RECIPIENT), size=(34, 1), enable_events=True)],
            [sg.Text("Postal"), sg.Input(key="-ORDER_SELLER_POSTAL-", default_text=_load_default_partners("-ORDER_SELLER_POSTAL-", default=f"{Z_RECIPIENT_ADDR}"), size=(34, 1), enable_events=True)],
        ])],
    ]
    
    order_buyer_column = [
        [sg.Frame("Nabywca", [
            [sg.Input(key="-ORDER_BUYER_NAME-", default_text=_load_default_partners("-ORDER_BUYER_NAME-", default=Z_SENDER), size=(38, 1), enable_events=True)],
            [sg.Text("Postal"), sg.Input(key="-ORDER_BUYER_POSTAL-", default_text=_load_default_partners("-ORDER_BUYER_POSTAL-", default=f"{Z_SENDER_ADDR}"), size=(38, 1), enable_events=True)],
        ])],
    ]

    business_partners = [sg.Col(invoice_seller_column, p=0), sg.Col(invoice_buyer_column, p=0)]
    order_partners = [sg.Col(order_seller_column, p=0), sg.Col(order_buyer_column, p=0)]
    common_business_partners = [sg.Col(common_seller_column, p=0), sg.Col(common_buyer_column, p=0)]
    save_default_partners = [sg.Button("Save Local Default Partners", key="-SAVE_DEFAULT_PARTNERS-", button_color=("white", "green")), sg.Text("", key="-SAVE_STATUS-", text_color="white", background_color="dark green", font=("Helvetica", 12, "bold"), pad=(10, 5))]

    invoice_frame = [sg.Frame("Invoice Details", [
                business_partners
            ], font=("Helvetica", 13))]

    order_frame = [sg.Frame("Order Details", [
                order_partners
            ], font=("Helvetica", 13))]

    common_frame = [sg.Frame("Common", [
                common_business_partners
            ], font=("Helvetica", 13))]
    
    save_section = save_default_partners

    business_partners_tab = [ common_frame, invoice_frame, order_frame, save_section ]

    main_layout = [[sg.TabGroup([[  sg.Tab('Main Details', main_screen),
                               sg.Tab('Business Partners', business_partners_tab)]])]]
                               
    main_layout[-1].append(sg.Sizegrip())
    return main_layout

def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    n = 1
    while True:
        candidate = parent / f"{stem} ({n}){suffix}"
        if not candidate.exists():
            return candidate
        n += 1


class App:
    def __init__(self) -> None:
        self.window = sg.Window(WINDOW_TITLE, build_layout(), finalize=True, size=(720, 459), resizable=True)
        self.window.refresh()
        self._recalc()

    def run(self) -> None:
        while True:
            event, values = self.window.read()
            
            match event:
                case sg.WINDOW_CLOSED | "-QUIT-":
                    break
                case "-BROWSE-" | "-FOLDER-":
                    folder = values.get("-FOLDER-")
                    if folder:
                        _save_last_folder(folder)
                case "-GENERATE-":
                    self._on_generate(values)
                case "-SAVE_DEFAULT_PARTNERS-":
                    values = {k: self.window[k].get() for k in (self._PARTNER_KEYS)}
                    _save_default_partners(values)
                    self.window["-SAVE_STATUS-"].update("Saved!")
            self._recalc(values)
        self.window.close()

    _PARTNER_KEYS = (
        "-SELLER_NAME-", "-SELLER_ADDRESS-", "-SELLER_POSTAL-", "-SELLER_NIP-",
        "-BUYER_NAME-", "-BUYER_ADDRESS-", "-BUYER_POSTAL-", "-BUYER_NIP-",
        "-ORDER_SELLER_NAME-", "-ORDER_SELLER_POSTAL-",
        "-ORDER_BUYER_NAME-", "-ORDER_BUYER_POSTAL-",
    )

    def _partner_kwargs(self, values: dict) -> dict:
        return {
            "seller_name": values.get("-SELLER_NAME-") or SELLER_NAME,
            "seller_address": values.get("-SELLER_ADDRESS-") or SELLER_ADDRESS,
            "seller_postal": values.get("-SELLER_POSTAL-") or f"{SELLER_POSTAL} {CITY}",
            "seller_nip": values.get("-SELLER_NIP-") or SELLER_NIP,
            "buyer_name": values.get("-BUYER_NAME-") or BUYER_NAME,
            "buyer_address": values.get("-BUYER_ADDRESS-") or BUYER_ADDRESS,
            "buyer_postal": values.get("-BUYER_POSTAL-") or f"{BUYER_POSTAL} {CITY}",
            "buyer_nip": values.get("-BUYER_NIP-") or BUYER_NIP,
            "order_seller_name": values.get("-ORDER_SELLER_NAME-") or Z_RECIPIENT,
            "order_seller_postal": values.get("-ORDER_SELLER_POSTAL-") or Z_RECIPIENT_ADDR,
            "order_buyer_name": values.get("-ORDER_BUYER_NAME-") or Z_SENDER,
            "order_buyer_postal": values.get("-ORDER_BUYER_POSTAL-") or Z_SENDER_ADDR,
        }

    def _recalc(self, values: dict | None = None) -> None:
        if values is None:
            values = {k: self.window[k].get() for k in ("-IN-", "-COMBO-", "-COMBOTYPE-", "-CURRENCY-", "-GROSS-") + self._PARTNER_KEYS}
        gross_raw = values.get("-GROSS-", "") or ""
        if gross_raw.strip():
            try:
                gross = Decimal(str(gross_raw).replace(",", "."))
            except (InvalidOperation, ValueError):
                gross = Decimal("0")
        else:
            gross = None
        date_raw = (values.get("-IN-") or _today_iso())
        try:
            d = datetime.date.fromisoformat(str(date_raw).strip())
        except ValueError:
            d = datetime.date.today()
        days_label = values.get("-COMBO-") or ""
        days = parse_days(days_label) if days_label else 0
        currency = values.get("-CURRENCY-") or "PLN"
        data = InvoiceData(date=d, combotype="MIKRO", days=days, currency=currency, gross=gross or Decimal("0"), **self._partner_kwargs(values))
        if gross is None:
            self.window["-NETTO-"].update("")
            self.window["-VAT-"].update("")
            self.window["-BRUTTO-"].update("")
        else:
            self.window["-NETTO-"].update(f"{fmt_pln(data.netto)} {values.get('-CURRENCY-')}")
            self.window["-VAT-"].update(f"{fmt_pln(data.vat)} {values.get('-CURRENCY-')}")
            self.window["-BRUTTO-"].update(f"{fmt_pln(data.brutto)} {values.get('-CURRENCY-')}")
        if days > 0:
            deadline = d + datetime.timedelta(days=days)
            self.window["-DEADLINE-"].update(f"Deadline: {deadline.isoformat()}")
        else:
            self.window["-DEADLINE-"].update("")

    def _on_generate(self, values: dict) -> None:
        date_raw = str(values.get("-IN-") or "").strip()
        if not date_raw:
            self.window["-OUTPUT-"].update("ERROR: pick a date (yyyy-mm-dd).")
            return
        try:
            d = datetime.date.fromisoformat(date_raw)
        except ValueError:
            self.window["-OUTPUT-"].update("ERROR: date must be yyyy-mm-dd.")
            return

        combotype = values.get("-COMBOTYPE-") or "MIKRO"
        term_label = values.get("-COMBO-") or "30 dni"
        days = parse_days(term_label)
        currency = values.get("-CURRENCY-") or "PLN"

        gross_raw = str(values.get("-GROSS-") or "").strip()
        if not gross_raw:
            self.window["-OUTPUT-"].update("ERROR: enter a gross amount.")
            return
        try:
            gross = Decimal(gross_raw.replace(",", "."))
        except InvalidOperation:
            self.window["-OUTPUT-"].update("ERROR: invalid amount.")
            return
        if gross <= 0:
            self.window["-OUTPUT-"].update("ERROR: amount must be positive.")
            return

        data = InvoiceData(date=d, combotype=combotype, days=days, currency=currency, gross=gross, **self._partner_kwargs(values))
        folder = Path(values.get("-FOLDER-") or str(PROJECT_DIR))
        folder.mkdir(parents=True, exist_ok=True)

        fv_file = f"FV_{data.filename}.pdf"
        order_file = f"ZLECENIE_{data.filename}.pdf"
        fv_path = _unique_path(folder / fv_file)
        order_path = _unique_path(folder / order_file)

        try:
            generate_invoice(data, str(fv_path))
            generate_order(data, str(order_path))
            msg = (f"OK  Generated:\n"
                   f"     {fv_path.name}\n"
                   f"     {order_path.name}\n"
                   f"Number: {data.number}\n"
                   f"Deadline: {data.deadline.isoformat()}\n"
                   f"Netto {fmt_pln(data.netto)} | VAT {fmt_pln(data.vat)} | Brutto {fmt_pln(data.brutto)}")
            self.window["-OUTPUT-"].update(msg)
        except Exception as exc:
            self.window["-OUTPUT-"].update(f"ERROR: {exc}")

if __name__ == "__main__":
    app = App()
    app.run()