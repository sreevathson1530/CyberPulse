// Makes the product tour screenshots in assets/tour/: the real app, with the
// rest of the page dimmed and numbered arrows on the parts each slide explains.
//
// 1. Run the app:  .venv/Scripts/streamlit run app.py --server.port 8601
// 2. Set OUT below to your clone's assets/tour folder.
// 3. Run this file with Playwright, e.g. the Playwright MCP tool
//    browser_run_code_unsafe with filename tools/tour_shots.js.
// 4. Turn the PNGs into WebP:  .venv/Scripts/python tools/tour_webp.py
//
// The numbers on the arrows match the numbered points in core/tour.py.

async (start) => {
  const APP = 'http://localhost:8601';
  const OUT = 'C:/Users/sreev/Projects/CyberPulse-streamlit/assets/tour/';
  const WIDTH = 1040, HEIGHT = 1750, SHOT_HEIGHT = 600;

  // A fresh browser context at 2x pixel density, so the text stays sharp.
  const context = await start.context().browser().newContext({ viewport: { width: WIDTH, height: HEIGHT }, deviceScaleFactor: 2 });
  const page = await context.newPage();

  async function open() {
    await page.goto(APP);
    await page.getByRole('button', { name: 'Run attack demo' }).waitFor();
    await page.waitForTimeout(1500);
    const skip = page.getByRole('button', { name: 'Skip tour' });
    if (await skip.isVisible()) {
      await skip.click();
      await page.waitForTimeout(1500);
    }
  }

  async function playAttackUntil(clock) {
    await page.getByRole('button', { name: 'Run attack demo' }).click();
    await page.waitForFunction((c) => (document.querySelector('.cp-clock')?.textContent || '') >= c, clock, { timeout: 60000 });
    await page.getByRole('button', { name: 'Pause' }).click();
    await page.waitForTimeout(2000);
  }

  // Dim the page, cut holes around the targets, and point a numbered label at each.
  async function annotate(items, dim = true) {
    await page.evaluate(({ items, dim }) => {
      document.getElementById('cp-annot')?.remove();
      const NS = 'http://www.w3.org/2000/svg', ACCENT = '#2F5FD0', W = innerWidth, H = innerHeight;
      const root = document.createElement('div');
      root.id = 'cp-annot';
      root.style.cssText = 'position:fixed;inset:0;z-index:2147483000;pointer-events:none;font-family:Geist,system-ui,sans-serif';
      document.body.appendChild(root);
      const svg = document.createElementNS(NS, 'svg');
      svg.setAttribute('width', W);
      svg.setAttribute('height', H);
      svg.style.cssText = 'position:absolute;inset:0';
      svg.innerHTML = `<defs><marker id="cp-head" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto">
        <path d="M0 0L10 5L0 10z" fill="${ACCENT}"/></marker><mask id="cp-holes"><rect width="${W}" height="${H}" fill="white"/></mask></defs>`;
      root.appendChild(svg);
      const add = (parent, tag, attrs) => {
        const node = document.createElementNS(NS, tag);
        Object.entries(attrs).forEach(([k, v]) => node.setAttribute(k, v));
        parent.appendChild(node);
        return node;
      };
      const find = (item) => {
        let nodes = [...document.querySelectorAll(item.sel)];
        if (item.text) nodes = nodes.filter((n) => n.textContent.trim().includes(item.text));
        let node = nodes.at(item.index ?? 0);
        if (node && item.closest) node = node.closest(item.closest);
        if (!node) throw new Error('Not found: ' + JSON.stringify(item));
        return node;
      };
      const boxes = items.map((item) => {
        const r = find(item).getBoundingClientRect(), pad = item.pad ?? 6;
        return { x: r.left - pad, y: r.top - pad, w: r.width + 2 * pad, h: r.height + 2 * pad };
      });
      if (dim) {
        boxes.forEach((b) => add(svg.querySelector('#cp-holes'), 'rect', { x: b.x, y: b.y, width: b.w, height: b.h, rx: 10, fill: 'black' }));
        add(svg, 'rect', { width: W, height: H, fill: 'rgba(22,24,29,0.45)', mask: 'url(#cp-holes)' });
      }
      boxes.forEach((b) => {
        add(svg, 'rect', { x: b.x, y: b.y, width: b.w, height: b.h, rx: 10, fill: 'none', stroke: 'rgba(47,95,208,0.25)', 'stroke-width': 7 });
        add(svg, 'rect', { x: b.x, y: b.y, width: b.w, height: b.h, rx: 10, fill: 'none', stroke: ACCENT, 'stroke-width': 2.5 });
      });
      items.forEach((item, i) => {
        const b = boxes[i], side = item.side || 'bottom';
        const anchor = {
          top: { x: b.x + b.w / 2, y: b.y }, bottom: { x: b.x + b.w / 2, y: b.y + b.h },
          left: { x: b.x, y: b.y + b.h / 2 }, right: { x: b.x + b.w, y: b.y + b.h / 2 },
          inside: { x: b.x + 14, y: b.y },
        }[side];
        const [dx, dy] = item.offset || { top: [0, -70], bottom: [0, 70], left: [-140, 0], right: [140, 0], inside: [0, 0] }[side];
        const label = document.createElement('div');
        label.style.cssText = 'position:absolute;display:flex;align-items:center;gap:8px;padding:6px 13px 6px 6px;border-radius:999px;' +
          'background:#16181D;color:#fff;font-size:15px;font-weight:500;white-space:nowrap;box-shadow:0 6px 18px rgba(22,24,29,0.28);' +
          (side === 'inside' ? 'transform:translate(0,-50%)' : 'transform:translate(-50%,-50%)');
        label.style.left = anchor.x + dx + 'px';
        label.style.top = anchor.y + dy + 'px';
        const number = document.createElement('b');
        number.textContent = item.n ?? i + 1;
        number.style.cssText = `display:inline-grid;place-items:center;width:24px;height:24px;border-radius:50%;background:${ACCENT};font-size:13px;font-weight:600`;
        const text = document.createElement('span');
        text.textContent = item.label;
        label.append(number, text);
        root.appendChild(label);
        if (side === 'inside') return;
        // Arrow from the edge of the label to the target, with a slight curve.
        const r = label.getBoundingClientRect();
        const c = { x: r.left + r.width / 2, y: r.top + r.height / 2 };
        const v = { x: anchor.x - c.x, y: anchor.y - c.y };
        const t = Math.min(v.x ? (r.width / 2 + 5) / Math.abs(v.x) : Infinity, v.y ? (r.height / 2 + 5) / Math.abs(v.y) : Infinity);
        const start = { x: c.x + v.x * t, y: c.y + v.y * t };
        const len = Math.hypot(anchor.x - start.x, anchor.y - start.y);
        const u = { x: (anchor.x - start.x) / len, y: (anchor.y - start.y) / len };
        const end = { x: anchor.x - u.x * 3, y: anchor.y - u.y * 3 };
        const bend = (item.bend ?? 0.12) * len;
        const mid = { x: (start.x + end.x) / 2 - u.y * bend, y: (start.y + end.y) / 2 + u.x * bend };
        const d = `M${start.x} ${start.y} Q${mid.x} ${mid.y} ${end.x} ${end.y}`;
        add(svg, 'path', { d, fill: 'none', stroke: 'white', 'stroke-width': 6, 'stroke-linecap': 'round', opacity: 0.9 });
        add(svg, 'path', { d, fill: 'none', stroke: ACCENT, 'stroke-width': 2.5, 'stroke-linecap': 'round', 'marker-end': 'url(#cp-head)' });
      });
    }, { items, dim });
  }

  async function top(sel, margin) {
    const y = await page.evaluate((s) => document.querySelector(s).getBoundingClientRect().top, sel);
    return Math.max(0, Math.round(y - margin));
  }

  async function shot(name, y = 0) {
    await page.waitForTimeout(300);
    await page.screenshot({ path: OUT + name + '.png', clip: { x: 0, y, width: WIDTH, height: SHOT_HEIGHT } });
    await page.evaluate(() => document.getElementById('cp-annot')?.remove());
  }

  // Before the attack: the normal day at 13:30.
  await open();
  await annotate([{ sel: '.st-key-run_attack button', label: 'Run attack demo', side: 'bottom', offset: [-170, 95] }]);
  await shot('2-run-attack');

  await annotate([
    { sel: '[role="radiogroup"][aria-label="Scenario"]', label: 'Scenario', side: 'bottom', offset: [0, 75] },
    { sel: '.st-key-play_pause button', label: 'Play / Pause', side: 'bottom', offset: [0, 150] },
    { sel: '.st-key-next_event button', label: 'Next event', side: 'bottom', offset: [10, 75] },
    { sel: '.st-key-reset button', label: 'Reset', side: 'bottom', offset: [20, 150] },
    { sel: '[role="radiogroup"][aria-label="Speed"]', label: 'Speed', side: 'bottom', offset: [40, 75] },
  ]);
  await shot('3-playback');

  await annotate([
    { sel: 'header a', text: 'Evidence', label: 'Evidence', side: 'bottom', offset: [-30, 85], pad: 2 },
    { sel: 'header a', text: 'Score card', label: 'Score card', side: 'bottom', offset: [70, 130], pad: 2 },
    { sel: '.st-key-open_tour button', label: 'Product tour', side: 'bottom', offset: [-70, 85] },
  ]);
  await shot('8-pages');

  // During the attack: paused just after 14:03, red, before the damage at 14:07.
  await playAttackUntil('14:04');
  await annotate([
    { sel: '.st-key-toolbar', label: 'Controls', side: 'inside' },
    { sel: 'section[aria-label="Danger score"]', closest: '[data-testid="stHorizontalBlock"]', label: 'Score, clock and response', side: 'inside' },
    { sel: '.st-key-card_timeline', label: 'Incident timeline', side: 'inside' },
  ], false);
  await shot('1-welcome');

  const kpiTop = await top('.st-key-toolbar', 24);
  await annotate([
    { sel: '.cp-score', label: 'Score', side: 'bottom', offset: [70, 125] },
    { sel: 'section[aria-label="Danger score"] .cp-badge', label: 'Level', side: 'top', offset: [40, -48] },
    { sel: '.cp-clock', label: 'Log clock', side: 'bottom', offset: [40, 150] },
  ]);
  await shot('4-score', kpiTop);

  await annotate([
    { sel: '.st-key-lock_account button', label: 'Lock account', side: 'left', offset: [-150, 0] },
    { sel: '.st-key-sign_out_sessions button', label: 'Sign out sessions', side: 'left', offset: [-170, 10] },
    { sel: '.st-key-remove_forwarding_rules button', label: 'Remove forwarding rule', side: 'left', offset: [-195, 20] },
  ]);
  await shot('5-response', kpiTop);

  await annotate([
    { sel: '.st-key-card_timeline .scatterlayer .point', index: 0, label: 'Warning sign', side: 'bottom', offset: [0, 95] },
    { sel: '.st-key-card_timeline .legend', label: 'Severity colours', side: 'right', offset: [130, 10] },
  ]);
  await shot('6-timeline', await top('.st-key-card_timeline', 30));

  await page.evaluate(() => {
    const feed = document.querySelector('.cp-feed');
    const row = feed.querySelector('.cp-row[class*="cp-s-"]');
    feed.scrollTop += row.getBoundingClientRect().top - feed.getBoundingClientRect().top - 2.2 * row.offsetHeight;
  });
  await annotate([
    { sel: '.cp-story', label: 'The story', side: 'top', offset: [0, -28] },
    { sel: '.cp-row[class*="cp-s-"]', label: 'Part of the incident', side: 'top', offset: [0, -85] },
  ]);
  await shot('7-story', await top('.cp-story', 62));

  await context.close();
  return 'done';
}
