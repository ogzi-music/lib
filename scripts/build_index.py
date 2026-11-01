#!/usr/bin/env python3
"""Generate hierarchical index.html pages for the published sample library.

Expected site layout (as produced by the workflow's collect step):

    index.toml                   library manifest: [group] / id = "Name"
    <group>/<id>.toml            instrument definition with [[samples]]
    <group>/<id>/<file>.flac     sample audio

Writes:

    index.html                    links to every group
    <group>/index.html            links to every instrument
    <group>/<id>/index.html       instrument details + links to flac files

Usage: build_index.py <site-dir>
"""

from __future__ import annotations

import html
import sys
import tomllib
import urllib.parse
from pathlib import Path

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
CHANNEL_NAMES = {1: "mono", 2: "stereo"}

CSS = (
    "body{font-family:system-ui,sans-serif;max-width:64em;margin:2em auto;"
    "padding:0 1em;line-height:1.5;color:#222}\n"
    "a{color:#0366d6}\n"
    "table{border-collapse:collapse;width:100%;margin:1em 0}\n"
    "th,td{border:1px solid #ddd;padding:.3em .6em;text-align:left;vertical-align:middle}\n"
    "audio{height:2em;vertical-align:middle}\n"
    ".crumbs{color:#666}\n"
    ".meta{display:flex;flex-wrap:wrap;gap:.4em 2em;margin:1em 0}\n"
    ".meta dt{font-weight:600}\n"
    ".meta dd{margin:0}\n"
    ".missing{color:#c00}\n"
    "small{color:#666}\n"
)


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def href(path) -> str:
    return urllib.parse.quote(str(path))


def note(midi: int) -> str:
    """MIDI note number to name (60 -> C4)."""
    return f"{NOTE_NAMES[int(midi) % 12]}{int(midi) // 12 - 1}"


def key_span(sample: dict):
    """(lo, hi) key span covered by a sample, or None."""
    lo = sample.get("key-from", sample.get("key"))
    hi = sample.get("key-to", sample.get("key"))
    if lo is None or hi is None:
        return None
    return int(lo), int(hi)


def fmt_seconds(length, frequency) -> str:
    if not frequency or not isinstance(length, (int, float)):
        return ""
    secs = length / frequency
    return f"{secs:.2f} s" if secs < 10 else f"{secs:.1f} s"


def page(title: str, body: str) -> str:
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        f'<meta charset="utf-8">\n<title>{esc(title)}</title>\n'
        f"<style>{CSS}</style>\n</head>\n<body>\n{body}</body>\n</html>\n"
    )


def instrument_page(site: Path, group: str, inst: str) -> bool:
    """Write <group>/<inst>/index.html. Returns True if the page was written."""
    idir = site / group / inst
    if not idir.is_dir():
        return False
    toml_path = site / group / f"{inst}.toml"

    data = {}
    if toml_path.is_file():
        data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    samples = data.get("samples", [])
    name = data.get("name") or inst

    meta = []
    if data.get("id"):
        meta.append(("id", data["id"]))
    if data.get("group"):
        meta.append(("group", data["group"]))
    if data.get("midi-program") is not None:
        meta.append(("midi-program", data["midi-program"]))
    meta.append(("samples", len(samples)))

    spans = [sp for sp in (key_span(s) for s in samples) if sp]
    if spans:
        lo = min(s for s, _ in spans)
        hi = max(h for _, h in spans)
        meta.append(("key range", f"{note(lo)}\u2013{note(hi)} ({lo}\u2013{hi})"))

    freqs = sorted({s["frequency"] for s in samples if "frequency" in s})
    bits = sorted({s["bit-depth"] for s in samples if "bit-depth" in s})
    chs = sorted({s["channels"] for s in samples if "channels" in s})
    modes = sorted({s["mode"] for s in samples if s.get("mode")})
    fmt = []
    if freqs:
        fmt.append(f"{freqs[0]} Hz" if len(freqs) == 1 else f"{freqs[0]}\u2013{freqs[-1]} Hz")
    if bits:
        fmt.append(" / ".join(f"{b}-bit" for b in bits))
    if chs:
        fmt.append(" / ".join(CHANNEL_NAMES.get(c, str(c)) for c in chs))
    if modes:
        fmt.append(" / ".join(modes))
    if fmt:
        meta.append(("format", " \u00b7 ".join(fmt)))

    crumbs = (
        f'<p class="crumbs"><a href="../../index.html">lib</a> / '
        f'<a href="../index.html">{esc(group)}</a> / {esc(inst)}</p>\n'
    )
    meta_html = (
        f"<h1>{esc(name)}</h1>\n"
        + '<dl class="meta">\n'
        + "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>\n" for k, v in meta)
        + "</dl>\n"
    )
    toml_html = (
        f'<p><a href="../{href(inst)}.toml">{esc(inst)}.toml</a>'
        " \u2014 instrument definition</p>\n"
        if toml_path.is_file()
        else ""
    )

    rows = []
    for s in samples:
        f = s.get("file", "")
        present = bool(f) and (idir / f).is_file()
        link = f'<a href="{href(f)}">{esc(f)}</a>' if present else f'<span class="missing">{esc(f)}</span>'
        key = s.get("key")
        keycell = f"{key} ({note(key)})" if key is not None else ""
        sp = key_span(s)
        if sp:
            lo, hi = sp
            rangehtml = f"{lo} ({note(lo)})" if lo == hi else f"{lo}\u2013{hi} ({note(lo)}\u2013{note(hi)})"
        else:
            rangehtml = ""
        audio = f'<audio controls preload="none" src="{href(f)}"></audio>' if present else ""
        rows.append(
            f"<tr><td>{link}</td><td>{esc(keycell)}</td><td>{esc(rangehtml)}</td>"
            f"<td>{esc(s.get('level', ''))}</td><td>{esc(s.get('mode', ''))}</td>"
            f"<td>{esc(fmt_seconds(s.get('length'), s.get('frequency')))}</td>"
            f"<td>{audio}</td></tr>\n"
        )

    listed = {s.get("file") for s in samples}
    for f in sorted(idir.glob("*.flac")):
        if f.name not in listed:  # on disk but not described in the toml
            rows.append(
                f'<tr><td><a href="{href(f.name)}">{esc(f.name)}</a></td>'
                "<td></td><td></td><td></td><td></td><td></td>"
                f'<td><audio controls preload="none" src="{href(f.name)}"></audio></td></tr>\n'
            )

    table = (
        "<table>\n<tr><th>file</th><th>key</th><th>range</th><th>level</th>"
        "<th>mode</th><th>length</th><th>play</th></tr>\n" + "".join(rows) + "</table>\n"
    )

    body = crumbs + meta_html + toml_html + table
    (idir / "index.html").write_text(
        page(f"{name} \u2014 ogzi-music/lib", body), encoding="utf-8"
    )
    return True


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <site-dir>", file=sys.stderr)
        return 2
    site = Path(sys.argv[1])
    if not site.is_dir():
        print(f"error: {site} is not a directory", file=sys.stderr)
        return 2

    manifest = {}
    manifest_path = site / "index.toml"
    if manifest_path.is_file():
        manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))

    # Group order: manifest order first, then any unexpected directories.
    group_dirs = sorted(p.name for p in site.iterdir() if p.is_dir())
    ordered_groups = [g for g in manifest if (site / g).is_dir()]
    ordered_groups += [g for g in group_dirs if g not in manifest]

    root_items = []
    n_instruments = 0
    n_samples = 0

    for group in ordered_groups:
        gdir = site / group
        names = manifest.get(group, {})

        for inst in names:
            if not (gdir / inst).is_dir() and not (gdir / f"{inst}.toml").is_file():
                print(f"warning: {group}/{inst} in manifest but missing on disk", file=sys.stderr)

        # Instrument order: manifest order first, then any unexpected dirs.
        inst_dirs = sorted(p.name for p in gdir.iterdir() if p.is_dir())
        ordered = [i for i in names if (gdir / i).is_dir() or (gdir / f"{i}.toml").is_file()]
        ordered += [i for i in inst_dirs if i not in names]

        items = []
        for inst in ordered:
            name = names.get(inst) or inst
            if (gdir / inst).is_dir():
                if instrument_page(site, group, inst):
                    n_instruments += 1
                    n_flac = sum(1 for _ in (gdir / inst).glob("*.flac"))
                    n_samples += n_flac
                    items.append(
                        f'<li><a href="{href(inst)}/">{esc(name)}</a> '
                        f"<small>{esc(inst)} \u00b7 {n_flac} samples</small></li>"
                    )
            elif (gdir / f"{inst}.toml").is_file():
                items.append(
                    f'<li><a href="{href(inst)}.toml">{esc(name)}</a> '
                    f"<small>{esc(inst)} \u00b7 definition only</small></li>"
                )

        # toml files with no manifest entry and no samples dir
        for t in sorted(gdir.glob("*.toml")):
            if t.stem not in ordered:
                items.append(f'<li><a href="{href(t.name)}">{esc(t.stem)}</a> <small>.toml</small></li>')

        body = (
            f'<p class="crumbs"><a href="../index.html">lib</a> / {esc(group)}</p>\n'
            f"<h1>{esc(group)}</h1>\n"
            f"<p>{len(items)} instruments</p>\n<ul>\n" + "\n".join(items) + "\n</ul>\n"
        )
        (gdir / "index.html").write_text(
            page(f"{group} \u2014 ogzi-music/lib", body), encoding="utf-8"
        )
        root_items.append(f'<li><a href="{href(group)}/">{esc(group)}</a> <small>({len(items)})</small></li>')

    body = (
        "<h1>ogzi-music/lib</h1>\n"
        f"<p>{n_instruments} instruments \u00b7 {n_samples} samples</p>\n"
        '<p><a href="index.toml">index.toml</a> \u2014 library manifest</p>\n'
        "<ul>\n" + "\n".join(root_items) + "\n</ul>\n"
    )
    (site / "index.html").write_text(page("ogzi-music/lib", body), encoding="utf-8")

    print(
        f"index: {len(ordered_groups)} groups, {n_instruments} instruments, "
        f"{n_samples} samples, {1 + len(ordered_groups) + n_instruments} pages"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
