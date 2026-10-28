# WowDeck Skill

WowDeck 是一个场景驱动的 HTML 演示生成 Skill。它先理解受众、传播任务、内容依赖、事实风险和交付环境，再生成适合当前场景的内容逻辑、视觉语言、可选运行能力与验收方案。

它不是固定的商业提案模板，也不默认要求 16:9、讲稿、视频、计时或行业视觉。

## 仓库结构

```text
skill/wowdeck/   可安装的 Skill
tests/           脚本、fixture 与前向验证
docs/            设计决策与方法论
```

## 安装

首次安装时，将 `skill/wowdeck` 复制到 Codex 的 Skills 目录后重启或重新加载会话：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills/wowdeck"
cp -R skill/wowdeck/. "${CODEX_HOME:-$HOME/.codex}/skills/wowdeck/"
```

验证过的本地安装副本位于 `$CODEX_HOME/skills/wowdeck`；该目录不是源码事实源。升级时先在源码仓库完成测试，再用干净的临时目录原子替换旧安装，不要把新文件合并进旧目录，否则已删除的旧 reference 或 fixture 会残留并继续误导调用。

## 使用范围

- 主要产物：浏览器原生 HTML 演示
- 可选能力：navigation、presenter、media、dialog
- 独立验收：HTML、PDF、PPTX、自动路演、MP4、离线包、二维码、公网链接和正式发布

方法论与质量边界见 [通用设计规格](docs/superpowers/specs/2026-10-02-general-presentation-skill-design.md)。

## 验证

```bash
python3 -m py_compile skill/wowdeck/scripts/*.py
python3 -m unittest discover -s tests -v
```

自动化测试覆盖 core-only、条件 features、presenter 浏览器行为、媒体准备、poster/manifest 规则、依赖闭包、脚本注入防护，以及验收回执的陈旧检测。真实演示仍需按目标浏览器、视口和交付格式做视觉与行为验收。

## 状态

本仓库只管理 Skill 源码与测试，不部署原 WowDeck 案例网站，也不包含案例私密材料和大媒体。
