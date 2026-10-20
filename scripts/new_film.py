# -*- coding: utf-8 -*-
"""建一个新片工程：
  python new_film.py <工程目录> --world C|B [--size WxH] [--secs N] [--force]
C 夜曲（抽象概念、看不见的机制）· B 寓言（心理和行为机制）。怎么选见 references/worlds.md。

画幅：默认 16:9 横屏 1920×1080；要竖屏/方形用 --size，如 --size 1080x1920、--size 1080x1080。
时长：默认取自带 BGM(assets/default_bgm.mp3)的时长——让"BGM 放完视频就结尾"；用 --secs 覆盖。

工程里是 index.html 和一份只能跑起来的 film.js 骨架——里面一行画面都没有。
文案不同，屏上的东西就不同，代码也不同：每一镜照 storyboard.md 现写，不要从别的片子里搬画面。
引擎留在 skill 目录里，由 engine/render.py 挂载。"""
import shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BGM = ROOT / "assets" / "default_bgm.mp3"
WORLD = {   # 外观名、theme、字幕样式、色板、这套外观的常驻元素（都在 vk-kit.js，用法见 references/engine.md）
    "B": ("B 寓言", "flat", "flat", "flat", "仪表 K.gauge、片名卡 K.titleGilt；场景自己画进 fr.look.under"),
    "C": ("C 夜曲", "night", "night", "night", "章节标 K.chapterMark、片名卡 K.titleNight；字幕带一行英文（en）"),
}
SKELETON = """/* ★ 片名 · {name}
 * 这是骨架，一行画面都没有。每一镜照 storyboard.md 现写——文案不同，屏上的东西就不同。
 * 每个场景的函数头上先写一行：这是什么（日常的词）/ 它在干什么（一个动词）/ 观众明白了什么。
 * 事实和出处、哪些是示意，写在这段注释里。
 * 画幅 {w}×{h}；时长 {dur}s（默认对齐自带 BGM，让 BGM 放完视频就结尾）。坐标都用 W/H，换画幅不必重写。
 * 这套外观的常驻元素：{standing}。规格见 references/worlds.md。 */
(function () {{
'use strict';
const {{ clamp, lerp, seg, smooth, ss, E, fade, hash, rng, rgba, mix }} = VK;
const W = {w}, H = {h};                                     // 画幅：画面坐标都相对 W/H，竖屏/方形改 --size 即可
const K = VKit, P = K.PAL.{pal};

const T = {{ end: {dur} }};                                 // 关键时刻集中写在这里，挪动时只改一处；end 默认=BGM 时长
const SUBS = [                                             // 一句字幕一行，和分镜表对着写；{{词}} 金色，{{!词}} 红色
  // {{ a: 0.8, b: 4.2, zh: '……'{en} }},
];

/* 一个场景一个函数，自己管自己的进场和退场。 */
function scene1(fr, t) {{
}}

VK.film({{
  dur: T.end, w: W, h: H, theme: '{theme}', meta: {{ title: '' }},
  // 卡点：先 python engine/audio.py <工程> --beats 量 BGM 的 BPM/小节头/段落，把场景关键时刻对到 audio/bgm_beats.json 的 downbeats/sections。
  draw(fr, t) {{
    scene1(fr, t);
    K.subs(fr, t, SUBS, '{subs}');                         // 字幕永远最后画，压在一切之上
  }},
}});
}})();
"""

def bgm_seconds():
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(DEFAULT_BGM)], capture_output=True, text=True)
        return round(float(r.stdout.strip()), 2)
    except Exception:
        return None

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 1 or a[0].startswith("-"): sys.exit(__doc__)
    proj = Path(a[0]).resolve(); world = (a[a.index("--world") + 1] if "--world" in a else "C").upper()
    if world not in WORLD: sys.exit("--world 只能是 C 或 B")
    w, h = 1920, 1080
    if "--size" in a:
        try: w, h = (int(v) for v in a[a.index("--size") + 1].lower().split("x"))
        except Exception: sys.exit("--size 形如 1080x1920")
    if "--secs" in a: dur = float(a[a.index("--secs") + 1])
    else: dur = bgm_seconds() or 30
    proj.mkdir(parents=True, exist_ok=True)
    film = proj / "film.js"
    if film.exists() and "--force" not in a: sys.exit(f"{film} 已经存在。要覆盖加 --force")
    name, theme, subs, pal, standing = WORLD[world]
    shutil.copy(ROOT / "engine/index.html", proj / "index.html")
    film.write_text(SKELETON.format(name=name, theme=theme, subs=subs, pal=pal, standing=standing,
                                    w=w, h=h, dur=dur, en=", en: '……'" if world == "C" else ""),
                    encoding="utf-8", newline="\n")
    render = ROOT / "engine/render.py"; audio = ROOT / "engine/audio.py"
    print(f"建好了：{proj}（{name}，{w}×{h}，{dur}s）\n"
          f"  量拍点  python \"{audio}\" \"{proj}\" --beats        # 先看 BGM 的小节头 / 段落,写分镜时对齐\n"
          f"  预览    python \"{render}\" \"{proj}\" --serve\n"
          f"  拼图    python \"{render}\" \"{proj}\" --sheet 16\n"
          f"  渲染    python \"{render}\" \"{proj}\"\n"
          f"  声音    python \"{render}\" \"{proj}\" --events && python \"{audio}\" \"{proj}\"   # 默认叠自带 BGM\n"
          f"  封面    python \"{render}\" \"{proj}\" --cover <时刻>\n"
          f"下一步：film.js 里现在一行画面都没有。照 storyboard.md，从最难画的那一镜写起。")
