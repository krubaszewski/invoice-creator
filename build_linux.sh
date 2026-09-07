#!/bin/bash
set -e
cd "$(dirname "$0")"
echo "Building for Linux..."
rm -rf build/ dist/
./venv/bin/pyinstaller invoice_creator.spec --noconfirm
echo "Build complete! Output: dist/invoice_creator/"
