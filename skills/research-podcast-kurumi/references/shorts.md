# 一分钟系列：给 Shorts / Reels 用的音频

用户要做竖屏短视频（每集一个 short）时，把同一份资料拆成多集**各自独立、每集一分钟以内**的对话音频，再交给 [AI_Animation-Kurumi](https://github.com/jowilksasella/AI_Animation-Kurumi) 的 `kurumi-shorts` 技能做画面。本仓库只负责音频、字幕、时间码和逐句来源对照；视频由另一个 Agent / 会话制作。

完整示例（GEX 白皮书，16 集）：[examples/gex/](../../../examples/gex/)（输入）与 [gallery/gex-20261022/](../../../gallery/gex-20261022/)（成品）。

## 写法

- **不自我介绍**，第一句就是钩子，3–5 秒内让人停下（约 16–26 个字）：反常识结论、具体数字或一句提问。
- 每集只讲一个点，能单独看懂；按顺序看是一条完整线。可加一集**开场集**（ep00）说明系列是什么、共几集、每集一分钟以内、为什么拆短。
- 目标约 55 秒、不超过 60 秒。动画音色实测约 **5.9 字/秒**（含轮间停顿），约 300–335 个可见字。不足时补实质内容（例子、图上细节、研究范围、局限），不注水。
- 其余规则同 [writing.md](writing.md)：标准普通话简体、久留美 65–75%、研究在讲到时带出作者/期刊/日期、不念页码。结尾给一句结论或引向下一集，不说“下次见”式客套（开场集除外）。
- 每轮约 50 字以内，**少用冒号和长分句**：冒号处最容易出现 1–3 秒的句内静音。

## 步骤

1. **系列文件**：一个 JSON 写全部集，结构见 [examples/gex/series.json](../../../examples/gex/series.json)（`series`、`lead`、`source`、`first_episode`、`config_hint`、`episodes[].title/sources/lines`）。
2. **拆分并检查**（不需要模型环境）：

       python -m kurumi_podcast split-series series.json --out outputs/my-series

   写出 `epNN/plan.json` 与 `series.md`，每集跑 core 校验，并报告字数、主讲占比、钩子字数、估计秒数；`warnings` 里有 `estimated_length`、`long_hook`、`long_turn` 就先改稿。
3. **先做一集样片**给用户听（通常 ep01，必要时连同 ep00），确认写法与长度后再批量：

       .\scripts\run.ps1 render-series outputs/my-series --config config.anime.local.json --only 1
       .\scripts\run.ps1 render-series outputs/my-series --config config.anime.local.json

   每集按 preview 阶段渲染（30–60 秒），共用一个引擎实例；缓存只重做改过的句子。
4. **检查**：每集跑 `qa`（含 `long_internal_pause`，默认 ≥1.3 秒），再跑一次逐句转写：

       python -m kurumi_podcast qa outputs/my-series/ep01/out
       .\scripts\run.ps1 asr-check outputs/my-series/ep01/out --config config.anime.local.json

   `asr-check` 写出 `out/asr.json`，列出相似度最低的句子和 `buy_sell_listen`（并列的“买…卖”常被 Whisper 同化，是该去听的线索，不是结论）。
5. **修技术缺陷**（见 [revisions.md](revisions.md)）：长静音或重复循环的那一句，原地改写成更短的同义句（不改编号），只重做那一句；不挑 seed、不逐句主观重录。
6. **来源对照**：给视频 Agent 的逐句来源表——

       python -m kurumi_podcast source-map outputs/my-series --catalog source-catalog.json --lines source-lines.json --out outputs/my-series/source-map --pdf paper.pdf

   `source-catalog.json` 列出主资料的段落/图（页码、PDF 坐标、原文开头、中文摘要）、外部论文（书目、定位、阅读深度）和非论文标签（`OURS-ANALOGY` 比喻、`OURS-ANALYSIS` 我们的解读、`OURS-DEF` 常识、`OURS-BRIDGE` 衔接、`OURS-SERIES` 串场）；`source-lines.json` 给每集每句标来源 ID 和建议主画面。工具会校验句数与 manifest 一致、ID 都存在，生成 `source-map.md/json`，有 `--pdf`（需 PyMuPDF）时再出整页图和段落裁切。改过任何一句都要重跑。
7. **交付**：每集 `out/episode.wav|mp3`、`subtitles.srt`、`manifest.json`（每句 start/end/说话人）、`transcript.txt`，加 `series.md` 与 `source-map/`。告诉用户待听的时间点；听感未验证。

## 片尾等单句素材

视频需要一句通用片尾（如“觉得这一分钟有帮助，就关注我吧”）时，计划里写 `"allow_solo": true` 就能只放久留美一句；或照 [gallery 的 outro](../../../gallery/gex-20261022/outro/) 做双人后剪出久留美那段。总长不到 30 秒时 preview 会以退出码 3 结束，但文件照常写出。
