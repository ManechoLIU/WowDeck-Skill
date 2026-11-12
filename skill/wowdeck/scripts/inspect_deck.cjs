#!/usr/bin/env node
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { pathToFileURL } = require('node:url');

if (process.argv.includes('--help')) {
  console.log('Usage: node inspect_deck.cjs HTML OUTPUT_DIR [--settle-ms MILLISECONDS]\nCaptures browser rendering evidence in normal and reduced-motion modes.\nRequires Playwright and sharp; set NODE_PATH to their node_modules directory if needed.');
  process.exit(0);
}
const args = process.argv.slice(2);
const settleMs = args.length === 4 && args[2] === '--settle-ms' ? Number(args[3]) : 1100;
if (![2, 4].includes(args.length) || (args.length === 4 && args[2] !== '--settle-ms') || !Number.isFinite(settleMs) || settleMs < 0 || settleMs > 10000) {
  console.error('Usage: node inspect_deck.cjs HTML OUTPUT_DIR [--settle-ms MILLISECONDS] (see --help)');
  process.exit(1);
}
let chromium, sharp;
try {
  ({ chromium } = require('playwright'));
  sharp = require('sharp');
} catch (error) {
  console.error('Playwright and sharp are required. Set NODE_PATH to the directory containing their node_modules packages.');
  process.exit(1);
}
const html = path.resolve(args[0]);
const output = path.resolve(args[1]);
const digest = data => crypto.createHash('sha256').update(data).digest('hex');
async function main() {
  const source = fs.readFileSync(html);
  // Exclusive creation prevents accidental replacement of prior evidence.
  fs.mkdirSync(output);
  const report = { type: 'render_runtime_evidence', settle_ms: settleMs, html: { path: html, sha256: digest(source) }, visibility_scope: 'slide bounds and ancestor styles; occlusion, clipping and content legibility require screenshot review', modes: {} };
  const browser = await chromium.launch({ headless: true });
  try {
    for (const mode of ['normal', 'reduced-motion']) {
      const context = await browser.newContext({ viewport: { width: 1280, height: 720 }, reducedMotion: mode === 'normal' ? 'no-preference' : 'reduce' });
      const page = await context.newPage();
      const evidence = { navigation: [], resource_failures: [], console_errors: [], screenshots: [] };
      report.modes[mode] = evidence;
      page.on('console', message => { if (message.type() === 'error') evidence.console_errors.push(message.text()); });
      page.on('pageerror', error => evidence.console_errors.push(error.message));
      page.on('requestfailed', request => evidence.resource_failures.push({ url: request.url(), error: request.failure()?.errorText || 'request failed' }));
      page.on('response', response => { if (response.status() >= 400) evidence.resource_failures.push({ url: response.url(), status: response.status() }); });
      await page.goto(pathToFileURL(html).href, { waitUntil: 'load' });
      evidence.viewport = page.viewportSize();
      const info = await page.evaluate(() => ({ count: document.querySelectorAll('.slide').length, api: typeof window.WowDeck?.show === 'function' }));
      if (!info.count) throw new Error('No .slide elements found');
      const tiles = [];
      for (let index = 0; index < info.count; index++) {
        const nav = await page.evaluate(async ({ index, api, settleMs }) => {
          const slides = [...document.querySelectorAll('.slide')];
          if (api) await window.WowDeck.show(index);
          else if (slides.length > 1) location.hash = slides[index].id || `slide-${index + 1}`;
          await Promise.race([document.fonts.ready, new Promise(resolve => setTimeout(resolve, 1000))]);
          await Promise.all([...document.images].map(img => img.complete ? Promise.resolve() : Promise.race([
            new Promise(resolve => { img.addEventListener('load', resolve, { once: true }); img.addEventListener('error', resolve, { once: true }); }),
            new Promise(resolve => setTimeout(resolve, 1000))
          ])));
          const sample = () => {
            const slide = slides[index], rect = slide.getBoundingClientRect(), style = getComputedStyle(slide);
            let effectiveOpacity = 1;
            const blockers = [];
            for (let node = slide; node; node = node.parentElement) {
              const ancestorStyle = getComputedStyle(node);
              effectiveOpacity *= Number(ancestorStyle.opacity);
              if (ancestorStyle.display === 'none' || ancestorStyle.contentVisibility === 'hidden') {
                blockers.push({ tag: node.tagName.toLowerCase(), id: node.id || null, reason: ancestorStyle.display === 'none' ? 'display:none' : 'content-visibility:hidden' });
              }
            }
            // visibility is inherited but descendants may override it. Opacity
            // and display, in contrast, suppress the entire descendant subtree.
            if (style.visibility !== 'visible') blockers.push({ tag: slide.tagName.toLowerCase(), id: slide.id || null, reason: `visibility:${style.visibility}` });
            if (effectiveOpacity <= 0) blockers.push({ reason: 'effective opacity is zero' });
            return { x: rect.x, y: rect.y, width: rect.width, height: rect.height, opacity: Number(style.opacity), effective_opacity: effectiveOpacity, display: style.display, visibility: style.visibility, blockers,
              visible: rect.width > 0 && rect.height > 0 && rect.right > 0 && rect.bottom > 0 && rect.left < innerWidth && rect.top < innerHeight && blockers.length === 0 };
          };
          const before = sample();
          await new Promise(resolve => setTimeout(resolve, settleMs));
          await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
          const after = sample();
          const active = slides.findIndex(s => s.classList.contains('is-active') || s.classList.contains('active') || s.getAttribute('aria-current') === 'true');
          const current = typeof window.WowDeck?.currentIndex === 'function' ? window.WowDeck.currentIndex() : null;
          const identityOK = (current === null || current === index) && (active === -1 || active === index);
          return { requested_index: index, id: slides[index].id || null, title: slides[index].getAttribute('data-title') || slides[index].getAttribute('aria-label') || slides[index].querySelector('h1,h2,h3')?.textContent?.trim() || null,
            method: api ? 'WowDeck.show' : slides.length === 1 ? 'single-visible-slide' : 'hash', current_index: current, active_index: active, hash: location.hash,
            bounds: after, motion_sample: { before, after }, failed_images: [...document.images].filter(img => !img.complete || img.naturalWidth === 0 || img.naturalHeight === 0).map(img => img.currentSrc || img.src),
            confirmed: identityOK && after.visible && (current === index || active === index || slides.length === 1) };
        }, { index, api: info.api, settleMs });
        evidence.navigation.push(nav);
        if (!nav.confirmed) throw new Error(`Navigation to slide ${index + 1} could not be confirmed (${mode})`);
        const filename = `${mode}-slide-${String(index + 1).padStart(3, '0')}.png`;
        const buffer = await page.screenshot({ path: path.join(output, filename) });
        evidence.screenshots.push({ file: filename, sha256: digest(buffer) });
        tiles.push(await sharp(buffer).resize({ width: 320 }).png().toBuffer());
      }
      const meta = await sharp(tiles[0]).metadata();
      const columns = Math.min(3, tiles.length), rows = Math.ceil(tiles.length / columns);
      const sheet = await sharp({ create: { width: columns * meta.width, height: rows * meta.height, channels: 4, background: '#ffffff' } }).composite(tiles.map((input, i) => ({ input, left: (i % columns) * meta.width, top: Math.floor(i / columns) * meta.height }))).png().toBuffer();
      const sheetName = `${mode}-contact-sheet.png`;
      fs.writeFileSync(path.join(output, sheetName), sheet);
      evidence.contact_sheet = { file: sheetName, sha256: digest(sheet), tile_width: meta.width, tile_height: meta.height };
      await context.close();
    }
  } finally {
    await browser.close();
    fs.writeFileSync(path.join(output, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  }
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
