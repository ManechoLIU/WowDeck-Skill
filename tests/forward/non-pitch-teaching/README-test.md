# 重建与验证

在本目录运行：

```bash
python3 build.py
python3 ../../../skill/wowdeck/scripts/validate_deck.py index.html --receipt
python3 ../../../skill/wowdeck/scripts/validate_deck.py index.html --check-receipt validation-receipt.json
node browser-check.cjs
node browser-check.cjs --verify
```

`build.py` 同时更新 `deck-dependencies.json` 中的 canonical source 与 builder 哈希。

真实 Chromium 的标准视口、小视口、键盘/hash 导航、布局溢出、控制台错误、统一背景模式与 reduced-motion 结果记录在 `browser-check.json`，全部页面的渲染缩略图写入 `contact-sheet.png`。`--verify` 会先验真已提交证据，再把实时 Chromium 和 contact sheet 输出到临时目录，不改写仓库。脚本优先使用已安装的 Playwright；Codex 桌面环境会自动回退到其内置运行时，也可通过 `WOWDECK_NODE_PATH` 指定 `node_modules`。
