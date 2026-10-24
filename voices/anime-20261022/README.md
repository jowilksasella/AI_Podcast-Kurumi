# 动画对白音色参考（2026-10-22）

《FX战士久留美》动画对白里久留美（铃木爱奈配音）与萌智子（濑户麻沙美配音）的声音，去 BGM 后由用户逐段确认。版权归原权利人；按仓库所有者的决定放在这里，供本工作流做 variant 音色参考，不适用 MIT。成品是 AI 生成的普通话，不是配音演员本人的录音。

## 定稿参考（GEX 正在使用）

| 文件 | 角色 | 来源 | 长度 |
|---|---|---|---|
| `kurumi_anime_dense_ja.wav` | 久留美 | 第 2 集 05:58.95–06:08.09、06:07.99–06:13.21、08:21.92–08:27.20 三段确认片段（`confirmed/kurumi/2b_0358.95…`、`2b_0367.99…`、`2b_0501.92…`）拼接，句内长停顿压到 ≤0.4 秒 | 14.9 秒 |
| `mochiko_anime_dense_ja.wav` | 萌智子 | 第 2 集 09:25.82–09:39.92（`confirmed/mochiko/2b_0565.82-0579.92_s0.94.wav`），句内长停顿压到 ≤0.4 秒 | 11.6 秒 |

两份都用 FFmpeg `silenceremove` 制作（停顿 >0.25 秒保留 0.15 秒，片段间 0.2 秒）；仓库里的 `compress-pauses` 命令做同样的事，输出接近但不逐位相同。IndexTTS 只读参考的前 15 秒。配置模板见 [examples/anime-cast.variant.json](../../examples/anime-cast.variant.json)。

用户听过 A/B 短样后认可（`gallery/gex-20261022/preview/` 是两位都换成定稿参考后的短样）。

## 弃用的参考（为什么要压停顿）

- 久留美单段 `confirmed/kurumi/2b_0358.95-0368.09_s0.89.wav`：9.1 秒里 4.1 秒是停顿。整份短样里 008 句中间约 8 秒静音、006 漏读后半句。
- 萌智子原片段 `confirmed/mochiko/2b_0565.82-0579.92_s0.94.wav`（未压停顿）：句内有 0.6–1.1 秒停顿，生成的 002/007 句出现 1.57/1.94 秒空白，用户也听出“有时候会有点停顿”。

## 其余素材

| 目录 | 内容 |
|---|---|
| `confirmed/kurumi/` | 用户确认的久留美对白 105 段（第 2、3 集，去 BGM），`kurumi.lst` 为“文件名⇥日文转写”；文件名里的数字是集内起止秒数与声线分数 |
| `confirmed/mochiko/` | 用户确认的萌智子对白 47 段，`mochiko.lst` 同上 |
| `anchors/yasuko/` | 高根安子 4 段，作反例：CAM++ 听来她与久留美很接近，`find-speaker` 找久留美时要给她单独一组 |
| `user-cut/mochiko/` | 用户手剪的萌智子片段（去 BGM 后），最早的正例 |
| `kurumi-ep1/` | 第 1 集久留美 6 段（去 BGM 后） |

整集的分离人声（约 480 MB）与原始剧集视频不在仓库里；需要时用 `separate-vocals` 从本机剧集重新分离。找新角色、核对与确认的流程见 [runtime.md](../../skills/research-podcast-kurumi/references/runtime.md#动画对白声线素材本地可选)。
