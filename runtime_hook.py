import sys
import os
import tempfile

stderr_path = os.path.join(tempfile.gettempdir(), "invoice_creator_stderr.log")
try:
    sys.stderr = open(stderr_path, "w")
except Exception:
    pass
