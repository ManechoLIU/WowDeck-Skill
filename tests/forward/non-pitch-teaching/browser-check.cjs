#!/usr/bin/env node
'use strict';

const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

function loadPlaywright() {
  const candidates = [
    'playwright',
    process.env.WOWDECK_NODE_PATH
      ? path.join(process.env.WOWDECK_NODE_PATH, 'playwright')
      : null,
    path.join(
      os.homedir(),
      '.cache',
      'codex-runtimes',
      'codex-primary-runtime',
      'dependencies',
      'node',
      'node_modules',
      'playwright',
    ),
  ].filter(Boolean);
  for (const candidate of candidates) {
    try {
      return require(candidate);
    } catch (error) {
      if (error.code !== 'MODULE_NOT_FOUND') throw error;
    }
  }
  throw new Error(
    'Playwright is unavailable; install it or set WOWDECK_NODE_PATH to its node_modules directory.',
  );
}

const { chromium } = loadPlaywright();
const ROOT = __dirname;
const VERIFY_ONLY = process.argv.includes('--verify');
const INDEX_PATH = path.join(ROOT, 'index.html');
const RECEIPT_PATH = path.join(ROOT, 'validation-receipt.json');
const CHECK_PATH = path.join(ROOT, 'browser-check.json');
const COMMITTED_CONTACT_SHEET_PATH = path.join(ROOT, 'contact-sheet.png');
const VERIFY_DIRECTORY = VERIFY_ONLY
  ? fs.mkdtempSync(path.join(os.tmpdir(), 'wowdeck-browser-check-'))
  : null;
const CONTACT_SHEET_PATH = VERIFY_DIRECTORY
  ? path.join(VERIFY_DIRECTORY, 'contact-sheet.png')
  : COMMITTED_CONTACT_SHEET_PATH;
const VALIDATOR_PATH = path.resolve(
  ROOT,
  '../../../skill/wowdeck/scripts/validate_deck.py',
);

function sha256(filePath) {
  return crypto.createHash('sha256').update(fs.readFileSync(filePath)).digest('hex');
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[character]);
}

function mimeType(filePath) {
  return {
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
  }[path.extname(filePath).toLowerCase()] || 'application/octet-stream';
}

function startServer() {
  const server = http.createServer((request, response) => {
    const url = new URL(request.url, 'http://127.0.0.1');
    const requested = decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname);
    const relative = requested.replace(/^\/+/, '');
    const candidate = path.resolve(ROOT, relative);
    if (!candidate.startsWith(`${ROOT}${path.sep}`) || !fs.existsSync(candidate)) {
      response.writeHead(404).end('Not found');
      return;
    }
    response.writeHead(200, { 'Content-Type': mimeType(candidate) });
    fs.createReadStream(candidate).pipe(response);
  });
  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => resolve(server));
  });
}

function currentValidation() {
  const completed = spawnSync(
    'python3',
    [
      VALIDATOR_PATH,
      INDEX_PATH,
      '--json',
      '--check-receipt',
      RECEIPT_PATH,
    ],
    { cwd: ROOT, encoding: 'utf8' },
  );
  assert.equal(
    completed.status,
    0,
    `validator failed:\n${completed.stdout}\n${completed.stderr}`,
  );
  const result = JSON.parse(completed.stdout);
  assert.equal(result.ok, true);
  assert.equal(result.facts.receipt_status, 'current');
  return result.facts;
}

function verifyRecordedEvidence(facts) {
  const recorded = JSON.parse(fs.readFileSync(CHECK_PATH, 'utf8'));
  assert.equal(recorded.status, 'PASS', 'recorded browser check is not passing');
  for (const field of [
    'index_sha256',
    'artifact_sha256',
    'source_revision',
    'builder_revision',
    'source_sha256',
    'variant',
    'background_mode',
  ]) {
    assert.equal(recorded.artifact[field], facts[field], `stale browser artifact field: ${field}`);
  }
  assert.equal(recorded.runner.path, path.basename(__filename));
  assert.equal(recorded.runner.sha256, sha256(__filename), 'stale browser runner hash');
  assert.equal(recorded.contact_sheet.path, path.basename(COMMITTED_CONTACT_SHEET_PATH));
  assert.equal(
    recorded.contact_sheet.sha256,
    sha256(COMMITTED_CONTACT_SHEET_PATH),
    'stale contact-sheet hash',
  );
  assert.equal(recorded.contact_sheet.slide_count, 7);
  assert.deepEqual(recorded.console_errors, []);
  assert.equal(Object.values(recorded.assertions).every(Boolean), true);
  assert.deepEqual(
    recorded.checks.map((check) => [check.profile, check.pages.length, check.pass]),
    [
      ['standard', 7, true],
      ['small', 7, true],
      ['reduced-motion', 7, true],
    ],
  );
  assert.equal(recorded.checks.every((check) => check.pages.every((page) => page.pass)), true);
}

async function waitForReady(page) {
  await page.waitForFunction(() => (
    Boolean(window.WowDeck)
    && document.documentElement.dataset.ready === 'true'
  ));
}

async function settle(page) {
  await page.evaluate(() => new Promise((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(resolve));
  }));
  await page.waitForTimeout(850);
}

async function inspectActivePage(page) {
  return page.evaluate(() => {
    const active = document.querySelector('.slide.is-active');
    const stage = document.getElementById('stage');
    const shell = document.getElementById('stage-shell');
    const counter = document.getElementById('slide-counter');
    if (!active || !stage || !shell || !counter) throw new Error('deck runtime is incomplete');

    const rectObject = (rect) => ({
      left: rect.left,
      top: rect.top,
      right: rect.right,
      bottom: rect.bottom,
      width: rect.width,
      height: rect.height,
    });
    const shellRect = shell.getBoundingClientRect();
    const canvasRect = stage.getBoundingClientRect();
    const overflowElements = Array.from(active.querySelectorAll('*'))
      .filter((node) => {
        const style = getComputedStyle(node);
        if (style.display === 'none' || style.visibility === 'hidden') return false;
        const rect = node.getBoundingClientRect();
        if (rect.width === 0 && rect.height === 0) return false;
        return rect.left < canvasRect.left - 1
          || rect.right > canvasRect.right + 1
          || rect.top < canvasRect.top - 1
          || rect.bottom > canvasRect.bottom + 1;
      })
      .slice(0, 12)
      .map((node) => node.id || node.className || node.tagName.toLowerCase());
    const stageStyle = getComputedStyle(stage);
    const slideStyle = getComputedStyle(active);
    const stageCanvas = `${stageStyle.backgroundImage}|${stageStyle.backgroundColor}`;
    const slideCanvas = `${slideStyle.backgroundImage}|${slideStyle.backgroundColor}`;
    const slideCanvasTransparent = slideStyle.backgroundImage === 'none'
      && ['rgba(0, 0, 0, 0)', 'transparent'].includes(slideStyle.backgroundColor);
    const colorNumbers = stageStyle.backgroundColor.match(/[\d.]+/g)?.slice(0, 3).map(Number) || [];
    const relativeLuminance = colorNumbers.length === 3
      ? colorNumbers.map((channel) => {
        const value = channel / 255;
        return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
      }).reduce((sum, channel, index) => sum + channel * [0.2126, 0.7152, 0.0722][index], 0)
      : null;
    const renderedMode = relativeLuminance === null
      ? 'unknown'
      : (relativeLuminance >= 0.5 ? 'light' : 'dark');
    const config = JSON.parse(document.getElementById('deck-config').textContent);
    const stateSynchronized = active.getAttribute('aria-hidden') === 'false'
      && !active.hasAttribute('inert')
      && counter.textContent.trim() === `${Array.from(stage.children).indexOf(active) + 1} / ${stage.children.length}`;
    const stageWithinViewport = shellRect.left >= -1
      && shellRect.top >= -1
      && shellRect.right <= innerWidth + 1
      && shellRect.bottom <= innerHeight + 1;
    const documentOverflow = document.documentElement.scrollWidth > innerWidth + 1
      || document.documentElement.scrollHeight > innerHeight + 1;
    const slideOverflow = active.scrollWidth > active.clientWidth + 1
      || active.scrollHeight > active.clientHeight + 1;
    const backgroundModeMatches = config.background_mode === renderedMode
      && document.documentElement.dataset.backgroundMode === config.background_mode
      && slideCanvasTransparent;

    return {
      active_id: active.id,
      hash: location.hash,
      counter: counter.textContent.trim(),
      viewport: { width: innerWidth, height: innerHeight },
      stage_rect: rectObject(shellRect),
      stage_within_viewport: stageWithinViewport,
      document_overflow: documentOverflow,
      slide_overflow: slideOverflow,
      overflow_elements: overflowElements,
      state_synchronized: stateSynchronized,
      background: {
        declared_mode: config.background_mode,
        rendered_mode: renderedMode,
        stage_canvas: stageCanvas,
        slide_canvas: slideCanvas,
        slide_canvas_transparent: slideCanvasTransparent,
        pass: backgroundModeMatches,
      },
      pass: stageWithinViewport
        && !documentOverflow
        && !slideOverflow
        && overflowElements.length === 0
        && stateSynchronized
        && backgroundModeMatches,
    };
  });
}

async function inspectAllSlides(page, captureScreenshots = false) {
  const slides = await page.locator('.slide').evaluateAll((nodes) => (
    nodes.map((node) => ({ id: node.id, title: node.dataset.title || node.id }))
  ));
  const checks = [];
  const screenshots = [];
  for (const slide of slides) {
    await page.evaluate((id) => window.WowDeck.show(id), slide.id);
    await page.waitForFunction((id) => (
      document.querySelector('.slide.is-active')?.id === id
    ), slide.id);
    await settle(page);
    checks.push(await inspectActivePage(page));
    if (captureScreenshots) {
      const image = await page.locator('#stage').screenshot({ type: 'png' });
      screenshots.push({ ...slide, data: image.toString('base64') });
    }
  }
  return { checks, screenshots };
}

async function navigationCheck(page) {
  const steps = [];
  const record = async (action) => {
    const state = await page.evaluate(() => ({
      id: document.querySelector('.slide.is-active')?.id,
      hash: location.hash,
      focus: document.activeElement?.tagName.toLowerCase() || null,
    }));
    steps.push({ action, ...state });
  };
  await page.evaluate(() => window.WowDeck.show(0));
  await record('initial');
  for (const key of ['ArrowRight', 'PageDown', 'End', 'Home', ' ', 'ArrowLeft']) {
    await page.keyboard.press(key === ' ' ? 'Space' : key);
    await settle(page);
    await record(key === ' ' ? 'Space' : key);
  }
  await page.locator('#next-slide').click();
  await record('next button');
  await page.locator('#previous-slide').click();
  await record('previous button');
  await page.evaluate(() => { location.hash = '#practice-58'; });
  await page.waitForFunction(() => document.querySelector('.slide.is-active')?.id === 'practice-58');
  await record('hash id');
  await page.evaluate(() => { location.hash = '#3'; });
  await page.waitForFunction(() => document.querySelector('.slide.is-active')?.id === 'step-one');
  await record('hash number');
  const expectedIds = [
    'start-in-the-middle', 'order-makes-it-safe', 'step-one', 'practice-answer',
    'start-in-the-middle', 'order-makes-it-safe', 'start-in-the-middle',
    'order-makes-it-safe', 'start-in-the-middle', 'practice-58', 'step-one',
  ];
  return {
    pass: steps.map((step) => step.id).join('|') === expectedIds.join('|'),
    steps,
  };
}

async function renderContactSheet(browser, screenshots) {
  const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
  const page = await context.newPage();
  const cards = screenshots.map((item, index) => (
    `<figure><img src="data:image/png;base64,${item.data}" alt=""><figcaption>${index + 1}. ${escapeHtml(item.title)}</figcaption></figure>`
  )).join('');
  await page.setContent(`<!doctype html><meta charset="utf-8"><style>
    *{box-sizing:border-box}body{margin:0;padding:28px;background:#e8e4da;color:#182b31;font:18px/1.35 system-ui,sans-serif}
    h1{margin:0 0 22px;font-size:28px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}
    figure{margin:0;padding:10px;background:#fff;border:1px solid #c9c4b7;border-radius:10px;box-shadow:0 8px 22px rgb(0 0 0 / 10%)}
    img{display:block;width:100%;aspect-ratio:16/9;object-fit:cover;border:1px solid #d8d2c5}figcaption{padding:9px 3px 2px;font-weight:650}
  </style><h1>WowDeck forward fixture · all-slide contact sheet</h1><main class="grid">${cards}</main>`);
  await page.screenshot({ path: CONTACT_SHEET_PATH, fullPage: true, type: 'png' });
  await context.close();
}

async function runProfile(browser, baseUrl, profile, consoleErrors) {
  const context = await browser.newContext({
    viewport: profile.viewport,
    reducedMotion: profile.reducedMotion ? 'reduce' : 'no-preference',
  });
  const page = await context.newPage();
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(`${profile.name}: ${message.text()}`);
  });
  page.on('pageerror', (error) => consoleErrors.push(`${profile.name}: ${error.message}`));
  const suffix = profile.name === 'small' ? '#practice-58' : '';
  await page.goto(`${baseUrl}/${suffix}`, { waitUntil: 'networkidle' });
  await waitForReady(page);
  const initialDeepLink = profile.name === 'small'
    ? await page.evaluate(() => ({
      requested: '#practice-58',
      resolved: location.hash,
      active_id: document.querySelector('.slide.is-active')?.id,
    }))
    : null;
  const { checks, screenshots } = await inspectAllSlides(page, profile.name === 'standard');
  const result = {
    profile: profile.name,
    viewport: profile.viewport,
    reduced_motion: profile.reducedMotion,
    pages: checks,
  };
  if (profile.name === 'standard') result.navigation = await navigationCheck(page);
  if (profile.name === 'small') {
    result.deep_link = initialDeepLink;
    result.deep_link.pass = result.deep_link.resolved === '#practice-58'
      && result.deep_link.active_id === 'practice-58';
  }
  if (profile.name === 'reduced-motion') {
    result.state = await page.evaluate(() => ({
      media_matches: matchMedia('(prefers-reduced-motion: reduce)').matches,
      all_reveals_visible: Array.from(document.querySelectorAll('.reveal'))
        .every((node) => getComputedStyle(node).opacity === '1'),
      all_reveal_animations_disabled: Array.from(document.querySelectorAll('.reveal'))
        .every((node) => getComputedStyle(node).animationName === 'none'),
    }));
    result.state.pass = Object.values(result.state).every(Boolean);
  }
  result.pass = result.pages.every((item) => item.pass)
    && (result.navigation?.pass ?? true)
    && (result.deep_link?.pass ?? true)
    && (result.state?.pass ?? true);
  await context.close();
  return { result, screenshots };
}

(async () => {
  const facts = currentValidation();
  if (VERIFY_ONLY) verifyRecordedEvidence(facts);
  const server = await startServer();
  const address = server.address();
  const baseUrl = `http://127.0.0.1:${address.port}`;
  const browser = await chromium.launch({ headless: true });
  const consoleErrors = [];
  try {
    const probeContext = await browser.newContext();
    const probePage = await probeContext.newPage();
    const cdp = await probeContext.newCDPSession(probePage);
    const browserInfo = await cdp.send('Browser.getVersion');
    await probeContext.close();

    const profiles = [
      { name: 'standard', viewport: { width: 1440, height: 900 }, reducedMotion: false },
      { name: 'small', viewport: { width: 800, height: 600 }, reducedMotion: false },
      { name: 'reduced-motion', viewport: { width: 1440, height: 900 }, reducedMotion: true },
    ];
    const checks = [];
    let screenshots = [];
    for (const profile of profiles) {
      const outcome = await runProfile(browser, baseUrl, profile, consoleErrors);
      checks.push(outcome.result);
      if (outcome.screenshots.length) screenshots = outcome.screenshots;
    }
    await renderContactSheet(browser, screenshots);

    const canvasSignatures = new Set(
      checks.flatMap((check) => check.pages.map((item) => item.background.stage_canvas)),
    );
    const assertions = {
      seven_slides: checks.every((check) => check.pages.length === 7),
      navigation_only: facts.features.join('|') === 'navigation',
      keyboard_pointer_and_hash_navigation: Boolean(
        checks.find((check) => check.profile === 'standard')?.navigation?.pass,
      ),
      no_layout_overflow: checks.every((check) => check.pages.every((item) => (
        item.stage_within_viewport && !item.document_overflow && !item.slide_overflow
      ))),
      no_console_errors: consoleErrors.length === 0,
      reduced_motion_preserves_meaning: Boolean(
        checks.find((check) => check.profile === 'reduced-motion')?.state?.pass,
      ),
      background_mode_consistent: checks.every((check) => check.pages.every((item) => (
        item.background.pass && item.background.declared_mode === facts.background_mode
      ))) && canvasSignatures.size === 1,
      contact_sheet_generated: fs.existsSync(CONTACT_SHEET_PATH) && screenshots.length === 7,
      artifact_matches_receipt: facts.receipt_status === 'current'
        && facts.index_sha256 === sha256(INDEX_PATH),
    };
    const passed = checks.every((check) => check.pass)
      && Object.values(assertions).every(Boolean);
    const output = {
      schema_version: 1,
      status: passed ? 'PASS' : 'FAIL',
      generated_at: new Date().toISOString(),
      artifact: {
        path: 'index.html',
        index_sha256: facts.index_sha256,
        artifact_sha256: facts.artifact_sha256,
        source_revision: facts.source_revision,
        builder_revision: facts.builder_revision,
        source_sha256: facts.source_sha256,
        variant: facts.variant,
        background_mode: facts.background_mode,
      },
      browser: {
        name: browserInfo.product,
        protocol_version: browserInfo.protocolVersion,
        mode: 'headless',
      },
      runner: {
        path: path.basename(__filename),
        sha256: sha256(__filename),
      },
      target: { transport: 'loopback HTTP', stage: facts.config.aspect },
      contact_sheet: {
        path: path.basename(CONTACT_SHEET_PATH),
        sha256: sha256(CONTACT_SHEET_PATH),
        slide_count: screenshots.length,
      },
      assertions,
      console_errors: consoleErrors,
      checks,
    };
    if (VERIFY_ONLY) {
      assert.equal(passed, true, 'live browser verification failed');
      console.log('Browser verification: PASS');
    } else {
      fs.writeFileSync(CHECK_PATH, `${JSON.stringify(output, null, 2)}\n`, 'utf8');
      console.log(`Browser check: ${output.status}`);
      console.log(`Contact sheet: ${path.basename(CONTACT_SHEET_PATH)}`);
    }
    console.log(`Artifact SHA256: ${facts.artifact_sha256}`);
    if (!passed) process.exitCode = 1;
  } finally {
    await browser.close();
    await new Promise((resolve) => server.close(resolve));
    if (VERIFY_DIRECTORY) {
      fs.rmSync(VERIFY_DIRECTORY, { recursive: true, force: true });
    }
  }
})().catch((error) => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
