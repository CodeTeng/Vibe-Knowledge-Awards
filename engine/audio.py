# -*- coding: utf-8 -*-
"""按画面事件表合成配乐和音效，再和画面合成成片。
  python audio.py <工程目录>                       # 默认用自带 BGM(assets/default_bgm.mp3)垫底 + 事件音 → renders/final.mp4
  python audio.py <工程目录> --bgm 曲子.mp3 [-8]   # 指定配乐垫底（默认 -8 dB），事件音照叠
  python audio.py <工程目录> --no-bgm              # 不要 BGM，只用合成的事件音 / 床
  python audio.py <工程目录> --beats               # 分析 BGM 的 BPM/拍点/段落 → audio/bgm_beats.json + .png（用于卡点）
  python audio.py <工程目录> --bed                 # 合成一层 76–78BPM 的持续节拍织体（床）垫底，事件音叠在上面
  python audio.py <工程目录> --dense               # 爆款那种"满"：床 + 不留白（关 hush）+ 响一点（-14 LUFS）
  python audio.py <工程目录> --no-hush             # 不执行 hush 彻底静音（保留留白但不全静）
  python audio.py <工程目录> --lufs -12            # 指定成片响度（默认：合成 -18、带床/dense -14、外来 BGM -14）
  python audio.py <工程目录> --probe               # 导出音轨体检图 audio/probe.png（波形 + 频段能量 + 事件时间线）
  python audio.py <工程目录> --wav-only            # 只出 wav，不合成

事件表由 render.py --events 导出：film.js 里每个 fr.sfx(时刻, 名字, 参数) 就是一条。
声音的写法学自参考片：
  C 夜曲（稀疏留白派）：低频长音垫底 · 每章一记带泛音的钟/垫和弦 · 屏上每打一个字一声"嗒" ·
    提问处上滑音 · 说到噪声就铺噪声 · 定理落地后 hush 2–3 秒彻底静音。整体安静（约 -18 LUFS）。
  爆款知识大赏（密集织体派，如《内卷的天平》）：全片几乎无静音、-10dB 上下、76BPM 脉冲 + 不断的
    shaker 颗粒织体垫底，事件重音叠在床上，段落随叙事起伏。要这种质感就加 --bed / --dense。

事件名：tick / soft / chord / bloom / rise / thud / tock / stamp / shimmer / hush（参数 dur，秒）
META（film.js 的 meta）：{ root: 半音偏移, noise: [[起,止,强度0..1],...], silence: [[起,止],...], drone: 0..1,
  bed: { bpm: 77, key: 'Am'|'Dm'|'Em', gain: 1.0, sections: '0,8,pad;8,40,full;...' } }
  bed 的段落织体从轻到满：pad < piano < full < arp < outro。写了 bed 字段就默认合成床（无需 --bed）。
  床是连续的音乐垫底，不受 hush / silence 门控——这正是"爆款从不留白"的来源。
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from scipy.signal import fftconvolve, lfilter, butter

SR = 48000
D3 = 146.83
PENTA = [0, 2, 4, 7, 9, 12, 14, 16, 19, 21]           # 大调五声，嗒声从这里取音高
CHORD = [0, 7, 12, 14, 19, 24, 26]                   # 根音、五度、八度、九度…… 叠成"开阔"的和弦
KEY_TONIC = {"Am": 7, "Dm": 0, "Em": 2}              # 相对 D3 基准的主音半音偏移（床的调）
DEFAULT_BGM = Path(__file__).resolve().parent.parent / "assets" / "default_bgm.mp3"   # 没指定 --bgm 时默认用它

def hz(semi, base=D3): return base * 2 ** (semi / 12)
def env_exp(n, tau, attack=0.004):
    t = np.arange(n) / SR
    return np.minimum(1, t / attack) * np.exp(-t / tau)
def soft_onset(n, rise):                              # 等功率 S 形淡入：把"从静音里瞬间满响"软化成缓起，专治大事件的"炸"
    e = np.ones(n); r = min(int(rise * SR), n)
    if r > 0: e[:r] = np.sin(np.linspace(0, np.pi / 2, r)) ** 2
    return e
def lowpass(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2), "low"); return lfilter(b, a, x, axis=0)
def highpass(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2), "high"); return lfilter(b, a, x, axis=0)
def pan(x, p):                                        # p: -1 左 … 1 右
    l, r = np.cos((p + 1) * np.pi / 4), np.sin((p + 1) * np.pi / 4); return np.stack([x * l, x * r], 1)
def add(buf, x, t):
    i = int(t * SR)
    if i >= len(buf) or i < 0: return
    n = min(len(x), len(buf) - i); buf[i:i + n] += x[:n]

def tone(f, dur, tau, partials=((1, 1.0),), attack=0.004, vib=0.0):
    n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros(n)
    for mult, amp in partials:
        ph = 2 * np.pi * f * mult * t + (vib * np.sin(2 * np.pi * 4.3 * t) if vib else 0)
        out += amp * np.sin(ph) * np.exp(-t / (tau / (1 + 0.35 * (mult - 1))))   # 高次泛音衰减更快
    return out * np.minimum(1, t / attack)

def ev_tick(rng, p):
    f = hz(PENTA[int(p.get("pitch", 0)) % len(PENTA)] + 24)
    x = tone(f, .5, .09, ((1, 1), (2.01, .28), (3.02, .1)), attack=.002)
    click = highpass(rng.standard_normal(int(.012 * SR)) * env_exp(int(.012 * SR), .003), 3000) * .25
    x[:len(click)] += click
    return pan(x * .16 * p.get("gain", 1), rng.uniform(-.35, .35))
def ev_soft(rng, p):
    return pan(tone(hz(12 + 7), 2.2, .7, ((1, 1), (2, .2)), attack=.03) * .12 * p.get("gain", 1), 0)
def ev_chord(rng, p):
    root = p.get("root", 0); n = int(9 * SR); out = np.zeros((n, 2))
    for k, semi in enumerate(CHORD):
        f = hz(root + semi); x = tone(f, 9, 2.6 - k * .12, ((1, 1), (2.003, .32), (3.01, .14), (4.02, .06)), attack=.012, vib=.6)
        out += pan(x * (.11 / (1 + k * .22)), (k % 3 - 1) * .5)
    sub = tone(hz(root - 12), 6, 2.2, ((1, 1),), attack=.02)
    out[:len(sub)] += pan(sub * .16, 0)
    out *= soft_onset(len(out), .18)[:, None]         # 整块大和弦从静音里缓起（~0.18s），不再"炸"地满响
    return out * p.get("gain", 1)
def ev_bloom(rng, p):                                 # 闪白：和弦 + 一口气的噪声扫过
    out = ev_chord(rng, {"root": p.get("root", 0), "gain": p.get("gain", 1)})
    n = int(1.6 * SR); ns = rng.standard_normal((n, 2)) * env_exp(n, .35, .05)[:, None]
    out[:n] += lowpass(highpass(ns, 500), 7000) * .1 * soft_onset(n, .12)[:, None]   # 噪声扫频也缓起，不在起点炸
    return out
def ev_rise(rng, p):                                  # 上滑音：提问、蓄势
    dur = p.get("dur", 1.0); n = int(dur * SR); t = np.arange(n) / SR
    f = hz(7) * 2 ** (t / dur * 1.0); ph = 2 * np.pi * np.cumsum(f) / SR
    e = np.sin(np.pi * np.minimum(1, t / dur) ** 1.6) ** 1.2
    ns = lowpass(rng.standard_normal(n), 2500) * (t / dur) ** 2 * .22
    return pan((np.sin(ph) * .1 + ns * .1) * e * p.get("gain", 1), 0)
def ev_thud(rng, p):
    n = int(.6 * SR); t = np.arange(n) / SR; f = 95 * np.exp(-t * 9) + 48
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, .13, .002) + lowpass(rng.standard_normal(n), 600) * env_exp(n, .04) * .5
    return pan(x * .42 * p.get("gain", 1), 0)
def ev_tock(rng, p):
    f = 520 * 2 ** (int(p.get("pitch", 0)) * 2 / 12); n = int(.25 * SR)
    x = tone(f, .25, .04, ((1, 1), (2.7, .4), (5.1, .15)), attack=.001) + highpass(rng.standard_normal(n), 2500) * env_exp(n, .006) * .3
    return pan(x * .2 * p.get("gain", 1), rng.uniform(-.5, .5))
def ev_stamp(rng, p):
    n = int(.5 * SR); x = ev_thud(rng, {"gain": 1.1})[:n, 0] + highpass(rng.standard_normal(n), 1800) * env_exp(n, .02) * .35
    return pan(x * p.get("gain", 1), 0)
def ev_shimmer(rng, p):
    n = int(2.4 * SR); t = np.arange(n) / SR; out = np.zeros(n)
    for k in range(7): out += np.sin(2 * np.pi * hz(24 + PENTA[k + 2]) * t + rng.uniform(0, 6)) * np.exp(-((t - .25 - k * .06) / .5) ** 2)
    return pan(out * .035 * p.get("gain", 1), 0)
EV = dict(tick=ev_tick, soft=ev_soft, chord=ev_chord, bloom=ev_bloom, rise=ev_rise, thud=ev_thud, tock=ev_tock, stamp=ev_stamp, shimmer=ev_shimmer)

def reverb(x, rng, t60=3.6, wet=.42):
    n = int(t60 * SR); t = np.arange(n) / SR
    ir = lowpass(rng.standard_normal((n, 2)) * np.exp(-6.9 * t / t60)[:, None], 5200); ir[:int(.012 * SR)] *= np.linspace(0, 1, int(.012 * SR))[:, None]
    ir /= np.sqrt((ir ** 2).sum(0)).max()
    wetsig = np.stack([fftconvolve(x[:, c], ir[:, c])[:len(x)] for c in (0, 1)], 1)
    return x + wetsig * wet

# ───────────────────────── 持续节拍织体（床 / bed）─────────────────────────
# 爆款的声音底色：76–78BPM 的小调进行（i–VI–III–VII），sub-bass pad 持续铺底 +
# 钢琴柱式和弦落在小节头 + 8 分音符 shaker 的颗粒织体 + 可选琶音。段落从轻到满随叙事起伏。
# 床连续不断，不受 hush/silence 门控——满、不留白，正是《内卷的天平》那类片子的质感。
PROG = [                                              # 相对主音的和弦音（半音）；bass 是该和弦的低音
    dict(bass=-24, notes=[0, 3, 7, 12]),              # i    （如 Am）
    dict(bass=-28, notes=[-4, 0, 3, 8]),              # VI   （F）
    dict(bass=-21, notes=[3, 7, 10, 15]),             # III  （C）
    dict(bass=-26, notes=[-2, 2, 5, 10]),             # VII  （G）
]
TEX_LVL = {"pad": .55, "piano": .75, "full": 1.0, "arp": .9, "outro": .5}

def bed_env(n, fin, fout):
    e = np.ones(n); fi = min(int(fin * SR), n // 2); fo = min(int(fout * SR), n // 2)
    if fi > 0: e[:fi] = np.linspace(0, 1, fi) ** 0.6
    if fo > 0: e[-fo:] *= np.linspace(1, 0, fo)
    return e
def bed_pad(f, dur):                                  # 持续、微失谐的 pad（合唱感）
    n = int(dur * SR); t = np.arange(n) / SR
    w = (np.sin(2 * np.pi * f * t) + .45 * np.sin(2 * np.pi * f * 1.004 * t)
         + .22 * np.sin(2 * np.pi * f * 2 * t) + .12 * np.sin(2 * np.pi * f * .5 * t))
    return w * bed_env(n, .9, .9)
def bed_shaker(rng, amp):
    n = int(.06 * SR); ns = highpass(rng.standard_normal(n), 5500)
    return ns * np.exp(-np.arange(n) / (n * .2)) * amp
def bed_kick(amp):
    n = int(.3 * SR); t = np.arange(n) / SR; f = 90 * np.exp(-t * 20) + 45
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8) * amp

def synth_bed(dur, rng, bpm=77, key="Am", gain=1.0, sections=None, root=0):
    n = int((dur + .3) * SR); out = np.zeros((n, 2))
    beat = 60.0 / bpm; bar = beat * 4; tonic = KEY_TONIC.get(key, 7) + root
    def tex(t):
        if not sections: return "full"
        for a, b, x in sections:
            if a <= t < b: return x
        return sections[-1][2]
    tpos, ci = 0.0, 0                                 # pad + bass：每小节换和弦，交叠不断层
    while tpos < dur:
        ch = PROG[ci % 4]; d = min(bar, dur - tpos)
        if d < .3: break
        lvl = TEX_LVL.get(tex(tpos), .9)
        for k, semi in enumerate(ch["notes"]):
            add(out, pan(bed_pad(hz(tonic + semi), d + .8) * (.05 * lvl / (1 + .35 * k)), (k % 3 - 1) * .45), tpos)
        add(out, pan(bed_pad(hz(tonic + ch["bass"]), d + .6) * .085 * lvl, 0), tpos)
        tpos += d; ci += 1
    tpos, ci = 0.0, 0                                 # 钢琴柱式和弦：小节头
    while tpos < dur - .4:
        tx = tex(tpos)
        if tx in ("piano", "full", "arp", "outro"):
            for semi in PROG[ci % 4]["notes"][2:]:
                x = tone(hz(tonic + semi + 12), beat * 3.2, 1.6, ((1, 1), (2, .4), (3, .18)), attack=.004)
                add(out, pan(x * (.08 if tx != "outro" else .05), 0), tpos)
        tpos += bar; ci += 1
    tpos, bi = 0.0, 0                                 # kick：full 段每两拍
    while tpos < dur - .2:
        if tex(tpos) == "full" and bi % 2 == 0: add(out, pan(bed_kick(.18), 0), tpos)
        tpos += beat; bi += 1
    tpos = 0.0                                        # shaker：full/arp 走 8 分，piano 走 4 分（持续颗粒织体）
    while tpos < dur - .1:
        tx = tex(tpos)
        if tx in ("full", "arp"):
            add(out, pan(bed_shaker(rng, .05), rng.uniform(-.2, .2)), tpos)
            add(out, pan(bed_shaker(rng, .03), rng.uniform(-.2, .2)), tpos + beat / 2)
        elif tx == "piano":
            add(out, pan(bed_shaker(rng, .028), 0), tpos)
        tpos += beat
    tpos, ci = 0.0, 0                                 # 琶音：arp 段
    while tpos < dur - .2:
        if tex(tpos) == "arp":
            for k, semi in enumerate(PROG[ci % 4]["notes"]):
                x = tone(hz(tonic + semi + 12), beat * .8, .5, ((1, 1), (2, .3)), attack=.003)
                add(out, pan(x * .05, (k % 2 * 2 - 1) * .3), tpos + k * beat / 2)
        tpos += bar; ci += 1
    out = out[:int(dur * SR)]; t = np.arange(len(out)) / SR
    out *= (np.clip(t / 1.0, 0, 1) * np.clip((dur - t) / 1.2, 0, 1))[:, None]   # 整床缓起缓收
    return out * gain * .9

def resolve_bed(cfg, root):
    """把 meta.bed（True / {} / dict）规整成 synth_bed 的参数。"""
    if cfg is True or cfg == {} or cfg is None: cfg = {}
    sec = cfg.get("sections"); sections = None
    if isinstance(sec, str) and sec.strip():
        sections = []
        for s in sec.split(";"):
            s = s.strip()
            if not s: continue
            a, b, tx = s.split(","); sections.append((float(a), float(b), tx.strip()))
    elif isinstance(sec, (list, tuple)):
        sections = [(float(x[0]), float(x[1]), str(x[2])) for x in sec]
    return dict(bpm=cfg.get("bpm", 77), key=cfg.get("key", "Am"),
                gain=cfg.get("gain", 1.0), sections=sections, root=root)

def synth(spec, bgm=False, bed=None, hush_scale=1.0):
    end = spec["end"]; meta = spec.get("meta") or {}; n = int((end + .05) * SR); rng = np.random.default_rng(20261006)
    dry = np.zeros((n, 2)); t = np.arange(n) / SR; root = meta.get("root", 0)
    hush = [(when, when + p.get("dur", 2.5)) for when, name, p in spec["events"] if name == "hush"] if hush_scale > 0 else []
    last_big = -9.9                                   # 同刻叠多个大和弦(chord/bloom)能量会翻倍→炸；临近(0.35s内)就自动分摊增益
    for when, name, p in sorted(spec["events"], key=lambda e: e[0]):
        if name in EV:
            if name in ("chord", "bloom"):
                if when - last_big < 0.35: p = dict(p, gain=p.get("gain", 1) * 0.6)
                last_big = when
            add(dry, EV[name](rng, dict(p, root=p.get("root", 0) + root) if name in ("chord", "bloom") else p), when)
    out = reverb(dry, rng)
    if not bgm:                                       # 低频长音垫底：两个略微失谐的正弦 + 很慢的呼吸
        lv = .05 * meta.get("drone", 1)
        d = (np.sin(2 * np.pi * hz(root - 24) * t) + .6 * np.sin(2 * np.pi * hz(root - 24 + .08) * 2 * t) + .25 * np.sin(2 * np.pi * hz(root - 12 + 7) * t)) * (.75 + .25 * np.sin(2 * np.pi * t / 11))
        air = lowpass(highpass(rng.standard_normal(n), 300), 1800) * .012 * (.6 + .4 * np.sin(2 * np.pi * t / 17))
        out += np.stack([d * lv + air, d * lv + np.roll(air, 4000)], 1)
    for a, b, k in meta.get("noise", []):             # 文案说到噪声，配乐里就真的有噪声
        g = np.clip((t - a) / max(.01, b - a), 0, 1) ** 1.5 * (t <= b) * k
        out += lowpass(highpass(rng.standard_normal((n, 2)), 200), 6000) * (g * .12)[:, None]
    g = np.ones(n)
    for a, b in list(meta.get("silence", [])) + hush:  # 彻底静音：0.15s 收掉，0.4s 回来
        g *= 1 - np.clip((t - a) / .15, 0, 1) * (1 - np.clip((t - b) / .4, 0, 1))
    g *= np.clip(t / .6, 0, 1) * np.clip((end - t) / 1.2, 0, 1)
    out *= g[:, None]                                 # 事件音 / drone / 噪声 受 hush·silence 门控
    if not bgm and bed is not None:                   # 床垫在门控之后：连续不断，hush 也不掐它
        b = synth_bed(end, rng, **bed); m = min(len(b), len(out)); out[:m] += b[:m]
    return out

def write_wav(path, x):
    import wave
    x = np.clip(x, -1, 1); pcm = (x * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

def probe(path, x, spec):
    """音轨体检图：你听不到声音，就把它画出来看。波形包络 + 低/中/高频能量 + 事件时间线。"""
    from PIL import Image, ImageDraw, ImageFont
    mono = x.mean(1); dur = len(mono) / SR
    W, H = 1600, 560; m = 70; pw = W - 2 * m
    img = Image.new("RGB", (W, H), (16, 16, 22)); d = ImageDraw.Draw(img)
    fdir = Path(__file__).resolve().parent / "fonts"; font = None
    for fn in ("NotoSansSC-VF.ttf", "NotoSerifSC-VF.ttf", "JetBrainsMono.ttf"):   # 标签含中文，优先用带 CJK 的字体
        try: font = ImageFont.truetype(str(fdir / fn), 15); break
        except Exception: pass
    if font is None: font = ImageFont.load_default()
    def X(tt): return m + pw * tt / max(dur, 1e-9)
    # 1) 波形包络（峰值）
    y0, y1 = 40, 190; cy = (y0 + y1) // 2
    hop = max(1, len(mono) // pw)
    d.text((m, y0 - 22), "波形包络 waveform", font=font, fill=(200, 200, 210))
    for px in range(pw):
        i = px * hop; seg = mono[i:i + hop]
        if not len(seg): break
        a = np.abs(seg).max(); hh = int(a * (y1 - y0) / 2)
        d.line([(m + px, cy - hh), (m + px, cy + hh)], fill=(120, 200, 255))
    d.line([(m, cy), (m + pw, cy)], fill=(60, 60, 70))
    # 2) 频段能量（低<250 / 中250-2k / 高>2k），随时间
    y0, y1 = 250, 400
    d.text((m, y0 - 22), "频段能量 低(蓝) 中(绿) 高(橙)  —— 高频是'嗒/沙'类音效/织体", font=font, fill=(200, 200, 210))
    N, Hh = 2048, 1024; from numpy.fft import rfft, rfftfreq
    freqs = rfftfreq(N, 1 / SR); win = np.hanning(N)
    los, mis, his, ts = [], [], [], []
    for i in range(0, len(mono) - N, Hh):
        sp = np.abs(rfft(mono[i:i + N] * win))
        los.append(sp[freqs < 250].sum()); mis.append(sp[(freqs >= 250) & (freqs < 2000)].sum()); his.append(sp[freqs >= 2000].sum()); ts.append(i / SR)
    los, mis, his = np.array(los), np.array(mis), np.array(his)
    mx = max(los.max(), mis.max(), his.max(), 1e-9)
    for arr, col in ((los, (90, 150, 255)), (mis, (110, 220, 130)), (his, (255, 170, 80))):
        pts = [(X(ts[j]), y1 - (y1 - y0) * arr[j] / mx) for j in range(len(ts))]
        if len(pts) > 1: d.line(pts, fill=col, width=1)
    d.line([(m, y1), (m + pw, y1)], fill=(60, 60, 70))
    # 3) 事件时间线
    y0 = 440; names = sorted({nm for _, nm, _ in spec["events"]})
    palette = [(255, 120, 120), (120, 220, 255), (255, 210, 110), (180, 150, 255), (140, 230, 160), (255, 160, 200), (200, 200, 200), (120, 255, 220), (255, 180, 120), (160, 200, 255)]
    colmap = {nm: palette[i % len(palette)] for i, nm in enumerate(names)}
    d.text((m, y0 - 22), f"事件时间线 ({len(spec['events'])} 条)", font=font, fill=(200, 200, 210))
    for when, nm, _ in spec["events"]:
        row = names.index(nm); yy = y0 + row * 10
        c = colmap.get(nm, (200, 200, 200)); d.line([(X(when), yy), (X(when), yy + 8)], fill=c, width=2)
    lx = m + pw - 150
    for i, nm in enumerate(names):
        d.rectangle([lx, 440 + i * 16, lx + 10, 450 + i * 16], fill=colmap[nm]); d.text((lx + 16, 438 + i * 16), nm, font=font, fill=(200, 200, 210))
    # 时间刻度
    for s in range(0, int(dur) + 1, 10): d.text((X(s), H - 18), f"{s}s", font=font, fill=(150, 150, 160))
    # 概况
    peak = float(np.abs(mono).max()); rms = float(np.sqrt((mono ** 2).mean()))
    sil = int((np.abs(mono) < rms * 0.12).mean() * 100)
    d.text((m, 8), f"dur {dur:.1f}s  peak {peak:.3f}  rms {20 * np.log10(rms + 1e-9):.1f}dBFS  低音静默占比≈{sil}%  (静默越低越'满')", font=font, fill=(230, 230, 120))
    img.save(path); print("probe:", path)

def media_dur(path):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
        return float(r.stdout.strip())
    except Exception: return None

def analyze_bgm(path, outdir):
    """量 BGM 的 BPM、拍点、小节头、段落边界，写 bgm_beats.json + .png。卡点时把分镜关键时刻对到小节头、最大揭晓对到段落边界。"""
    import tempfile, wave, json as _json
    sr = 22050; tmp = Path(tempfile.mktemp(suffix=".wav"))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-ac", "1", "-ar", str(sr), str(tmp)], check=True)
    w = wave.open(str(tmp), "rb"); x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(float) / 32768; w.close(); tmp.unlink()
    dur = len(x) / sr; N, Hh = 1024, 256; win = np.hanning(N); fe = sr / Hh
    prev = None; flux = []; rms = []
    for i in range(0, len(x) - N, Hh):
        sp = np.abs(np.fft.rfft(x[i:i + N] * win)); rms.append(np.sqrt((x[i:i + N] ** 2).mean()))
        flux.append(0.0 if prev is None else float(np.maximum(0, sp - prev).sum())); prev = sp
    flux = np.array(flux); flux = np.maximum(0, flux - flux.mean()); rms = np.array(rms)
    ac = np.correlate(flux, flux, "full")[len(flux) - 1:]
    lo, hi = int(fe * 60 / 200), int(fe * 60 / 60)
    lag = lo + int(np.argmax(ac[lo:hi])); bpm = 60 * fe / lag; beat = 60 / bpm
    best = (0.0, -1)                                       # 相位：让拍网格对齐到最强的 onset
    for o in np.arange(0, beat, beat / 24):
        idx = (np.arange(o, dur, beat) * fe).astype(int); idx = idx[idx < len(flux)]
        s = flux[idx].sum()
        if s > best[1]: best = (o, s)
    beats = [round(float(b), 3) for b in np.arange(best[0], dur, beat)]
    downbeats = beats[::4]
    sm = np.convolve(rms, np.ones(max(1, int(fe * 2))) / max(1, int(fe * 2)), "same")   # 段落：RMS 大变化
    nov = np.abs(np.diff(sm)); thr = nov.mean() + 2.5 * nov.std(); rt = np.arange(len(rms)) * Hh / sr; sec = [0.0]
    for i in range(1, len(nov)):
        if nov[i] > thr and rt[i] - sec[-1] > 6: sec.append(round(float(rt[i]), 2))
    data = {"file": str(path), "duration": round(dur, 2), "bpm": round(bpm, 1), "beat": round(beat, 3), "beats": beats, "downbeats": downbeats, "sections": sec}
    Path(outdir).mkdir(parents=True, exist_ok=True)
    _json.dump(data, open(Path(outdir) / "bgm_beats.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    try:
        from PIL import Image, ImageDraw, ImageFont
        W2, H2, mg = 1600, 300, 60; pw = W2 - 2 * mg; img = Image.new("RGB", (W2, H2), (16, 16, 22)); d = ImageDraw.Draw(img)
        fdir = Path(__file__).resolve().parent / "fonts"; font = None
        for fn in ("NotoSansSC-VF.ttf", "JetBrainsMono.ttf"):
            try: font = ImageFont.truetype(str(fdir / fn), 15); break
            except Exception: pass
        if font is None: font = ImageFont.load_default()
        X = lambda tt: mg + pw * tt / max(dur, 1e-9); y0, y1 = 60, 210; mx = sm.max() + 1e-9
        pts = [(X(rt[j]), y1 - (y1 - y0) * sm[j] / mx) for j in range(0, len(sm), 4)]
        if len(pts) > 1: d.line(pts, fill=(110, 200, 255))
        for b in beats: d.line([(X(b), y1), (X(b), y1 + 9)], fill=(90, 110, 130))
        for b in downbeats: d.line([(X(b), y1), (X(b), y1 + 20)], fill=(255, 210, 110), width=2)
        for s in sec: d.line([(X(s), y0 - 10), (X(s), y1 + 24)], fill=(255, 120, 120), width=2)
        d.text((mg, 12), f"{Path(path).name}  {dur:.1f}s  ~{bpm:.0f}BPM  beat {beat:.3f}s   金=小节头  红=段落边界", font=font, fill=(230, 230, 120))
        for s in range(0, int(dur) + 1, 15): d.text((X(s), H2 - 18), f"{s}s", font=font, fill=(150, 150, 160))
        img.save(Path(outdir) / "bgm_beats.png")
    except Exception as e: print("(beats 图跳过:", e, ")")
    print(f"beats: {Path(outdir) / 'bgm_beats.json'}  ~{bpm:.0f}BPM  {len(beats)} 拍  段落 {sec}")
    return data

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    proj = Path(a[0]).resolve(); spec = json.load(open(proj / "audio/events.json", encoding="utf-8"))
    meta = spec.get("meta") or {}; root = meta.get("root", 0)
    no_bgm = "--no-bgm" in a
    if "--bgm" in a: bgm = a[a.index("--bgm") + 1]
    elif no_bgm: bgm = None
    else: bgm = str(DEFAULT_BGM) if DEFAULT_BGM.exists() else None      # 没指定就用自带 BGM
    bgm_db = -5
    if "--bgm" in a and len(a) > a.index("--bgm") + 2 and a[a.index("--bgm") + 2].lstrip("-").replace(".", "").isdigit(): bgm_db = float(a[a.index("--bgm") + 2])
    ev_db = float(a[a.index("--ev") + 1]) if "--ev" in a else 2.0      # 事件音（动效声）相对增益，让动效声浮在 BGM 之上
    soften = [float(s) for s in a[a.index("--soften") + 1].split(",")] if "--soften" in a else []   # 手动在这些秒对 BGM 做高斯音量 dip（默认空=完全不碰 BGM），其余全曲不动
    if "--beats" in a:                                                 # 只分析 BGM 的拍点 / 段落,给卡点用
        analyze_bgm(bgm or str(DEFAULT_BGM), proj / "audio"); sys.exit()
    dense = "--dense" in a
    want_bed = ("--bed" in a) or dense or (meta.get("bed") is not None and meta.get("bed") is not False)
    no_hush = ("--no-hush" in a) or dense
    bed = resolve_bed(meta.get("bed"), root) if (want_bed and not bgm) else None
    x = synth(spec, bgm=bool(bgm), bed=bed, hush_scale=0.0 if no_hush else 1.0)
    pk = np.abs(x).max() or 1; x = x / pk * 10 ** (-3 / 20)
    wav = proj / "audio/score.wav"; write_wav(wav, x)
    print("score:", wav, f"{len(x) / SR:.1f}s", len(spec["events"]), "events",
          f"bed={bed['bpm']}BPM {bed['key']}" if bed else "bed=off", "hush=off" if no_hush else "hush=on")
    if "--probe" in a: probe(proj / "audio/probe.png", x, spec)
    if "--wav-only" in a: sys.exit()
    # 成片响度：合成很安静可留 -18；带床/dense/外来 BGM 要"满"，收到 -14（可用 --lufs 覆盖）
    if "--lufs" in a: lufs = float(a[a.index("--lufs") + 1])
    elif bgm or bed is not None or dense: lufs = -14
    else: lufs = -18
    raw, out, end = proj / "renders/raw.mp4", proj / "renders/final.mp4", spec["end"]
    if bgm:   # 配乐垫底 + 事件音；不循环，BGM 放完即结束（工程 dur 设成 BGM 时长时正好收尾）
        bdur = media_dur(bgm) or end; flen = min(end, bdur); fo = max(0.1, flen - 2)
        # 线性混音 + 只限峰（alimiter），不做动态 loudnorm：BGM 保持原曲动态，不会被事件音瞬态触发忽大忽小（泵感）。
        # 默认完全不碰 BGM；只有显式 --soften 秒,秒 才在那几秒对 BGM 做局部高斯凹陷（窗口外=原曲）。
        sv = (",volume=eval=frame:volume='1" + "".join(f"*(1-0.7*exp(-((t-{ti})/0.6)*((t-{ti})/0.6)))" for ti in soften) + "'") if soften else ""
        fc = f"[2:a]volume={bgm_db}dB{sv},afade=t=in:d=0.6,afade=t=out:st={fo}:d=2[b];[1:a]volume={ev_db}dB[e];[e][b]amix=inputs=2:normalize=0:duration=longest,alimiter=level_in=1:level_out=1:limit=0.95:attack=5:release=60[a]"
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-i", str(wav), "-i", bgm, "-filter_complex", fc]
    else:
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-i", str(wav), "-filter_complex", f"[1:a]loudnorm=I={lufs}:TP=-1.5:LRA={11 if bed is not None else 14}[a]"]
    subprocess.run(cmd + ["-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", str(out)], check=True)
    print("done", out, (f"linear+limit bgm={Path(bgm).name} {bgm_db}dB ev+{ev_db}dB（无动态归一/无泵感）" if bgm else f"loudnorm {lufs} LUFS bgm=off"))
