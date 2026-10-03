# 发布说明 · v0.2.0

## 版本与历史

v0.2.0 是独立版本，版本分支为 `release/v0.2.0`，版本 tag 标识为 `v0.2.0`。旧 `main` 与既有远端历史 `e23d5bf` 保持不变；不覆盖或强制改写旧 refs，旧输出保留。
包版本从 `0.1.0` 更新到 `0.2.0`；此前没有对应的 `v0.1.0` 发布 tag。README 的安装、clone 与 tree 引用固定到 `v0.2.0`，不使用未修改的 `main`。

## 新默认：continuous

- `speech_mode` 默认 `continuous`：每个 dialogue turn 的完整 `tts_text` 一次 native call，不再外部逐句调用，也不让 bounded repair 静默改成碎片。
- `legacy_chunks` 是显式旧模式，保留旧分段策略；`segment_chars` 属于旧模式，不控制 continuous。
- 一次外部调用不保证内部一个 context。低显存原始文本大于 40 字符的拆段路径、token 预算拆段都必须考虑；continuous 超限明确失败，重写为自然角色 exchange 或显式选择旧模式，不遗漏文本或绕过容量。
- 同一 turn 的短段保持完整，不把整个多角色 podcast 合为一个文本；正式预览仍为 30–60 秒，独立校准可以约 5–15 秒。

## 显式生成参数与声音默认

本版显式 recipe：`do_sample=false`、`top_p=0.8`、`top_k=30`、`temperature=0.4`、`num_beams=3`、`repetition_penalty=8`、`length_penalty=0`、`max_mel_tokens=1500`、`diffusion_steps=25`；`max_text_tokens_per_segment=160`、`interval_silence_ms=0`。
配置字段与 native 的映射及其他运行值以 [runtime.md](../skills/research-podcast-kurumi/references/runtime.md) 为准。

speaker 与默认 emotion 沿用同一用户确认的平稳原声；额外 `emotion_audio` 只在用户明确需要时配置，delivery 标签不自动转强情绪。
示例使用通用角色 reference 占位，不提交真人/声优音频，不把旧被否决 PV 处理声作为默认库。

## 缓存与失效

- 已生成音频缓存纳入模式和有效生成参数、seed、文本与参考状态。迁移模式、改变参数或参考时使相关 turn 失效，不能把旧碎片作为新的 continuous 结果。
- 可选 `voice_cache_dir` 跨进程保存 native conditioning tensors。源码随本版打包；缓存 `.pt` 和真实声音留本地，不提供预建角色声音库。
- conditioning 缓存依赖兼容的 native source、基础权重、参考和运行环境；不是训练模型、LoRA 或 VC，不能独立代替 base 权重。参考同路径替换和模型/编码环境变化必须失效，缓存 miss 回到 native 编码。

## 本次认可短样与局限

正文“大家好，我是久留美。今天聊期权对冲。”共 18 字符（含标点），whole-text 单 native call，actual native 日志 `segments count=1`，输出 5.91 秒；同原声、同默认 IndexTTS 2.5、同 seed 与显式参数记录。用户试听认可，没有外部分句/拼接/剪静音/额外 fade/别人 emotion/LoRA/VC。

此前剪三处 pause 没有解决 TTS 连续生成需求。目标是平滑韵律状态，不是零停顿或固定 F0。
认可仅限这次短样，不保证所有 voice 或长稿无气声/无跳层，也不是 ASR 认证。历史 UI 实际参数未知，不宣称唯一根因或逐位复现。20.067 秒 JA reference 在所用 native 中只取前 15 秒；音色仍需人类确认。
完整事实、机制与适用边界见 [continuity-v0.2.0.md](continuity-v0.2.0.md)。

## 迁移与验证边界

固定 `v0.2.0` 源码/Skill，使用本地已确认参考与显式 recipe；旧分段确有需要时明确配置 `legacy_chunks`。正常 turn 继续复用，新生成结果按新缓存签名检查，不为少量修订重推整集。

- 按 AGENTS 规定完成完整 CPU 单元测试：**47 项通过，耗时 10.061 秒，无 skip**。
- 本次整合未新增 GPU 测试或 ASR 推理。
- **5.91 秒用户认可短样来自此前真实的原生 IndexTTS 2.5 实验，不是 CPU fixture 生成的音频。** CPU 测试结果与人类试听反馈是不同证据，前者不证明声线或听感。

公开仓库只保存代码、文档和原创结构示例；私有素材、实际本机路径、登录态、权重、音频、`.pt` 与完整 ASR 私有记录保持本地。
