#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="Terminal Explorer"
APP_BUNDLE="$ROOT_DIR/dist/$APP_NAME.app"
DMG_NAME="terminal-explorer-macos.dmg"
DMG_PATH="$ROOT_DIR/dist/$DMG_NAME"
STAGING_DIR="$ROOT_DIR/build/dmg-staging"
RW_DMG="$ROOT_DIR/build/terminal-explorer-macos-temp.dmg"
VOLUME_NAME="$APP_NAME"

require_file() {
    local path="$1"
    local description="$2"
    if [[ ! -e "$path" ]]; then
        echo "$description not found: $path" >&2
        exit 1
    fi
}

mkdir -p "$ROOT_DIR/build" "$ROOT_DIR/dist"

"$ROOT_DIR/build_macos_app.sh"
require_file "$APP_BUNDLE" "App bundle"

rm -rf "$STAGING_DIR" "$RW_DMG" "$DMG_PATH"
mkdir -p "$STAGING_DIR"

cp -R "$APP_BUNDLE" "$STAGING_DIR/"
ln -s /Applications "$STAGING_DIR/Applications"

hdiutil create \
    -volname "$VOLUME_NAME" \
    -srcfolder "$STAGING_DIR" \
    -ov \
    -format UDRW \
    "$RW_DMG"

hdiutil convert "$RW_DMG" -ov -format UDZO -imagekey zlib-level=9 -o "$DMG_PATH"

rm -rf "$STAGING_DIR" "$RW_DMG"

echo "Built DMG: $DMG_PATH"