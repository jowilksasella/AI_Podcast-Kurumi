# GEX 一分钟系列：输入文件

成品在 [gallery/gex-20261022/](../../gallery/gex-20261022/)。新资料照这三个文件的结构写，流程见 [shorts.md](../../skills/research-podcast-kurumi/references/shorts.md)。

| 文件 | 给哪个命令 | 内容 |
|---|---|---|
| `series.json` | `split-series` | 16 集（`first_episode: 0` 起）：每集 `title`、`hook_note`、`sources`（本集依据，`p` 开头表示主资料页码）、`lines`（`[说话人, delivery, 台词]`）。第一句即钩子 |
| `source-catalog.json` | `source-map --catalog` | `paper` 元数据；`white_paper`：主资料段落/图的 ID → 页码、PDF 点坐标 `rects`（612×792.5，左上原点；跨页段落用 `extra`）、位置、原文开头、中文摘要；`external`：外部论文 ID → 书目、依据与定位（含阅读深度）、用途；`tags`：非论文标签；`notes`：写进对照表开头的提醒 |
| `source-lines.json` | `source-map --lines` | `episodes["00"…"15"]`：`visual` 建议主画面 ID；`lines` 每句 `[[来源ID…], 说明]`，句数必须与该集计划一致 |

坐标可用 PyMuPDF 读出：`page.get_text("blocks")` 给出每段文字的矩形；图表区域按整页渲染图量出后换算成点（点 = 像素 × 72 / dpi）。
