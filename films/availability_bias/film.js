/* ★ 片名 · 可得性偏差 — THE AVAILABILITY BIAS（鎏金暗场 / gilt，1920×1080，120s）
 * 没有旁白：观众读底部字幕，同时看屏上把这句话演出来。照 storyboard.md 现写。
 * 全片形象：一张新闻头条卡（戏剧性死因发红发亮、常见死因发灰）＋ 一把对照真实数字的尺子。
 * 颜色含义：金=答案/真相数字/术语；朱红=被高估的、戏剧性的坏消息；米白=中性字与字幕。
 * 事实与出处见 storyboard.md（Lichtenstein/Slovic 1978；Combs & Slovic 1979；Tversky & Kahneman 1973）。
 * 纯 t 函数：不用 requestAnimationFrame / Date / 无种子随机；渲染由 render.py 的 seek(t) 驱动。 */
(function () {
'use strict';
const { clamp, lerp, seg, smooth, ss, E, fade, hash, rng, rgba, mix } = VK;
const W = 1920, H = 1080;
const K = VKit, P = K.PAL.gilt;

/* ─── 时间锚点（已对齐 BGM 段落/小节头，~112BPM，小节≈2.136s；120.007 为小节头）─── */
const T = { end: 120,
  s1a:0.5,  s1b:5.8,   s2a:6.06, s2b:12.0,  s3a:12.2, s3b:16.2,
  tiA:16.49, ti0:17.0, tiB:22.69,
  s4a:22.9, s4b:27.6,  s5a:28.15, s5b:33.5, s6a:34.56, s6b:38.2, s7a:38.83, s7b:45.6,
  s8a:46.39, s8b:51.3, s9a:51.6, s9b:54.6,  s10a:54.88, s10b:60.1,
  s11a:60.19, s11b:65.5, s12a:66.6, s12b:71.3,
  s13a:73.01, s13b:78.3, s14a:79.42, s14b:85.0, s15a:85.83, s15b:91.8,
  s16a:92.5, s16b:98.3,
  s18a:98.73, s18b:104.3, s19a:105.94, s19b:111.0, s20a:111.46, s20b:114.6,
  s21a:114.69, s21b:119.4 };

/* ─── 字幕（{词}=金，{!词}=红）─── */
const SUBS = [
  { a:T.s1a, b:T.s1b, zh:'每天刷到的坏消息，越来越多。' },
  { a:T.s2a, b:T.s2b, zh:'于是你以为——世界，{!越来越危险}了。' },
  { a:T.s3a, b:T.s3b, zh:'可一场真实的测验说：你，猜反了。' },
  { a:T.s4a, b:T.s4b, zh:'1978 年，几个学者做了个测验。' },
  { a:T.s5a, b:T.s5b, zh:'龙卷风，和哮喘，哪个夺命更多?' },
  { a:T.s6a, b:T.s6b, zh:'几乎所有人，都指向{!龙卷风}。' },
  { a:T.s7a, b:T.s7b, zh:'可真相是——{哮喘}多杀了近 20 倍的人。' },
  { a:T.s8a, b:T.s8b, zh:'换一对：闪电，还是肉毒杆菌?' },
  { a:T.s9a, b:T.s9b, zh:'人人都更怕中毒——' },
  { a:T.s10a, b:T.s10b, zh:'可被{闪电}劈中的，其实多出 52 倍。' },
  { a:T.s11a, b:T.s11b, zh:'我们觉得，天灾人祸，和疾病一样致命。' },
  { a:T.s12a, b:T.s12b, zh:'可疾病夺走的命，是意外的 {16} 倍。' },
  { a:T.s13a, b:T.s13b, zh:'为什么全反了?去数数头条，就懂了。' },
  { a:T.s14a, b:T.s14b, zh:'头条偏爱{!龙卷风、空难、凶案}——' },
  { a:T.s15a, b:T.s15b, zh:'却几乎不写：又一个人，悄悄死于哮喘。' },
  { a:T.s16a, b:T.s16b, zh:'想起来越容易，就以为它发生得越频繁。' },
  { a:T.s18a, b:T.s18b, zh:'回到那块屏幕——' },
  { a:T.s19a, b:T.s19b, zh:'你看见的，不是更危险的世界，' },
  { a:T.s20a, b:T.s20b, zh:'是更多，被反复推到眼前的坏消息。' },
  { a:T.s21a, b:T.s21b, zh:'世界没变得更坏，只是坏事，更容易被你{记住}。', big:1 },
];

/* ───────── 小工具 ───────── */
function SC(fr, t, a, b, fn, fin, fout) {           // 一段戏：窗口内才画，自带进出淡化；fn(t,k)
  const k = fade(t, a, b, fin == null ? .5 : fin, fout == null ? .5 : fout);
  if (k <= 0) return; fr.g({ a: k }, () => fn(t, k));
}
function roundRun(val, k) { return Math.round(val * E.out3(clamp(k))); }

/* ───────── 新闻头条卡（全片的那个形象）───────── */
const HEADS = [
  '七级地震　整座城化为废墟', '客机失联　机上无人生还', '持刀男子　当街行凶',
  '特大龙卷风　掀翻屋顶', '山火失控　万人连夜撤离', '洪水决堤　多地被淹',
  '连环爆炸　伤亡惨重', '冰雪连环车祸　数十车追尾',
];
/* 一张卡：dark 卡面 + 细边 + 类目点 + 一行标题 + 一根正文灰线。tone: 'red' 戏剧性 / 'mute' 常见被忽略 */
function card(fr, cx, cy, w, o) {
  const a = o.a == null ? 1 : o.a; if (a <= .003) return;
  const h = o.h || 74, red = o.tone === 'red', mute = o.tone === 'mute';
  const bcol = red ? P.red : mute ? '#4A4842' : '#8C7A5A';
  fr.g({ a, at: [cx, cy], s: o.s == null ? 1 : o.s }, () => {
    fr.rect(-w / 2, -h / 2, w, h, { r: 9, fill: mute ? '#120F0C' : '#1A130C', a: mute ? .5 : .9 });
    fr.rect(-w / 2, -h / 2, w, h, { r: 9, color: bcol, w: red ? 1.8 : 1.1, a: red ? .9 : mute ? .3 : .5, glow: red ? 10 : 0, glowColor: P.red, glowA: .5 });
    fr.rect(-w / 2 + 16, -h / 2 + 15, 10, 10, { r: 2, fill: red ? P.red : mute ? '#5A564C' : P.goldLo, a: .95 });
    fr.text(red ? '突发' : '讣告', -w / 2 + 50, -h / 2 + 20, { font: 'sansm', size: 15, track: 2, color: red ? P.red : P.mute, align: 'l', a: .9 });
    fr.text(o.title, -w / 2 + 34, 4, { font: 'serifm', size: 25, track: 1, color: red ? '#F3E3CF' : mute ? '#6E6A60' : P.ink, align: 'l', a: red ? 1 : mute ? .6 : .85, glow: red ? 6 : 0, glowColor: '#F0C98A', glowA: .25 });
    fr.line(-w / 2 + 34, h / 2 - 16, -w / 2 + 34 + (w - 120), h / 2 - 16, { w: 2, color: mute ? '#3A362E' : '#6B5E44', a: .4, cap: 'butt' });
  });
}
/* 一列不断上滚的头条流（钩子与回场复用）。纯 t：卡的位置由 t 直接算出 */
function feed(fr, t, o) {
  const gap = 150, span = HEADS.length * gap, speed = o.speed || 92;
  const cx = o.cx == null ? W / 2 : o.cx, top = o.top == null ? 120 : o.top, w = o.w || 680;
  const off = ((t - (o.t0 || 0)) * speed) % span;
  for (let i = 0; i < HEADS.length; i++) {
    const y = top + (((i * gap - off) % span) + span) % span;
    if (y < 30 || y > 868) continue;                 // 不探入字幕区（y>840 只给字幕）
    const a = clamp((y - 55) / 110) * clamp((840 - y) / 120) * (o.a == null ? 1 : o.a);
    card(fr, cx, y, w, { title: HEADS[i], tone: 'red', a, h: 76 });
  }
}

/* ───────── 小图标（线描，不发白）───────── */
function mTornado(fr, cx, cy, s, col, a) {   // 龙卷风：上宽下窄的几圈
  fr.g({ at: [cx, cy], a }, () => {
    for (let i = 0; i < 5; i++) { const yy = -s + i * s * .5, rw = s * (1 - i * .17); fr.ellipse(0, yy, rw, rw * .3, { color: col, w: 2.4, a: .9 - i * .08, glow: 7, glowColor: col, glowA: .3 }); }
    fr.line(-s * .18, s * 1.0, s * .16, s * 1.5, { w: 2.4, color: col, a: .7 });
  });
}
function mLungs(fr, cx, cy, s, col, a) {      // 哮喘：气管 + 两片肺叶
  fr.g({ at: [cx, cy], a }, () => {
    fr.line(0, -s * 1.1, 0, -s * .1, { w: 2.6, color: col, a: .9 });
    fr.line(0, -s * .1, -s * .55, s * .1, { w: 2.4, color: col, a: .85 });
    fr.line(0, -s * .1, s * .55, s * .1, { w: 2.4, color: col, a: .85 });
    fr.ellipse(-s * .62, s * .55, s * .52, s * .8, { color: col, w: 2.4, a: .9, glow: 6, glowColor: col, glowA: .25 });
    fr.ellipse(s * .62, s * .55, s * .52, s * .8, { color: col, w: 2.4, a: .9, glow: 6, glowColor: col, glowA: .25 });
  });
}
function mBolt(fr, cx, cy, s, col, a) {       // 闪电
  fr.g({ at: [cx, cy], a }, () => {
    fr.poly([[-s * .15, -s * 1.2], [-s * .6, s * .1], [-s * .1, s * .1], [s * .55, s * 1.2], [s * .18, s * .05], [s * .62, s * .05]], { color: col, fill: rgba(col, .14), w: 2.6, a: .95, glow: 8, glowColor: col, glowA: .35, close: true });
  });
}
function mCan(fr, cx, cy, s, col, a) {        // 肉毒杆菌：一只罐头
  fr.g({ at: [cx, cy], a }, () => {
    fr.rect(-s * .62, -s * .8, s * 1.24, s * 1.6, { r: 4, color: col, w: 2.4, a: .9 });
    fr.ellipse(0, -s * .8, s * .62, s * .2, { color: col, w: 2.2, a: .9 });
    fr.ellipse(0, s * .8, s * .62, s * .2, { color: col, w: 2.2, a: .6 });
    fr.line(-s * .4, -s * .1, s * .4, -s * .1, { w: 1.6, color: col, a: .5 });
    fr.line(-s * .4, s * .2, s * .4, s * .2, { w: 1.6, color: col, a: .5 });
  });
}

/* ───────── 并排配对题 + 揭晓尺子 ───────── */
/* o: {lz,rz 标签, lmotif,rmotif, pick 'L'|'R'|0, selK, revealK 0..1, winner 'L'|'R', ratio} */
function pair(fr, t, o) {
  const cxL = W / 2 - 330, cxR = W / 2 + 330, cy = 360, cw = 500, ch = 150;
  const sel = o.pick, selK = o.selK || 0;
  [['L', cxL, o.lz, o.lmotif], ['R', cxR, o.rz, o.rmotif]].forEach(function (rowc) {
    const side = rowc[0], cx = rowc[1], label = rowc[2], motif = rowc[3];
    const on = sel === side, win = o.winner === side && o.revealK > 0;
    fr.g({ at: [cx, cy] }, () => {
      if (win) fr.glow(0, 0, 230, P.goldHi, .22 * o.revealK);
      else if (on) fr.glow(0, 0, 200, P.red, .20 * selK);
      fr.rect(-cw / 2, -ch / 2, cw, ch, { r: 14, fill: '#17110A', a: .9 });
      fr.rect(-cw / 2, -ch / 2, cw, ch, { r: 14, color: win ? P.gold : on ? P.red : '#6E5E42', w: win ? 2.6 : on ? 2.4 : 1.3, a: win ? .95 : on ? .9 : .5, glow: win ? 14 : on ? 10 : 0, glowColor: win ? P.gold : P.red, glowA: .5 });
      if (motif) motif(fr, 0, -22, 34, win ? P.goldHi : on ? P.red : P.dim, .95);
      fr.text(label, 0, 48, { font: 'serif', size: 40, track: 3, color: win ? P.goldHi : on ? '#F3E3CF' : P.ink, glow: win ? 10 : 0, glowColor: P.gold, glowA: .4 });
    });
  });
  fr.text('?', W / 2, cy - 4, { font: 'serifh', size: 96, color: P.gold, a: (1 - o.revealK) * (o.qa == null ? 1 : o.qa), glow: 16, glowColor: P.gold, glowA: .4 });
  if (o.revealK > 0) {
    const k = o.revealK, barY = cy + 150, maxL = 440;
    const winCx = o.winner === 'L' ? cxL : cxR, loseCx = o.winner === 'L' ? cxR : cxL;
    fr.text('真实死亡人数', W / 2, barY - 34, { font: 'sansm', size: 22, track: 4, color: P.mute, a: .9 * ss(k, 0, .3) });
    fr.rect(loseCx - 42, barY - 9, 84 * ss(k, 0, .5), 18, { r: 5, fill: P.red, a: .8 });
    const wl = maxL * E.out3(k);
    fr.rect(winCx - wl / 2, barY - 11, wl, 22, { r: 6, fill: fr.grad(winCx - wl / 2, 0, winCx + wl / 2, 0, [[0, P.goldLo], [1, P.goldHi]]), glow: 12, glowColor: P.gold });
    fr.text('× ' + roundRun(o.ratio, k), winCx, barY - 46, { font: 'latinm', size: 56, color: P.goldHi, a: ss(k, .25, .7), glow: 14, glowColor: P.gold, glowA: .4 });
  }
}

/* ───────── 事故 vs 疾病：两根会长高的竖条 + 刻度 ───────── */
function stacks(fr, t, growK) {
  const baseY = 812, cxA = W / 2 - 240, cxB = W / 2 + 240, bw = 150, unit = 40;
  const diseaseH = unit * (1 + 15 * E.out3(growK));
  fr.g({ a: .5 }, () => { for (let g = 2; g <= 16; g += 2) { const y = baseY - unit * g; if (y < 150) break; fr.line(cxB - 360, y, cxB + 300, y, { w: 1, color: '#4A4030', a: .5 * ss(growK, .1, .5), cap: 'butt', dash: [4, 8] }); fr.text('×' + g, cxB + 320, y, { font: 'latin', size: 20, color: P.faint, align: 'l', a: .7 * ss(growK, .1, .5) }); } });
  fr.rect(cxA - bw / 2, baseY - unit, bw, unit, { r: 5, fill: '#6E5E42' });
  fr.rect(cxA - bw / 2, baseY - unit, bw, unit, { r: 5, color: '#8C7A5A', w: 1.2, a: .6 });
  fr.text('意外', cxA, baseY + 34, { font: 'serifm', size: 30, track: 3, color: P.ink });
  const dh = diseaseH;
  fr.rect(cxB - bw / 2, baseY - dh, bw, dh, { r: 5, fill: fr.grad(0, baseY - dh, 0, baseY, [[0, P.goldHi], [1, P.goldLo]]), glow: 10, glowColor: P.gold });
  fr.text('疾病', cxB, baseY + 34, { font: 'serifm', size: 30, track: 3, color: P.goldHi, glow: 8, glowColor: P.gold, glowA: .3 });
  if (growK > .15) fr.text('× ' + roundRun(16, growK), cxB, baseY - dh - 34, { font: 'latinm', size: 48, color: P.goldHi, a: ss(growK, .2, .6), glow: 12, glowColor: P.gold, glowA: .4 });
}

/* ───────── 镜像尺子（哦——）：头条次数 ↔ 真实死亡，完全相反 ───────── */
const MROWS = [
  { zh: '龙卷风', head: .95, real: .09, drama: true },
  { zh: '空难',   head: .82, real: .05, drama: true },
  { zh: '凶杀',   head: .90, real: .16, drama: true },
  { zh: '哮喘',   head: .07, real: .80, drama: false },
  { zh: '中风',   head: .05, real: .96, drama: false },
];
function mirror(fr, t, k) {
  const axis = W / 2, y0 = 320, rh = 84, maxL = 540;
  fr.text('头条里·出现次数', axis - 70, y0 - 54, { font: 'sansm', size: 23, track: 3, color: P.red, align: 'r', a: .95 });
  fr.text('真实中·死亡人数', axis + 70, y0 - 54, { font: 'sansm', size: 23, track: 3, color: P.goldHi, align: 'l', a: .95 });
  fr.line(axis, y0 - 30, axis, y0 + MROWS.length * rh - 40, { w: 1.2, color: '#6E5E42', a: .5, cap: 'butt' });
  MROWS.forEach(function (r, i) {
    const y = y0 + i * rh, kk = ss(k, .1 + i * .08, .55 + i * .08);
    const hl = maxL * r.head * E.out3(kk), rl = maxL * r.real * E.out3(kk);
    fr.rect(axis - 64 - hl, y - 13, hl, 26, { r: 5, fill: fr.grad(axis - 64 - hl, 0, axis - 64, 0, [[0, '#7A2A1C'], [1, P.red]]), glow: r.drama ? 9 : 0, glowColor: P.red, glowA: .4 });
    fr.rect(axis + 64, y - 13, rl, 26, { r: 5, fill: fr.grad(axis + 64, 0, axis + 64 + rl, 0, [[0, P.goldLo], [1, P.goldHi]]), glow: r.drama ? 0 : 9, glowColor: P.gold, glowA: .4 });
    fr.text(r.zh, axis, y, { font: 'serifm', size: 26, color: r.drama ? '#F0D6B0' : P.goldHi });
  });
}

/* ───────── 顶部常驻钩子标题 ───────── */
function topHook(fr, t) {
  let a = .9;
  a *= 1 - ss(t, T.tiA - .3, T.tiA + .4) * (1 - ss(t, T.tiB - .4, T.tiB + .3));
  a *= 1 - ss(t, 115.3, 116.2);
  if (a <= .01) return;
  fr.text('刷到的坏消息越多，世界就越危险?', W / 2, 54, { font: 'serifm', size: 26, track: 4, color: P.dim, a, glow: 5, glowColor: '#C9A86A', glowA: .2 });
  fr.line(W / 2 - 250, 78, W / 2 + 250, 78, { w: 1, color: '#7A6A4A', a: .3 * a, cap: 'butt' });
}

/* ───────── 前景层：几颗失焦的大金尘，横穿而过（景深）───────── */
function fgDust(fr, t) {
  fr.g({ add: true }, () => {
    for (let i = 0; i < 7; i++) {
      const sp = 24 + hash(i * 2.3) * 40, r = 22 + hash(i + 5) * 34;
      const px = ((hash(i + 1) * W + t * sp) % (W + 400)) - 200;
      const py = hash(i + 9) * H + Math.sin(t * .3 + i) * 40;
      const a = (.05 + .05 * hash(i + 3)) * (.6 + .4 * Math.sin(t * .7 + i * 2));
      fr.glow(px, py, r, '#F0D49A', a);
    }
  });
}

/* ───────── 各场景 ───────── */
function sceneHook(fr, t) {
  if (t > T.s3b + .8) return;
  const k = 1 - ss(t, T.s3b, T.s3b + .6);            // t=0 即满亮（不做淡入，首帧就有画面），sub3 后淡出
  fr.g({ a: k }, () => {
    const tt = t;
    const frozen = ss(tt, T.s3a, T.s3a + .8);
    fr.glow(W / 2, 520, 440, '#5A1A10', .16 + .12 * ss(tt, T.s2a, T.s2b));     // 背景：隐隐发红的问号光
    fr.text('?', W / 2, 560, { font: 'serifh', size: 790, color: '#431A12', a: .6 + .24 * ss(tt, T.s2a, T.s2b), blur: 1, glow: 26, glowColor: '#7A2A18', glowA: .22 });
    fr.g({ a: 1 - frozen * .45 }, () => feed(fr, tt, { speed: 96, cx: W / 2, w: 700, a: 1 }));
    if (tt > T.s3a - .3) fr.text('一场真实的测验', W / 2, 150, { font: 'serifm', size: 30, track: 6, color: P.goldHi, a: ss(tt, T.s3a, T.s3a + .6) * (1 - ss(tt, T.s3b - .3, T.s3b)), glow: 8, glowColor: P.gold, glowA: .3 });
    fr.sfx(0.6, 'tock', {}); fr.sfx(1.6, 'tock', {}); fr.sfx(2.6, 'tock', {}); fr.sfx(3.6, 'tock', {}); fr.sfx(4.7, 'tock', {});
    fr.sfx(T.s2a + .2, 'thud', { gain: .8 }); fr.sfx(T.s3a + .1, 'rise', { dur: 1.2 });
  });
}

function sceneTitle(fr, t) {
  SC(fr, t, T.tiA, T.tiB, (tt) => {
    const lt = tt - T.ti0;
    K.titleGilt(fr, lt, { la: 'THE AVAILABILITY BIAS', zh: '可得性偏差', tag: '为什么我们总觉得坏事更容易发生',
      tagDy: 212, motif: (f, l, aa) => { mTornado(f, W / 2 - 46, 640, 20, P.gold, ss(l, 1.0, 1.8) * aa * .8); mLungs(f, W / 2 + 46, 640, 20, P.goldHi, ss(l, 1.2, 2.0) * aa * .8); } });
    fr.sfx(T.ti0, 'bloom', { gain: .9 }); fr.sfx(T.ti0 + 1.4, 'shimmer', {});
  }, .3, .5);
  if (t >= T.tiA - .2 && t <= T.ti0 + .3) K.flash(fr, t, T.ti0, { rise: .35, fall: .45, peak: .8 });
}

function scenePair1(fr, t) {
  SC(fr, t, T.s4a - .2, T.s7b + .4, (tt) => {
    const ck = ss(tt, T.s4a, T.s4a + .7);
    fr.text('1978 · 俄勒冈大学 · 致死事件判断实验', W / 2, 150, { font: 'serifm', size: 26, track: 3, color: P.dim, a: .9 * ck * (1 - ss(tt, T.s7a, T.s7a + .5) * .3) });
    const pick = tt >= T.s6a ? 'L' : 0, selK = ss(tt, T.s6a, T.s6a + .6);
    const revealK = ss(tt, T.s7a, T.s7a + 1.4);
    pair(fr, tt, { lz: '龙卷风', rz: '哮喘', lmotif: mTornado, rmotif: mLungs, pick, selK, revealK, winner: 'R', ratio: 20, qa: 1 - ss(tt, T.s6a, T.s6a + .5) });
    fr.sfx(T.s4a + .1, 'tock', {}); fr.sfx(T.s5a + .2, 'rise', { dur: 1.0 });
    fr.sfx(T.s6a + .1, 'tick', { pitch: 3 }); fr.sfx(T.s7a, 'bloom', { gain: .85 }); fr.sfx(T.s7a + .15, 'thud', { gain: .7 });
  }, .4, .5);
}

function scenePair2(fr, t) {
  SC(fr, t, T.s8a - .2, T.s10b + .3, (tt) => {
    const pick = tt >= T.s9a ? 'R' : 0, selK = ss(tt, T.s9a, T.s9a + .6);
    const revealK = ss(tt, T.s10a, T.s10a + 1.4);
    pair(fr, tt, { lz: '闪电', rz: '肉毒杆菌', lmotif: mBolt, rmotif: mCan, pick, selK, revealK, winner: 'L', ratio: 52, qa: 1 - ss(tt, T.s9a, T.s9a + .5) });
    fr.sfx(T.s8a + .1, 'tock', {}); fr.sfx(T.s9a + .1, 'tick', { pitch: 2 });
    fr.sfx(T.s10a, 'bloom', { gain: .85 }); fr.sfx(T.s10a + .15, 'thud', { gain: .7 });
  }, .4, .5);
}

function sceneDisease(fr, t) {
  SC(fr, t, T.s11a - .2, T.s12b + .3, (tt) => {
    const growK = ss(tt, T.s12a, T.s12a + 2.6);
    fr.text('你以为一样多，其实——', W / 2, 150, { font: 'serifm', size: 26, track: 3, color: P.dim, a: .85 * (1 - ss(tt, T.s12a, T.s12a + .8) * .4) * ss(tt, T.s11a, T.s11a + .5) });
    stacks(fr, tt, growK);
    for (let i = 0; i < 5; i++) fr.sfx(T.s11a + .3 + i * .5, 'tick', { pitch: i });
    for (let i = 0; i < 6; i++) fr.sfx(T.s12a + .2 + i * .33, 'tick', { pitch: 3 + i });
    fr.sfx(T.s12a + 2.4, 'thud', { gain: .8 });
  }, .4, .5);
}

function sceneMechanism(fr, t) {
  SC(fr, t, T.s13a - .2, T.s15b + .4, (tt) => {
    const wallA = ss(tt, T.s13a, T.s13a + 1.2) * (1 - ss(tt, 80.0, 82.0));
    const mirA = ss(tt, 80.2, 82.4);
    if (wallA > .01) {
      fr.g({ a: wallA }, () => {
        for (let c = 0; c < 3; c++) for (let r = 0; r < 4; r++) {
          const cx = W / 2 + (c - 1) * 600, cy = 250 + r * 150 - ((tt - T.s13a) * 26) % 150;
          const idx = (c * 4 + r) % HEADS.length;
          card(fr, cx, cy, 540, { title: HEADS[idx], tone: 'red', a: clamp((cy - 120) / 120) * clamp((900 - cy) / 150), h: 74 });
        }
      });
    }
    if (mirA > .01) fr.g({ a: mirA }, () => mirror(fr, tt, ss(tt, 80.4, 86.0)));
    if (tt >= T.s15a - .3) { const q = ss(tt, T.s15a, T.s15b); card(fr, W / 2 - 560 + q * 180, 862, 420, { title: '某人　因哮喘离世', tone: 'mute', a: ss(tt, T.s15a, T.s15a + .8) * (1 - ss(tt, T.s15b - .6, T.s15b)) * .9, h: 64, s: .9 }); }
    fr.sfx(T.s13a + .1, 'rise', { dur: 1.2 }); fr.sfx(T.s14a, 'tock', {}); fr.sfx(T.s14a + .6, 'tock', {});
    fr.sfx(80.41, 'bloom', { gain: .95 }); fr.sfx(80.6, 'thud', { gain: .75 }); fr.sfx(T.s15a + .2, 'soft', {});
  }, .4, .5);
  if (t >= 80.2 && t <= 82.0) K.ripple(fr, t, 80.41, W / 2, 470, { r0: 60, r1: 760, dur: 1.4, color: '#E7C477' });
}

function sceneName(fr, t) {
  SC(fr, t, T.s16a - .2, T.s16b + .3, (tt) => {
    const k = ss(tt, T.s16a + .3, T.s16a + 1.6);
    fr.chars('可得性偏差', W / 2, 430, { font: 'serifh', size: 150, track: 20, grad: [[0, '#F7E8C2'], [.5, '#E2C07A'], [1, '#B98A3E']], glow: 24, glowColor: '#B8873C', glowA: .4 },
      i => { const kk = seg(k, i * .12, i * .12 + .4); return { a: smooth(kk), blur: (1 - kk) * 14 }; });
    fr.text('AVAILABILITY  HEURISTIC', W / 2, 536, { font: 'mono', size: 18, track: 8, color: P.mute, a: ss(tt, T.s16a + 1.3, T.s16a + 2.0) });
    fr.text('卡尼曼 · 特沃斯基　1972–73', W / 2, 586, { font: 'serifm', size: 24, track: 3, color: P.goldLo, a: ss(tt, T.s16a + 1.6, T.s16a + 2.3) });
    fr.sfx(T.s16a + .2, 'chord', { root: 0 }); fr.sfx(T.s16a + 1.4, 'stamp', {});
  }, .4, .5);
}

function sceneYou(fr, t) {
  SC(fr, t, T.s18a - .2, T.s20b + .4, (tt) => {
    const warmBack = ss(tt, T.s19a, T.s20b);
    const feedOut = ss(tt, T.s20a, T.s20b + .3);
    fr.g({ a: (1 - feedOut) }, () => feed(fr, tt, { speed: 40, cx: W / 2, w: 700, a: .85 * (1 - warmBack * .25) }));
    fr.sfx(T.s18a + .2, 'soft', {}); fr.sfx(T.s20a + .3, 'tick', { pitch: 1 });
  }, .4, .6);
}

function sceneHeart(fr, t) {
  SC(fr, t, T.s21a - .2, T.end, (tt) => {
    const ek = ss(tt, 116.4, 117.8);
    fr.text('可得性偏差', W / 2, 452, { font: 'serifh', size: 80, track: 16, grad: [[0, '#F7E8C2'], [.5, '#E2C07A'], [1, '#B98A3E']], a: ek, glow: 14, glowColor: '#B8873C', glowA: .35 });
    fr.text('THE  AVAILABILITY  BIAS', W / 2, 520, { font: 'mono', size: 16, track: 7, color: P.mute, a: ek * .9 });
    const refA = ss(tt, 117.2, 118.4);
    fr.text('文献线索', W / 2, 820, { font: 'serifm', size: 22, track: 6, color: P.goldLo, a: refA });
    const refs = [
      'Lichtenstein, Slovic, Fischhoff, Layman & Combs (1978). Judged Frequency of Lethal Events.',
      'Combs & Slovic (1979). Newspaper Coverage of Causes of Death.',
      'Tversky & Kahneman (1973). Availability: A heuristic for judging frequency and probability.',
    ];
    refs.forEach((r, i) => fr.text(r, W / 2, 858 + i * 30, { font: 'serifr', size: 19, track: .5, color: P.faint, a: refA * .9 }));
    fr.sfx(T.s21a + .3, 'chord', { root: -5 }); fr.sfx(118.0, 'hush', { dur: 2.0 });
  }, .5, .01);
}

/* ───────── 合成影片 ───────── */
VK.film({
  dur: T.end, w: W, h: H, theme: 'gilt',
  meta: { title: '可得性偏差', root: 0, drone: 1 },
  draw(fr, t) {
    fr.look.bgo = { warm: clamp(t < 60 ? .82 : t < 92 ? lerp(.55, .5, ss(t, 60, 74)) : lerp(.5, .9, ss(t, 100, 118)), 0, 1), dust: 1, pool: 1, floor: .28, cy: .42 };
    fr.look.bloom = t >= T.tiA && t <= T.tiB ? .42 : .34;
    fr.look.grain = .055;

    sceneHook(fr, t);
    sceneTitle(fr, t);
    scenePair1(fr, t);
    scenePair2(fr, t);
    sceneDisease(fr, t);
    sceneMechanism(fr, t);
    sceneName(fr, t);
    sceneYou(fr, t);
    sceneHeart(fr, t);

    fgDust(fr, t);
    topHook(fr, t);
    K.subs(fr, t, SUBS, 'gilt');
  },
});
if (window.seek) window.draw = window.seek;   // 满足"暴露 window.draw(t)"：draw 即 seek，画面完全由 t 决定
})();
