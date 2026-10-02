# WowDeck 通用场景演示生成 Skill 重构设计

日期：2026-10-02

状态：待用户书面审查

目标 Skill：`/Users/echoman/.codex/skills/wowdeck`

## 1. 目标

把 WowDeck 从“证据驱动的行业方案／产品提案型 HTML 演示生成器”重构为“根据具体传播场景与分享群体，动态设计内容逻辑、解释深度、注意力节奏、视觉逻辑、运行能力和验收逻辑的通用演示生成 Skill”。

这里的“通用”不等于准备更多固定模板，而是让 Skill 先理解本次演示为什么存在，再为本次任务生成合适的演示策略。主要交付仍为高质量 HTML 演示；不在本轮扩展到原生 PPTX 或 Google Slides。

## 2. 成功标准

重构后的 Skill 必须满足：

1. 教学、研究答辩、数据报告、内部汇报、品牌发布、融资／销售和产品演示不会被强制套入同一条商业提案叙事。
2. 每次生成前都形成一份与当前任务对应的 `Presentation Strategy Contract`，说明内容为什么按该顺序推进。
3. 场景类型只作为推理先验和检查清单，不能直接决定固定页序或固定视觉模板。
4. 真实性、可读性、隐私、无障碍与目标环境验收保留为通用质量底线；证据账本、明确决策、讲稿、计时、视频和交互按需要启用。
5. HTML Runtime 的功能能够按交付环境组合；静态演示不因缺少讲稿或视频而失败。
6. 独立前向测试必须证明多个场景产生了实质不同的内容逻辑，而不只是不同视觉。
7. 内容深度、术语、示例、信息密度和展示方式必须匹配具体分享群体，使新手能建立直觉、专业受众也能获得必要细节。
8. 每份演示必须有明确的强调层级；叙事型或较长演示还要设计节奏峰谷。需要强调的内容可以使用比例、留白、对比、渐进揭示、空间连续性、动效或媒体形成高光，但不得全局平均用力或为炫技添加特效。

## 3. 非目标

- 不在本轮生成或编辑原生 `.pptx`、Google Slides。
- 不建立行业视觉模板市场或大量固定主题。
- 不以关键词分类器代替对材料、受众与传播任务的理解。
- 不保证所有演示都包含动画、视频、目录、讲稿或计时。
- 不把当前 WowDeck 案例的事件闭环、试点结构或证据标签保留为全局默认。

## 4. 核心架构

```text
输入材料与交付约束
        ↓
Scenario Diagnosis
        ↓
Presentation Strategy Contract
        ↓
Content Logic Synthesis
        ↓
Explanation + Attention Choreography
        ↓
Visual Grammar Synthesis
        ↓
Runtime Profile Composition
        ↓
HTML Construction
        ↓
Universal + Conditional Quality Gates
```

### 4.1 Scenario Diagnosis

生成前先描述本次演示，而不是先选择页型：

| 维度 | 要回答的问题 |
|---|---|
| audience | 谁看、专业程度、已有认知、关注点、语言习惯、可能抗拒什么 |
| audience shift | 希望观众在认知、能力、情绪或行动上发生什么变化 |
| communication job | 教会、解释、汇报、说服、探索、发布、答辩、演示或组合任务 |
| content nature | 概念、流程、数据、研究、故事、产品、品牌、项目状态或混合内容 |
| claim risk | 错误陈述会造成多大影响，来源与限定需要多严格 |
| delivery context | 现场演讲、课堂、答辩、异步阅读、大屏发布、打印或混合环境 |
| sharing profile | 内容是现场一次性观看、会后转发、群聊分享、管理层逐级转发还是长期自助阅读 |
| time and scale | 时长、预计页数范围、信息密度与观众注意力条件 |
| media role | 证明、解释、操作演示、情绪氛围、品牌资产或不需要媒体 |
| interaction need | 是否需要目录、深链、弹层、练习、演示控制、讲稿或计时 |

如果信息足以合理推断，则记录假设并继续；只有缺失信息会实质改变受众、目标、交付格式、外部成本或发布权限时才询问用户。

### 4.2 Presentation Strategy Contract

诊断后生成本次专属策略，不采用统一的“痛点—方案—能力—机制—试点”合同：

```text
Audience:
Audience shift:
Communication job:
Central question or thesis:
Starting point:
Content movement:
Sequence rationale:
Slide roles:
Explanation ladder:
Emphasis map:
Rhythm and reveal plan:
Claim and evidence policy:
Visual grammar:
Media role:
Closing behavior:
Sharing profile:
Runtime profile:
Acceptance profile:
```

`Content movement` 描述观众的理解如何一步步变化；`Sequence rationale` 解释为什么必须按该顺序；`Slide roles` 只定义页面承担的作用，不规定固定页数、标题或布局。`Explanation ladder` 声明本次选择、压缩或跳过哪些解释层及原因；`Emphasis map` 和 `Rhythm and reveal plan` 说明是否需要高潮、哪些内容应被突出、哪些页面承担铺垫与呼吸。

### 4.3 Content Logic Synthesis

Skill 根据材料的内在依赖关系生成内容顺序。以下只是可组合的叙事先验，不是模板：

- 教学：诊断已有认知 → 学习目标 → 概念脚手架 → 示例 → 练习／迁移 → 反馈 → 回顾。
- 研究：问题 → 已知与缺口 → 方法 → 结果 → 解释 → 局限 → 贡献／讨论。
- 数据分析：问题与口径 → 观察 → 模式 → 驱动因素 → 不确定性 → 情景／行动。
- 状态汇报：目标与范围 → 变化 → 原因 → 风险／阻塞 → 所需支持 → 下一阶段。
- 品牌发布：世界观／信念 → 张力 → 揭晓 → 体验 → 记忆锚点 → 行动号召。
- 说服／融资：变化与机会 → 问题 → 方案 → 证据 → 可行性／模式 → 风险 → 请求。
- 产品演示：用户任务 → 关键时刻 → 操作体验 → 结果 → 边界 → 下一步。

允许混合和重组。Skill 必须记录对相关先验的采用、改写和拒绝，以及它们与材料依赖和 audience shift 的关系；如果现有先验都不匹配，则从内容依赖和 audience shift 重新生成逻辑。

通用写作底线：

- 每页有一个明确的主要作用和视觉焦点，但不强制每页都是“结论证明”。
- 标题可以承担结论、问题、步骤、章节或情绪节拍，取决于场景。
- 复杂性逐步增加，前置观众理解后续内容所需的信息。
- 来源、限定与不确定性靠近相关声明；其显著程度与 claim risk 成比例。
- 结尾由传播任务决定，可以是决策、总结、练习、讨论、启发、庆祝、行动或开放问题。

### 4.4 Explanation and Attention Choreography

“深入浅出”不是统一减少文字，而是根据分享群体选择解释层。以下层级可以采用、跳过、压缩、展开或回溯，不是固定播放顺序：

1. 从观众已经理解的事物或具体情境进入；
2. 用一个例子、类比、演示或可视关系建立直觉；
3. 给出准确概念、模型、机制或数据；
4. 只在当前群体需要时展开方法、边界和专业细节；
5. 通过对比、练习、总结或应用确认观众已经完成预期转变。

不同分享群体采用不同表达：

- 新手：减少前置术语，以具体例子和渐进揭示搭建理解。
- 专业受众：保留精确定义、方法、边界和可质询细节，避免过度简化。
- 管理者：优先影响、权衡、风险和所需支持，技术细节按需展开。
- 公众或群聊转发：保证脱离现场讲解也能理解，关键语境、字幕和结论不能只存在于讲稿。
- 品牌受众：允许情绪、审美和记忆先行，但核心承诺仍需清晰可辨。

每份 deck 的策略合同都要说明 `Emphasis and rhythm decision`。短格式、参考资料或非叙事产物可以没有高潮，但仍需清晰强调层级；需要演讲节奏或情绪推进时，再生成可审查的 `Emphasis map`：

- 标出主要高潮、章节峰值或局部重点；如果不设置高潮，说明为什么层级而非节奏更适合当前场景。
- 每个重点至少记录：`slide id / 受众要注意什么 / 强调手段 / 服务的语义 / 静态或 reduced-motion 等价物`。
- 为每个重点选择与语义匹配的强调手段：尺寸与留白、强对比、构图变化、局部放大、渐进揭示、空间连续转场、数据变化、媒体或短暂动效。
- 让普通页面承担铺垫、连接和呼吸，避免所有页面同样密集、同样响亮、同样运动。
- 重点效果必须解释“为什么此处需要强调”；如果删除效果不损失理解、层级、因果或情绪，则不应添加。
- 重要信息不能只在动画过程中短暂出现；reduced-motion 下必须保留完整含义和清晰层级。

静态强调包括比例、留白、对比、构图、色彩和排版层级，适用于所有 deck。时间型特效包括转场、渐进揭示、局部动画和媒体时序，只在启用 `motion` profile 且具有语义理由时使用。

需要节奏推进时，至少同时考虑信息密度、页面尺度、视觉焦点位置、切换速度和媒体时长。演示应有收放与峰谷，不能全局平淡，也不能持续高刺激导致重点消失。

### 4.5 Claim Integrity

保留真实性原则，但把完整证据账本从全局强制改为风险驱动：

- 高风险商业、科学、医疗、财务或生产声明：使用来源、状态、置信度和允许措辞。
- 普通内部汇报或教学：保留必要来源与事实／推断区分，不强制在画面上显示四类状态标签。
- 模拟界面、生成数据、未来能力和未经验证结果必须明确标识。
- 品牌氛围素材可以承担情绪作用，但不得伪装成事实证明。

`VERIFIED / PROPOSED / SIMULATED / UNKNOWN` 作为可用语义，不再要求每份 deck 都显式展示。

### 4.6 Visual Grammar Synthesis

视觉不从行业名称直接映射模板，而从以下因素共同推导：

- 内容的认知任务：比较、记忆、理解关系、观察趋势、体验品牌或练习技能；
- 受众与场合：课堂、董事会、会议论文、发布会、异步阅读；
- 内容载体：数据、照片、流程、代码、概念、人物故事；
- 品牌资产与语言；
- 信息密度、节奏和演示距离。

每次生成视觉合同：

```text
Visual purpose:
Composition model:
Primary geometry:
Material and depth:
Typography behavior:
Color semantics:
Diagram or chart grammar:
Image and media treatment:
Emphasis hierarchy:
Rhythm and density:
Motion grammar:
Traits to avoid:
```

视觉隐喻是可选策略，不是强制项。研究与数据场景可以优先选择清晰、中性的分析语言；品牌发布可以让媒体承担氛围与记忆；教学场景可以以知识结构和练习反馈为主。视觉系统必须定义普通状态和重点状态；需要节奏推进时再定义章节高潮，不能把同一组件密度与动画强度复制到全部页面。

## 5. Runtime 模块

HTML 运行能力按需组合：

| 模块 | 能力 | 启用条件 |
|---|---|---|
| `core-static` | slide DOM、比例、缩放、打印、本地资源 | 所有 HTML 演示 |
| `interactive-navigation` | 前后翻页、键盘、Hash、目录、进度 | 需要浏览器交互时 |
| `presenter` | 讲稿、计划时长、累计计时、演讲控制 | 有演讲者模式时 |
| `media` | 视频／音频、来源、播放状态、重播、失败兜底 | 存在媒体时 |
| `dialog` | 弹层、焦点陷阱、证据或细节展开 | 确有分层阅读需要时 |
| `data` | 图表语义、单位、来源、注释和替代文本 | 数据密集场景 |
| `learning` | 练习、答案揭示、进度或复习交互 | 教学场景确有需要时 |
| `motion` | 重点揭示、状态过渡、空间连续性和 reduced-motion fallback | 动效能改善理解、层级或情绪时 |

页面内嵌 `#deck-config` JSON，声明比例和启用模块。校验器根据配置选择条件规则，不再要求每份 deck 都包含 notes、timer、agenda 或 media controller。

## 6. 验收模型

### 6.1 通用门禁

- 产物与 Audience Shift、Communication Job 一致。
- 术语、示例、解释深度、信息密度和语气与实际分享群体相称。
- 内容顺序有明确依赖和推进理由。
- 事实、推断、模拟与生成内容没有误导。
- 信息层级、字体、对比度、色彩编码和安全区可读。
- 所有演示都有清晰的强调层级；需要叙事节奏时，重点页与普通页有可辨认的强弱关系，并形成铺垫、峰值和呼吸。
- 动效和特效服务于理解、强调、因果、连续性或情绪；没有全局滥用，reduced-motion 下含义完整。
- 没有私密材料、凭据、本机绝对路径或未授权素材。
- 目标交付载体能够真实打开、阅读和导航。

### 6.2 条件门禁

- 教学：学习目标、认知脚手架、示例／练习、回顾是否成立。
- 研究：问题、方法、结果、局限、来源和不确定性是否成立。
- 数据：口径、单位、来源、图表选择、异常与不确定性是否成立。
- 汇报：范围、变化、风险、负责人和所需支持是否清楚。
- 说服：价值、证据、反对意见、可行性和请求是否相称。
- 品牌：品牌资产、情绪节奏、媒体角色和记忆锚点是否一致。
- Presenter：notes 与 slide 数量、计时和控制状态是否同步。
- Media：按 `kind` 校验；只有 video 强制 poster，audio 不伪造 poster。
- Interactive：Hash、键盘、进度、inactive slide、焦点和 reduced-motion 是否正确。
- Motion：启用时，重点效果与 Emphasis Map 对应；无意义的循环、延迟和不可跳过动画不得进入成品。
- Print：分页和媒体静态替代物是否真实可用。

## 7. 文件级改造

计划调整：

```text
wowdeck/
├── SKILL.md                         # 通用入口、诊断和路由
├── references/
│   ├── scenario-routing.md          # 场景诊断与策略合同
│   ├── content-logic.md             # 动态内容逻辑与叙事先验
│   ├── attention-and-explanation.md # 受众适配、解释阶梯、重点与节奏
│   ├── claim-integrity.md           # 风险驱动真实性规则
│   ├── visual-system.md             # 场景驱动视觉语法
│   ├── html-runtime.md              # 可组合运行模块
│   └── quality-gates.md             # 通用 + 条件门禁
├── assets/
│   ├── starter/index.html           # 无业务语义的结构壳
│   └── examples/decision-pitch.html # 当前案例能力仅作条件示例
└── scripts/
    ├── init_deck.py                 # 比例与 runtime modules
    ├── prepare_media.py             # kind-aware 媒体清单
    └── validate_deck.py             # 读取 deck-config 的条件校验
```

当前 `evidence-and-story.md` 的通用部分进入 `claim-integrity.md` 和 `content-logic.md`；受众解释深度、强调层级、节奏和动效决策进入 `attention-and-explanation.md`；事件闭环、试点决策和产品能力故事只保留为条件示例。当前 runtime demo 改名并移到 examples，入口不默认读取它。

Starter 只提供结构和运行时插槽。它不得包含 Audience、Decision、Evidence、Pilot、Capability 等叙事提示，避免在第一步锚定生成方向。

## 8. 迁移与兼容

- 保持 `name: wowdeck` 和现有自动发现行为。
- 继续支持 `index.html + relative assets` 的便携交付。
- 默认比例仍可为 16:9，但改为显式可配置，不把它描述为所有演示唯一格式。
- 旧的决策提案能力作为一个可组合场景保留，不降低其真实性或媒体验收强度。
- 旧命令尽可能继续工作；新增参数提供 runtime modules 和 aspect ratio。破坏性参数变化必须在计划阶段明确。

## 9. 验证策略

### 9.1 Skill 结构与脚本

- 运行 skill 结构校验。
- 对所有 Python 脚本执行语法检查和参数级回归测试。
- 验证 starter 必须因占位 marker 不能被误当成成品。
- 验证 profile-aware validator：static 不要求 notes；presenter 要求 notes；video 要求 poster；audio 不要求 poster。

### 9.2 独立场景前向测试

至少使用以下六类请求生成策略合同，检查内容推进是否实质不同：

1. 初中科学教学；
2. 学术会议研究报告；
3. 管理层项目状态汇报；
4. 消费品牌新品发布；
5. 经营数据分析报告；
6. B2B 产品／融资提案。

至少选择教学、研究、品牌或数据中的三个生成完整 HTML。验收重点不是颜色不同，而是：中央问题、内容依赖、解释阶梯、页面角色、结尾行为、媒体角色和质量门禁都不同。每个成品还要说明其分享群体，并验证术语、信息密度和自解释程度与该群体匹配。

另做一组“同源材料、不同分享群体”的受众对照测试：同一份材料分别面向初学者、专业评审、管理层和会后群聊转发。事实与原始证据必须保持不变；中央问题、术语解释、细节层级、信息密度、自解释程度、互动形式和结尾行为应根据群体产生有理由的差异。该测试用于排除“只是换了主题或套了场景先验”的假阳性。

每个场景还要记录采用、改写和拒绝了哪些叙事先验，以及材料依赖和 audience shift 如何支持该选择；同类型任务不得在缺少理由时机械复用同一页序。

需要节奏峰值的前向样例必须检查 Emphasis Map 是否真实落地：逐项核对 `slide id / 注意目标 / 强调手段 / 服务语义 / 静态或 reduced-motion 等价物`。短格式或非叙事样例可以不设高潮，但必须验证静态强调层级清楚。所有样例都不能把每一页做成同等强度的“高光页”。

### 9.3 浏览器验收

- `core-static`：打开、比例缩放、打印和静态阅读。
- `interactive-navigation`：Hash、键盘、进度、可访问状态。
- `presenter`：讲稿、计时和状态同步。
- `media`：video 与 audio 分别测试播放、失败和打印替代。
- `motion`：检查重点揭示、转场、无动画初始状态与 reduced-motion fallback；确认关键内容不依赖动画结束事件。
- 至少检查两个常见视口和 reduced-motion；截图检查最密集页面。

## 10. 停止条件与边界

- 不发布、不上传、不调用付费生成服务，除非另获授权。
- 不修改原 WowDeck 项目仓库。
- 不把前向测试产物放入原项目或最终 Skill 包。
- 如果实现发现原生 PPTX 已成为必要目标，停止并重新确认范围；本设计只承诺通用场景的 HTML 演示。
- 最终交付前进行独立只读审查，并报告实际覆盖的场景和仍未验证的边界。
