# 连续语气经验 · v0.2.0

本记录区分三类证据：用户试听认可的短样事实、官方 native source 的机制、本仓库据此采用的默认策略。仅公开必要的经验，不附原音频、权重、conditioning `.pt`、本机实际绝对路径、登录数据或完整 ASR 私有记录。

## 1. 问题不是停顿长度

起初把跨句语气的“跳层”误当成空白长短，剪了三处 pause，仍没有解决用户要的 TTS 生成效果。独立句段容易重新启动音高、力度和发声方式；把片段之间的空白缩短，不能恢复生成时已经失去的上下文。

本次目标是**韵律状态平滑延续**：可以有句间停顿、呼吸和自然音高变化，而不是全程无停顿、固定 F0 或去掉所有气声。停顿剪辑和连续生成是不同问题。

## 2. 用户实际认可的短样

| 项目 | 本次事实 |
|---|---|
| 文本 | 大家好，我是久留美。今天聊期权对冲。 |
| 文本长度 | 18 字符（含标点），是一个角色的短 turn |
| 引擎 | 同一既有默认 IndexTTS 2.5，没有换模型 |
| 声音与对照条件 | 沿用同一用户确认原声、同一 seed 与显式参数记录 |
| 调用 | whole-text 单次 native call，不按两句外部分开请求 |
| 内部证据 | actual native 日志的 `segments count` 为 1 |
| 输出时长 | 5.91 秒 |
| 判断 | 用户试听认可该短样的连续语气与声线 |

该样本没有外部分句、片段拼接、剪静音或额外 fade，也没有借用别人 emotion、LoRA 或 VC。这里的“没有”指该短样的外部制作链路，不改写或推断 native 内部的音频处理实现。

这是**用户确认的个案**，不是 ASR 认证，也不是任意 voice、任意长稿都无气声或无跳层的保证。本记录不附完整私有日志；调用数与时长是本次案例摘要，不声称读者能仅凭摘要重建位元相同的音频。

## 3. 保留原声，准确标注参考

本次 preferred reference 是用户确认的平稳原声。真人/声优 sample 与真实角色对白不是同一身份；角色标签表达节目分工，不把样本参考说成角色专用模型或本人新录音。

官网 PV 含 BGM；去 BGM、强 clean 可能使音色失真，不能因“官方来源”就选被用户否决的处理声音作为默认库。本次新的平稳 JA reference 文件长 20.067 秒，但所用 native 只读取前 15 秒，不声称整段 20 秒都参与 conditioning。

音色由人类确认。ASR 用于必要的文字核对，SNR、无 clipping、文件成功或模型名称不能证明角色声线符合要求。

## 4. 显式 recipe 比“同模型”更具体

本版参数的唯一配置说明见 [runtime.md](../skills/research-podcast-kurumi/references/runtime.md)：采样关闭、temperature 0.4、repetition penalty 8，以及其他完整的生成与 segmentation 设置。

检索到的原 native 默认 temperature 0.8、repetition penalty 10，与此前工作台 0.4/8 不同，所以必须明确记录实际 recipe。历史 UI 会话的实际参数未知；本次认可不能反推“唯一根因已查明”，也不宣称历史 UI 与新调用位元相同。

对照时固定同一 reference、同一 text、同一实际 seed 与显式参数，一次只改变 context 方式。先验证输入和调用事实，再交付用户直接试听；不用换声、重装、全文 ASR 或重新训练替代这一步。

## 5. one call 的长度边界

本次 18 字符短样有内部 `segments count=1` 证据。**一个 external call 本身不足以证明一个内部 context**：所检索 native 在低显存模式且原始 text 大于 40 字符时自动拆段，token 预算也可另行拆段。

v0.2.0 的 `continuous` 因此按自然短 turn 保持完整，而不是承诺长段或整篇多角色播客一次生成。超限时明确失败，将长解释重写为自然角色 exchange，或显式用 `legacy_chunks` 接受旧分段；不静默碎切、不省略文本，也不绕模型容量。具体边界与参数见 [运行约定](../skills/research-podcast-kurumi/references/runtime.md#continuous-与容量边界)。

## 6. 最小排查与交付

可执行的排查步骤随 Skill 打包在 [continuity.md](../skills/research-podcast-kurumi/references/continuity.md)。重点是固定条件、只改 context、用实际调用证据配合人类试听。
用户认可且证据足够就交付，不继续花约 34 分钟剪掉 0.32 秒空白。正式节目仍另做 30–60 秒样片，确认角色分工、内容与接话后再做全篇。

缓存可以复用 native conditioning，不能补回句级独立生成丢失的韵律状态。相关失效和持久化规则见 [两类缓存](../skills/research-podcast-kurumi/references/runtime.md#两类缓存)。

## 来源与适用范围

- Web 独立研究：[IndexTTS 2.5 官方演示与技术报告](https://index-tts.github.io/index-tts2-5.github.io/) 描述 speaker/emotion conditioning 能力；没有保证本案例中任何声线或长稿的连续性。
- GitHub 独立 prior-art 研究：[官方 infer_v2_5.py](https://github.com/index-tts/index-tts/blob/d9e41aac89fd00b3d71497fddb287b7f24613712/indextts/infer_v2_5.py) 提供参考前 15 秒裁切、低显存与 token 拆段、native 默认参数及进程内 conditioning cache 的依据。
- 可复用现有 native whole-text 推理与 conditioning 编码；本版新增的是项目的调用/失败/缓存约定与经验文档，不是另训一套声音模型。用户短样反馈只来自本次实践，不冒充上游研究结论。
