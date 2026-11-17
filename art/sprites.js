/* 學習精靈 — 12 種原創精靈 × 3 階段（SVG，程式繪製）
   畫風：收集型怪獸遊戲風格的原創角色。第 1 階大頭可愛 → 第 3 階修長、眼神銳利、有光環。
   全部為原創設計，不參考任何既有角色。 */
const SPRITES = (() => {
  const OUT = '#2b2230';
  let uid = 0, DEFS = [], GC = {};
  const rgb = h => { h = h.replace('#', ''); if (h.length === 3) h = [...h].map(c => c + c).join(''); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)); };
  const hex = a => '#' + a.map(v => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0')).join('');
  const mix = (a, b, t) => { const A = rgb(a), B = rgb(b); return hex(A.map((v, i) => v + (B[i] - v) * t)); };
  const dark = (c, t = .55) => mix(mix(c, '#2b1830', t), '#000', .12);
  const light = (c, t = .45) => mix(c, '#ffffff', t);
  // 立體漸層：左上亮、右下暗
  function grad(f, sh) {
    const k = f + (sh || ''); if (GC[k]) return GC[k];
    const id = 'g' + (++uid); GC[k] = id; sh = sh || mix(f, '#3a2040', .28);
    DEFS.push(`<radialGradient id="${id}" cx="38%" cy="30%" r="78%"><stop offset="0" stop-color="${light(f, .5)}"/><stop offset=".45" stop-color="${f}"/><stop offset="1" stop-color="${mix(f, sh, .75)}"/></radialGradient>`);
    return id;
  }
  const E = (cx, cy, rx, ry) => `M${cx - rx} ${cy} a${rx} ${ry} 0 1 0 ${2 * rx} 0 a${rx} ${ry} 0 1 0 ${-2 * rx} 0Z`;
  const ln = (w = 2.4, c = OUT) => `fill="none" stroke="${c}" stroke-width="${w}" stroke-linecap="round" stroke-linejoin="round"`;
  const fl = (f, w = 2.6) => `fill="url(#${grad(f)})" stroke="${dark(f)}" stroke-width="${w}" stroke-linejoin="round" stroke-linecap="round"`;
  // 有明暗的形狀：底色 → 右下陰影（裁切在形狀內）→ 左上高光 → 外框
  function shaded(d, fill, shade, o = {}) {
    const id = 'c' + (++uid);
    const sx = o.sx ?? 7, sy = o.sy ?? 6;
    const gid = grad(fill, shade);
    return `<clipPath id="${id}"><path d="${d}"/></clipPath><path d="${d}" fill="url(#${gid})"/><g clip-path="url(#${id})"><path d="${d}" fill="${dark(shade, .25)}" opacity=".42"/><path d="${d}" fill="url(#${gid})" transform="translate(${-sx} ${-sy})"/>`
      + `<path d="${d}" fill="none" stroke="#fff" stroke-width="2" opacity=".35" transform="translate(${sx * .35} ${sy * .35})"/>`
      + (o.hl ? `<ellipse cx="${o.hl[0]}" cy="${o.hl[1]}" rx="${o.hl[2]}" ry="${o.hl[3]}" fill="#fff" opacity=".55" transform="rotate(-30 ${o.hl[0]} ${o.hl[1]})"/>` : '') + `</g>`
      + `<path d="${d}" fill="none" stroke="${o.line || dark(fill)}" stroke-width="${o.w ?? 2.8}" stroke-linejoin="round"/>`;
  }
  // 多個圓合成一團（雲、羊毛）：先畫粗外框再蓋上底色，重疊處不會出現線
  function union(d, fill, shade, sx = 3, sy = 3) {
    const id = 'c' + (++uid);
    const gid = grad(fill, shade);
    return `<path d="${d}" fill="${dark(fill)}" stroke="${dark(fill)}" stroke-width="5.4" stroke-linejoin="round"/><clipPath id="${id}"><path d="${d}"/></clipPath>`
      + `<g clip-path="url(#${id})"><path d="${d}" fill="${shade}"/><path d="${d}" fill="url(#${gid})" transform="translate(${-sx} ${-sy})"/></g>`;
  }
  // 各階段比例
  const G = [
    { hx: 50, hy: 49, hr: 24, by: 79, brx: 15, bry: 12, eye: 0 },
    { hx: 50, hy: 39, hr: 20, by: 68, brx: 17, bry: 18, eye: 1 },
    { hx: 50, hy: 30, hr: 18, by: 60, brx: 21, bry: 23, eye: 2 },
  ];

  function eyes(g, iris, o = {}) {
    const y = g.hy + (o.dy ?? 3), dx = g.hr * (o.sp ?? 0.42), cx = g.hx;
    const ig = grad(light(iris, .25), dark(iris, .3));
    const one = (x, flip) => {
      if (g.eye === 0) return `<ellipse cx="${x}" cy="${y}" rx="4.8" ry="6" fill="${OUT}"/><ellipse cx="${x}" cy="${y + 1.4}" rx="3.7" ry="3.9" fill="url(#${ig})"/><ellipse cx="${x}" cy="${y + 1.4}" rx="1.8" ry="2.2" fill="${OUT}"/>`
        + `<ellipse cx="${x + 1.5}" cy="${y - 2.4}" rx="2.2" ry="2" fill="#fff"/><circle cx="${x - 1.6}" cy="${y + 3}" r="1" fill="#fff"/><path d="M${x - 5} ${y - 4.5} Q${x} ${y - 8} ${x + 5} ${y - 4.5}" ${ln(1.6)}/>`;
      if (g.eye === 1) return `<ellipse cx="${x}" cy="${y}" rx="4.2" ry="5" fill="#fff" stroke="${OUT}" stroke-width="1.4"/><ellipse cx="${x + (flip ? -.5 : .5)}" cy="${y + .5}" rx="3" ry="3.8" fill="url(#${ig})"/><ellipse cx="${x + (flip ? -.5 : .5)}" cy="${y + .8}" rx="1.4" ry="2.4" fill="${OUT}"/><circle cx="${x + 1.5}" cy="${y - 1.7}" r="1.3" fill="#fff"/><circle cx="${x - 1}" cy="${y + 2.6}" r=".6" fill="#fff"/><path d="M${x - 4.6} ${y - 3.8} Q${x} ${y - 7} ${x + 4.6} ${y - 3.8}" ${ln(2.2)}/>`;
      if (false) return `<ellipse cx="${x}" cy="${y}" rx="4.4" ry="5.6" fill="${OUT}"/><ellipse cx="${x}" cy="${y + 1.8}" rx="3" ry="2.6" fill="${iris}"/><circle cx="${x + 1.6}" cy="${y - 2.2}" r="1.9" fill="#fff"/><circle cx="${x - 1.4}" cy="${y + 2}" r=".8" fill="#fff"/>`;
      if (g.eye === 1) return `<ellipse cx="${x}" cy="${y}" rx="3.8" ry="4.6" fill="#fff" stroke="${OUT}" stroke-width="1.6"/><ellipse cx="${x + (flip ? -.6 : .6)}" cy="${y + .6}" rx="2.6" ry="3.4" fill="${iris}"/><ellipse cx="${x + (flip ? -.6 : .6)}" cy="${y + .8}" rx="1.3" ry="2.2" fill="${OUT}"/><circle cx="${x + 1.4}" cy="${y - 1.6}" r="1.1" fill="#fff"/>`;
      const s = flip ? -1 : 1;
      return `<path d="M${x - 5 * s} ${y - 1} Q${x} ${y - 5} ${x + 5 * s} ${y - 3.2} Q${x + 3 * s} ${y + 4} ${x - 3 * s} ${y + 3} Z" fill="#fff" stroke="${OUT}" stroke-width="1.6" stroke-linejoin="round"/>`
        + `<ellipse cx="${x + 1 * s}" cy="${y}" rx="2.6" ry="3.1" fill="url(#${ig})"/><ellipse cx="${x + 1 * s}" cy="${y}" rx=".9" ry="2.4" fill="${OUT}"/><circle cx="${x + 1.8 * s}" cy="${y - 1.4}" r=".8" fill="#fff"/>`
        + `<path d="M${x - 6 * s} ${y - 7} L${x + 5 * s} ${y - 4.5}" ${ln(2.4)}/>`;
    };
    return one(cx - dx, true) + one(cx + dx, false);
  }
  function mouth(g, o = {}) {
    const y = g.hy + g.hr * 0.5 + (o.dy ?? 0), x = g.hx;
    if (o.beak) return `<path d="M${x - 4} ${y - 3} L${x + 4} ${y - 3} L${x} ${y + 3}Z" ${fl(o.beak, 1.8)}/>`;
    if (g.eye === 2) return `<path d="M${x - 5} ${y - 1} Q${x} ${y + 3} ${x + 5} ${y - 1}" ${ln(2)}/><path d="M${x - 3.5} ${y} L${x - 2.5} ${y + 2.6} L${x - 1.5} ${y + .8}" fill="#fff" stroke="${OUT}" stroke-width="1" stroke-linejoin="round"/>`;
    if (g.eye === 1) return `<path d="M${x - 4} ${y - 1} Q${x} ${y + 4} ${x + 4} ${y - 1} Z" fill="#c9504f" stroke="${OUT}" stroke-width="1.6" stroke-linejoin="round"/>`;
    return `<path d="M${x - 3.5} ${y} Q${x - 1.7} ${y + 2.5} ${x} ${y} Q${x + 1.7} ${y + 2.5} ${x + 3.5} ${y}" ${ln(1.8)}/>`;
  }
  const blush = (g, c = '#ff7f8f') => g.eye === 2 ? '' : `<ellipse cx="${g.hx - g.hr * .7}" cy="${g.hy + g.hr * .38}" rx="3.8" ry="2.2" fill="${c}" opacity=".55"/><ellipse cx="${g.hx + g.hr * .7}" cy="${g.hy + g.hr * .38}" rx="3.8" ry="2.2" fill="${c}" opacity=".55"/>`;

  // 腳與手
  function legs(g, s, c, sh, claw) {
    if (s === 0) return shaded(E(40, 91, 7, 4.2), c, sh, { hi: false, sx: 2, sy: 2 }) + shaded(E(60, 91, 7, 4.2), c, sh, { hi: false, sx: 2, sy: 2 });
    const top = g.by + g.bry * .55, w = s === 1 ? 6 : 7.5;
    let out = '';
    for (const x of [g.hx - g.brx * .5, g.hx + g.brx * .5]) {
      out += shaded(`M${x - w} ${top} L${x + w} ${top} L${x + w * .9} 88 L${x - w * .9} 88Z`, c, sh, { hi: false, sx: 3, sy: 0 });
      out += shaded(E(x, 90, w + 2.5, 4.4), c, sh, { hi: false, sx: 2, sy: 2 }) + `<path d="M${x - 2.5} 91.5 L${x - 2.5} 93.6 M${x + 2.5} 91.5 L${x + 2.5} 93.6" ${ln(1.2, dark(c))}/>`;
      if (claw) out += `<path d="M${x - 5} 93.5 L${x - 5} 96 M${x} 94.2 L${x} 97 M${x + 5} 93.5 L${x + 5} 96" ${ln(2, '#fff')}/><path d="M${x - 5} 93.5 L${x - 5} 96 M${x} 94.2 L${x} 97 M${x + 5} 93.5 L${x + 5} 96" ${ln(.8)}/>`;
    }
    return out;
  }
  function arms(g, s, c, sh, o = {}) {
    const y = g.by - g.bry * .35, L = [8, 11, 15][s], dx = g.brx - 2;
    let out = '';
    for (const k of [-1, 1]) {
      const x = g.hx + k * dx, x2 = x + k * L * .7, y2 = y + L * .8;
      out += shaded(`M${x} ${y - 4} Q${x + k * L} ${y - 2} ${x2 + k * 2} ${y2} Q${x2 - k * 4} ${y2 + 4} ${x2 - k * 6} ${y2 - 1} Q${x + k * 3} ${y + 6} ${x} ${y + 5}Z`, c, sh, { hi: false, sx: 2, sy: 2 });
      if (o.glove) out += shaded(E(x2, y2 + 1, 6 + s, 6 + s), o.glove, o.gloveSh || '#a8323a', { sx: 2, sy: 2 });
      else if (s === 2 && o.claw !== false) out += `<path d="M${x2 - 3} ${y2 + 3} l${-k * 1} 3 M${x2} ${y2 + 4} l0 3 M${x2 + 3} ${y2 + 3} l${k * 1} 3" ${ln(1.6)}/>`;
    }
    return out;
  }
  function wing(g, s, c, sh, k, o = {}) {
    const x = g.hx + k * (g.brx - 3), y = g.by - g.bry * .6, W = [12, 20, 30][s] * (o.big || 1), H = [10, 16, 24][s] * (o.big || 1);
    const d = `M${x} ${y} Q${x + k * W * .6} ${y - H * 1.1} ${x + k * W} ${y - H * .6} Q${x + k * W * .9} ${y + H * .1} ${x + k * W * .75} ${y + H * .3} Q${x + k * W * .55} ${y + H * .45} ${x + k * W * .4} ${y + H * .55} Q${x + k * W * .2} ${y + H * .6} ${x} ${y + H * .45}Z`;
    return shaded(d, c, sh, { sx: k * 3, sy: 3 }) + (o.lines ? `<path d="M${x + k * W * .25} ${y + H * .1} L${x + k * W * .8} ${y - H * .4} M${x + k * W * .2} ${y + H * .3} L${x + k * W * .65} ${y}" ${ln(1.2)} opacity=".6"/>` : '');
  }
  const body = (g, c, sh) => shaded(E(g.hx, g.by, g.brx, g.bry), c, sh, { hl: [g.hx - g.brx * .45, g.by - g.bry * .5, g.brx * .22, g.bry * .12] });
  const belly = (g, c) => c ? `<ellipse cx="${g.hx}" cy="${g.by + g.bry * .15}" rx="${g.brx * .62}" ry="${g.bry * .68}" fill="${c}" opacity=".95"/>` : '';
  const head = (g, c, sh, d) => shaded(d || E(g.hx, g.hy, g.hr, g.hr * .92), c, sh, { sx: 6, sy: 5, hl: [g.hx - g.hr * .5, g.hy - g.hr * .55, g.hr * .25, g.hr * .13] });
  // 毛：臉頰兩側的毛簇、頭頂呆毛
  const cheekFluff = (g, c, sh) => [-1, 1].map(k => shaded(`M${g.hx + k * g.hr * .7} ${g.hy - g.hr * .1} L${g.hx + k * g.hr * 1.25} ${g.hy + g.hr * .25} L${g.hx + k * g.hr * .95} ${g.hy + g.hr * .35} L${g.hx + k * g.hr * 1.18} ${g.hy + g.hr * .6} L${g.hx + k * g.hr * .6} ${g.hy + g.hr * .7}Z`, c, sh, { sx: k * 2, sy: 2 })).join('');
  const tuft = (g, c, sh) => shaded(`M${g.hx - 6} ${g.hy - g.hr * .85} Q${g.hx - 4} ${g.hy - g.hr * 1.3} ${g.hx + 2} ${g.hy - g.hr * 1.35} Q${g.hx} ${g.hy - g.hr * 1.15} ${g.hx + 6} ${g.hy - g.hr * 1.18} Q${g.hx + 4} ${g.hy - g.hr * .95} ${g.hx + 7} ${g.hy - g.hr * .85}Z`, c, sh, { sx: 1, sy: 2 });
  const auraC = c => { const id = 'a' + (++uid); DEFS.push(`<radialGradient id="${id}"><stop offset="0" stop-color="${light(c, .55)}" stop-opacity=".9"/><stop offset=".55" stop-color="${c}" stop-opacity=".28"/><stop offset="1" stop-color="${c}" stop-opacity="0"/></radialGradient>`);
    return `<circle cx="50" cy="52" r="52" fill="url(#${id})"/>` + [[14, 22, 1], [88, 30, .8], [10, 70, .7], [92, 74, .9], [28, 6, .6], [76, 8, .7]].map(([x, y, k]) => `<path d="M${x} ${y - 5 * k} L${x + 1.3 * k} ${y - 1.3 * k} L${x + 5 * k} ${y} L${x + 1.3 * k} ${y + 1.3 * k} L${x} ${y + 5 * k} L${x - 1.3 * k} ${y + 1.3 * k} L${x - 5 * k} ${y} L${x - 1.3 * k} ${y - 1.3 * k}Z" fill="#fff" stroke="${c}" stroke-width=".8" opacity=".9"/>`).join(''); };
  const star = (x, y, R, r, c, rot = -90) => { const p = [...Array(10)].map((_, i) => { const a = (rot + i * 36) * Math.PI / 180, q = i % 2 ? r : R; return `${(x + q * Math.cos(a)).toFixed(1)} ${(y + q * Math.sin(a)).toFixed(1)}`; }).join(' L'); return `<path d="M${p}Z" ${fl(c, 2)}/>`; };

  // ---------- 12 種 ----------
  const D = {
    // 食物｜飯糰龜：坦克。飯糰頭、海苔面罩，進化後背上長出壽司殼
    onigiri(s, g) {
      const c = '#fbf7ec', sh = '#d8cfbb', nori = '#1f2d26';
      const hd = `M${g.hx} ${g.hy - g.hr * 1.05} Q${g.hx + 6} ${g.hy - g.hr * 1.05} ${g.hx + 9} ${g.hy - g.hr * .7} L${g.hx + g.hr * 1.05} ${g.hy + g.hr * .55} Q${g.hx + g.hr * 1.1} ${g.hy + g.hr * .95} ${g.hx + g.hr * .7} ${g.hy + g.hr * .95} L${g.hx - g.hr * .7} ${g.hy + g.hr * .95} Q${g.hx - g.hr * 1.1} ${g.hy + g.hr * .95} ${g.hx - g.hr * 1.05} ${g.hy + g.hr * .55} L${g.hx - 9} ${g.hy - g.hr * .7} Q${g.hx - 6} ${g.hy - g.hr * 1.05} ${g.hx} ${g.hy - g.hr * 1.05}Z`;
      const shell = s ? shaded(E(g.hx, g.by - 2, g.brx + 8 + s * 3, g.bry + 4), s === 2 ? '#ff8c5a' : '#2c3d33', s === 2 ? '#d9653a' : '#16211b')
        + (s === 2 ? `<path d="M${g.hx - 18} ${g.by - 8} Q${g.hx} ${g.by - 16} ${g.hx + 18} ${g.by - 8} M${g.hx - 20} ${g.by} Q${g.hx} ${g.by - 8} ${g.hx + 20} ${g.by}" ${ln(2.2, '#fff')} opacity=".8"/>` : `<path d="M${g.hx - 10} ${g.by - 12} L${g.hx - 4} ${g.by - 4} L${g.hx + 6} ${g.by - 6} L${g.hx + 12} ${g.by - 12}" ${ln(1.5, '#4a6b58')}/>`) : '';
      return shell + legs(g, s, c, sh, s === 2) + body(g, c, sh) + arms(g, s, c, sh) + head(g, c, sh, hd)
        + `<path d="M${g.hx - g.hr * .8} ${g.hy + g.hr * .55} L${g.hx + g.hr * .8} ${g.hy + g.hr * .55} L${g.hx + g.hr * .72} ${g.hy + g.hr * .95} L${g.hx - g.hr * .72} ${g.hy + g.hr * .95}Z" fill="${nori}"/>`
        + eyes(g, '#7a4a2a', { dy: 1 }) + blush(g) + `<path d="M${g.hx - 3} ${g.hy + g.hr * .72} Q${g.hx} ${g.hy + g.hr * .82} ${g.hx + 3} ${g.hy + g.hr * .72}" ${ln(1.6, '#fff')}/>`
        + (s === 1 ? `<circle cx="${g.hx}" cy="${g.hy - g.hr * .55}" r="4.5" ${fl('#e5484d', 2)}/>` : '')
        + (s === 2 ? `<path d="M${g.hx - 12} ${g.hy - g.hr * .55} Q${g.hx} ${g.hy - g.hr * 1.5} ${g.hx + 12} ${g.hy - g.hr * .55}" ${fl('#ff8c5a', 2.2)}/><path d="M${g.hx - 6} ${g.hy - g.hr * .75} Q${g.hx} ${g.hy - g.hr * 1.15} ${g.hx + 6} ${g.hy - g.hr * .75}" ${ln(1.4, '#fff')}/>` : '');
    },
    // 食物｜莓狐：遠程。莓果尾巴發射種子，第 3 階變成葡萄九尾
    berry(s, g) {
      const c = ['#ef5b5b', '#e0475a', '#8e5bd6'][s], sh = ['#c23d4a', '#b0303f', '#6a3fb0'][s], bel = '#fff0e6';
      let tail = '';
      const n = s === 2 ? 3 : 1;
      for (let i = 0; i < n; i++) {
        const a = (n === 1 ? 0 : (i - 1) * 22) * Math.PI / 180, L = [16, 22, 26][s];
        const bx = g.hx + 12, by = g.by + 4, tx = bx + L * Math.cos(-0.9 + a), ty = by - L * 1.2 * Math.cos(a) - 4;
        tail += shaded(`M${bx} ${by} Q${tx + 4} ${by + 4} ${tx + 6} ${ty} Q${tx - 6} ${ty - 8} ${tx - 2} ${ty + 10} Q${bx + 6} ${by - 2} ${bx} ${by - 6}Z`, c, sh, { sx: 3, sy: 3 });
        tail += s === 2 ? `<circle cx="${tx + 2}" cy="${ty - 2}" r="4" ${fl('#b48cf0', 1.6)}/><circle cx="${tx + 6}" cy="${ty + 3}" r="3.5" ${fl('#b48cf0', 1.6)}/>` : `<path d="M${tx - 3} ${ty - 4} q4 -6 8 -2 q-4 0 -8 2Z" ${fl('#5fbf5a', 1.6)}/>`;
      }
      const ear = k => shaded(`M${g.hx + k * g.hr * .35} ${g.hy - g.hr * .7} L${g.hx + k * g.hr * 1.05} ${g.hy - g.hr * 1.45} L${g.hx + k * g.hr * .95} ${g.hy - g.hr * .3}Z`, c, sh, { sx: k * 2, sy: 2 })
        + `<path d="M${g.hx + k * g.hr * .5} ${g.hy - g.hr * .65} L${g.hx + k * g.hr * .95} ${g.hy - g.hr * 1.2} L${g.hx + k * g.hr * .88} ${g.hy - g.hr * .45}Z" fill="#ffd6dc"/>`;
      const seeds = [[-.5, -.2], [.5, -.25], [0, -.55], [-.3, .25], [.35, .2]].map(([a, b]) => `<ellipse cx="${g.hx + a * g.hr}" cy="${g.hy + b * g.hr}" rx="1" ry="1.6" fill="#ffe28a" opacity="${s === 2 ? 0 : 1}"/>`).join('');
      return tail + ear(-1) + ear(1) + legs(g, s, c, sh, s === 2) + body(g, c, sh) + belly(g, bel) + arms(g, s, c, sh) + cheekFluff(g, c, sh) + head(g, c, sh)
        + seeds + `<path d="M${g.hx} ${g.hy - g.hr * .9} q-7 -7 -12 -2 q7 2 12 2 q7 -7 12 -2 q-7 2 -12 2Z" ${fl('#5fbf5a', 1.8)}/>`
        + `<ellipse cx="${g.hx}" cy="${g.hy + g.hr * .45}" rx="${g.hr * .45}" ry="${g.hr * .32}" fill="${bel}"/>` + eyes(g, s === 2 ? '#ffd23f' : '#3f8f4f') + blush(g) + mouth(g, { dy: -1 })
        + (s === 2 ? `<path d="M${g.hx - 10} ${g.hy - g.hr * 1.05} L${g.hx - 6} ${g.hy - g.hr * 1.5} L${g.hx} ${g.hy - g.hr * 1.15} L${g.hx + 6} ${g.hy - g.hr * 1.5} L${g.hx + 10} ${g.hy - g.hr * 1.05}Z" ${fl('#ffd23f', 1.8)}/>` : '');
    },
    // 自然｜芽龍：治療。頭上的芽長成樹冠，尾巴是葉子
    sprout(s, g) {
      const c = ['#a9dc78', '#8fd16a', '#5fb35a'][s], sh = ['#7fbb52', '#69ad48', '#3f8f3f'][s], bel = '#f1f8d0';
      const L = [14, 22, 28][s], tx = g.hx + g.brx + L, ty = g.by - 2 - s * 4;
      const tail = shaded(`M${g.hx + g.brx - 6} ${g.by - 6} Q${tx - 4} ${g.by - 4} ${tx} ${ty} Q${tx - 6} ${g.by + 6} ${g.hx + g.brx - 6} ${g.by + 6}Z`, c, sh, { sx: 2, sy: 2 })
        + `<path d="M${tx} ${ty} q8 -10 16 -6 q-6 10 -16 6Z" ${fl('#3f9f4f', 2)}/>`;
      const spikes = s === 2 ? [0, 1, 2].map(i => `<path d="M${g.hx + 8 + i * 6} ${g.by - g.bry + 4 + i * 6} q8 -6 10 2 q-6 2 -10 -2Z" ${fl('#3f9f4f', 1.8)}/>`).join('') : '';
      const top = s === 0 ? `<path d="M${g.hx} ${g.hy - g.hr * .85} L${g.hx} ${g.hy - g.hr * 1.3}" ${ln(2.4)}/><path d="M${g.hx} ${g.hy - g.hr * 1.25} q-10 -10 -15 -2 q8 6 15 2Z M${g.hx} ${g.hy - g.hr * 1.25} q10 -10 15 -2 q-8 6 -15 2Z" ${fl('#4caf50', 2)}/>`
        : s === 1 ? `<path d="M${g.hx} ${g.hy - g.hr * .85} L${g.hx} ${g.hy - g.hr * 1.35}" ${ln(2.4)}/><path d="M${g.hx} ${g.hy - g.hr * 1.3} q-14 -14 -22 -2 q12 8 22 2Z M${g.hx} ${g.hy - g.hr * 1.3} q14 -14 22 -2 q-12 8 -22 2Z" ${fl('#4caf50', 2)}/><circle cx="${g.hx}" cy="${g.hy - g.hr * 1.4}" r="4.2" ${fl('#ff9ec0', 1.8)}/><circle cx="${g.hx}" cy="${g.hy - g.hr * 1.4}" r="1.6" fill="#ffd23f"/>`
        : shaded(`M${g.hx - 26} ${g.hy - 6} Q${g.hx - 34} ${g.hy - 22} ${g.hx - 20} ${g.hy - 26} Q${g.hx - 16} ${g.hy - 40} ${g.hx} ${g.hy - 36} Q${g.hx + 16} ${g.hy - 42} ${g.hx + 22} ${g.hy - 28} Q${g.hx + 36} ${g.hy - 22} ${g.hx + 28} ${g.hy - 6} Q${g.hx} ${g.hy - 12} ${g.hx - 26} ${g.hy - 6}Z`, '#3f9f4f', '#2c7a3a') + `<circle cx="${g.hx - 12}" cy="${g.hy - 24}" r="3" ${fl('#ff6b6b', 1.4)}/><circle cx="${g.hx + 14}" cy="${g.hy - 22}" r="3" ${fl('#ff6b6b', 1.4)}/>`;
      return tail + spikes + legs(g, s, c, sh, s === 2) + body(g, c, sh) + belly(g, bel) + arms(g, s, c, sh) + (s === 2 ? top : '') + head(g, c, sh) + (s < 2 ? top : '')
        + eyes(g, '#a0612b') + blush(g) + mouth(g);
    },
    // 自然｜雲羊：遠程控制。雲朵羊毛，第 3 階長出閃電角
    cloud(s, g) {
      const wool = ['#ffffff', '#e3ecf7', '#8f9db0'][s], wsh = ['#d6e0ee', '#b9c8dc', '#6b7a8e'][s], c = s === 2 ? '#3d4a5c' : '#7d8ea8', sh = s === 2 ? '#2a3442' : '#5f708a';
      const puff = (cx, cy, r) => [[0, 0], [-1, 0], [1, 0], [0, -1], [-.6, -.7], [.6, -.7], [-.6, .6], [.6, .6]].map(([a, b]) => `${E(cx + a * r * .75, cy + b * r * .55, r * .5, r * .5)}`).join(' ');
      const bodyWool = union(puff(g.hx, g.by, g.brx + 6), wool, wsh);
      const horns = s === 2 ? [-1, 1].map(k => `<path d="M0 0 L-4 -10 L1 -10 L-3 -21 L8 -7 L2.5 -7 L5 0Z" ${fl('#ffd23f', 1.8)} transform="translate(${g.hx + k * 9} ${g.hy - g.hr * .75}) rotate(${k * 22}) scale(${1.15 * k} 1.15)"/>`).join('') : '';
      const ears = [-1, 1].map(k => shaded(E(g.hx + k * g.hr * 1.05, g.hy + 1, 7, 4), c, sh, { sx: 1, sy: 2, hi: false })).join('');
      const drops = s >= 1 ? [[-1, 1], [1, 1]].map(([k]) => `<path d="M${g.hx + k * (g.brx + 12)} ${g.by + 2} q4 6 0 9 q-4 -3 0 -9Z" ${fl('#6fb6ff', 1.6)}/>`).join('') : '';
      return drops + legs(g, s, c, sh, false) + bodyWool + arms(g, s, c, sh, { claw: false }) + ears + head(g, c, sh, E(g.hx, g.hy + 2, g.hr * .78, g.hr * .8))
        + union(puff(g.hx, g.hy - g.hr * .62, g.hr * .95), wool, wsh, 2, 2) + horns
        + eyes(g, s === 2 ? '#ffd23f' : '#6fb6ff', { dy: 5, sp: .34 }) + blush(g, '#ffb3c1') + mouth(g, { dy: 1 });
    },
    // 身體｜心兔：輔助。耳尖是愛心，第 3 階長出天使翅膀
    heart(s, g) {
      const c = ['#ffb3cb', '#ff8fb5', '#f25c97'][s], sh = ['#e48aa8', '#e06c96', '#c63d77'][s], bel = '#fff0f5';
      const ear = k => {
        const L = [24, 26, 26][s], x = g.hx + k * g.hr * .45, top = g.hy - g.hr * .6 - L;
        return shaded(`M${x - 5} ${g.hy - g.hr * .5} Q${x - 7 + k * 4} ${top + 6} ${x + k * 3} ${top} Q${x + 7 + k * 4} ${top + 6} ${x + 5} ${g.hy - g.hr * .5}Z`, c, sh, { sx: 2, sy: 2 })
          + `<path d="M${x - 1.5} ${g.hy - g.hr * .6} Q${x - 2 + k * 3} ${top + 10} ${x + k * 3} ${top + 6} Q${x + 3 + k * 3} ${top + 10} ${x + 1.5} ${g.hy - g.hr * .6}Z" fill="#ffd6e4"/>`
          + (s === 2 ? `<path d="M${x + k * 3} ${top + 2} c-4 -6 -10 -2 -6 3 l6 6 l6 -6 c4 -5 -2 -9 -6 -3Z" ${fl('#ff4d88', 1.6)}/>` : '');
      };
      const heartD = (x, y, r) => `M${x} ${y + r} C${x - r * 1.6} ${y} ${x - r * 1.2} ${y - r * 1.3} ${x} ${y - r * .5} C${x + r * 1.2} ${y - r * 1.3} ${x + r * 1.6} ${y} ${x} ${y + r}Z`;
      return (s ? wing(g, s, '#ffffff', '#dfe6f2', -1, { lines: true }) + wing(g, s, '#ffffff', '#dfe6f2', 1, { lines: true }) : '')
        + ear(-1) + ear(1) + legs(g, s, c, sh, false) + body(g, c, sh) + belly(g, bel) + `<path d="${heartD(g.hx, g.by - 1, 3 + s * 1.6)}" ${fl('#ff4d88', 1.6)}/>`
        + arms(g, s, c, sh, { claw: false }) + head(g, c, sh) + eyes(g, '#c2185b') + blush(g) + mouth(g)
        + `<circle cx="${g.hx + g.brx + 2}" cy="${g.by + g.bry * .4}" r="${4 + s}" ${fl('#fff', 2)}/>`;
    },
    // 身體｜拳猴：近戰。頭帶與拳套，第 3 階換上鋼鐵護甲
    fist(s, g) {
      const c = ['#f2a35e', '#e48a43', '#b4c3d3'][s], sh = ['#c97c3c', '#b86a2c', '#7f93a8'][s], bel = '#ffe2bf', band = '#e5484d';
      const tail = `<path d="M${g.hx + g.brx - 4} ${g.by + 6} Q${g.hx + g.brx + 18} ${g.by + 8} ${g.hx + g.brx + 14} ${g.by - 10} Q${g.hx + g.brx + 10} ${g.by - 18} ${g.hx + g.brx + 4} ${g.by - 12}" ${ln(5.5)}/><path d="M${g.hx + g.brx - 4} ${g.by + 6} Q${g.hx + g.brx + 18} ${g.by + 8} ${g.hx + g.brx + 14} ${g.by - 10} Q${g.hx + g.brx + 10} ${g.by - 18} ${g.hx + g.brx + 4} ${g.by - 12}" ${ln(2.8, c)}/>`;
      const ears = [-1, 1].map(k => shaded(E(g.hx + k * g.hr * 1.02, g.hy + 2, 6, 7), c, sh, { sx: 2, sy: 2, hi: false }) + `<ellipse cx="${g.hx + k * g.hr * 1.02}" cy="${g.hy + 2}" rx="3" ry="4" fill="${bel}"/>`).join('');
      const armor = s === 2 ? [-1, 1].map(k => shaded(E(g.hx + k * (g.brx - 2), g.by - g.bry * .6, 9, 7), '#8091a6', '#5d6d82')).join('') : '';
      return tail + legs(g, s, c, sh, s === 2) + body(g, c, sh) + belly(g, s === 2 ? '#dfe7ef' : bel) + armor
        + arms(g, s, c, sh, { glove: s === 2 ? '#5d6d82' : band, gloveSh: s === 2 ? '#3e4b5c' : '#a8323a' }) + ears + tuft(g, c, sh) + head(g, c, sh)
        + `<ellipse cx="${g.hx}" cy="${g.hy + g.hr * .3}" rx="${g.hr * .62}" ry="${g.hr * .48}" fill="${bel}"/>`
        + `<path d="M${g.hx - g.hr * .98} ${g.hy - g.hr * .25} Q${g.hx} ${g.hy - g.hr * .65} ${g.hx + g.hr * .98} ${g.hy - g.hr * .25} L${g.hx + g.hr * .95} ${g.hy - g.hr * .02} Q${g.hx} ${g.hy - g.hr * .4} ${g.hx - g.hr * .95} ${g.hy - g.hr * .02}Z" ${fl(band, 2)}/>`
        + (s ? `<path d="M${g.hx + g.hr * .9} ${g.hy - g.hr * .2} l12 -4 l-4 7Z M${g.hx + g.hr * .9} ${g.hy - g.hr * .1} l10 8 l-7 1Z" ${fl(band, 1.8)}/>` : '')
        + eyes(g, '#5a3a1a', { dy: 2, sp: .36 }) + mouth(g, { dy: 1 });
    },
    // 生活｜燈蛾：遠程控制。發光觸角與腹部，第 3 階翅膀變成燈籠紋
    lamp(s, g) {
      const c = ['#ffe066', '#ffd23f', '#ffb347'][s], sh = ['#e0b93a', '#d4a51f', '#d9822b'][s], bel = '#fff7c2';
      const wc = s === 2 ? '#e5484d' : '#fff6d0', wsh = s === 2 ? '#b02a35' : '#e8d9a0';
      const glow = (x, y, r) => `<circle cx="${x}" cy="${y}" r="${r * 2}" fill="#ffe066" opacity=".35"/><circle cx="${x}" cy="${y}" r="${r}" ${fl('#fff3a0', 1.8)}/>`;
      const ant = [-1, 1].map(k => `<path d="M${g.hx + k * 6} ${g.hy - g.hr * .8} Q${g.hx + k * 10} ${g.hy - g.hr * 1.5} ${g.hx + k * 16} ${g.hy - g.hr * 1.6}" ${ln(2.2)}/>` + (s === 2 ? `<path d="M${g.hx + k * 16} ${g.hy - g.hr * 1.6 - 9} q5 6 0 10 q-5 -4 0 -10Z" ${fl('#ff7a1a', 1.6)}/>` : glow(g.hx + k * 16, g.hy - g.hr * 1.6, 3.2))).join('');
      const wings = s ? [-1, 1].map(k => wing(g, s, wc, wsh, k, { big: 1.05 }) + (s === 2 ? `<circle cx="${g.hx + k * (g.brx + 12)}" cy="${g.by - g.bry - 2}" r="4" ${fl('#ffd23f', 1.4)}/>` : `<circle cx="${g.hx + k * (g.brx + 6)}" cy="${g.by - g.bry + 2}" r="3" fill="#ffd23f" opacity=".8"/>`)).join('') : '';
      const abd = `<circle cx="${g.hx}" cy="${g.by + g.bry * .55}" r="${g.brx * .9}" fill="#fff3a0" opacity=".45"/>`;
      return wings + abd + legs(g, s, '#5a4632', '#3d2f22', false) + body(g, c, sh)
        + `<path d="M${g.hx - g.brx * .8} ${g.by} Q${g.hx} ${g.by + 4} ${g.hx + g.brx * .8} ${g.by} M${g.hx - g.brx * .7} ${g.by + g.bry * .45} Q${g.hx} ${g.by + g.bry * .7} ${g.hx + g.brx * .7} ${g.by + g.bry * .45}" ${ln(1.6)} opacity=".6"/>`
        + arms(g, s, '#5a4632', '#3d2f22', { claw: false }) + ant + head(g, c, sh) + `<ellipse cx="${g.hx}" cy="${g.hy + g.hr * .35}" rx="${g.hr * .55}" ry="${g.hr * .4}" fill="${bel}"/>`
        + eyes(g, '#ff8a00') + blush(g) + mouth(g);
    },
    // 生活｜抱抱熊：坦克。圍巾，第 3 階戴上屋頂頭盔、拿盾
    teddy(s, g) {
      const c = ['#c8935f', '#b98252', '#9c6a40'][s], sh = ['#9c6a3f', '#8f5f38', '#714a2a'][s], bel = '#f2c9a0';
      const ears = [-1, 1].map(k => shaded(E(g.hx + k * g.hr * .72, g.hy - g.hr * .72, 8, 8), c, sh, { sx: 2, sy: 2 }) + `<circle cx="${g.hx + k * g.hr * .72}" cy="${g.hy - g.hr * .72}" r="4" fill="${bel}"/>`).join('');
      const scarf = s ? `<path d="M${g.hx - g.hr * .8} ${g.hy + g.hr * .82} Q${g.hx} ${g.hy + g.hr * 1.15} ${g.hx + g.hr * .8} ${g.hy + g.hr * .82} L${g.hx + g.hr * .75} ${g.hy + g.hr * 1.1} Q${g.hx} ${g.hy + g.hr * 1.4} ${g.hx - g.hr * .75} ${g.hy + g.hr * 1.1}Z" ${fl('#4f7fe0', 2)}/><path d="M${g.hx + g.hr * .4} ${g.hy + g.hr * 1.1} l4 14 l6 -2 l-3 -13Z" ${fl('#4f7fe0', 1.8)}/>` : '';
      const roof = s === 2 ? `<path d="M${g.hx - g.hr * 1.2} ${g.hy - g.hr * .45} L${g.hx} ${g.hy - g.hr * 1.55} L${g.hx + g.hr * 1.2} ${g.hy - g.hr * .45}Z" ${fl('#e5484d', 2.2)}/><path d="M${g.hx - g.hr * .6} ${g.hy - g.hr * .95} L${g.hx + g.hr * .6} ${g.hy - g.hr * .95}" ${ln(1.6, '#fff')} opacity=".7"/>` : '';
      const shield = s === 2 ? shaded(`M${g.hx - g.brx - 16} ${g.by - 14} L${g.hx - g.brx + 4} ${g.by - 14} L${g.hx - g.brx + 4} ${g.by + 4} Q${g.hx - g.brx - 6} ${g.by + 16} ${g.hx - g.brx - 16} ${g.by + 4}Z`, '#ffd23f', '#d9a81a') + `<path d="M${g.hx - g.brx - 6} ${g.by - 8} L${g.hx - g.brx - 6} ${g.by + 6} M${g.hx - g.brx - 12} ${g.by - 2} L${g.hx - g.brx} ${g.by - 2}" ${ln(2.2, '#a8323a')}/>` : '';
      return legs(g, s, c, sh, s === 2) + body(g, c, sh) + belly(g, bel) + arms(g, s, c, sh) + ears + tuft(g, c, sh) + head(g, c, sh)
        + `<ellipse cx="${g.hx}" cy="${g.hy + g.hr * .42}" rx="${g.hr * .42}" ry="${g.hr * .3}" fill="${bel}"/><ellipse cx="${g.hx}" cy="${g.hy + g.hr * .3}" rx="3" ry="2.2" fill="${OUT}"/>`
        + eyes(g, '#3a2e2a', { dy: -1 }) + blush(g) + mouth(g, { dy: 2 }) + scarf + roof + shield;
    },
    // 社會｜信鴿：遠程狙擊。翅膀是信封，第 3 階戴郵差帽
    letter(s, g) {
      const c = ['#fff3d6', '#ffeec2', '#fbe3a6'][s], sh = ['#e3cf9e', '#dcc285', '#cfae63'][s], bel = '#fffaf0';
      const env = k => wing(g, s, '#fffdf6', '#e8dcc0', k) + `<path d="M${g.hx + k * (g.brx - 1)} ${g.by - g.bry * .55} L${g.hx + k * (g.brx + [6, 10, 15][s])} ${g.by - g.bry * .55 + [3, 6, 9][s]} L${g.hx + k * (g.brx + [12, 20, 30][s])} ${g.by - g.bry * .55 - [6, 10, 14][s]}" ${ln(1.6)}/>`;
      const tailF = [0, 1, 2].map(i => `<path d="M${g.hx + 6} ${g.by + g.bry * .5} l${10 + i * 4} ${-4 + i * 6} l-6 ${4}Z" ${fl(i === 1 ? '#e5484d' : c, 1.8)}/>`).join('');
      const crest = `<path d="M${g.hx - 2} ${g.hy - g.hr * .85} q-2 -12 6 -14 q-2 6 2 8 q2 -8 10 -6 q-6 4 -6 12Z" ${fl('#e5484d', 1.8)}/>`;
      const cap = s === 2 ? `<path d="M${g.hx - g.hr * .95} ${g.hy - g.hr * .35} Q${g.hx - g.hr * .9} ${g.hy - g.hr * 1.3} ${g.hx} ${g.hy - g.hr * 1.25} Q${g.hx + g.hr * .9} ${g.hy - g.hr * 1.3} ${g.hx + g.hr * .95} ${g.hy - g.hr * .35}Z" ${fl('#2f8f5b', 2.2)}/><path d="M${g.hx - g.hr * 1.05} ${g.hy - g.hr * .35} Q${g.hx} ${g.hy - g.hr * .15} ${g.hx + g.hr * 1.2} ${g.hy - g.hr * .4}" ${ln(3.2)}/><circle cx="${g.hx}" cy="${g.hy - g.hr * .8}" r="3" ${fl('#ffd23f', 1.4)}/>` : '';
      return tailF + env(-1) + env(1) + legs(g, s, '#ff9f43', '#d97a1f', false) + body(g, c, sh) + belly(g, bel)
        + (s ? `<circle cx="${g.hx}" cy="${g.by - g.bry * .2}" r="${3 + s}" ${fl('#e5484d', 1.6)}/>` : '') + (s === 2 ? '' : crest) + head(g, c, sh)
        + eyes(g, '#3a6fc2', { dy: 0 }) + blush(g) + mouth(g, { beak: '#ff9f43', dy: -2 }) + cap;
    },
    // 社會｜齒輪犬：近戰。機械狗，胸口齒輪，第 3 階戴工程頭盔
    gear(s, g) {
      const c = ['#9cc3e6', '#7fb0dc', '#5c94c8'][s], sh = ['#6f9cc7', '#5684b0', '#3b6c9c'][s], bel = '#dbe9f6';
      const ears = [-1, 1].map(k => shaded(`M${g.hx + k * g.hr * .3} ${g.hy - g.hr * .75} L${g.hx + k * g.hr * 1.0} ${g.hy - g.hr * 1.35} L${g.hx + k * g.hr * .95} ${g.hy - g.hr * .2}Z`, c, sh, { sx: k * 2, sy: 2 }) + `<circle cx="${g.hx + k * g.hr * .82}" cy="${g.hy - g.hr * .55}" r="1.4" fill="${OUT}"/>`).join('');
      const gearD = (x, y, r) => { let p = ''; for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; p += `<rect x="${x - 2.4}" y="${y - r - 3}" width="4.8" height="5" rx="1" ${fl('#ffd23f', 1.4)} transform="rotate(${i * 45} ${x} ${y})"/>`; } return p + `<circle cx="${x}" cy="${y}" r="${r}" ${fl('#ffd23f', 1.6)}/><circle cx="${x}" cy="${y}" r="${r * .4}" ${fl('#c99a10', 1.4)}/>`; };
      const tail = s === 1 ? `<path d="M${g.hx + g.brx - 2} ${g.by + 2} L${g.hx + g.brx + 14} ${g.by - 10}" ${ln(5, '#8a95a3')}/><path d="M${g.hx + g.brx + 10} ${g.by - 16} a6 6 0 1 0 8 8" ${fl('#b8bec6', 2)}/>`
        : `<path d="M${g.hx + g.brx - 2} ${g.by + 2} L${g.hx + g.brx + 10 + s * 4} ${g.by - 8 - s * 4}" ${ln(4, OUT)}/><circle cx="${g.hx + g.brx + 10 + s * 4}" cy="${g.by - 8 - s * 4}" r="3.4" ${fl('#ff6b6b', 1.6)}/>`;
      const hat = s === 2 ? `<path d="M${g.hx - g.hr * .95} ${g.hy - g.hr * .35} Q${g.hx - g.hr} ${g.hy - g.hr * 1.4} ${g.hx} ${g.hy - g.hr * 1.4} Q${g.hx + g.hr} ${g.hy - g.hr * 1.4} ${g.hx + g.hr * .95} ${g.hy - g.hr * .35}Z" ${fl('#ffc23f', 2.2)}/><path d="M${g.hx - g.hr * 1.15} ${g.hy - g.hr * .35} L${g.hx + g.hr * 1.15} ${g.hy - g.hr * .35}" ${ln(3.4)}/><path d="M${g.hx} ${g.hy - g.hr * 1.38} L${g.hx} ${g.hy - g.hr * .5}" ${ln(2)}/>` : '';
      return tail + legs(g, s, c, sh, s === 2) + body(g, c, sh) + belly(g, bel) + gearD(g.hx, g.by, 4 + s * 2) + arms(g, s, c, sh)
        + (s === 2 ? '' : ears) + cheekFluff(g, c, sh) + head(g, c, sh) + `<ellipse cx="${g.hx}" cy="${g.hy + g.hr * .42}" rx="${g.hr * .5}" ry="${g.hr * .34}" fill="${bel}"/><ellipse cx="${g.hx}" cy="${g.hy + g.hr * .3}" rx="3" ry="2" fill="${OUT}"/>`
        + `<path d="M${g.hx - g.hr * .7} ${g.hy - g.hr * .45} L${g.hx + g.hr * .7} ${g.hy - g.hr * .45}" ${ln(1.4)} opacity=".35"/>`
        + eyes(g, '#00c2d1', { dy: 0 }) + mouth(g, { dy: 3 }) + hat;
    },
    // 通用｜書梟：遠程範圍。翅膀是書頁，肚子上的字母隨進化變多
    abc(s, g) {
      const c = ['#7b8cde', '#6574d0', '#4a56b8'][s], sh = ['#5867c0', '#4a56b8', '#333d94'][s], bel = '#eef0ff';
      const pages = k => wing(g, s, '#fffaf0', '#e6dcc4', k) + `<path d="M${g.hx + k * (g.brx + 2)} ${g.by - g.bry * .3} l${k * [6, 10, 16][s]} ${-[3, 5, 8][s]} M${g.hx + k * (g.brx + 2)} ${g.by - g.bry * .1} l${k * [6, 10, 16][s]} ${-[2, 3, 5][s]}" ${ln(1.2)} opacity=".6"/>`;
      const tufts = [-1, 1].map(k => `<path d="M${g.hx + k * g.hr * .5} ${g.hy - g.hr * .75} L${g.hx + k * g.hr * 1.0} ${g.hy - g.hr * 1.4} L${g.hx + k * g.hr * .95} ${g.hy - g.hr * .45}Z" ${fl(c, 2)}/>`).join('');
      const disc = [-1, 1].map(k => `<circle cx="${g.hx + k * g.hr * .4}" cy="${g.hy + 2}" r="${g.hr * .38}" fill="${bel}"/>`).join('');
      const glasses = s === 2 ? [-1, 1].map(k => `<circle cx="${g.hx + k * g.hr * .4}" cy="${g.hy + 2}" r="${g.hr * .38}" fill="none" stroke="${OUT}" stroke-width="2.2"/>`).join('') + `<path d="M${g.hx - 2} ${g.hy + 1} L${g.hx + 2} ${g.hy + 1}" ${ln(2)}/>` : '';
      const cap = s === 2 ? `<path d="M${g.hx - 20} ${g.hy - g.hr * .9} L${g.hx} ${g.hy - g.hr * 1.45} L${g.hx + 20} ${g.hy - g.hr * .9} L${g.hx} ${g.hy - g.hr * .4}Z" ${fl('#2d2a26', 2)}/><path d="M${g.hx + 16} ${g.hy - g.hr * .95} L${g.hx + 18} ${g.hy - g.hr * .2}" ${ln(1.6)}/><circle cx="${g.hx + 18}" cy="${g.hy - g.hr * .15}" r="2.2" fill="#ffd23f"/>` : '';
      return pages(-1) + pages(1) + legs(g, s, '#ffb347', '#d98a1f', s === 2) + body(g, c, sh) + belly(g, bel)
        + `<text x="${g.hx}" y="${g.by + 4 + s}" text-anchor="middle" font-family="Georgia,serif" font-weight="700" font-size="${8 + s * 2}" fill="${sh}">${['A', 'Ab', 'ABC'][s]}</text>`
        + tufts + head(g, c, sh) + disc + eyes(g, '#ffb703', { dy: 2, sp: .4 }) + glasses + mouth(g, { beak: '#ffb347', dy: 0 }) + cap;
    },
    // 通用｜星狐：治療。額頭和尾巴上有星星，第 3 階長出小翅膀、拖著彗星尾
    star(s, g) {
      const c = ['#ffe27a', '#ffd23f', '#ffc21a'][s], sh = ['#e6b93a', '#e0a817', '#d18a00'][s], bel = '#fff6cc';
      const L = [14, 20, 26][s], tx = g.hx + g.brx + L * .6, ty = g.by - L;
      const tail = (s === 2 ? `<path d="M${tx} ${ty} Q${tx + 16} ${ty + 12} ${tx + 26} ${ty + 30} M${tx + 3} ${ty + 4} Q${tx + 14} ${ty + 20} ${tx + 16} ${ty + 36}" ${ln(4.5, '#ffb703')} opacity=".7"/>` : '')
        + shaded(`M${g.hx + g.brx - 6} ${g.by + 4} Q${tx + 8} ${g.by} ${tx} ${ty} Q${tx - 8} ${g.by - 4} ${g.hx + g.brx - 6} ${g.by - 6}Z`, c, sh, { sx: 2, sy: 2 })
        + star(tx, ty - 2, 7 + s * 1.5, 3.2 + s * .6, '#fff7b0');
      const ears = [-1, 1].map(k => shaded(`M${g.hx + k * g.hr * .3} ${g.hy - g.hr * .75} L${g.hx + k * g.hr * 1.0} ${g.hy - g.hr * 1.5} L${g.hx + k * g.hr * .95} ${g.hy - g.hr * .25}Z`, c, sh, { sx: k * 2, sy: 2 }) + `<path d="M${g.hx + k * g.hr * .48} ${g.hy - g.hr * .7} L${g.hx + k * g.hr * .9} ${g.hy - g.hr * 1.2} L${g.hx + k * g.hr * .86} ${g.hy - g.hr * .45}Z" fill="#fff3c2"/>`).join('');
      return tail + (s === 2 ? wing(g, 1, '#fff7d6', '#e8d8a0', -1) + wing(g, 1, '#fff7d6', '#e8d8a0', 1) : '') + ears + legs(g, s, c, sh, s === 2) + body(g, c, sh) + belly(g, bel)
        + arms(g, s, c, sh, { claw: false }) + cheekFluff(g, c, sh) + head(g, c, sh) + `<ellipse cx="${g.hx}" cy="${g.hy + g.hr * .45}" rx="${g.hr * .5}" ry="${g.hr * .32}" fill="${bel}"/>`
        + star(g.hx, g.hy - g.hr * .5, 4.5 + s, 2 + s * .4, s === 2 ? '#ff7a1a' : '#fff7b0') + eyes(g, '#8e5bd6') + blush(g) + mouth(g)
        + (s >= 1 ? `<path d="M${g.hx - 34} ${g.hy - 6} l1.5 3.5 l3.5 1.5 l-3.5 1.5 l-1.5 3.5 l-1.5 -3.5 l-3.5 -1.5 l3.5 -1.5Z" ${fl('#fff', 1)}/>` : '');
    },
  };

  const AURA = { onigiri: '#d9822b', berry: '#d9822b', sprout: '#3f8f4f', cloud: '#3f8f4f', heart: '#c2507a', fist: '#c2507a', lamp: '#7a62b8', teddy: '#7a62b8', letter: '#3a6fc2', gear: '#3a6fc2', abc: '#7a7268', star: '#7a7268' };
  function svg(id, stage, size = 96) {
    const g = G[stage]; DEFS = []; GC = {};
    const fid = 'f' + (++uid);
    const art = (stage === 2 ? auraC(AURA[id]) : '') + `<ellipse cx="50" cy="95" rx="${[20, 24, 28][stage]}" ry="4" fill="#2b1830" opacity=".22" filter="url(#${fid})"/>` + D[id](stage, g);
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="-6 -8 112 112" width="${size}" height="${size}"><defs><filter id="${fid}" x="-50%" y="-200%" width="200%" height="500%"><feGaussianBlur stdDeviation="2"/></filter>${DEFS.join('')}</defs>` + art + `</svg>`;
  }
  const uri = (id, stage, size) => 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg(id, stage, size));
  return { svg, uri, ids: Object.keys(D) };
})();
if (typeof module !== 'undefined') module.exports = SPRITES;
