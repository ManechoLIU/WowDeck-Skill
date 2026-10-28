# 重建与验证

在本目录运行：

```bash
python3 build.py
python3 ../../../skill/wowdeck/scripts/validate_deck.py index.html --receipt
python3 ../../../skill/wowdeck/scripts/validate_deck.py index.html --check-receipt validation-receipt.json
```

`build.py` 同时更新 `deck-dependencies.json` 中的 canonical source 与 builder 哈希。

真实 Chromium 的标准视口、小视口、键盘/hash 导航、布局溢出、控制台错误与 reduced-motion 结果记录在 `browser-check.json`。
