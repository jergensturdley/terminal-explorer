from __future__ import annotations

from pathlib import Path
import re


ROOT_DIR = Path(__file__).resolve().parent
VERSION_FILE = ROOT_DIR / "VERSION"
OUTPUT_FILE = ROOT_DIR / "build" / "windows_version_info.txt"


def load_version() -> str:
    version = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", version):
        raise ValueError(f"Unsupported version format: {version}")
    return version


def numeric_version_parts(version: str) -> tuple[int, int, int, int]:
    core = version.split("-", 1)[0].split("+", 1)[0]
    major, minor, patch = (int(part) for part in core.split("."))
    return major, minor, patch, 0


def build_version_file(version: str) -> str:
    major, minor, patch, build = numeric_version_parts(version)
    return f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({major}, {minor}, {patch}, {build}),
    prodvers=({major}, {minor}, {patch}, {build}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', 'jergensturdley'),
          StringStruct('FileDescription', 'Terminal Explorer'),
          StringStruct('FileVersion', '{version}'),
          StringStruct('InternalName', 'terminal-explorer'),
          StringStruct('OriginalFilename', 'Terminal Explorer.exe'),
          StringStruct('ProductName', 'Terminal Explorer'),
          StringStruct('ProductVersion', '{version}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def main() -> None:
    version = load_version()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(build_version_file(version), encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE} for version {version}")


if __name__ == "__main__":
    main()