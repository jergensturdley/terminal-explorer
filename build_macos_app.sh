#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="Terminal Explorer"
BINARY_NAME="terminal-explorer-macos"
PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
APP_SCRIPT="$ROOT_DIR/macos/terminal_explorer_launcher.applescript"
VERSION_FILE="$ROOT_DIR/VERSION"
APP_DIR="$ROOT_DIR/dist/$APP_NAME.app"
RESOURCE_BIN="$APP_DIR/Contents/Resources/$BINARY_NAME"
PLIST="$APP_DIR/Contents/Info.plist"
ICON_SOURCE_PNG="$ROOT_DIR/explorer.png"
ICON_SOURCE_ICNS="$ROOT_DIR/explorer.icns"
ICON_SOURCE_ICO="$ROOT_DIR/explorer.ico"
GENERATED_ICNS="$ROOT_DIR/build/terminal-explorer.icns"
GENERATED_PNG="$ROOT_DIR/build/terminal-explorer-icon.png"
APP_VERSION="$(tr -d '[:space:]' < "$VERSION_FILE")"

require_file() {
    local path="$1"
    local description="$2"
    if [[ ! -e "$path" ]]; then
        echo "$description not found: $path" >&2
        exit 1
    fi
}

generate_icns() {
    local png_path="$1"
    local icns_path="$2"
    local iconset_dir
    iconset_dir="$(mktemp -d "$ROOT_DIR/build/iconset.XXXXXX.iconset")"

    mkdir -p "$iconset_dir"
    sips -z 16 16 "$png_path" --out "$iconset_dir/icon_16x16.png" >/dev/null
    sips -z 32 32 "$png_path" --out "$iconset_dir/icon_16x16@2x.png" >/dev/null
    sips -z 32 32 "$png_path" --out "$iconset_dir/icon_32x32.png" >/dev/null
    sips -z 64 64 "$png_path" --out "$iconset_dir/icon_32x32@2x.png" >/dev/null
    sips -z 128 128 "$png_path" --out "$iconset_dir/icon_128x128.png" >/dev/null
    sips -z 256 256 "$png_path" --out "$iconset_dir/icon_128x128@2x.png" >/dev/null
    sips -z 256 256 "$png_path" --out "$iconset_dir/icon_256x256.png" >/dev/null
    sips -z 512 512 "$png_path" --out "$iconset_dir/icon_256x256@2x.png" >/dev/null
    sips -z 512 512 "$png_path" --out "$iconset_dir/icon_512x512.png" >/dev/null
    sips -z 1024 1024 "$png_path" --out "$iconset_dir/icon_512x512@2x.png" >/dev/null
    iconutil -c icns "$iconset_dir" -o "$icns_path"
    rm -rf "$iconset_dir"
}

apply_app_metadata() {
    /usr/libexec/PlistBuddy -c "Set :CFBundleDisplayName $APP_NAME" "$PLIST" 2>/dev/null || \
        /usr/libexec/PlistBuddy -c "Add :CFBundleDisplayName string $APP_NAME" "$PLIST"
    /usr/libexec/PlistBuddy -c "Set :CFBundleName $APP_NAME" "$PLIST" 2>/dev/null || \
        /usr/libexec/PlistBuddy -c "Add :CFBundleName string $APP_NAME" "$PLIST"
    /usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier com.jergensturdley.terminalexplorer" "$PLIST" 2>/dev/null || \
        /usr/libexec/PlistBuddy -c "Add :CFBundleIdentifier string com.jergensturdley.terminalexplorer" "$PLIST"
    /usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $APP_VERSION" "$PLIST" 2>/dev/null || \
        /usr/libexec/PlistBuddy -c "Add :CFBundleShortVersionString string $APP_VERSION" "$PLIST"
    /usr/libexec/PlistBuddy -c "Set :CFBundleVersion $APP_VERSION" "$PLIST" 2>/dev/null || \
        /usr/libexec/PlistBuddy -c "Add :CFBundleVersion string $APP_VERSION" "$PLIST"
    /usr/libexec/PlistBuddy -c "Set :NSHighResolutionCapable true" "$PLIST" 2>/dev/null || \
        /usr/libexec/PlistBuddy -c "Add :NSHighResolutionCapable bool true" "$PLIST"
    /usr/libexec/PlistBuddy -c "Delete :CFBundleIconName" "$PLIST" 2>/dev/null || true

    /usr/libexec/PlistBuddy -c "Delete :CFBundleDocumentTypes" "$PLIST" 2>/dev/null || true
    /usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes array" "$PLIST"
    /usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes:0 dict" "$PLIST"
    /usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes:0:CFBundleTypeName string Folder" "$PLIST"
    /usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes:0:CFBundleTypeRole string Viewer" "$PLIST"
    /usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes:0:LSHandlerRank string Default" "$PLIST"
    /usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes:0:LSItemContentTypes array" "$PLIST"
    /usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes:0:LSItemContentTypes:0 string public.folder" "$PLIST"
    /usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes:0:LSItemContentTypes:1 string public.directory" "$PLIST"
}

attach_icon_if_available() {
    local icon_path=""

    if [[ -f "$ICON_SOURCE_ICNS" ]]; then
        icon_path="$ICON_SOURCE_ICNS"
    elif [[ -f "$ICON_SOURCE_PNG" ]]; then
        mkdir -p "$ROOT_DIR/build"
        generate_icns "$ICON_SOURCE_PNG" "$GENERATED_ICNS"
        icon_path="$GENERATED_ICNS"
    elif [[ -f "$ICON_SOURCE_ICO" ]]; then
        mkdir -p "$ROOT_DIR/build"
        sips -s format png "$ICON_SOURCE_ICO" --out "$GENERATED_PNG" >/dev/null
        generate_icns "$GENERATED_PNG" "$GENERATED_ICNS"
        icon_path="$GENERATED_ICNS"
    fi

    if [[ -n "$icon_path" ]]; then
        cp "$icon_path" "$APP_DIR/Contents/Resources/AppIcon.icns"
        cp "$icon_path" "$APP_DIR/Contents/Resources/droplet.icns"
        /usr/libexec/PlistBuddy -c "Set :CFBundleIconFile AppIcon" "$PLIST" 2>/dev/null || \
            /usr/libexec/PlistBuddy -c "Add :CFBundleIconFile string AppIcon" "$PLIST"
    else
        echo "No explorer.icns, explorer.png, or explorer.ico found; building app with the default icon."
    fi
}

remove_code_signatures() {
    # Releases are intentionally unsigned. PyInstaller/macOS tooling may add
    # ad-hoc signatures to Mach-O outputs, so strip any signatures best-effort.
    if ! command -v codesign >/dev/null 2>&1; then
        return
    fi

    local targets=(
        "$ROOT_DIR/dist/$BINARY_NAME"
        "$RESOURCE_BIN"
        "$APP_DIR"
    )

    for target in "${targets[@]}"; do
        if [[ -e "$target" ]]; then
            codesign --remove-signature "$target" 2>/dev/null || true
        fi
    done
}

require_file "$PYTHON_BIN" "Project Python interpreter"
require_file "$APP_SCRIPT" "AppleScript launcher"
require_file "$VERSION_FILE" "Version file"

mkdir -p "$ROOT_DIR/dist" "$ROOT_DIR/build"

"$PYTHON_BIN" -m PyInstaller --clean --noconfirm --onefile --console --name "$BINARY_NAME" "$ROOT_DIR/explorer.py"

rm -rf "$APP_DIR"
osacompile -o "$APP_DIR" "$APP_SCRIPT"
mkdir -p "$APP_DIR/Contents/Resources"
cp "$ROOT_DIR/dist/$BINARY_NAME" "$RESOURCE_BIN"
chmod +x "$RESOURCE_BIN"

apply_app_metadata
attach_icon_if_available
remove_code_signatures

echo "Built unsigned app wrapper: $APP_DIR"