"""Build the app with the name and version from bible_passages.py embedded.

    pip install pyinstaller
    python build.py

Windows: creates the folder dist/<name>/ containing <name>.exe (version in its
         Properties > Details tab) and the _internal folder it needs. A folder
         build, rather than one self-unpacking exe, is less likely to be
         mistaken for malware by antivirus programs, and starts faster.
macOS:   creates dist/<name>.app, with the version in its Get Info window.

PyInstaller can only build for the system it runs on, so the Mac app has to be
built on a Mac (the GitHub workflow in .github/workflows does this for you).
Any extra arguments are passed on to PyInstaller.
"""

import plistlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import PyInstaller.__main__

HERE = Path(__file__).resolve().parent
WINDOWS = sys.platform == "win32"
MAC = sys.platform == "darwin"

source = (HERE / "bible_passages.py").read_text(encoding="utf-8")
version = re.search(r'^__version__\s*=\s*"([^"]+)"', source, re.M).group(1)
NAME = re.search(r'^APP_NAME\s*=\s*"([^"]+)"', source, re.M).group(1)

# PyInstaller's working files go in the system temp folder: a short path avoids
# Windows' 260-character path limit when the project sits in a deep folder.
build_dir = Path(tempfile.gettempdir()) / "bible_passages_build"
build_dir.mkdir(exist_ok=True)

args = [
    str(HERE / "bible_passages.py"),
    "--windowed", "--noconfirm",
    "--name", NAME,
    "--workpath", str(build_dir),
    "--specpath", str(build_dir),
    "--distpath", str(HERE / "dist"),
]

if WINDOWS:
    # version details for the exe's Properties tab
    parts = [int(p) for p in re.findall(r"\d+", version)][:4]
    parts += [0] * (4 - len(parts))
    nums = ", ".join(map(str, parts))
    version_file = build_dir / "version_info.txt"
    version_file.write_text(f"""\
VSVersionInfo(
  ffi=FixedFileInfo(filevers=({nums}), prodvers=({nums}), mask=0x3f, flags=0x0,
                    OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('FileDescription', '{NAME} - English / Spanish Bible verses'),
      StringStruct('FileVersion', '{version}'),
      StringStruct('ProductName', '{NAME}'),
      StringStruct('ProductVersion', '{version}'),
      StringStruct('OriginalFilename', '{NAME}.exe'),
      StringStruct('InternalName', '{NAME}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""", encoding="utf-8")
    args += ["--version-file", str(version_file)]
# On macOS --windowed builds a normal .app bundle.

print(f"Building {NAME} {version} for {sys.platform} ...")
PyInstaller.__main__.run(args + sys.argv[1:])

if MAC:
    # put the version into the app's Info.plist (shown in Finder's Get Info)
    plist_path = HERE / "dist" / f"{NAME}.app" / "Contents" / "Info.plist"
    with open(plist_path, "rb") as f:
        info = plistlib.load(f)
    info["CFBundleShortVersionString"] = version
    info["CFBundleVersion"] = version
    with open(plist_path, "wb") as f:
        plistlib.dump(info, f)
    # editing Info.plist breaks PyInstaller's signature, and Apple Silicon Macs
    # refuse to open apps with a broken one - so re-sign (ad hoc, no certificate)
    app = plist_path.parents[1]
    subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(app)], check=True)
    print(f"Done: {app}  (version {version})")
else:
    exe = NAME + (".exe" if WINDOWS else "")
    print(f"Done: {HERE / 'dist' / NAME / exe}  (version {version})")
