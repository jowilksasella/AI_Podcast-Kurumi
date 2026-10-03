# 本地运行与数据结构

只安装 Skill 时获得的是制作说明；要运行下面的 CLI，先克隆完整仓库的 `v0.2.0` tag。CLI 代码不藏在单独安装的 Skill 文件夹里。版本和发布状态见 [README](https://github.com/jowilksasella/AI_Podcast-Kurumi/tree/v0.2.0)。

## 环境分开

资料提取使用常规 Python + pypdf。音频渲染使用已安装 IndexTTS 2.5 的环境。
不要升级或重装用户的 torch/CUDA 环境。Windows 整合包虚拟环境可能使用相对基础解释器路径，必须先进入 INDEXTTS_HOME。

`scripts/run.ps1` 会设置临时 PYTHONPATH 指向本仓库，并在结束后恢复工作目录和 Python 环境变量。
普通调用：

    python -m kurumi_podcast validate plan.json --stage full
    python -m kurumi_podcast doctor --config config.local.json --plan plan.json

Linux / macOS 的已有模型环境：

    export INDEXTTS_HOME=/path/to/index-tts
    export PYTHONPATH=/path/to/AI_Podcast-Kurumi
    cd "$INDEXTTS_HOME"
    /path/to/model/python -m kurumi_podcast render /path/to/plan.json --config /path/to/config.local.json --out /path/to/output --stage preview

## 计划

必需：

- title、lead（默认久留美）
- lines：非空数组，每段包含 speaker、text、chapter
- delivery：explain / question / comment / joke，默认 explain
- id：可省略，自动按顺序编号；若填写只能用字母、数字、下划线、横线
- opening=true：开头铺垫的段落；至少首段需要标注。内容是否真正有铺垫由助手审核。
- source_refs：来源页码/图表说明，用于人工溯源

可选：

- tts_text：仅在误读时填发音控制文字；正文/字幕仍用 text
- after_ms：接话间隔，可有少量短重叠，不要每段统一停 0.7 秒
- reuse_audio：已确认音频的路径，相对计划文件解析；不重新推理

一条 line 对应一个自然角色 turn；可以包含连续的两三句，不按标点自动变成多个 TTS 请求。`tts_text` 存在时完整使用它，否则使用完整 `text`。

## 声线输入

voice 配置按角色名映射。每个角色至少有 reference_audio，路径相对配置文件解析；示例提供通用占位，用户填入自己已试听确认的参考。
source_kind 与 identity_label 用于输出身份标注。声优真人日语样本可作普通话合成参考，但它不等于真实角色对白、角色专用模型或本人新录音。

speaker 与默认 emotion 使用同一份用户已确认的平稳原声。`emotion_audio` 只在用户明确要求额外表演风格时配置；它技术上可来自另一说话人，但不能把这个能力当默认策略。
`delivery=explain/question/comment/joke` 是台词意图标签，不自动映射强 emotion。voice 的 emotion_audio 保持空配置即可沿用原声。

所检索的 native IndexTTS 2.5 会截取 speaker/emotion 参考的前 15 秒。20.067 秒参考文件不表示全部 20.067 秒参与 conditioning；换引擎版本后以实际 source/日志为准。
优先用户确认的声线；官网 PV 去 BGM 或强清洗可能损坏音色，不因为来源“官方”就替换已确认参考。ASR、SNR 或无 clipping 都不能代替人类听辨。

## continuous 与容量边界

`speech_mode` 默认为 `continuous`：每个 turn 完整 tts_text 一次外部 native 调用，不逐句请求，不通过 bounded repair 静默碎切。同一短 turn 的上下文保持完整；角色之间仍各自调用，再按时间轴混音。

**外部 one call 不等于内部 one context。** native 有两条独立拆段路径：

- 本次使用的低显存模式在原始 text 长度 **大于 40 字符**时自动拆段；包含标点及发音标签的原始长度也要考虑。这个边界不是所有设备都统一 40 字，也不表示所有不超过 40 字的文本都能通过。
- tokenizer 的 `max_text_tokens_per_segment` 预算也可能产生多个内部 segments；字符数不能代替实际 token 检查。

continuous 遇到上述容量边界应明确失败，让脚本重写成自然角色 exchange，或显式配置 `speech_mode="legacy_chunks"` 使用旧模式。完整保留原意与文本，不静默拆字、截断、遗漏，不关闭容量机制强行生成。
native 拆段 helper 或真实 token 容量无法验证时，也明确报告不兼容，不假装已经证明 single context 或自动切换旧模式。
`legacy_chunks` 才沿用自然分段和旧 bounded repair；`segment_chars` 仅为旧模式的分段设置，不能拿来调连续模式。
不保证任意长段或全篇一次 context；持续状态也不要求没有停顿或固定 F0。

仅做声线或连续语气校准时，可单独调用 native 生成约 5–15 秒短样；正式 CLI `--stage preview` 仍要求 30–60 秒。不要为短校准补废话凑满 30 秒，也不要用校准认可代替正式样片确认。

## 显式生成 recipe · v0.2.0

以下是本版项目默认值，不是上游全部默认值的转录：

```json
{
  "speech_mode": "continuous",
  "max_text_tokens_per_segment": 160,
  "interval_silence_ms": 0,
  "generation_kwargs": {
    "do_sample": false,
    "top_p": 0.8,
    "top_k": 30,
    "temperature": 0.4,
    "num_beams": 3,
    "repetition_penalty": 8.0,
    "length_penalty": 0.0,
    "max_mel_tokens": 1500,
    "diffusion_steps": 25
  }
}
```

`interval_silence_ms` 对应 native `interval_silence`，仅控制内部 segments 之间额外插入的静音，不消除句内自然停顿，也不修复韵律重启。角色间的 `after_ms` 是另一项接话时间设置。
即使 `do_sample=false` 时部分采样参数不参与随机采样，仍保留显式 recipe 与本地运行记录，不把它们改成未记录的 native 默认。
所检索的上游 native 默认 temperature=0.8、repetition_penalty=10；此前工作台用 0.4/8。本版明确写参数，避免“同模型”被误当“同实际配置”。历史 UI 会话的实际参数未知，不能声称唯一根因已查明或位元相同。
该上游 source 的 S2Mel 路径把 diffusion_steps 固定为 25；recipe 的 25 与之对应，但不能据此声称任意 native revision 都支持通过同名 kwargs 动态调节。整合时确认实际后端的参数接收/消费方式。
使用同一配置 seed 与同一 turn 的实际 seed 做对照；seed 固定本身不保证跨环境逐位复现。

其他运行默认：

- lang=ZH，duration_factor=1.0；无独立 emotion 参考时有效 emo_alpha=1.0
- BF16 按配置启用，默认不打开 DeepSpeed、自定义 CUDA kernel 或 torch.compile
- 不加载 QwenEmotion，使用音频情绪参考；没有独立情绪参考时使用声线参考
- 默认离线加载现有模型，辅助权重缺失会明确报错，不自动偷偷下载
- 仅修已出现问题的发音。不要给每一个“买、卖、伽马”都全局插入标注

配置模板写 emo_alpha=1.0。显式使用独立 emotion reference 时以配置值为准，未写该值的 wrapper 回退为 0.5；没有独立参考则沿用 speaker reference，有效值为 1.0。排查时记录实际有效输入，不把配置表面值误当全部 native 状态。

官方发音控制形如 `<卖|MAI4>出`；发音标签只放在 tts_text。
比如“接着卖”容易读混，可先改成语义更明确的“继续卖出”“做空”“追加空头仓位”，再考虑局部标注。

## 两类缓存

### 已生成 turn 的音频缓存

比较实际 text/tts_text、音色/有效情绪参考的文件状态、模式、seed、有效 generation_kwargs、token 预算和 interval 设置。显式参数变化或从旧模式迁移至 continuous 时，受影响 turn 失效，旧片段不能冒充新的连续样本。
改变某一 turn 只重生成该完整 turn，正常 turn 继续复用。原始片段存在但无匹配缓存记录，不视为已验证产物；显式 reuse_audio 是用户认可音频的独立复用入口。

### 可选 native conditioning 缓存

配置 `voice_cache_dir` 才跨进程保存 native 的 speaker/emotion conditioning tensors；例如使用忽略目录 `local-assets/voice-cache`。不配置时使用 native 自身的进程内缓存。
本版打包持久缓存实现代码，不打包既有缓存、真实参考音频或被否决的 PV 声音，不建立默认声音库。

缓存是参考经过 native encoder 后的张量结果，**不是训练模型、LoRA 或 VC**，仍需同一基础权重和兼容的推理环境。
参考、模型/配置、native source、运行 dtype/device 或身份元数据变化时，应重新编码；同路径替换参考也不能沿用旧 conditioning。失配/损坏的缓存作为 miss 回到 native 编码，不当作已经验证的声线。
实际声音与 `.pt` 仅留本地。输出缓存、时间轴、原始日志里的实际路径和完整 ASR 私有记录不上传仓库；不额外做与产品缓存键无关的整树哈希检查。

## 输出

主文件 episode.mp3、episode.wav；配套 transcript.txt、subtitles.srt、manifest.json。
字幕是发言区间内分配的初稿，不冒充精确字级对齐结果。需要精确字幕时再做有针对性的对齐。

## 连续语气排查入口

用户反馈跨句音高、力度或发声方式“跳层”时，读 [continuity.md](continuity.md)。有足够的 native 调用证据和用户试听反馈就交付；重装模型、全文 ASR、换声或重新训练不是默认路线。

容量、前 15 秒裁切、native 默认参数和进程内缓存的来源：[官方 infer_v2_5.py](https://github.com/index-tts/index-tts/blob/d9e41aac89fd00b3d71497fddb287b7f24613712/indextts/infer_v2_5.py)。能力说明：[IndexTTS 2.5 官方演示与技术报告](https://index-tts.github.io/index-tts2-5.github.io/)。项目 recipe 与用户短样反馈不冒充上游普遍结论。
