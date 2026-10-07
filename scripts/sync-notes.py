#!/usr/bin/env python3
"""Copy the spoken text from TALK.md into each slide's <aside class="notes"> in index.html.

TALK.md is the source of truth for the script; run this after editing it:
    python3 scripts/sync-notes.py
Section numbers in TALK.md map to slides as listed in SLIDES below. The old timing
marker "(mm:ss)" of a note is preserved as a trailing ⏱ line.
"""
import re, html, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
talk = (ROOT / "TALK.md").read_text(encoding="utf-8")
page = (ROOT / "index.html").read_text(encoding="utf-8")

# section number -> (section id, vertical index or None)
SLIDES = {
    "1": ("title", None), "2": ("disclaimer", None), "3": ("about", None), "4": ("origin", None), "5": ("bridge-meme", None),
    "6": ("takeaways", None), "7": ("setup", None), "8": ("why-banned", None),
    "9": ("fixes", None), "10": ("chips-jar", None),
    "11": ("constraints", None), "12": ("realisation", None), "13": ("flow", None), "14": ("shape", None),
    "15": ("demo", None), "16": ("invariants", 0),
    **{f"16.{i}": ("invariants", i) for i in range(1, 8)},
    "17": ("seam", 0), **{f"17.{i}": ("seam", i) for i in range(1, 3)},
    "18": ("opener", None), "19": ("grows", None), "20": ("constraints-done", None),
    "21": ("credits", None), "22": ("thanks", None),
}

# --- parse TALK.md into {number: body} ---
sections = {}
cur = None
for line in talk.splitlines():
    m = re.match(r"^#{2,3} (\d+(?:\.\d+)?) · (.*)$", line)
    if m:
        cur = m.group(1); sections[cur] = []
        continue
    if line.startswith("## Appendix"):
        cur = None
    if cur is not None:
        sections[cur].append(line)

def md_to_html(body):
    text = "\n".join(body).strip()
    text = re.sub(r"^---\s*$", "", text, flags=re.M)
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    out = []
    for p in paras:
        p = html.escape(p, quote=False)
        p = re.sub(r"`([^`]+)`", r"<code>\1</code>", p)
        p = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", p)
        p = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?!\w)", r"<i>\1</i>", p)
        p = p.replace("\n", "<br>")
        out.append(f"<p>{p}</p>")
    return "\n\t\t".join(out)

# --- locate each slide's <aside> and replace ---
def find_section_span(doc, sid):
    m = re.search(rf'<section id="{re.escape(sid)}"[^>]*>', doc)
    start = m.start()
    # end: next top-level <section id= or end of slides
    nxt = re.search(r'\n<section id=', doc[m.end():])
    end = m.end() + nxt.start() if nxt else doc.index("\n</div>\n</div>")
    return start, end

updated = page
count = 0
for num, (sid, vidx) in SLIDES.items():
    if num not in sections:
        print("no script for", num, sid); continue
    s, e = find_section_span(updated, sid)
    block = updated[s:e]
    # for a vertical stack, inner[0] is the outer <section> tag; inner[v+1] is vertical slide v
    inner = re.split(r"(?=\n\t<section)", block) if vidx is not None else [block]
    target = inner[vidx + 1] if vidx is not None else block
    old_note = re.search(r"<aside class=\"notes\">(.*?)</aside>", target, re.S)
    timing = re.search(r"\((\d{1,2}:\d{2})\)", old_note.group(1)) if old_note else None
    note = md_to_html(sections[num])
    if timing:
        note += f"\n\t\t<p>⏱ {timing.group(1)}</p>"
    new_aside = f'<aside class="notes">\n\t\t{note}\n\t</aside>'
    if old_note:
        new_target = target[:old_note.start()] + new_aside + target[old_note.end():]
    else:
        new_target = target.replace("</section>", "\t" + new_aside + "\n</section>", 1)
    if vidx is not None:
        inner[vidx + 1] = new_target
        new_block = "".join(inner)
    else:
        new_block = new_target
    updated = updated[:s] + new_block + updated[e:]
    count += 1

(ROOT / "index.html").write_text(updated, encoding="utf-8")
print(f"synced {count} notes")
