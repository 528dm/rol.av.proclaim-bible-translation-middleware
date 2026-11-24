# Proclaim - Bible Passages

A small Windows app that shows Bible passages in English and Spanish side by side,
a couple of verses at a time — handy for preparing bilingual readings, slides or handouts.
Choose from 10 English and 10 Spanish versions; the defaults are **NIVUK** and **NVI**.

Type one or more references, click **Get verses**, and copy the result.

## What the output looks like

Each passage is split into small groups. For every group you get the English verses,
then the same verses in Spanish. Groups are separated by a `--` line (there's no `--`
after the last one):

```
John 3:16-18
16 For God so loved the world that he gave his one and only Son, ... 17 For God did not send his Son into the world ...
16 »Porque tanto amó Dios al mundo que dio a su Hijo único, ... 17 Dios no envió a su Hijo al mundo ...
--
18 Whoever believes in him is not condemned, ...
18 El que cree en él no es condenado, ...
--
Romans 8:28
28 And we know that in all things God works for the good of those who love him, ...
28 Ahora bien, sabemos que Dios dispone todas las cosas para el bien de quienes lo aman, ...
```

How verses are grouped:

- Normally **two verses** per group.
- If the two English verses together are **more than 50 words**, the group has **one verse** instead.
- When you enter **more than one passage**, each starts with its reference on its own line
  (first letter capitalised). A single passage has no label.

## Using it

1. Go to the [latest release](../../releases/latest) and, under **Assets**, download the file
   for your computer. Python is **not** needed.

   | Computer | Download |
   |---|---|
   | Windows | `Proclaim-Bible-Passages-Windows.zip` |
   | Mac with Apple Silicon (M1, M2, M3, M4…) | `Proclaim-Bible-Passages-Mac-AppleSilicon.zip` |
   | Mac with an Intel processor | `Proclaim-Bible-Passages-Mac-Intel.zip` |

   On Windows, right-click the zip → **Extract All…**, and choose where to put it (for example
   your Documents folder). Open the extracted **Proclaim - Bible Passages** folder and
   double-click **Proclaim - Bible Passages.exe**. Keep the exe together with the `_internal`
   folder next to it – it needs it to run. To start it more easily, right-click the exe →
   **Show more options → Send to → Desktop (create shortcut)**.

   On a Mac, double-click the zip to unpack it, then drag **Proclaim - Bible Passages** into
   your Applications folder. (Not sure which Mac you have? Apple menu → **About This Mac**:
   it says "Chip: Apple M…" or "Processor: … Intel …".)
2. Open the app.
3. Enter passages separated by commas, for example:

   ```
   John 3:16-18, Romans 8:28, Psalm 23
   ```

4. Press **Enter** or click **Get verses**, then **Copy all**.

Options in the window:

- **English** and **Spanish** – pick the Bible version for each language.
- **Show first** – choose whether English or Spanish comes first in each group.
- **Show verse numbers** – turn the verse numbers on or off.

### Available versions

| English | Spanish |
|---|---|
| NIVUK – New International Version (UK) *(default)* | NVI – Nueva Versión Internacional *(default)* |
| NIV – New International Version | RVR1960 – Reina-Valera 1960 |
| ESV – English Standard Version | NTV – Nueva Traducción Viviente |
| KJV – King James Version | LBLA – La Biblia de las Américas |
| NKJV – New King James Version | NBLA – Nueva Biblia de las Américas |
| NLT – New Living Translation | DHH – Dios Habla Hoy |
| NASB – New American Standard Bible | RVC – Reina Valera Contemporánea |
| CSB – Christian Standard Bible | TLA – Traducción en Lenguaje Actual |
| NRSVUE – New Revised Standard Version Updated Edition | PDT – Palabra de Dios para Todos |
| AMP – Amplified Bible | RVA-2015 – Reina Valera Actualizada |

The 50-word rule always counts the words in the English version, whichever language is shown first.

### Entering references

- Separate passages with commas or semicolons.
- A number on its own continues the previous book and chapter:
  `John 3:16, 18` means John 3:16 and John 3:18.
- Common abbreviations work, e.g. `Gen`, `Ps`, `Prov`, `Isa`, `Mt`, `Jn`, `Rom`, `1 Cor`,
  `1Cor`, `Phil`, `Heb`, `1 Pet`, `1Jn`, `Rev`. (A few, such as `Jhn` and `SoS`, aren't recognised.)
- Lower case is fine: `1 john 1:9`.

### Notes

- **Internet connection required.** The text is fetched from
  [BibleGateway.com](https://www.biblegateway.com) each time; no Bible text is stored in
  this repository. If BibleGateway changes its page layout, the app may need updating.
- **"Windows protected your PC" warning.** The exe isn't digitally signed, so Windows
  SmartScreen may warn you the first time. Click **More info → Run anyway**.
- **Mac: "can't be opened" / "Apple could not verify…" warning.** The app isn't notarised
  by Apple. Click **Done**, then go to **System Settings → Privacy & Security**, scroll
  down and click **Open Anyway** next to the message about the app. You only need to do
  this once. If macOS instead says the app "is damaged", open Terminal and run
  `xattr -cr "/Applications/Proclaim - Bible Passages.app"`, then open it again.
- **Antivirus false alarms.** Some antivirus programs (especially ones that use AI to guess,
  such as HP Wolf Security) may wrongly flag the app, because malware sometimes uses the same
  packaging tool (PyInstaller). The builds are made in ways that reduce this, but it can still
  happen with a new, unsigned app. You can check a download yourself at
  [virustotal.com](https://www.virustotal.com).

## Running or building from source

Requires Python 3.10 or later (Windows or Mac). The app uses only the standard library
(Tkinter for the window), so there's nothing else to install to run it:

```powershell
python bible_passages.py
```

Quick test without the window (prints the output to the console):

```powershell
python bible_passages.py "John 3:16-18, Romans 8:28"
```

To build the standalone app yourself with [PyInstaller](https://pyinstaller.org):

```powershell
pip install pyinstaller
python build.py
```

On Windows this creates the folder `dist/Proclaim - Bible Passages/`, containing the exe (with
the version number in its **Properties → Details** tab) and the `_internal` folder it needs. On a Mac it creates `dist/Proclaim - Bible Passages.app`.
PyInstaller can only build for the computer it runs on, so the Mac app must be built on a Mac.

### Automatic builds (GitHub Actions)

You don't normally need to build anything by hand. The workflow in
`.github/workflows/build.yml` builds the Windows exe and both Mac apps on GitHub's machines:

- **When you publish a release**, all three are built and attached to it automatically
  (allow about 5 minutes).
- **On demand:** **Actions** tab → **Build apps** → **Run workflow**. Enter a release tag
  (e.g. `v1.0.0`) to attach the builds to an existing release, or leave it empty to just
  build; the files then appear under **Artifacts** at the bottom of the run's page.

### Versioning

The version lives in one place: `__version__` at the top of `bible_passages.py`. It appears
in the window title and in the exe's properties, and `python bible_passages.py --version`
prints it. Releases follow [semantic versioning](https://semver.org) (MAJOR.MINOR.PATCH):

- **PATCH** (1.0.0 → 1.0.1) – bug fixes, e.g. after a BibleGateway layout change
- **MINOR** (1.0.0 → 1.1.0) – new features
- **MAJOR** (1.x → 2.0.0) – big changes in how the app works

To release: update `__version__`, commit and push, then create a GitHub Release tagged to
match (e.g. `v1.0.1`). The workflow attaches the Windows and Mac downloads a few minutes
after you publish.

### Changing the behaviour

These settings are at the top of `bible_passages.py`:

| Setting | Default | Meaning |
|---|---|---|
| `ENGLISH_VERSIONS` | NIVUK first | English versions in the dropdown (BibleGateway code, name); the first is the default |
| `SPANISH_VERSIONS` | NVI first | Spanish versions in the dropdown; the first is the default |
| `SEPARATOR` | `--` | Line printed between groups |
| `MAX_WORDS` | `50` | Two-verse groups longer than this (in English) become one verse |

## Copyright

Scripture quotations are fetched from BibleGateway at run time and remain the property of
their copyright holders (for example, the *New International Version® (Anglicised)* and the
*Nueva Versión Internacional* are © Biblica, Inc.). Each version has its own publisher and
terms; check them before reproducing large amounts of text.
