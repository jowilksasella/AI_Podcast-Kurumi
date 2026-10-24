# AI Podcast · 久留美主讲工作流

**把 PDF / research paper 做成普通话女生闲聊：久留美主讲，先短试听，确认后做全篇。**

当前 `main`（**v0.4.0**）的恢复工作流使用 `original-chat-20261002`（v0.3.0 起）：恢复 10 月 2 日的**独立日语演员音色 + 原始中文聊天情绪**，并恢复有铺垫、好奇、轻吐槽、搭档有贡献的写法。不是仅退回 v0.1.0；v0.2.0 是另一个未获认可的实验，不作为默认制作入口。保留[历史标签](https://github.com/jowilksasella/AI_Podcast-Kurumi/tags)供追溯，不按“最新 release”自动更换配方。

配方恢复不表示新文本的听感已通过。原来获认可的约 41 秒试听、后来修订的 60 秒开场和正文情绪库是不同产物；新预览仍须实际生成、试听和用户确认。详见[恢复与迁移](docs/original-chat-restoration.md)。

这是音频制作仓库，与 [AI_Animation-Kurumi](https://github.com/jowilksasella/AI_Animation-Kurumi) 分工：这里负责资料、剧本、音频、字幕、章节，以及给短视频用的一分钟系列和逐句来源对照；动漫小人与视频由 AI_Animation-Kurumi 的 `kurumi-shorts` 制作。

## 以后怎么用

把根仓库链接和**本次的新资料**发给 AI 助手：

> 按 https://github.com/jowilksasella/AI_Podcast-Kurumi 当前 main 的 original-chat-20261002 和已绑定本地配置，把这份 PDF 做成普通话角色闲聊。久留美主讲、萌智子搭档，先给 30–60 秒试听，确认后才做全篇。

**助手先读 [SKILL.md](skills/research-podcast-kurumi/SKILL.md)。** 根 URL 指定做法，不指定旧论文；只有复核历史示例才沿用 GEX。Skill 可以单独安装，但执行 CLI 需要完整仓库。

    npx skills add https://github.com/jowilksasella/AI_Podcast-Kurumi/tree/main/skills/research-podcast-kurumi

想直接做成 Shorts（每集一分钟以内、一集一条竖屏短片）：

> 按 https://github.com/jowilksasella/AI_Podcast-Kurumi 当前 main，用动画音色把这份 PDF 拆成一分钟系列：先给 ep01 样片，确认后批量生成，再出逐句来源对照交给 AI_Animation-Kurumi 做 short。

## 固定制作约定

- **久留美主讲**：台词量目标 65–75%，全篇成片至少占 60% 有效发言时间。搭档默认萌智子，参与解释、补充、追问和校对，而不是只当学生。
- 前两句铺垫人物、话题和怪现象，再引出机制；保留好奇心、轻玩笑和想明白的反应。可以连续几轮由主讲推进，不强制交替问答。
- 先写约 220–270 字、每轮约 50 字以内的短样；预览上限 360 字。30–60 秒是目标，实际时长以渲染为准，文字校验不是时长或自然度证明。
- 沿用已绑定的本地 IndexTTS 2.5、演员音色、中文情绪库和采样参数。**不清空 emotion_audio、不自动换演员/搭档/版本、不切 Edge。** 用户明确变更时另做短样，不覆盖原始配置。
- 原始素材缺失或身份不符时，列出具体槽位与错误；不生成替代情绪、重剪新演员样本或拿普通女声降级冒充。
- 修改一两句只重做受影响段落；补开场保留正常正文母带，字幕和章节随之调整。
- 全部台词用标准普通话简体；研究在讨论中自然带出作者、平台/期刊与日期，口播不念页码或 DOI。完整版不设时长上限，按资料讲透。
- 逐句好/坏反馈用来选定整集配置，不逐句重录。

## 换搭档（variant 配置）

想让久留美配其他搭档（例如山师芽吹），或整集统一情绪映射，不要改原始配置，另写一个 `recipe: "variant"` 的本地配置，`base_config` 指向已绑定的原始配置：

    .\scripts\run.ps1 doctor --config config.mebuki.local.json --plan preview.json
    .\scripts\run.ps1 render preview.json --config config.mebuki.local.json --out outputs/mebuki-preview --stage preview

variant 继承原始配置的全部采样设置与 IndexTTS 环境（写了不同值会报错），执行方式与原始配方一致：每轮固定 seed、原始发音转换、不做分段重试、每种 delivery 必须有独立情绪参考。成品标为 `variant`，不是原始恢复。结构见 [variant.example.json](examples/variant.example.json) 与[运行文档](skills/research-podcast-kurumi/references/runtime.md#换搭档或换情绪映射variant-配置)。

## 动画对白声线（本地、可选）

想用动画里角色本身的声音做 variant 音色参考时，用四个命令在本机准备素材：

| 命令 | 做什么 |
|---|---|
| `separate-vocals` | 用 audio-separator（独立 venv）的 MelBand RoFormer 去掉 BGM |
| `find-speaker` | 用 IndexTTS 的 CAM++ 声线嵌入，从整集里按角色排出候选；OP/ED 自动排除 |
| `review-video` | 从原片剪出带编号、时间戳和日文转写的核对视频 |
| `confirm-review` | 记录用户结论：认错的转成该角色反例，其余进入已确认集 |

自动排名只是候选，必须由人看过确认。做参考前用 `compress-pauses` 把片段里的长停顿压到 ≤0.4 秒（停顿多的参考会让生成出现长静音和漏读）。细节见[运行文档](skills/research-podcast-kurumi/references/runtime.md#动画对白声线素材本地可选)。

## 动画音色定稿（GEX）

2026-10-22 用户听过短样后认可：**久留美与萌智子都用动画对白音色**，中文情绪、seed 规则与采样设置继承原始配置。参考已提交在 [voices/anime-20261022/](voices/anime-20261022/)（含用户确认的对白片段集），配置模板是 [anime-cast.variant.json](examples/anime-cast.variant.json)：复制到根目录为 `config.anime.local.json` 即可，中文情绪参考仍用本机原始库。

    .\scripts\run.ps1 render preview.json --config config.anime.local.json --out outputs/anime-preview --stage preview

## 一分钟系列（给 Shorts / Reels）

把一份资料拆成多集各自独立、每集一分钟以内的对话：第一句就是 3–5 秒钩子、不自我介绍，目标约 55 秒（动画音色约 5.9 字/秒）。流程见 [shorts.md](skills/research-podcast-kurumi/references/shorts.md)：

| 命令 | 做什么 |
|---|---|
| `split-series` | 一个系列 JSON → 每集 `epNN/plan.json` 与 `series.md`；报告字数、主讲占比、钩子长度、估计秒数 |
| `render-series` | 每集按试听阶段渲染（30–60 秒），共用一个引擎；`--only 1` 先做样片 |
| `qa` / `asr-check` | 句内长静音、语速、削波；逐句 Whisper 对稿，列出待听的买卖等动作词 |
| `source-map` | 每句台词 → 主资料的页、段、图（附截图）/ 外部论文 / 我们的比喻与解读，带时间码，交给视频 Agent |

完整例子：输入 [examples/gex/](examples/gex/)（系列稿、来源目录、逐句来源），成品 [gallery/gex-20261022/](gallery/gex-20261022/)（16 集一分钟系列、完整版、认可短样、片尾句与来源对照）。

## 仓库里有什么

| 入口 | 用途 |
|---|---|
| [SKILL.md](skills/research-podcast-kurumi/SKILL.md) | AI 助手执行流程与版本选择 |
| [写作规则](skills/research-podcast-kurumi/references/writing.md) | 铺垫、分工、口语感；唯一规范短样 |
| [运行与配置](skills/research-podcast-kurumi/references/runtime.md) | 原始素材槽位、绑定、本机环境与计划结构 |
| [修订与检查](skills/research-podcast-kurumi/references/revisions.md) | 局部返工、实际试听与最小检查 |
| [原始配方](recipes/original-chat-20261002.json) | 公开配方及原始资产身份，无原始声音 |
| [配置结构示例](examples/config.example.json) | 非运行配置；不替代 bind-original |
| [换搭档示例](examples/variant.example.json) | variant 配置结构；继承已绑定原始配置 |
| [短试听示例](examples/preview.json) | 从原始 GEX 开场保留的写作示例；新渲染待认可 |
| [恢复与迁移](docs/original-chat-restoration.md) | 空情绪映射根因、历史产物区别和迁移 |
| [GEX 经验](docs/case-study.md) | 原制作实践中保留的方法 |
| [一分钟系列](skills/research-podcast-kurumi/references/shorts.md) | Shorts 用的拆集、钩子、批量渲染、检查与来源对照 |
| [动画音色参考](voices/anime-20261022/) | 定稿音色参考、用户确认的对白片段集与来历 |
| [动画音色配置](examples/anime-cast.variant.json) | 定稿 variant 配置模板 |
| [GEX 系列输入](examples/gex/) | 系列稿、主资料来源目录、逐句来源 ID |
| [GEX 成品](gallery/gex-20261022/) | 一分钟系列 16 集、完整版、认可短样、片尾句、来源对照 |

## 快速运行

在完整仓库根目录操作。复用已有 Python 工具和模型环境，不重装 torch/CUDA 或下载大权重。

    python -m kurumi_podcast extract "YOUR_PAPER.pdf" --out outputs/source.json
    python -m kurumi_podcast validate examples/preview.json --stage preview

**本地一次性准备原始库**：将已有的八个原始文件放在忽略的 `local-assets/original-20261002/`，或直接指定已经按公共槽位命名的现有目录。文件名见[运行文档](skills/research-podcast-kurumi/references/runtime.md#原始资产槽位)。无需上传声音。

让绑定命令检查原始文件并生成冻结的本地配置，**不要复制模板后直接渲染**：

    .\scripts\run.ps1 bind-original --assets local-assets/original-20261002 --index-home "YOUR_EXISTING_INDEXTTS_DIRECTORY" --out config.local.json
    .\scripts\run.ps1 doctor --config config.local.json --plan examples/preview.json
    .\scripts\run.ps1 render examples/preview.json --config config.local.json --out outputs/preview --stage preview

`--index-home` 定位启动器的已有模型 Python；不需要先设置环境变量。`config.local.json` 及 `*.local.json` 均不提交。绑定完成后沿用此配置；模板展示路径和非空情绪映射，**本身不代表资产已验证或可运行**。

确认样片后，由助手按本次资料写完整剧本，再执行：

    .\scripts\run.ps1 render episode.json --config config.local.json --out outputs/episode --stage full --approved-preview

`--approved-preview` 只记录已经发生的用户确认，不用参数替代确认。Linux/macOS 的已有模型环境调用方式见运行文档。

## 输出与修订

- `episode.wav`、`episode.mp3`
- `transcript.txt`：角色、章节、来源和身份说明
- `subtitles.srt`：按文字长度分配并对齐到实际停顿的字幕，非字级对齐
- `manifest.json`：时间轴、每轮停顿、主讲比例、`duration_ok` 及制作信息
- `work/cache.json`：恢复与局部重做使用的缓存

试听超出 30–60 秒时仍会输出全部文件，但命令以退出码 3 结束并提示修改台词。生成后可以：

    python -m kurumi_podcast qa outputs/episode
    python -m kurumi_podcast package-chapters outputs/episode

`qa` 列出语速异常（疑似重复或漏读）、句内长静音（≥1.3 秒）、削波、主讲占比和粤语/繁体/口播定位符等该去听的轮次；`package-chapters` 切出 `chapters/` 分章 MP3；`.\scripts\run.ps1 asr-check outputs/episode --config …` 逐句转写对稿。长静音或重复循环的句子原地改写后只重做那一句，见[修订与检查](skills/research-podcast-kurumi/references/revisions.md#长静音与重复循环技术缺陷)。

只改开头：

    .\scripts\run.ps1 patch-opening opening.json --base outputs/episode --config config.local.json --out outputs/opening-v2 --replace-until 6.215

`replace-until` 必须对齐已有发言边界，默认 0 表示前置；示例数值应换成这次母带的真实边界。旧版保留，正文母带复用，章节、字幕和前 60 秒试听更新。

## 材料与检查

仓库发布流程、代码、配方元数据和写作示例；按用户决定（2026-10-24）另外发布动画音色参考（`voices/`）与 GEX 展示成品（`gallery/`）。不发布原始演员样本与中文情绪库、PDF 原文、模型、密钥或本机路径（成品 manifest 里的本机路径已替换为 `<repo>` 等占位符）。演员日语样本是音色参考，中文聊天片段是表演参考，不是演员本人的普通话录音或角色专用模型；成品是 AI 生成普通话。

结构检查：

    python -m kurumi_podcast validate examples/preview.json --stage preview
    python -m unittest discover -s tests -v

测试不加载 GPU；文件成功、无削波、ASR 正确都**不能证明聊得自然**。新预览需实际检查声线区分、情绪、接话和主讲分工，再交用户试听。未听辨的声音不标为获认可，详见[针对性检查](skills/research-podcast-kurumi/references/revisions.md#针对性检查)。

## 上游与历史

- [IndexTTS](https://github.com/index-tts/index-tts) 与 [IndexTTS 2.5 模型说明](https://huggingface.co/IndexTeam/IndexTTS-2.5)
- [FX 战士久留美角色资料](https://fxkurumi-info.com/)
- [历史标签](https://github.com/jowilksasella/AI_Podcast-Kurumi/tags)：v0.1.0 是历史模板，v0.2.0 是独立实验，v0.3.0 恢复原始配方，v0.4.0 加入 variant 换搭档、qa/分章工具与本地动画声线素材流程；默认使用当前 main 恢复工作流

本仓库自有代码与文档采用 MIT；不分发上游模型。`voices/` 里的动画对白片段与 `gallery/` 里的白皮书页面/截图属第三方素材，版权归原权利人（《FX战士久留美》、SqueezeMetrics / Prior Analytics LLC），不适用 MIT，按仓库所有者的决定放在这里供本工作流复用。
