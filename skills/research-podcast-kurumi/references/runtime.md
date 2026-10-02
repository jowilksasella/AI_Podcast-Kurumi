# 本地运行与数据结构

只安装 Skill 时获得的是制作说明；要运行下面的 CLI，先克隆完整仓库。CLI 代码不藏在单独安装的 Skill 文件夹里。

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

voice 配置按角色名映射。每个角色至少有 reference_audio，路径相对配置文件解析。
source_kind 与 identity_label 用于输出身份标注。声优日语样本可生成普通话，但不能叫作角色专用模型。
emotion_audio 可以是其他说话人的音频：它控制表演风格，reference_audio 控制音色。

## 渲染默认值

- lang=ZH，duration_factor=1.0，emo_alpha=0.5
- BF16 按配置启用，默认不打开 DeepSpeed、自定义 CUDA kernel 或 torch.compile
- 不加载 QwenEmotion，使用音频情绪参考；没有独立情绪参考时使用声线参考
- 默认离线加载现有模型，辅助权重缺失会明确报错，不自动偷偷下载
- 自然句子约 50 字一段；异常时只针对该段用更短片段重试一次
- 仅修已出现问题的发音。不要给每一个“买、卖、伽马”都全局插入标注

官方发音控制形如 `<卖|MAI4>出`；发音标签只放在 tts_text。
比如“接着卖”容易读混，可先改成语义更明确的“继续卖出”“做空”“追加空头仓位”，再考虑局部标注。

## 缓存

每段缓存比较实际文字、音色/情绪参考的文件状态和合成参数。不做无意义的文件哈希校验。
改变台词、参考音频或参数只使相关段落失效。原始片段存在但无匹配缓存记录，不视为已验证产物。
输出目录里的缓存与时间轴是本地工作状态，不上传代码仓库。

## 输出

主文件 episode.mp3、episode.wav；配套 transcript.txt、subtitles.srt、manifest.json。
字幕是发言区间内分配的初稿，不冒充精确字级对齐结果。需要精确字幕时再做有针对性的对齐。
