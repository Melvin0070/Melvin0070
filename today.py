#!/usr/bin/env python3
"""
today.py  —  Andrew6rant-style animated neofetch profile generator.

Builds dark_mode.svg + light_mode.svg (self-contained, CSS-animated) and a
README.md that embeds them responsively. Stats can be static (from CONFIG) or
pulled live from the GitHub GraphQL API when a token is present.

Run locally:      python3 today.py
Run with stats:   ACCESS_TOKEN=<pat> GITHUB_USER=Melvin0070 python3 today.py
"""

import os
import json
import datetime
from urllib import request as urlrequest

# ────────────────────────────────────────────────────────────────────────────
#  CONFIG — edit this block. Everything the profile shows lives here.
# ────────────────────────────────────────────────────────────────────────────
CONFIG = {
    "user":   "melvin",
    "host":   "kannan",
    "ascii":  "me.txt",                 # ascii portrait file (100 cols)
    "title":  "melvin@kannan: ~",       # terminal titlebar text
    "command": "neofetch --ascii me.png",
    "info": [                            # ("kv", label, value) | ("hdr", text) | ("rule",) | ("blank",)
        ("kv", "OS",     "macOS 14, Android 17"),
        ("kv", "Uptime", "21 years, 2 months, 5 days"),
        ("kv", "Host",   "XavierAI"),
        ("kv", "School", "Kalvium"),
        ("kv", "Kernel", "Software Engineer"),
        ("kv", "Editor", "VS Code"),
        ("blank",),
        ("kv", "Languages.Programming", "Python, TypeScript, Rust"),
        ("kv", "Stack.Frontend",        "HTML, CSS, React, Tailwind"),
        ("kv", "Languages.Spoken",      "English, Hindi, Tamil, Malayalam"),
        ("blank",),
        ("kv", "Hobbies.Software", "Open Source"),
        ("kv", "Hobbies.Hardware", "IEMs, Laptops, Tuning & Optimizing"),
        ("kv", "Hobbies.Offline",  "Guitar, Chess"),
        ("blank",),
        ("hdr", "Contact"),
        ("rule",),
        ("blank",),
        ("kv", "Email",     "Melvin.aspirant@gmail.com"),
        ("kv", "LinkedIn",  "in/melvin-kannan-800196283"),
        ("kv", "Instagram", "melvin_kannan"),
        ("kv", "GitHub",    "Melvin0070"),
        ("blank",),
        ("hdr", "GitHub Stats"),
        ("rule",),
        ("blank",),
        ("two", "Repos",   "18",      "Stars",     "34"),
        ("two", "Commits", "1,286",   "Followers", "27"),
        ("loc", "Lines of Code", "142,530", "196,470", "53,940"),
    ],
    # repo where the svgs live (used for the README embed urls)
    "gh_user": "Melvin0070",
    "gh_repo": "Melvin0070",
}

INFO_W = 54  # info-panel column width (values right-align to here)

# ── theme palettes ──────────────────────────────────────────────────────────
DARK = dict(bg="#17181c", bar="#202227", border="#2e3137",
            title="#8b929c", fg="#c9d0d8", dim="#5b626c", portrait="#aab1bd",
            cyan="#6cc0ff", green="#7ee787", red="#ff7b72", value="#f0f3f7",
            label="#c9d0d8", puser="#7ee787", ppath="#6cc0ff")
LIGHT = dict(bg="#ffffff", bar="#f0f2f5", border="#d0d7de",
             title="#0969da", fg="#24292f", dim="#8c959f", portrait="#57606a",
             cyan="#0969da", green="#1a7f37", red="#cf222e", value="#24292f",
             label="#0969da", puser="#1a7f37", ppath="#0969da")
DOTS = ("#ff5f56", "#ffbd2e", "#27c93f")  # mac traffic lights (both themes)

# ── geometry ────────────────────────────────────────────────────────────────
FT_P, LH_P, CW_P = 7, 7, 4.2       # portrait font / line-height / char-width
FT_I, LH_I, CW_I = 10, 13, 6.0     # info panel
FT_PR = 11                          # prompt
PAD, BAR = 18, 34
GUTTER = 34


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ────────────────────────────────────────────────────────────────────────────
#  OPTIONAL live stats — fills repos/stars/followers/commits if a token exists.
#  (LOC with +/- is intentionally left to CONFIG; counting it needs a full
#   per-repo history crawl, exactly like Andrew6rant's heavier today.py.)
# ────────────────────────────────────────────────────────────────────────────
def fetch_live_stats():
    token = os.environ.get("ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    user = os.environ.get("GITHUB_USER", CONFIG["gh_user"])
    if not token:
        return None
    q = """
    query($login:String!){
      user(login:$login){
        followers{totalCount}
        repositories(ownerAffiliations:OWNER, first:100){totalCount nodes{stargazerCount}}
        contributionsCollection{totalCommitContributions}
      }
    }"""
    body = json.dumps({"query": q, "variables": {"login": user}}).encode()
    req = urlrequest.Request("https://api.github.com/graphql", data=body,
                             headers={"Authorization": f"bearer {token}",
                                      "Content-Type": "application/json"})
    try:
        with urlrequest.urlopen(req, timeout=20) as r:
            d = json.load(r)["data"]["user"]
        stars = sum(n["stargazerCount"] for n in d["repositories"]["nodes"])
        return {
            "Repos": f'{d["repositories"]["totalCount"]:,}',
            "Stars": f"{stars:,}",
            "Followers": f'{d["followers"]["totalCount"]:,}',
            "Commits": f'{d["contributionsCollection"]["totalCommitContributions"]:,}',
        }
    except Exception as e:
        print("live stats unavailable:", e)
        return None


def apply_live(info, live):
    if not live:
        return info
    out = []
    for row in info:
        if row[0] == "two":
            _, l1, v1, l2, v2 = row
            v1 = live.get(l1, v1); v2 = live.get(l2, v2)
            out.append(("two", l1, v1, l2, v2))
        else:
            out.append(row)
    return out


# ── info-row → list of (text, colorkey) tspans, right-aligned to INFO_W ──────
def kv_segs(label, value, width=INFO_W):
    disp = label + ":"
    dots = max(width - len(disp) - 2 - len(value), 1)
    return [(disp, "label"), (" ", "fg"), ("\u00b7" * dots, "dim"),
            (" ", "fg"), (value, "value")]


def row_segs(row):
    t = row[0]
    if t == "blank":
        return []
    if t == "hdr":
        return [(row[1], "cyan")]
    if t == "rule":
        return [("\u2500" * INFO_W, "dim")]
    if t == "user":
        return [(CONFIG["user"], "cyan"), ("@", "fg"), (CONFIG["host"], "cyan")]
    if t == "kv":
        return kv_segs(row[1], row[2])
    if t == "two":
        half = (INFO_W - 3) // 2
        return kv_segs(row[1], row[2], half) + [(" ", "fg"), ("\u2502", "dim"),
               (" ", "fg")] + kv_segs(row[3], row[4], half)
    if t == "loc":
        _, label, total, plus, minus = row
        val_plain = f"{total} ( {plus}++, {minus}-- )"
        disp = label + ":"
        dots = max(INFO_W - len(disp) - 2 - len(val_plain), 1)
        return [(disp, "label"), (" ", "fg"), ("\u00b7" * dots, "dim"), (" ", "fg"),
                (f"{total} ( ", "value"), (f"{plus}++", "green"),
                (", ", "value"), (f"{minus}--", "red"), (" )", "value")]
    return []


def build_svg(theme, ascii_lines):
    C = theme
    info_rows = [("user",), ("rule",)] + [("blank",)] + apply_live(CONFIG["info"], LIVE)

    ph = len(ascii_lines)
    pw_cols = max(len(l) for l in ascii_lines)
    pw_px = pw_cols * CW_P
    info_x = PAD + pw_px + GUTTER

    prompt1_y = BAR + 22
    col_top = prompt1_y + 20
    p_first = col_top + FT_P
    i_first = col_top + 4 + FT_I

    p_last = p_first + (ph - 1) * LH_P
    i_last = i_first + (len(info_rows) - 1) * LH_I
    bottom_y = max(p_last, i_last) + 26
    W = int(info_x + INFO_W * CW_I + PAD)
    H = int(bottom_y + PAD)

    def col(key):
        return {"fg": C["fg"], "dim": C["dim"], "label": C["label"], "value": C["value"],
                "cyan": C["cyan"], "green": C["green"], "red": C["red"]}.get(key, C["fg"])

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
                 f'viewBox="0 0 {W} {H}" fill="none" font-family="\'Courier New\',Courier,monospace">')
    parts.append(f'''<style>
  @keyframes fadein {{ from {{ opacity:0 }} to {{ opacity:1 }} }}
  @keyframes blink  {{ 0%,49% {{ opacity:1 }} 50%,100% {{ opacity:0 }} }}
  .r {{ opacity:1; animation:fadein .45s ease forwards both; }}
  .cur {{ animation:blink 1s step-end infinite; animation-delay:2.9s; }}
  text {{ white-space:pre; }}
</style>''')

    # window
    parts.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="9" '
                 f'fill="{C["bg"]}" stroke="{C["border"]}"/>')
    parts.append(f'<path d="M0.5,{BAR} V9 A8.5,8.5 0 0 1 9,0.5 H{W-9} '
                 f'A8.5,8.5 0 0 1 {W-0.5},9 V{BAR} Z" fill="{C["bar"]}" stroke="{C["border"]}"/>')
    for i, dc in enumerate(DOTS):
        parts.append(f'<circle cx="{18+i*18}" cy="{BAR/2:.0f}" r="5.5" fill="{dc}"/>')
    parts.append(f'<text x="{W/2:.0f}" y="{BAR/2+4:.0f}" text-anchor="middle" '
                 f'font-size="11" fill="{C["dim"]}">{esc(CONFIG["title"])}</text>')

    # top prompt line
    parts.append(f'<text class="r" style="animation-delay:.1s" x="{PAD}" y="{prompt1_y}" font-size="{FT_PR}">'
                 f'<tspan fill="{C["puser"]}">{CONFIG["user"]}@{CONFIG["host"]}</tspan>'
                 f'<tspan fill="{C["fg"]}">:</tspan><tspan fill="{C["ppath"]}">~</tspan>'
                 f'<tspan fill="{C["fg"]}">$ {esc(CONFIG["command"])}</tspan></text>')

    # portrait
    for i, line in enumerate(ascii_lines):
        y = p_first + i * LH_P
        d = 0.35 + i * 0.010
        parts.append(f'<text class="r" style="animation-delay:{d:.3f}s" x="{PAD}" '
                     f'y="{y:.1f}" font-size="{FT_P}" fill="{C["portrait"]}">{esc(line)}</text>')

    # info panel
    n_port = len(ascii_lines)
    info_start_delay = 0.35 + n_port * 0.010 + 0.15
    for j, row in enumerate(info_rows):
        segs = row_segs(row)
        if not segs:
            continue
        y = i_first + j * LH_I
        d = info_start_delay + j * 0.05
        tspans = "".join(f'<tspan fill="{col(k)}">{esc(tx)}</tspan>' for tx, k in segs)
        parts.append(f'<text class="r" style="animation-delay:{d:.3f}s" x="{info_x:.0f}" '
                     f'y="{y:.1f}" font-size="{FT_I}">{tspans}</text>')

    # bottom prompt + blinking cursor
    by = bottom_y
    parts.append(f'<text class="r" style="animation-delay:2.7s" x="{PAD}" y="{by:.0f}" font-size="{FT_PR}">'
                 f'<tspan fill="{C["puser"]}">{CONFIG["user"]}@{CONFIG["host"]}</tspan>'
                 f'<tspan fill="{C["fg"]}">:</tspan><tspan fill="{C["ppath"]}">~</tspan>'
                 f'<tspan fill="{C["fg"]}">$ </tspan></text>')
    cur_x = PAD + len(f'{CONFIG["user"]}@{CONFIG["host"]}:~$ ') * (FT_PR * 0.6)
    parts.append(f'<rect class="cur" x="{cur_x:.1f}" y="{by-FT_PR:.1f}" width="{FT_PR*0.6:.1f}" '
                 f'height="{FT_PR:.1f}" fill="{C["fg"]}"/>')

    parts.append("</svg>")
    return "\n".join(parts)


def build_readme():
    u, r = CONFIG["gh_user"], CONFIG["gh_repo"]
    base = f"https://raw.githubusercontent.com/{u}/{r}/main"
    return (
        f'<a href="https://github.com/{u}">\n'
        f'  <picture>\n'
        f'    <source media="(prefers-color-scheme: dark)" srcset="{base}/dark_mode.svg">\n'
        f'    <source media="(prefers-color-scheme: light)" srcset="{base}/light_mode.svg">\n'
        f'    <img alt="{CONFIG["user"]}@{CONFIG["host"]}" src="{base}/light_mode.svg">\n'
        f'  </picture>\n'
        f'</a>\n'
    )


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, CONFIG["ascii"])) as f:
        raw = [ln.rstrip("\n") for ln in f]
    while raw and not raw[0].strip():
        raw.pop(0)
    while raw and not raw[-1].strip():
        raw.pop()
    left = min((len(l) - len(l.lstrip(" ")) for l in raw if l.strip()), default=0)
    ascii_lines = [l[left:] for l in raw]
    width = max(len(l) for l in ascii_lines)
    ascii_lines = [l.ljust(width) for l in ascii_lines]

    LIVE = fetch_live_stats()
    globals()["LIVE"] = LIVE

    for name, theme in (("dark_mode.svg", DARK), ("light_mode.svg", LIGHT)):
        svg = build_svg(theme, ascii_lines)
        with open(os.path.join(here, name), "w") as f:
            f.write(svg)
        print("wrote", name)

    with open(os.path.join(here, "README.md"), "w") as f:
        f.write(build_readme())
    print("wrote README.md at", datetime.datetime.now().isoformat(timespec="seconds"))
