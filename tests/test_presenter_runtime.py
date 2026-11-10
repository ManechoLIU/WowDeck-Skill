from __future__ import annotations

import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INIT_DECK = REPO_ROOT / "skill" / "wowdeck" / "scripts" / "init_deck.py"
BUNDLED_NODE_ROOT = (
    Path.home()
    / ".cache"
    / "codex-runtimes"
    / "codex-primary-runtime"
    / "dependencies"
    / "node"
)


BROWSER_RUNNER = r"""
const assert = require('node:assert/strict');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');

async function text(page, selector) {
  return (await page.locator(selector).textContent()).trim();
}

(async () => {
  const [htmlPath, scenario, expectedAspect] = process.argv.slice(2);
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  page.setDefaultTimeout(3000);
  const pageErrors = [];
  page.on('pageerror', (error) => pageErrors.push(String(error)));

  try {
    await page.goto(pathToFileURL(htmlPath).href);
    await page.waitForFunction(() => document.documentElement.dataset.ready === 'true');

    if (scenario === 'notes') {
      assert.equal(await page.locator('#deck-controls').getAttribute('hidden'), null);
      assert.equal(await page.locator('#presenter-controls').getAttribute('hidden'), null);
      assert.equal(await text(page, '#notes-toggle'), 'Notes');

      await page.locator('#notes-toggle').click();
      assert.equal(await text(page, '#presenter-notes'), 'Alpha speaker note');
      assert.equal(await text(page, '#planned-time'), 'Planned time: 00:30');

      await page.locator('#next-slide').click();
      assert.equal(await page.evaluate(() => window.WowDeck.currentIndex()), 1);
      assert.equal(await text(page, '#presenter-notes'), 'Beta speaker note');
      assert.equal(await text(page, '#planned-time'), 'Planned time: 00:45');
    } else if (scenario === 'timer') {
      assert.equal(await text(page, '#elapsed-time'), '00:00');
      assert.equal(await text(page, '#presenter-timer-toggle'), 'Start');
      await page.waitForTimeout(1200);
      assert.equal(await text(page, '#elapsed-time'), '00:00');

      await page.locator('#presenter-timer-toggle').click();
      assert.equal(await text(page, '#presenter-timer-toggle'), 'Pause');
      await page.waitForTimeout(1200);
      assert.equal(await text(page, '#elapsed-time'), '00:01');

      await page.locator('#presenter-timer-toggle').click();
      assert.equal(await text(page, '#presenter-timer-toggle'), 'Resume');
      const pausedAt = await text(page, '#elapsed-time');
      await page.waitForTimeout(1200);
      assert.equal(await text(page, '#elapsed-time'), pausedAt);

      await page.locator('#presenter-timer-toggle').click();
      assert.equal(await text(page, '#presenter-timer-toggle'), 'Pause');
    } else if (scenario === 'unavailable') {
      assert.notEqual(await page.locator('#deck-controls').getAttribute('hidden'), null);
      assert.notEqual(await page.locator('#presenter-controls').getAttribute('hidden'), null);
      assert.equal(await page.locator('#notes-toggle').isDisabled(), true);
      assert.equal(await page.locator('#presenter-timer-toggle').isDisabled(), true);
      await page.keyboard.press('n');
      assert.notEqual(await page.locator('#presenter-panel').getAttribute('hidden'), null);
    } else if (scenario === 'zh') {
      assert.equal(await page.locator('#deck-controls').getAttribute('aria-label'), '演示控制');
      assert.equal(await page.locator('#previous-slide').getAttribute('aria-label'), '上一张');
      assert.equal(await page.locator('#next-slide').getAttribute('aria-label'), '下一张');
      assert.equal(await text(page, '#notes-toggle'), '备注');
      assert.equal(await text(page, '#presenter-timer-toggle'), '开始');
      assert.equal(await page.locator('#elapsed-time').getAttribute('aria-label'), '已用时间');

      await page.locator('#notes-toggle').click();
      assert.equal(await text(page, '#presenter-title'), '演讲者备注');
      assert.equal(await page.locator('#notes-close').getAttribute('aria-label'), '关闭演讲者备注');
      assert.equal(await text(page, '#planned-time'), '计划时长：00:30');

      await page.locator('#presenter-timer-toggle').click();
      assert.equal(await text(page, '#presenter-timer-toggle'), '暂停');
      await page.locator('#presenter-timer-toggle').click();
      assert.equal(await text(page, '#presenter-timer-toggle'), '继续');
    } else if (scenario === 'aspect') {
      assert.equal(await page.evaluate(() => window.WowDeck.config.aspect), expectedAspect);
      assert.equal(
        await page.evaluate(() => document.documentElement.dataset.aspect),
        expectedAspect,
      );
      const expectedWidth = expectedAspect === '4:3' ? '1200px' : '1600px';
      assert.equal(
        await page.evaluate(() => getComputedStyle(document.documentElement)
          .getPropertyValue('--stage-width').trim()),
        expectedWidth,
      );
    } else if (scenario === 'background-mode') {
      assert.equal(await page.evaluate(() => window.WowDeck.config.background_mode), expectedAspect);
      assert.equal(
        await page.evaluate(() => document.documentElement.dataset.backgroundMode),
        expectedAspect,
      );
      const tokens = await page.evaluate(async () => {
        const root = document.documentElement;
        const readTokens = () => {
          const style = getComputedStyle(root);
          return [
            root.dataset.backgroundMode,
            style.getPropertyValue('--slide-bg').trim(),
            style.getPropertyValue('--ink').trim(),
          ];
        };
        const before = readTokens();
        window.WowDeck.next();
        await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        const after = readTokens();
        return [before, after];
      });
      assert.ok(tokens[0][1]);
      assert.ok(tokens[0][2]);
      assert.deepEqual(tokens[0], tokens[1]);
    } else if (scenario === 'navigation') {
      assert.equal(await page.evaluate(() => window.WowDeck.currentIndex()), 0);
      assert.equal(await page.locator('#presenter-controls').getAttribute('hidden'), '');
      await page.locator('#next-slide').click();
      assert.equal(await page.evaluate(() => window.WowDeck.currentIndex()), 1);
      assert.equal(await text(page, '#slide-counter'), '2 / 2');
      assert.equal(await page.evaluate(() => location.hash), '#slide-2');
    } else if (scenario === 'navigation-focus') {
      await page.locator('#next-slide').click();
      assert.equal(await page.evaluate(() => window.WowDeck.currentIndex()), 1);
      assert.equal(await page.evaluate(() => document.activeElement?.id), 'next-slide');

      await page.keyboard.press('ArrowRight');
      assert.equal(await page.evaluate(() => window.WowDeck.currentIndex()), 2);
      await page.waitForFunction(() => document.activeElement?.id === 'slide-3');

      await page.evaluate(() => {
        const sentinel = document.createElement('button');
        sentinel.id = 'focus-sentinel';
        document.body.append(sentinel);
        sentinel.focus();
      });
      await page.evaluate(() => { location.hash = '#1'; });
      await page.waitForFunction(() => window.WowDeck.currentIndex() === 0);
      assert.equal(await page.evaluate(() => document.activeElement?.id), 'focus-sentinel');
    } else if (scenario === 'core') {
      assert.equal(await page.evaluate(() => window.WowDeck.currentIndex()), 0);
      assert.equal(await page.evaluate(() => typeof window.WowDeck.next), 'undefined');
      assert.notEqual(await page.locator('#deck-controls').getAttribute('hidden'), null);
    } else {
      throw new Error(`Unknown browser scenario: ${scenario}`);
    }

    assert.deepEqual(pageErrors, []);
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error.stack || error);
  process.exitCode = 1;
});
"""


class PresenterRuntimeBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.node, cls.node_path = cls.resolve_playwright()

    @classmethod
    def resolve_playwright(cls) -> tuple[str, str]:
        node_override = os.environ.get("WOWDECK_NODE")
        node_candidates = [
            node_override,
            str(BUNDLED_NODE_ROOT / "bin" / "node"),
            shutil.which("node"),
        ]
        node = next((candidate for candidate in node_candidates if candidate and Path(candidate).is_file()), None)
        if node is None:
            raise unittest.SkipTest("Node.js is unavailable; Chromium runtime regression not run")

        node_path = os.environ.get("WOWDECK_NODE_PATH", str(BUNDLED_NODE_ROOT / "node_modules"))
        environment = {**os.environ, "NODE_PATH": node_path}
        probe = subprocess.run(
            [node, "-e", "require.resolve('playwright')"],
            cwd=REPO_ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        if probe.returncode != 0:
            raise unittest.SkipTest(
                "Playwright is unavailable; set WOWDECK_NODE_PATH to its node_modules directory"
            )
        return node, node_path

    def create_deck(
        self,
        root: Path,
        *,
        features: tuple[str, ...],
        slides: tuple[tuple[str, str | None, int], ...],
        lang: str = "en",
        aspect: str = "16:9",
        background_mode: str = "light",
    ) -> Path:
        deck_dir = root / "deck"
        feature_args = features or ("none",)
        completed = subprocess.run(
            [
                sys.executable,
                str(INIT_DECK),
                str(deck_dir),
                "--title",
                "Runtime Test Deck",
                "--lang",
                lang,
                "--aspect",
                aspect,
                "--background-mode",
                background_mode,
                "--features",
                *feature_args,
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

        slide_markup = []
        for index, (title, note, duration) in enumerate(slides, start=1):
            note_markup = ""
            if note is not None:
                note_markup = (
                    f'<aside data-notes data-duration="{duration}" hidden>'
                    f"{html.escape(note)}</aside>"
                )
            slide_markup.append(
                textwrap.dedent(
                    f"""
                    <section
                      class="slide{' is-active' if index == 1 else ''}"
                      id="slide-{index}"
                      data-title="{html.escape(title, quote=True)}"
                      aria-labelledby="slide-{index}-title"
                      aria-hidden="{'false' if index == 1 else 'true'}"
                      tabindex="-1"
                    >
                      <div class="slide-content">
                        <h1 id="slide-{index}-title">{html.escape(title)}</h1>
                      </div>
                      {note_markup}
                    </section>
                    """
                ).strip()
            )

        index_path = deck_dir / "index.html"
        source = index_path.read_text(encoding="utf-8").replace(
            "WOWDECK_PLACEHOLDER", "Runtime test content"
        )
        source, replacements = re.subn(
            r'(<main\s+id="stage"[^>]*>).*?(</main>)',
            lambda match: f"{match.group(1)}\n{''.join(slide_markup)}\n{match.group(2)}",
            source,
            count=1,
            flags=re.DOTALL,
        )
        self.assertEqual(replacements, 1)
        index_path.write_text(source, encoding="utf-8")
        return index_path

    def run_browser(self, index_path: Path, scenario: str, *arguments: str) -> None:
        runner_path = index_path.parent / "presenter-runtime-runner.cjs"
        runner_path.write_text(BROWSER_RUNNER, encoding="utf-8")
        completed = subprocess.run(
            [self.node, str(runner_path), str(index_path), scenario, *arguments],
            cwd=REPO_ROOT,
            env={**os.environ, "NODE_PATH": self.node_path},
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )

    def test_presenter_notes_follow_the_current_slide(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            index_path = self.create_deck(
                Path(temporary),
                features=("navigation", "presenter"),
                slides=(
                    ("Alpha", "Alpha speaker note", 30),
                    ("Beta", "Beta speaker note", 45),
                ),
            )
            self.run_browser(index_path, "notes")

    def test_presenter_timer_waits_for_explicit_start_and_pauses(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            index_path = self.create_deck(
                Path(temporary),
                features=("presenter",),
                slides=(("Alpha", "Alpha speaker note", 30),),
            )
            self.run_browser(index_path, "timer")

    def test_presenter_controls_are_unavailable_without_nonempty_notes(self) -> None:
        for label, note in (("missing", None), ("empty", "   ")):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                index_path = self.create_deck(
                    Path(temporary),
                    features=("presenter",),
                    slides=(("Alpha", note, 30),),
                )
                self.run_browser(index_path, "unavailable")

    def test_presenter_runtime_uses_zh_copy_for_zh_language(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            index_path = self.create_deck(
                Path(temporary),
                features=("navigation", "presenter"),
                slides=(("甲", "甲页备注", 30),),
                lang="zh-CN",
            )
            self.run_browser(index_path, "zh")

    def test_navigation_only_standard_aspect_stays_operational(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            index_path = self.create_deck(
                Path(temporary),
                features=("navigation",),
                slides=(("Alpha", None, 0), ("Beta", None, 0)),
                aspect="16:9",
            )
            self.run_browser(index_path, "aspect", "16:9")
            self.run_browser(index_path, "navigation")

    def test_deck_wide_background_mode_stays_constant_across_navigation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            index_path = self.create_deck(
                Path(temporary),
                features=("navigation",),
                slides=(("Alpha", None, 0), ("Beta", None, 0)),
                background_mode="dark",
            )
            self.run_browser(index_path, "background-mode", "dark")

    def test_navigation_focus_depends_on_the_input_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            index_path = self.create_deck(
                Path(temporary),
                features=("navigation",),
                slides=(
                    ("Alpha", None, 0),
                    ("Beta", None, 0),
                    ("Gamma", None, 0),
                ),
            )
            self.run_browser(index_path, "navigation-focus")

    def test_core_only_four_three_initializes_without_controls(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            index_path = self.create_deck(
                Path(temporary),
                features=(),
                slides=(("Alpha", None, 0),),
                aspect="4:3",
            )
            self.run_browser(index_path, "aspect", "4:3")
            self.run_browser(index_path, "core")


if __name__ == "__main__":
    unittest.main()
