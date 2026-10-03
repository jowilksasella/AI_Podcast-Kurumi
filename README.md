# AI Podcast · 久留美主讲工作流

**把 PDF / research paper 做成普通话女生闲聊：久留美主讲，先短试听，确认后做全篇。**

这是音频制作仓库，与 [AI_Animation-Kurumi](https://github.com/jowilksasella/AI_Animation-Kurumi) 分工：
本仓库负责资料、剧本、声线、音频、字幕和章节；动画仓库可接收这些产物做画面。这里默认不制作动漫小人或视频。

## 版本链：v0.1.0 原版与 v0.2.0 连续模式尝试

**v0.1.0** 是此次从原始 commit `e23d5bf` 补标的完整原版快照（原包版本为 `0.1.0`），不是此前已经发布过的版本。**v0.2.0** 是独立的连续模式尝试，版本分支为 `release/v0.2.0`，版本 tag 标识为 `v0.2.0`。旧 `main` 仍保持在 `e23d5bf`，不覆盖原版历史。

| 版本 | 内容 | 源码与发布入口 |
|---|---|---|
| v0.1.0 | 原始 commit `e23d5bf` 的完整原版 | [源码 tree](https://github.com/jowilksasella/AI_Podcast-Kurumi/tree/v0.1.0) · [Release](https://github.com/jowilksasella/AI_Podcast-Kurumi/releases/tag/v0.1.0) |
| v0.2.0 | 连续调用模式、显式参数与缓存的独立尝试 | [源码 tree](https://github.com/jowilksasella/AI_Podcast-Kurumi/tree/v0.2.0) · [Release](https://github.com/jowilksasella/AI_Podcast-Kurumi/releases/tag/v0.2.0) |

[比较 v0.1.0 与 v0.2.0](https://github.com/jowilksasella/AI_Podcast-Kurumi/compare/v0.1.0...v0.2.0)。需要原版时直接克隆：

    git clone --branch v0.1.0 https://github.com/jowilksasella/AI_Podcast-Kurumi.git

也可从 [GitHub Tags](https://github.com/jowilksasella/AI_Podcast-Kurumi/tags) 下载 `v0.1.0` 原版源码，无需 revert 或 cherry-pick。下文安装与运行说明对应 `v0.2.0`，不修改旧 `main`。

- 默认 `speech_mode="continuous"`：每个角色 turn 的完整 `tts_text` 一次 native 调用，保持短段的跨句上下文，而不是逐句重启。
- 一次外部调用不等于内部一个 context。低显存或 token 预算会触发 native 拆段；连续模式明确拒绝这种超限，不静默碎切或漏字。
- 保留用户确认的平稳原声与显式生成参数。声线校准约 5–15 秒即可，不能代替正式 30–60 秒样片的确认。
- [版本化连续语气经验](docs/continuity-v0.2.0.md) 记录 5.91 秒认可短样的个案；[发布说明](docs/release-notes-v0.2.0.md) 同时记录后续 52.51 秒双人音频与两位声优轻状态校准均未获用户认可。v0.2.0 不代表整体声线优化成功，47 项 CPU 测试通过也不保证音色或连续听感。

## 以后怎么用

把这个链接和新资料直接发给 AI 助手：

> 按 https://github.com/jowilksasella/AI_Podcast-Kurumi/tree/v0.2.0 的流程，把这份 PDF 做成普通话角色闲聊。久留美主讲，开头先铺垫，先出 30–60 秒试听。

**给助手的入口：先读 [SKILL.md](skills/research-podcast-kurumi/SKILL.md)。**
仓库链接用来指定做法，PDF / 文章用来指定内容。不要自动拿上一次的论文代替这一次的资料。

可选安装成 Agent Skill：

    npx skills add https://github.com/jowilksasella/AI_Podcast-Kurumi/tree/v0.2.0/skills/research-podcast-kurumi

需要 CLI 时克隆完整版本（仅安装 Skill 不含 CLI）：

    git clone --branch v0.2.0 https://github.com/jowilksasella/AI_Podcast-Kurumi.git
    cd AI_Podcast-Kurumi

## 固定制作约定

- **久留美必须主讲**：目标占 65–75% 台词量，成片至少占 60% 有效发言时间。
- 搭档默认萌智子，也可在萌智子、芽吹、やす子中选 1–3 位轮流参与；部分知识可以交给搭档解释。
- **开头要铺垫**：一两句交代谁在聊、聊什么、为什么有意思，再自然接入正题。不要第一秒就丢术语。
- **女生闲聊，不像上课**：主讲者可以讲清机制，搭档可以吐槽、补充、追问、校对。不要固定成一个人一直装不懂、一个人一直当老师。
- **先试听后全篇**：30–60 秒样片 → 用户反馈 → 修改 → 用户明确确认 → 完整版。不会一次直接生成十几分钟。
- 默认复用现成本地 **IndexTTS 2.5**。不自动重装整合包、不下载大权重、不改回 Edge TTS。
- speaker 与默认 emotion 都沿用同一份用户已确认参考；额外 `emotion_audio` 只在用户明确需要时配置，`delivery` 标签不自动转强情绪。
- 修改一两句只重生成受影响的完整 turn，保留其内部上下文；补开场只换音频头部，正文母带保留，字幕与章节随之顺延。

## 仓库里有什么

| 入口 | 用途 |
|---|---|
| [SKILL.md](skills/research-podcast-kurumi/SKILL.md) | AI 助手执行流程 |
| [写作规则](skills/research-podcast-kurumi/references/writing.md) | 铺垫、角色分工、口语化、信息密度 |
| [运行与配置](skills/research-podcast-kurumi/references/runtime.md) | 本机模型、JSON 结构、声线配置、缓存 |
| [修订与检查](skills/research-podcast-kurumi/references/revisions.md) | 局部返工、开场替换、关键读音和字幕 |
| [配置模板](examples/config.example.json) | 本地模型与角色参考音频配置 |
| [短试听示例](examples/preview.json) | 可校验的剧本结构示例 |
| [连续语气经验 v0.2.0](docs/continuity-v0.2.0.md) | 用户认可短样、跳层与停顿的区别、长度边界 |
| [发布说明 v0.2.0](docs/release-notes-v0.2.0.md) | 新默认值、兼容模式、缓存与历史保留 |
| [早期制作经验](docs/case-study.md) | 早期 GEX 工作流及本版修正入口 |
| [命令行](kurumi_podcast/cli.py) | 提取、校验、生成、修订开场 |

## 快速运行

准备常规 Python 工具环境，仅装轻量依赖：

    python -m pip install -r requirements.txt
    python -m kurumi_podcast extract "YOUR_PAPER.pdf" --out outputs/source.json
    python -m kurumi_podcast validate examples/preview.json --stage preview

复制本地配置并填参考音频路径，配置文件不提交：

    Copy-Item examples/config.example.json config.local.json
    $env:INDEXTTS_HOME = "<已有 IndexTTS 目录>"

Windows 整合包推荐用启动器：它会进入模型目录、使用整合包自己的 Python，防止相对虚拟环境路径失效。

    .\scripts\run.ps1 render examples/preview.json --config config.local.json --out outputs/preview --stage preview

确认样片后，由助手写好完整剧本，再显式执行：

    .\scripts\run.ps1 render episode.json --config config.local.json --out outputs/episode --stage full --approved-preview

**IndexTTS 的 torch / CUDA 依赖由已有模型环境提供，不要把整个模型环境重新 pip 安装一遍。**
Linux/macOS 可在已有模型环境内设置仓库为 PYTHONPATH 后运行同样的 Python CLI，详见运行文档。

## 连续模式与缓存

完整参数 recipe、`speech_mode`、`max_text_tokens_per_segment`、`interval_silence_ms` 和可选 `voice_cache_dir` 见 [运行与配置](skills/research-podcast-kurumi/references/runtime.md)。
`continuous` 保持的是**同一角色同一 turn 的短段**，不是把整集多角色稿塞进一个文本。超出 native 容量时，重写为自然角色接话，或显式设为 `legacy_chunks` 接受旧分段模式；不靠剪静音或 fade 修复已经重启的韵律状态。
音频缓存会随模式、有效参数及参考状态失效。可选 conditioning 缓存只持久化 native 编码结果，仍需基础模型权重，既不是训练、LoRA，也不是默认声音库。

## 输出与修订

每次生成输出：

- `episode.wav`、`episode.mp3`
- `transcript.txt`（角色台词、章节时间、声线身份与来源信息）
- `subtitles.srt`（发言区间内按文字长度分配的字幕初稿）
- `manifest.json`（发言时间轴、主讲比例、声线来源）
- `work/cache.json`（按文本、参考状态、模式和有效合成参数缓存，便于恢复）

只改开头：

    .\scripts\run.ps1 patch-opening opening.json --base outputs/episode --config config.local.json --out outputs/opening-v2 --replace-until 6.215

`replace-until` 必须对齐现有发言边界，默认 0 表示只前置铺垫。
修订会生成新的完整版、前 60 秒试听、更新的文字稿与字幕；旧版不会被覆盖。

## 材料边界

仓库只发布流程、代码与原创结构示例，不包含原 PDF、配音样本、声优音频、图片、模型或成片。
公开来源链接写在文档/本地配置中；实际音频与可选 conditioning 缓存放在忽略的 `local-assets/`。示例只提供通用角色 reference 占位，不附真实声优素材或把曾被否决的 PV 声音设为默认。
“声优样本参考”“其他角色样本”“角色专用模型”是不同类型，输出必须按实际输入标注，不混称。
用户私有素材、本机实际绝对路径、登录态、权重、音频、`.pt` 与完整 ASR 私有记录不进入仓库；公开经验仅记录必要的短样事实。

## 测试

    python -m unittest discover -s tests -v

测试不加载 GPU 模型，使用临时合成波形检查缓存、主讲比例、调用边界、音频拼接、开场修订和时间轴。
真正的声线与听感通过短试听验证，不把测试波形作为用户成品。

## 上游

- [IndexTTS](https://github.com/index-tts/index-tts)
- [IndexTTS 2.5 模型说明](https://huggingface.co/IndexTeam/IndexTTS-2.5)
- [FX 战士久留美角色资料](https://fxkurumi-info.com/)

本仓库自有代码与文档采用 MIT；不分发上游模型或第三方素材。
