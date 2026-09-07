import sys
import os

# Redirect stderr to suppress fontconfig/weasyprint warnings that cause terminal window on macOS
stderr_path = os.path.join(os.environ.get("TMPDIR", "/tmp"), "invoice_creator_stderr.log")
try:
    sys.stderr = open(stderr_path, "w")
except Exception:
    pass

import FreeSimpleGUI as sg
from ui import App

if __name__ == "__main__":
    App().run()
