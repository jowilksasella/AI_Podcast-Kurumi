# 本地运行与原始配方

单独安装 Skill 获得的是制作说明，CLI 需要完整仓库。根仓库 URL 默认指向当前 main 的 `original-chat-20261002`，不自动取 latest release。

## 一次准备、绑定后复用

配方是公开元数据；原始声音留在本地。已有的原始文件可一次性复制/按槽位命名到忽略的 `local-assets/original-20261002/`，也可直接绑定已具备这些文件名的现有目录。只复制已有原件，不自动下载、重剪或重新生成替代声音。

### 原始资产槽位

| 文件名 | 用途 |
|---|---|
| `kurumi_ja.wav` | 久留美音色：铃木爱奈原始公开日语演员参考 |
| `mochiko_ja.wav` | 萌智子音色：濑户麻沙美原始公开日语演员参考 |
| `kurumi_explain.wav` | 久留美中文 explain / comment 情绪 |
| `kurumi_question.wav` | 久留美中文 question 情绪 |
| `kurumi_joke.wav` | 久留美中文 joke；原正文也供萌智子 joke 使用 |
| `mochiko_explain.wav` | 萌智子中文 explain 情绪 |
| `mochiko_comment.wav` | 萌智子中文 comment 情绪 |
| `mochiko_question.wav` | 萌智子中文 question 情绪 |

中文片段是原始 AI 聊天表演参考，不能标为演员本人的中文样本。共享 joke 是原正文库的情绪输入，不会更换萌智子的 JA 音色。

公开配方的资产身份需与原件一致，不能仅凭文件名或采样率相同视为原件。缺文件时报告具体槽位；身份不匹配时说明对应槽位，不生成降级替代品。

在仓库根目录，使用已有模型环境绑定：

    .\scripts\run.ps1 bind-original --assets local-assets/original-20261002 --index-home "YOUR_EXISTING_INDEXTTS_DIRECTORY" --out config.local.json

CLI 等价入口（需在已有环境能导入完整仓库）：

    python -m kurumi_podcast bind-original --assets DIRECTORY --index-home DIRECTORY --out config.local.json

输出必须以 `.local.json` 结尾；`config.local.json`、`config.original.local.json` 都是忽略的本地配置。绑定会验证八个原始文件并记录**当前本机**环境，不证明历史 native 完全相同、历史音频逐位相同或听感已通过。绑定成功后保留配置，后续 doctor/render 复用它；配置内的 `original_lock` 不手写。

[config.example.json](../../../examples/config.example.json) 仅展示非空情绪映射和相对路径结构，**未绑定，不能直接渲染**。从历史空字典模板复制来的配置也不能充当原始模式。

## 环境与命令

资料提取用已有常规 Python + pypdf；音频渲染用已有本地 IndexTTS 2.5，不重装 torch/CUDA、不下载大模型、不换 Edge。

Windows 启动器先定位环境，再原样转发参数：
显式 `--index-home` → `INDEXTTS_HOME` → `--config` 中的 index_home。进入模型目录使用其 Python，结束后恢复工作目录和临时 Python 环境变量。已有环境变量若指向另一个模型，会与绑定冲突；纠正该变量，不静默改用另一引擎。

    python -m kurumi_podcast validate examples/preview.json --stage preview
    .\scripts\run.ps1 doctor --config config.local.json --plan examples/preview.json
    .\scripts\run.ps1 render examples/preview.json --config config.local.json --out outputs/preview --stage preview

Linux/macOS 已有模型环境的占位调用：

    export PYTHONPATH=/path/to/AI_Podcast-Kurumi
    cd /path/to/index-tts
    /path/to/model/python -m kurumi_podcast bind-original --assets /path/to/original-assets --index-home /path/to/index-tts --out /path/to/AI_Podcast-Kurumi/config.local.json
    /path/to/model/python -m kurumi_podcast render /path/to/preview.json --config /path/to/AI_Podcast-Kurumi/config.local.json --out /path/to/output --stage preview

冻结配置绑定具体输入/环境；环境确实变更需要新绑定时，说明这是当前环境的新绑定，不伪称找回历史环境。原始资产或情绪不得借“重新绑定”改成替代品。

## 恢复参数的意义

完整权威值在公开 `recipes/original-chat-20261002.json`；下表说明不能混淆的开关：

| 维度 | 原始正文配方 |
|---|---|
| 声音 | JA `reference_audio` + 角色/delivery 对应的独立 ZH `emotion_audio` |
| 情绪 | `emo_alpha=0.5`，`use_random=False`，不加载 QwenEmotion、不加情绪向量 |
| 解码 | `do_sample=True`、`top_p=0.8`、`repetition_penalty=10.0`；`top_k=30`、temperature 0.8 |
| 正文长度与停顿 | text tokens 180、mel tokens 1500、interval silence 110 ms、duration factor 1.0 |
| 正文 seed | `20261002 + 900 + turn`；数字轮次保持稳定 |
| 开场修订 | 单独的 opening seed 和 token 上限由配方指定，不能误当正文或原 41 秒试听参数 |

`use_random=False` 不会关闭解码采样。没有独立情绪参考时 native 会退回音色参考并将有效 alpha 设为 1，所以“配置写了 0.5”与“实际混入了中文情绪”不是一回事。原始模式必须使用非空映射；不能缺 reference 就静默 fallback。

当前可用 native 已在 10 月 3 日变化，未确立 10 月 2 日 native 备份；锁的是选定原始资产和配方参数在当前环境的绑定，不是历史波形认证。约 41 秒试听、修订 60 秒开场与正文库的区别见[恢复说明](../../../docs/original-chat-restoration.md)。

## 计划结构

必需 title、lead 和非空 lines；每轮包含 speaker、text、chapter。

- delivery：explain / question / comment / joke。原始模式按公共配方选情绪，不新增空映射。
- id：可省略，core 按顺序给数字编号；填写时仅字母、数字、下划线、横线。正文 seed 与 id 对应，修订保留正常轮次 id。
- opening=true：首两轮铺垫标注；标记本身不能证明内容真有铺垫。
- source_refs：来源页码/图表说明供溯源。
- tts_text：需要时独立写发音控制，text/字幕保持正常文字。原始模式的历史发音转换由配方执行，不再全局叠加另一套替换。
- after_ms：接话间隔；不为追求连续性把每轮统一静音或全部拼成超长段。
- reuse_audio：已有确认音频的路径，相对计划解析；不重新推理。历史认可不能自动传给新增片段。

声音路径相对配置文件解析，角色名映射到 reference_audio / emotion_audio。原始模式固定两位角色，不能把新搭档塞进配置还称恢复。默认预览约 220–270 字、每轮约 50 字以内；360 字上限不是写到 360 字的目标。

## 缓存与输出

只重做文本、参考输入或参数确实变化的段落。原始资产身份检查属于配方绑定，不额外做普通保存的整树哈希；配方变化与本机路径状态需要纳入缓存，不能拿不匹配缓存当有效声音。

主文件 episode.mp3 / episode.wav，配套 transcript.txt、subtitles.srt、manifest.json。字幕是发言区间内分配的初稿，不冒充字级对齐。缓存、配置和生成产物留在本地。
