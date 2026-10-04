# AI Podcast · 久留美主讲工作流

**把 PDF / research paper 做成普通话女生闲聊：久留美主讲，先短试听，确认后做全篇。**

当前 `main` 的 **v0.3.0 恢复工作流**使用 `original-chat-20261002`：恢复 10 月 2 日的**独立日语演员音色 + 原始中文聊天情绪**，并恢复有铺垫、好奇、轻吐槽、搭档有贡献的写法。不是仅退回 v0.1.0；v0.2.0 是另一个未获认可的实验，不作为默认制作入口。保留[历史标签](https://github.com/jowilksasella/AI_Podcast-Kurumi/tags)供追溯，不按“最新 release”自动更换配方。

配方恢复不表示新文本的听感已通过。原来获认可的约 41 秒试听、后来修订的 60 秒开场和正文情绪库是不同产物；新预览仍须实际生成、试听和用户确认。详见[恢复与迁移](docs/original-chat-restoration.md)。

这是音频制作仓库，与 [AI_Animation-Kurumi](https://github.com/jowilksasella/AI_Animation-Kurumi) 分工：这里负责资料、剧本、音频、字幕和章节，默认不制作动漫小人或视频。

## 以后怎么用

把根仓库链接和**本次的新资料**发给 AI 助手：

> 按 https://github.com/jowilksasella/AI_Podcast-Kurumi 当前 main 的 original-chat-20261002 和已绑定本地配置，把这份 PDF 做成普通话角色闲聊。久留美主讲、萌智子搭档，先给 30–60 秒试听，确认后才做全篇。

**助手先读 [SKILL.md](skills/research-podcast-kurumi/SKILL.md)。** 根 URL 指定做法，不指定旧论文；只有复核历史示例才沿用 GEX。Skill 可以单独安装，但执行 CLI 需要完整仓库。

    npx skills add https://github.com/jowilksasella/AI_Podcast-Kurumi/tree/main/skills/research-podcast-kurumi

## 固定制作约定

- **久留美主讲**：台词量目标 65–75%，全篇成片至少占 60% 有效发言时间。搭档默认萌智子，参与解释、补充、追问和校对，而不是只当学生。
- 前两句铺垫人物、话题和怪现象，再引出机制；保留好奇心、轻玩笑和想明白的反应。可以连续几轮由主讲推进，不强制交替问答。
- 先写约 220–270 字、每轮约 50 字以内的短样；预览上限 360 字。30–60 秒是目标，实际时长以渲染为准，文字校验不是时长或自然度证明。
- 沿用已绑定的本地 IndexTTS 2.5、演员音色、中文情绪库和采样参数。**不清空 emotion_audio、不自动换演员/搭档/版本、不切 Edge。** 用户明确变更时另做短样，不覆盖原始配置。
- 原始素材缺失或身份不符时，列出具体槽位与错误；不生成替代情绪、重剪新演员样本或拿普通女声降级冒充。
- 修改一两句只重做受影响段落；补开场保留正常正文母带，字幕和章节随之调整。

## 仓库里有什么

| 入口 | 用途 |
|---|---|
| [SKILL.md](skills/research-podcast-kurumi/SKILL.md) | AI 助手执行流程与版本选择 |
| [写作规则](skills/research-podcast-kurumi/references/writing.md) | 铺垫、分工、口语感；唯一规范短样 |
| [运行与配置](skills/research-podcast-kurumi/references/runtime.md) | 原始素材槽位、绑定、本机环境与计划结构 |
| [修订与检查](skills/research-podcast-kurumi/references/revisions.md) | 局部返工、实际试听与最小检查 |
| [原始配方](recipes/original-chat-20261002.json) | 公开配方及原始资产身份，无原始声音 |
| [配置结构示例](examples/config.example.json) | 非运行配置；不替代 bind-original |
| [短试听示例](examples/preview.json) | 从原始 GEX 开场保留的写作示例；新渲染待认可 |
| [恢复与迁移](docs/original-chat-restoration.md) | 空情绪映射根因、历史产物区别和迁移 |
| [GEX 经验](docs/case-study.md) | 原制作实践中保留的方法 |

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
- `subtitles.srt`：按发言区间分配的字幕初稿，非精确字级对齐
- `manifest.json`：时间轴、主讲比例及制作信息
- `work/cache.json`：恢复与局部重做使用的缓存

只改开头：

    .\scripts\run.ps1 patch-opening opening.json --base outputs/episode --config config.local.json --out outputs/opening-v2 --replace-until 6.215

`replace-until` 必须对齐已有发言边界，默认 0 表示前置；示例数值应换成这次母带的真实边界。旧版保留，正文母带复用，章节、字幕和前 60 秒试听更新。

## 材料与检查

仓库只发布流程、代码、配方元数据和写作示例；不发布 PDF、原声音、模型、密钥、本机路径或成片。演员日语样本是音色参考，中文聊天片段是表演参考，不是演员本人的普通话录音或角色专用模型。

结构检查：

    python -m kurumi_podcast validate examples/preview.json --stage preview
    python -m unittest discover -s tests -v

测试不加载 GPU；文件成功、无削波、ASR 正确都**不能证明聊得自然**。新预览需实际检查声线区分、情绪、接话和主讲分工，再交用户试听。未听辨的声音不标为获认可，详见[针对性检查](skills/research-podcast-kurumi/references/revisions.md#针对性检查)。

## 上游与历史

- [IndexTTS](https://github.com/index-tts/index-tts) 与 [IndexTTS 2.5 模型说明](https://huggingface.co/IndexTeam/IndexTTS-2.5)
- [FX 战士久留美角色资料](https://fxkurumi-info.com/)
- [历史标签](https://github.com/jowilksasella/AI_Podcast-Kurumi/tags)：v0.1.0 是历史模板，v0.2.0 是独立实验，默认使用当前 main 恢复工作流

本仓库自有代码与文档采用 MIT；不分发上游模型或第三方素材。
