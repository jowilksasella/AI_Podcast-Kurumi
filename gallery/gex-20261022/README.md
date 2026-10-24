# GEX 成品（2026-10-22）

主资料：SqueezeMetrics《Gamma Exposure (GEX)™: Quantifying hedge rebalancing in SPX options》白皮书（2016-03 首发，2017-12 修订，8 页）。PDF 原文不在仓库里。
音色：久留美 + 萌智子动画对白音色（[voices/anime-20261022/](../../voices/anime-20261022/)，配置 [anime-cast.variant.json](../../examples/anime-cast.variant.json)），中文情绪、seed 规则与采样设置继承原始配置。成品是 AI 生成普通话；**整体听感未经人完整试听验证**。

| 目录 | 内容 |
|---|---|
| `preview/` | 用户认可音色的短样（50.4 秒，8 轮）：两位都用定稿参考 |
| `full/` | 完整版 17 分 50 秒，192 轮，12 章；`plan.json` 全稿、`coverage.md` 覆盖计划与修改记录、`asr.json` 逐句转写 |
| `shorts/` | 一分钟系列 16 集（ep00 系列开场 + ep01–ep15），每集独立，合计 14.8 分钟；`series.md` 总览，`source-map/` 逐句来源对照 |
| `outro/` | 通用片尾句“觉得这一分钟有帮助，就关注我吧！我们一起把这个系列看完。”；`out/kurumi_outro.wav` 是只有久留美那句的 4.105 秒切片 |

每个成品目录里：`episode.mp3`（`shorts/`、`outro/` 另有 24 kHz 单声道 `episode.wav`）、`subtitles.srt`（简体，按停顿对齐，非字级）、`manifest.json`（每句 start/end 秒、说话人；本机路径已换成 `<repo>`、`<INDEXTTS_HOME>` 等占位符）、`transcript.txt`。完整版分章 MP3 可用 `package-chapters` 从 WAV 重新切出，这里只放 `chapters.json`。

## 一分钟系列

| 集 | 标题 | 开场钩子 | 钩子长度 | 总长 |
|---|---|---|---|---|
| 00 | 系列开场 | 每天只要一分钟，带你读完一份期权白皮书。 | 3.6 秒 | 56.2 秒 |
| 01 | 恐慌指数的盲区 | 预测波动时，恐慌指数十二和十五，几乎是一回事。 | 3.9 秒 | 55.5 秒 |
| 02 | 一把更细的尺子 | 同样风平浪静的两天，有一把尺子能分出哪天更危险。 | 4.2 秒 | 55.4 秒 |
| 03 | 期权会推着股价走 | 期权到期那天，股价好像会被钉住。 | 2.8 秒 | 56.4 秒 |
| 04 | 越跌越卖的人 | 有一群人，股价越跌，他们越得卖。 | 3.0 秒 | 53.3 秒 |
| 05 | 减震器和放大器 | 同一群做市商，有时在帮市场减震，有时却在火上浇油。 | 4.3 秒 | 51.2 秒 |
| 06 | 先问单位 | 看到一个吓人的伽马敞口数字，先别慌，先问单位。 | 3.7 秒 | 57.5 秒 |
| 07 | 它其实在猜 | 伽马敞口最大的秘密，是它其实在猜谁买谁卖。 | 3.8 秒 | 58.4 秒 |
| 08 | 被期刊借走的假设 | 这份白皮书的算法，后来被一篇期刊论文原样借走了。 | 4.0 秒 | 53.8 秒 |
| 09 | 看不清的账本 | 就算知道每笔交易是谁做的，也看不清做市商的账本。 | 4.0 秒 | 56.4 秒 |
| 10 | 那张散点图 | 一张图上，市场的暴涨暴跌，几乎全挤在一边。 | 3.5 秒 | 51.9 秒 |
| 11 | 谁导致了谁 | 也许不是负伽马让市场乱，而是市场乱了，才有负伽马。 | 3.5 秒 | 58.8 秒 |
| 12 | 浴缸和大海 | 同样一桶水，倒进浴缸和倒进大海，效果完全不一样。 | 3.8 秒 | 54.5 秒 |
| 13 | 零日期权的反转 | 大家都怕零日到期期权放大波动，有研究却发现正好相反。 | 4.3 秒 | 57.7 秒 |
| 14 | 没给数字的超额收益 | 这份白皮书说能挑出超额收益的股票，却没给一个数字。 | 4.1 秒 | 55.9 秒 |
| 15 | 看图前的五个问题 | 下次看到伽马敞口的图，先问这五个问题。 | 3.2 秒 | 52.4 秒 |

[`shorts/source-map/source-map.md`](shorts/source-map/source-map.md) 把 204 句台词逐句对应到白皮书的页、段、图（`crops/` 段落/图表裁切，`pages/` 整页，150 dpi）、8 篇外部论文（书目、定位、阅读深度）或我们自己的比喻/解读/常识/串场（93 / 37 / 74 句），带时间码与每集建议主画面——给做 short 的 Agent 用。

## 怎么做出来的（可复现）

    python -m kurumi_podcast split-series examples/gex/series.json --out outputs/gex-shorts
    .\scripts\run.ps1 render-series outputs/gex-shorts --config config.anime.local.json
    python -m kurumi_podcast qa outputs/gex-shorts/ep01/out
    .\scripts\run.ps1 asr-check outputs/gex-shorts/ep01/out --config config.anime.local.json
    python -m kurumi_podcast source-map outputs/gex-shorts --catalog examples/gex/source-catalog.json --lines examples/gex/source-lines.json --out outputs/gex-shorts/source-map --pdf white_paper.pdf

`split-series` 从 `examples/gex/series.json` 生成的 16 份计划与这里的 `shorts/epNN/plan.json` 完全相同；`source-map` 重跑得到相同的对照与逐字节相同的裁切。完整版的稿是 `full/plan.json`（`--stage full --approved-preview`，在用户说“开始吧”之后渲染）。

## 检查与修改记录

- 全部成品：`qa` 无标记、无削波；逐句 Whisper 转写对照无漏句（相似度低的多为数字写法与同音字）。
- 完整版：063 原句在固定 seed 下重复循环（“股价跌了他会亏”×3），拆成两句同义短句；048/130/154/190 句内 1.4–3.5 秒静音，原地改写同义句、只重做这四句。
- 一分钟系列：ep00/011、ep06/007、ep10/007 句内 1.35–1.86 秒静音，原地改写、只重做该句。
- 待人听：并列“买…卖”的句子 Whisper 会同化（完整版 8:05、9:33、9:45、10:25、11:28、11:35、16:53；一分钟 ep05 0:34.1），ep01 0:12.6“百分之零点五一”（ASR 记成“0.5亿”）。多半是 ASR 偏差，未经人耳确认。

白皮书页面与图表的版权属 SqueezeMetrics / Prior Analytics LLC，按仓库所有者的决定放在这里；公开发布视频与否由用户决定。
