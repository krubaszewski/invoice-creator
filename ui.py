from __future__ import annotations

import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import FreeSimpleGUI as sg
from models import (
    PAYMENT_TERMS, INVOICE_TYPES, CURRENCIES,
    InvoiceData, parse_days, fmt_pln, SETTINGS_FILE, PROJECT_DIR,
)
from pdf import generate_invoice, generate_order

WINDOW_TITLE = "Invoice and Transport order generator"
_LAST_FOLDER_FILE = SETTINGS_FILE

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

def build_layout() -> list:
    last_folder = _load_last_folder()
    return [
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
        self.window = sg.Window(WINDOW_TITLE, build_layout(), finalize=True, size=(720, 435), resizable=True)
        self.window.refresh()
        self._recalc()

    def run(self) -> None:
        while True:
            event, values = self.window.read()
            if event in (sg.WINDOW_CLOSED, "-QUIT-"):
                break
            if event == "-BROWSE-" or event == "-FOLDER-":
                folder = values.get("-FOLDER-")
                if folder:
                    _save_last_folder(folder)
            if event == "-GENERATE-":
                self._on_generate(values)
            self._recalc(values)
        self.window.close()

    def _recalc(self, values: dict | None = None) -> None:
        if values is None:
            values = {k: self.window[k].get() for k in ("-IN-", "-COMBO-", "-COMBOTYPE-", "-CURRENCY-", "-GROSS-")}
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
        data = InvoiceData(date=d, combotype="MIKRO", days=days, currency=currency, gross=gross or Decimal("0"))
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

        data = InvoiceData(date=d, combotype=combotype, days=days, currency=currency, gross=gross)
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