import json
import hashlib
import os
import shutil
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skill/wowdeck/scripts/inspect_deck.cjs'
RUNTIME = Path.home() / '.cache/codex-runtimes/codex-primary-runtime/dependencies/node'


class DeckInspectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        candidates = [os.environ.get('WOWDECK_NODE'), str(RUNTIME / 'bin/node'), shutil.which('node')]
        cls.node = next((candidate for candidate in candidates if candidate and Path(candidate).is_file()), None)
        if not cls.node:
            raise unittest.SkipTest('Node.js is unavailable')
        cls.env = dict(os.environ, NODE_PATH=os.environ.get('WOWDECK_NODE_PATH', str(RUNTIME / 'node_modules')))
        probe = subprocess.run([cls.node, '-e', "require.resolve('playwright'); require.resolve('sharp')"],
                               cwd=ROOT, env=cls.env, capture_output=True)
        if probe.returncode:
            raise unittest.SkipTest('Playwright or sharp unavailable; set WOWDECK_NODE_PATH')

    def test_capture_and_refuse_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            html = base / 'deck.html'
            html.write_text('''<!doctype html><style>.slide{display:none}.slide.is-active{display:block}</style>
<section id="first" data-title="Preferred title" class="slide is-active"><h1>one</h1><img src="missing.png"></section><section id="second" class="slide"><h1>two</h1></section>
<script>console.error('synthetic error'); let current=0; window.WowDeck={show(i){current=i; document.querySelectorAll('.slide').forEach((s,n)=>s.classList.toggle('is-active',n===i));},currentIndex(){return current}}</script>''')
            output = base / 'evidence'
            env = self.env
            command = [self.node, str(SCRIPT), str(html), str(output)]
            subprocess.run(command, env=env, check=True, capture_output=True, text=True)
            report = json.loads((output / 'report.json').read_text())
            self.assertEqual(report['type'], 'render_runtime_evidence')
            for mode in ('normal', 'reduced-motion'):
                result = report['modes'][mode]
                self.assertEqual(len(result['screenshots']), 2)
                for screenshot in result['screenshots']:
                    data = (output / screenshot['file']).read_bytes()
                    self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
                    self.assertEqual(hashlib.sha256(data).hexdigest(), screenshot['sha256'])
                self.assertTrue(all(n['confirmed'] for n in result['navigation']))
                self.assertTrue(result['resource_failures'])
                self.assertEqual(result['navigation'][0]['title'], 'Preferred title')
                self.assertTrue(result['navigation'][0]['failed_images'])
                self.assertTrue(result['navigation'][1]['bounds']['visible'])
                self.assertEqual(result['viewport'], {'width': 1280, 'height': 720})
                self.assertTrue(any('synthetic error' in e for e in result['console_errors']))
                self.assertTrue((output / result['contact_sheet']['file']).is_file())
            original = (output / 'report.json').read_bytes()
            retry = subprocess.run(command, env=env, capture_output=True, text=True)
            self.assertNotEqual(retry.returncode, 0)
            self.assertEqual(original, (output / 'report.json').read_bytes())

    def test_single_slide_and_delayed_fade(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            html = base / 'deck.html'
            html.write_text('''<!doctype html><style>
.slide { width: 500px; height: 300px; opacity: 0; animation: fade 0.5s 0.2s forwards }
@keyframes fade { to { opacity: 1 } }</style><section class="slide" id="only"><h1>Only</h1></section>''')
            output = base / 'evidence'
            env = self.env
            subprocess.run([self.node, str(SCRIPT), str(html), str(output)], env=env, check=True, capture_output=True, text=True)
            report = json.loads((output / 'report.json').read_text())
            for mode in ('normal', 'reduced-motion'):
                nav = report['modes'][mode]['navigation'][0]
                self.assertEqual(nav['method'], 'single-visible-slide')
                self.assertTrue(nav['confirmed'])
                self.assertGreater(nav['bounds']['opacity'], 0.99)
                self.assertEqual(nav['id'], 'only')

    def test_transparent_ancestor_cannot_confirm_visible_navigation(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            html = base / 'deck.html'
            html.write_text('<main style="opacity:0"><section class="slide is-active">'
                            '<h1>Hidden by ancestor</h1></section></main>'
                            '<script>window.WowDeck={show(){},currentIndex(){return 0}}</script>')
            output = base / 'evidence'
            result = subprocess.run([self.node, str(SCRIPT), str(html), str(output), '--settle-ms', '0'],
                                    env=self.env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            report = json.loads((output / 'report.json').read_text())
            nav = report['modes']['normal']['navigation'][0]
            self.assertEqual(nav['current_index'], 0)
            self.assertEqual(nav['bounds']['opacity'], 1)
            self.assertEqual(nav['bounds']['effective_opacity'], 0)
            self.assertFalse(nav['bounds']['visible'])
            self.assertFalse(nav['confirmed'])
            self.assertIn('occlusion', report['visibility_scope'])

    def test_noop_api_cannot_confirm_a_multislide_document(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            html = base / 'deck.html'
            html.write_text('<section class="slide"><h1>A</h1></section>'
                            '<section class="slide"><h1>B</h1></section>'
                            '<script>window.WowDeck={show(){}}</script>')
            result = subprocess.run([self.node, str(SCRIPT), str(html), str(base / 'evidence')],
                                    env=self.env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('could not be confirmed', result.stderr)


if __name__ == '__main__':
    unittest.main()
