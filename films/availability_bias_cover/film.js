/* 竖版 3:4 封面（1080×1440）· 可得性偏差 — 与成片同一套鎏金暗场引擎现画
 * 注意：vk-kit 的件（titleGilt/subs）在加载时把 W 冻结为 1920，竖屏会偏心，
 * 所以这里标题块自己按本画幅 W/2 居中现画，不调用 titleGilt。 */
(function () {
'use strict';
const { clamp, lerp, ss, seg, E, hash, rng, rgba } = VK;
const W = 1080, H = 1440, K = VKit, P = K.PAL.gilt;

function card(fr, cx, cy, w, o) {                         // 红色灾难头条卡（示意）
  const h = o.h || 86;
  fr.g({ at: [cx, cy] }, () => {
    fr.rect(-w / 2, -h / 2, w, h, { r: 11, fill: '#1A130C', a: .92 });
    fr.rect(-w / 2, -h / 2, w, h, { r: 11, color: P.red, w: 1.8, a: .9, glow: 11, glowColor: P.red, glowA: .5 });
    fr.rect(-w / 2 + 20, -h / 2 + 18, 12, 12, { r: 2, fill: P.red });
    fr.text('突发', -w / 2 + 58, -h / 2 + 24, { font: 'sansm', size: 18, track: 2, color: P.red, align: 'l' });
    fr.text(o.title, -w / 2 + 40, 6, { font: 'serifm', size: 31, track: 1, color: '#F3E3CF', align: 'l', glow: 6, glowColor: '#F0C98A', glowA: .25 });
    fr.line(-w / 2 + 40, h / 2 - 18, w / 2 - 80, h / 2 - 18, { w: 2, color: '#6B5E44', a: .4, cap: 'butt' });
  });
}
function mTornado(fr, cx, cy, s, col, a) {
  fr.g({ at: [cx, cy], a }, () => { for (let i = 0; i < 5; i++) { const yy = -s + i * s * .5, rw = s * (1 - i * .17); fr.ellipse(0, yy, rw, rw * .3, { color: col, w: 2.6, a: .9 - i * .08, glow: 7, glowColor: col, glowA: .3 }); } fr.line(-s * .18, s, s * .16, s * 1.5, { w: 2.4, color: col, a: .7 }); });
}
function mLungs(fr, cx, cy, s, col, a) {
  fr.g({ at: [cx, cy], a }, () => { fr.line(0, -s * 1.1, 0, -s * .1, { w: 2.8, color: col, a: .9 }); fr.line(0, -s * .1, -s * .55, s * .1, { w: 2.6, color: col, a: .85 }); fr.line(0, -s * .1, s * .55, s * .1, { w: 2.6, color: col, a: .85 }); fr.ellipse(-s * .62, s * .55, s * .52, s * .8, { color: col, w: 2.6, a: .9, glow: 6, glowColor: col, glowA: .25 }); fr.ellipse(s * .62, s * .55, s * .52, s * .8, { color: col, w: 2.6, a: .9, glow: 6, glowColor: col, glowA: .25 }); });
}

function rays(fr, cx, cy, n) {                            // 放射金线
  const x = fr.x; x.save(); x.globalCompositeOperation = 'lighter'; x.translate(cx, cy);
  for (let i = 0; i < n; i++) {
    const ang = i / n * Math.PI * 2 + hash(i) * .08, len = 440 + hash(i + 9) * 460, w = .02 + hash(i + 3) * .03, al = .04 + hash(i + 5) * .06;
    const g = x.createLinearGradient(0, 0, Math.cos(ang) * len, Math.sin(ang) * len);
    g.addColorStop(0, rgba('#E7C477', 0)); g.addColorStop(.18, rgba('#E7C477', al)); g.addColorStop(1, rgba('#E7C477', 0));
    x.fillStyle = g; x.beginPath(); x.moveTo(0, 0); x.lineTo(Math.cos(ang - w) * len, Math.sin(ang - w) * len); x.lineTo(Math.cos(ang + w) * len, Math.sin(ang + w) * len); x.closePath(); x.fill();
  }
  x.restore();
}

function poster(fr) {
  const cx = W / 2;
  fr.text('刷到的坏消息越多，世界就越危险?', cx, 132, { font: 'serifm', size: 30, track: 4, color: P.dim, glow: 5, glowColor: '#C9A86A', glowA: .2 });
  fr.line(cx - 270, 160, cx + 270, 160, { w: 1, color: '#7A6A4A', a: .3, cap: 'butt' });
  ['特大龙卷风　掀翻屋顶', '客机失联　机上无人生还', '持刀男子　当街行凶'].forEach((s, i) => card(fr, cx, 300 + i * 118, 780, { title: s }));
  const ty = 940;
  rays(fr, cx, ty + 20, 56);
  { const r0 = rng(31); for (let i = 0; i < 90; i++) { const px = r0() * W, py = 640 + r0() * 760, s0 = r0(); fr.glow(px, py, 2.5 + s0 * 4, '#F1D9A0', .25 + .5 * s0); } }
  fr.glow(cx, ty, 560, '#6B4A1C', .24);
  fr.text('THE  AVAILABILITY  BIAS', cx, ty - 150, { font: 'latinl', size: 28, track: 14, color: P.mute });
  fr.chars('可得性偏差', cx, ty, { font: 'serifh', size: 158, track: 14, grad: [[0, '#F7E8C2'], [.38, '#E2C07A'], [.62, '#C39A52'], [1, '#8E6A2F']], glow: 26, glowColor: '#B8873C', glowA: .42 }, () => ({}));
  mTornado(fr, cx - 60, ty + 150, 24, P.gold, .85); mLungs(fr, cx + 60, ty + 150, 24, P.goldHi, .85);
  fr.text('为什么我们总觉得坏事更容易发生', cx, ty + 268, { font: 'serifm', size: 33, track: 10, color: '#D4D2CC' });
}

VK.film({ dur: 2, w: W, h: H, theme: 'gilt', meta: { title: '可得性偏差 · 封面' },
  draw(fr) {
    fr.look.bgo = { warm: .82, dust: 1, pool: 1, floor: .3, cy: .42 };
    fr.look.bloom = .4; fr.look.grain = .05;
    poster(fr);
  },
});
if (window.seek) window.draw = window.seek;
})();
