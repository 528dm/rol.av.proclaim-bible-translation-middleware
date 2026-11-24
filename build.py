"""Build the app's exe with the name and version from bible_passages.py embedded.

    pip install pyinstaller
    python build.py

The exe is written to dist/. The version shown in the window title and in the
exe's Properties > Details tab both come from __version__ in bible_passages.py.
Any extra arguments are passed on to PyInstaller (e.g. --distpath somewhere).
"""

import re
import sys
import tempfile
from pathlib import Path

import PyInstaller.__main__

HERE = Path(__file__).resolve().parent
source = (HERE / "bible_passages.py").read_text(encoding="utf-8")
version = re.search(r'^__version__\s*=\s*"([^"]+)"', source, re.M).group(1)
NAME = re.search(r'^APP_NAME\s*=\s*"([^"]+)"', source, re.M).group(1)
parts = [int(p) for p in re.findall(r"\d+", version)][:4]
parts += [0] * (4 - len(parts))
nums = ", ".join(map(str, parts))

version_info = f"""\
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
"""

# PyInstaller's working files go in the system temp folder: a short path avoids
# Windows' 260-character path limit when the project sits in a deep folder.
build_dir = Path(tempfile.gettempdir()) / "bible_passages_build"
build_dir.mkdir(exist_ok=True)
version_file = build_dir / "version_info.txt"
version_file.write_text(version_info, encoding="utf-8")

print(f"Building {NAME} {version} ...")
PyInstaller.__main__.run([
    str(HERE / "bible_passages.py"),
    "--onefile", "--windowed", "--noconfirm",
    "--name", NAME,
    "--version-file", str(version_file),
    "--workpath", str(build_dir),
    "--specpath", str(build_dir),
    "--distpath", str(HERE / "dist"),
    *sys.argv[1:],
])
print(f"Done: {HERE / 'dist' / (NAME + '.exe')}  (version {version})")
