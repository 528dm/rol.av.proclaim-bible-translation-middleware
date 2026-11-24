"""Proclaim - Bible Passages: English / Spanish side-by-side pairs (default NIVUK / NVI).

Enter comma-separated passages; the app fetches each from BibleGateway and
outputs two verses in one version, the same two verses in the other, then "--".
If the two English verses total more than 50 words, it shows one verse instead.

Uses only the Python standard library, so it bundles cleanly with PyInstaller.
Build the exe (with the version embedded) using:
    python build.py

Command-line test (no window):
    python bible_passages.py "John 3:16-18, Romans 8:28"
"""

import html
import re
import sys
import threading
import urllib.parse
import urllib.request
from collections import OrderedDict

__version__ = "1.0.0"  # MAJOR.MINOR.PATCH - the only place to change the version
APP_NAME = "Proclaim - Bible Passages"  # window title and exe name (build.py reads it)

USER_AGENT ="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
# BibleGateway version codes offered in the dropdowns; the first of each is the default
ENGLISH_VERSIONS = [
    ("NIVUK", "New International Version (UK)"),
    ("NIV", "New International Version"),
    ("ESV", "English Standard Version"),
    ("KJV", "King James Version"),
    ("NKJV", "New King James Version"),
    ("NLT", "New Living Translation"),
    ("NASB", "New American Standard Bible"),
    ("CSB", "Christian Standard Bible"),
    ("NRSVUE", "New Revised Standard Version Updated Edition"),
    ("AMP", "Amplified Bible"),
]
SPANISH_VERSIONS = [
    ("NVI", "Nueva Versión Internacional"),
    ("RVR1960", "Reina-Valera 1960"),
    ("NTV", "Nueva Traducción Viviente"),
    ("LBLA", "La Biblia de las Américas"),
    ("NBLA", "Nueva Biblia de las Américas"),
    ("DHH", "Dios Habla Hoy"),
    ("RVC", "Reina Valera Contemporánea"),
    ("TLA", "Traducción en Lenguaje Actual"),
    ("PDT", "Palabra de Dios para Todos"),
    ("RVA-2015", "Reina Valera Actualizada"),
]
SEPARATOR = "--"
MAX_WORDS = 50  # if two English verses total more than this, show one verse at a time

# ------------------------------------------------------------------ references

_NUMERIC = re.compile(r"^\d+(:\d+)?(\s*-\s*\d+(:\d+)?)?$")
_BOOK_CHAPTER = re.compile(r"^(.*?[A-Za-z].*?)\s+(\d+)(?::\d+)?")


def split_references(text):
    """Split "John 3:16-18, 20; Psalm 23" into full references.

    A part that is only numbers ("20" or "5:1-3") reuses the previous book,
    and the previous chapter when it has no colon.
    """
    refs = []
    book = chapter = None
    for raw in re.split(r"[,;\r\n]+", text):
        part = re.sub(r"\s+", " ", raw).strip()
        if not part:
            continue
        if _NUMERIC.match(part) and book:
            if ":" in part or not chapter:
                refs.append(f"{book} {part}")
            else:
                refs.append(f"{book} {chapter}:{part}")
        else:
            refs.append(part)
        m = _BOOK_CHAPTER.match(refs[-1])
        if m:
            book = m.group(1)
            chapter = m.group(2) if ":" in refs[-1] else None
    return refs


# ------------------------------------------------------------------ fetching

_FLAGS = re.S | re.I


def fetch_html(ref, version):
    url = ("https://www.biblegateway.com/passage/?search="
           + urllib.parse.quote(ref) + "&version=" + version)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def get_verses(ref, version):
    """Return an OrderedDict: "John-3-16" -> verse text."""
    page = fetch_html(ref, version)
    m = re.search(r"class=['\"]passage-content", page)
    if not m:
        raise ValueError(f"No passage found for '{ref}' ({version}).")
    body = page[m.start():]

    # cut off everything after the passage text: the footnotes and cross-reference
    # lists, the "Read full chapter" link and the next/previous chapter links.
    # (Matches the class name anywhere in the attribute, e.g. "footnotes resources-section".)
    end = re.search(r"""class=['"][^'"]*\b(footnotes|crossrefs|full-chap-link|passage-scroller)\b""",
                    body, flags=_FLAGS)
    if end:
        body = body[:end.start()]
    body = re.sub(r"<[^>]*$", "", body)  # half tag left by the cut

    # remove headings, footnote/cross-ref markers, verse/chapter numbers, spacers
    body = re.sub(r"<h[1-6][^>]*>.*?</h[1-6]>", "", body, flags=_FLAGS)
    body = re.sub(r"<sup[^>]*class=['\"](footnote|crossreference)['\"][^>]*>.*?</sup>",
                  "", body, flags=_FLAGS)
    body = re.sub(r"<sup[^>]*class=['\"]versenum['\"][^>]*>.*?</sup>", "", body, flags=_FLAGS)
    body = re.sub(r"<span[^>]*class=['\"]chapternum['\"][^>]*>.*?</span>", "", body, flags=_FLAGS)
    body = re.sub(r"<span[^>]*class=['\"]indent-\d+-breaks['\"][^>]*>.*?</span>",
                  "", body, flags=_FLAGS)
    body = re.sub(r"<br\s*/?>", " ", body, flags=_FLAGS)

    # every verse fragment starts with <span ... class="text Book-C-V">
    verses = OrderedDict()
    markers = list(re.finditer(
        r"<span[^>]*class=['\"]text ([A-Za-z0-9]+-\d+-\d+)['\"][^>]*>", body, flags=_FLAGS))
    for k, mk in enumerate(markers):
        end = markers[k + 1].start() if k + 1 < len(markers) else len(body)
        chunk = re.sub(r"<[^>]+>", "", body[mk.end():end])
        chunk = re.sub(r"[\s ]+", " ", html.unescape(chunk)).strip()
        if not chunk:
            continue
        key = mk.group(1)
        verses[key] = f"{verses[key]} {chunk}".strip() if key in verses else chunk
    if not verses:
        raise ValueError(f"No verses found for '{ref}' ({version}).")
    return verses


# ------------------------------------------------------------------ formatting

def format_line(keys, verses, numbers):
    parts = []
    for k in keys:
        if k in verses:
            n = k.rsplit("-", 1)[-1]
            parts.append(f"{n} {verses[k]}" if numbers else verses[k])
    return " ".join(parts)


def build_output(text, english="NIVUK", spanish="NVI", english_first=True,
                 numbers=True, status=None):
    first, second = (english, spanish) if english_first else (spanish, english)
    lines = []
    refs = split_references(text)
    for ref in refs:
        if status:
            status(f"Fetching {ref} ...")
        if len(refs) > 1:  # label each passage only when there is more than one
            # first letter in upper case: "1 john 1:9" -> "1 John 1:9"
            lines.append(re.sub(r"[A-Za-z]", lambda m: m.group().upper(), ref, count=1))
        try:
            a = get_verses(ref, first)
            b = get_verses(ref, second)
        except Exception as e:  # network error, bad reference, etc.
            lines += [f"[{ref}] Error: {e}", SEPARATOR]
            continue
        english_verses = a if english_first else b
        # verse order from the first version, plus any only in the second
        keys = list(a) + [k for k in b if k not in a]
        i = 0
        while i < len(keys):
            # two verses at a time, unless the two English verses exceed MAX_WORDS
            size = 1
            if i + 1 < len(keys):
                words = sum(len(english_verses.get(k, "").split()) for k in keys[i:i + 2])
                if words <= MAX_WORDS:
                    size = 2
            group = keys[i:i + size]
            lines += [format_line(group, a, numbers), format_line(group, b, numbers), SEPARATOR]
            i += size
    if lines and lines[-1] == SEPARATOR:
        lines.pop()  # separators go between groups only, not after the last one
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ GUI

def run_gui():
    import tkinter as tk
    from tkinter import ttk, scrolledtext

    root = tk.Tk()
    root.title(f"{APP_NAME} {__version__}")
    root.geometry("860x660")
    root.minsize(640, 420)

    frm = ttk.Frame(root, padding=12)
    frm.pack(fill="both", expand=True)
    frm.columnconfigure(0, weight=1)
    frm.rowconfigure(4, weight=1)

    ttk.Label(frm, text="Passages (comma separated), e.g.  John 3:16-18, Romans 8:28, Psalm 23"
              ).grid(row=0, column=0, columnspan=2, sticky="w")

    entry = ttk.Entry(frm, font=("Segoe UI", 11))
    entry.grid(row=1, column=0, sticky="ew", pady=(4, 8), padx=(0, 8))
    entry.focus_set()
    btn_go = ttk.Button(frm, text="Get verses")
    btn_go.grid(row=1, column=1, sticky="ew", pady=(4, 8))

    versions = ttk.Frame(frm)
    versions.grid(row=2, column=0, sticky="w", pady=(0, 8))
    ttk.Label(versions, text="English:").grid(row=0, column=0, sticky="w")
    eng = ttk.Combobox(versions, state="readonly", width=46,
                       values=[f"{c} - {n}" for c, n in ENGLISH_VERSIONS])
    eng.current(0)
    eng.grid(row=0, column=1, padx=(6, 0), pady=(0, 4))
    ttk.Label(versions, text="Spanish:").grid(row=1, column=0, sticky="w")
    spa = ttk.Combobox(versions, state="readonly", width=46,
                       values=[f"{c} - {n}" for c, n in SPANISH_VERSIONS])
    spa.current(0)
    spa.grid(row=1, column=1, padx=(6, 0))

    opts = ttk.Frame(frm)
    opts.grid(row=3, column=0, sticky="w", pady=(0, 8))
    ttk.Label(opts, text="Show first:").pack(side="left")
    order = ttk.Combobox(opts, state="readonly", width=10, values=["English", "Spanish"])
    order.current(0)
    order.pack(side="left", padx=(6, 18))
    show_nums = tk.BooleanVar(value=True)
    ttk.Checkbutton(opts, text="Show verse numbers", variable=show_nums).pack(side="left")

    btn_copy = ttk.Button(frm, text="Copy all")
    btn_copy.grid(row=3, column=1, sticky="ew", pady=(0, 8))

    out = scrolledtext.ScrolledText(frm, wrap="word", font=("Segoe UI", 11), state="disabled")
    out.grid(row=4, column=0, columnspan=2, sticky="nsew")

    status = ttk.Label(frm, foreground="gray",
                       text="Text from BibleGateway.com (internet connection required).")
    status.grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def set_status(msg):
        root.after(0, lambda: status.config(text=msg))

    def show_result(text):
        out.config(state="normal")
        out.delete("1.0", "end")
        out.insert("1.0", text)
        out.config(state="disabled")
        status.config(text="Done.")
        btn_go.state(["!disabled"])
        root.config(cursor="")

    def go(_event=None):
        text = entry.get().strip()
        if not text:
            status.config(text="Enter at least one passage.")
            return
        english = ENGLISH_VERSIONS[eng.current()][0]
        spanish = SPANISH_VERSIONS[spa.current()][0]
        english_first = order.current() == 0
        numbers = show_nums.get()
        btn_go.state(["disabled"])
        root.config(cursor="watch")

        def work():  # network calls off the UI thread so the window stays responsive
            result = build_output(text, english, spanish, english_first, numbers, set_status)
            root.after(0, lambda: show_result(result))

        threading.Thread(target=work, daemon=True).start()

    def copy_all():
        text = out.get("1.0", "end-1c")
        if text:
            root.clipboard_clear()
            root.clipboard_append(text)
            status.config(text="Copied to clipboard.")

    btn_go.config(command=go)
    btn_copy.config(command=copy_all)
    entry.bind("<Return>", go)
    root.mainloop()


if __name__ == "__main__":
    if sys.argv[1:] == ["--version"]:
        print(__version__)
    elif len(sys.argv) > 1:
        sys.stdout.reconfigure(encoding="utf-8")
        print(build_output(" ".join(sys.argv[1:])), end="")
    else:
        run_gui()
