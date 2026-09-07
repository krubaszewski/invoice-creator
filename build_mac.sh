#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "Building for macOS..."
rm -rf build/ dist/
./venv/bin/pyinstaller invoice_creator.spec --noconfirm

echo "Creating .app bundle..."
APP="dist/invoice_creator.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
mv dist/invoice_creator "$APP/Contents/MacOS/invoice_creator"
cp Info.plist "$APP/Contents/Info.plist"
cp resources/icon.icns "$APP/Contents/Resources/app.icns"

echo "Done! App: $APP"
