# 本地运行与原始配方

单独安装 Skill 获得的是制作说明，CLI 需要完整仓库。根仓库 URL 默认指向当前 main 的 `original-chat-20261002`，不自动取 latest release。

## 一次准备、绑定后复用

配方是公开元数据。八个原始文件按用户决定（2026-10-24）已提交在 `voices/original-20261002/`，身份（sha256）与公开配方一致，可直接绑定；也可绑定其他已具备这些文件名的目录（如本机忽略的 `local-assets/original-20261002/`）。只复制已有原件，不自动下载、重剪或重新生成替代声音。

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

    .\scripts\run.ps1 bind-original --assets voices/original-20261002 --index-home "YOUR_EXISTING_INDEXTTS_DIRECTORY" --out config.local.json

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

## 换搭档或换情绪映射：variant 配置

用户明确换搭档（如山师芽吹）或要求整集统一情绪映射时，不改原始配置，另写一个 `recipe: "variant"` 的 `*.local.json`：

    {
      "recipe": "variant",
      "base_config": "config.original.local.json",
      "voices": {
        "久留美": { "...": "照抄原始配置的久留美条目" },
        "山师芽吹": {
          "actor": "伊藤彩沙", "identity_label": "…", "source_kind": "seiyuu_sample",
          "source_url": "…", "reference_language": "ja",
          "reference_audio": "local-assets/mebuki/mebuki_ja.wav",
          "emotion_audio": {"explain": "…", "comment": "…", "question": "…", "joke": "…"}
        }
      }
    }

结构示例见 [variant.example.json](../../../examples/variant.example.json)。variant 的行为：

- 采样、情绪 alpha、token、后处理等全部设置、IndexTTS 位置都继承 `base_config`；variant 里写了不同的值即报错（drift），不能借 variant 偷改参数。
- 执行方式与原始配方相同：每轮固定 seed（不加分段偏移）、原始发音转换、不做短分段重试；每个用到的 delivery 都要有独立且不同于音色参考的 emotion_audio。
- 每次运行都先验证 base 的原始锁（资产身份、引擎文件、软件版本）；base 失效时 variant 也不能运行。
- manifest 标为 `variant`、`restoration: false`，并记录每个用到的音色/情绪文件身份；它不是原始恢复，也不能用于给原始正文补开场。

用 doctor/render 时把 `--config` 指向 variant 文件即可；计划里如写了 `recipe`，需为 `variant`。variant 没有 `index_home`：`run.ps1` 会沿 `base_config` 找到原始配置里的模型目录，也可显式传 `--index-home` 或设 `INDEXTTS_HOME`（启动器会替不认识此参数的命令去掉它）。在 PowerShell 里直接 `.\scripts\run.ps1 …` 调用；经 `powershell -File` 转一层时 PowerShell 会把 `--out` 当作自己的参数。

## 动画音色定稿（GEX，2026-10-22）

用户听过短样后认可：久留美与萌智子都用动画对白音色，中文情绪、seed 规则与全部设置继承原始配置。

- 参考：`voices/anime-20261022/kurumi_anime_dense_ja.wav`（第 2 集三段确认片段拼接，停顿压到 ≤0.4 秒，14.9 秒）与 `mochiko_anime_dense_ja.wav`（第 2 集 09:25.82–09:39.92，停顿压到 ≤0.4 秒，11.6 秒）。来历、确认片段集与弃用参考见该目录 README。
- 配置：复制 [anime-cast.variant.json](../../../examples/anime-cast.variant.json) 到仓库根目录为 `config.anime.local.json`，`base_config` 指向已绑定的原始配置；中文情绪参考用已提交的 `voices/original-20261002/`。
- 教训：第一次用的久留美单段参考有 45% 是停顿，生成时出现约 8 秒静音与漏读；萌智子原片段 0.6–1.1 秒的停顿让台词里出现 1.6–1.9 秒空白。参考片段一律先压停顿。

## 动画对白声线素材（本地、可选）

默认音色仍是演员公开样本。用户明确要求试动画对白时，才走这条流程，产物用于 variant 短样；用户认可后可作定稿（如上）。素材来自用户本机已有的剧集或片段：不下载或录制串流、不上传到在线分离服务。用户认可的参考与确认片段按其决定提交在 `voices/`；整集分离人声等大文件仍只在本机。

1. **去 BGM**：audio-separator（[nomadkaraoke/python-audio-separator](https://github.com/nomadkaraoke/python-audio-separator)）装在独立 venv，不装进 IndexTTS 环境；首次使用会下载所选模型权重，需用户同意。

       python -m kurumi_podcast separate-vocals 片段或剧集... --out voice-refs/vocals-run --separator PATH\audio-separator.exe

   默认模型 `vocals_mel_band_roformer.ckpt`。`separation.json` 的 `removed_db` 越负说明原片越干净（约 −45 dB 以下几乎没去掉东西，−10～−20 dB 是明显 BGM 被去掉）。

2. **按声线找角色**：在 IndexTTS 模型环境运行（需要其中的 CAM++ 权重与已缓存的 faster-whisper；不会下载）。正例是已确认的目标片段，反例按角色分组：

       .\scripts\run.ps1 find-speaker --config config.original.local.json --target mochiko --positive 已确认萌智子\*.wav --negative kurumi=已确认久留美\a.wav yasuko=安子\b.wav --episode 2b=vocals\2b.wav=input\2b.wav --out voice-refs/mochiko_candidates

   - 嵌入与 IndexTTS 合成时用的说话人条件相同（CAM++）。分数相对**最接近的其他角色**计算，所以每个容易混淆的声音都要有自己的反例组（例：CAM++ 听来铃木爱奈的久留美与冈咲美保的安子很接近）。
   - 两集里完全相同的音频（OP/ED、预告）自动排除，避免把主题曲歌词当对白。
   - Whisper 把快速对话并成一段时，前后半段声线不一致会标 `mixed`，不进高信心组。
   - `--high SCORE MARGIN` 默认 0.6 / 0.15；声音接近的组合按用户确认结果校准（久留美对安子时 margin 0 更合适）。

3. **人工核对**：从原片剪带编号、集数、时间戳、分数和日文转写的核对视频：

       python -m kurumi_podcast review-video voice-refs/mochiko_candidates/candidates.json --episode 2b=D:\剧集\2b.mp4 --out voice-refs/review.mp4

   同名 `.json` 记录每段在核对视频里的时间，便于用户说“7:37 以后”。

4. **记录结论**：用户看完后，把认错的段落转为该角色的反例，其余进入已确认集（带 `.lst` 与 README 记录）：

       python -m kurumi_podcast confirm-review voice-refs/review.json --confirmed voice-refs/kurumi_confirmed --reject 7:37- --reject-as yasuko --anchors voice-refs/anchors

   `--reject` 接编号（`92-94`）或核对视频时间（`0:51~0:54`、`7:37-`）。自动排名不是身份证明；只有用户确认过的片段才进入已确认集，再用于下一集的正例或做 variant 音色参考。

5. **做音色参考**：挑语气平稳、声线干净的确认片段（独白/旁白最好），压掉句内长停顿后拼成一条 ≤15 秒的参考（IndexTTS 只读前 15 秒）：

       python -m kurumi_podcast compress-pauses 确认片段a.wav 确认片段b.wav --out local-assets/anime/kurumi_ja.wav

   默认 `--max-pause 0.4`；超出 15 秒的片段会跳过并在结果里注明。先用同一份短样文本做只换一位角色音色的 A/B（另一位逐字节不变），用户听过再定。

## 计划结构

必需 title、lead 和非空 lines；每轮包含 speaker、text、chapter。

- delivery：explain / question / comment / joke。原始模式按公共配方选情绪，不新增空映射。
- id：可省略，core 按顺序给数字编号；填写时仅字母、数字、下划线、横线。正文 seed 与 id 对应，修订保留正常轮次 id。
- opening=true：首两轮铺垫标注；标记本身不能证明内容真有铺垫。
- source_refs：来源页码/图表说明供溯源。
- tts_text：需要时独立写发音控制，text/字幕保持正常文字。原始模式的历史发音转换由配方执行，不再全局叠加另一套替换。
- after_ms：接话间隔；不为追求连续性把每轮统一静音或全部拼成超长段。
- reuse_audio：已有确认音频的路径，相对计划解析；不重新推理。历史认可不能自动传给新增片段。

声音路径相对配置文件解析，角色名映射到 reference_audio / emotion_audio。原始模式固定两位角色，不能把新搭档塞进配置还称恢复；换搭档用上面的 variant 配置。默认预览约 220–270 字、每轮约 50 字以内；360 字上限不是写到 360 字的目标。

## 缓存与输出

只重做文本、参考输入或参数确实变化的段落。原始资产身份检查属于配方绑定，不额外做普通保存的整树哈希；配方变化与本机路径状态需要纳入缓存，不能拿不匹配缓存当有效声音。

主文件 episode.mp3 / episode.wav，配套 transcript.txt、subtitles.srt、manifest.json。字幕在每轮发言内按文字长度分配，再就近对齐到该轮实际测得的停顿（manifest 每轮 `pauses`）；仍不冒充字级对齐。缓存、配置和生成产物留在本地。

生成后的辅助命令（前两个不需要模型环境）：

    python -m kurumi_podcast qa outputs/episode
    python -m kurumi_podcast package-chapters outputs/episode
    .\scripts\run.ps1 asr-check outputs/episode --config config.anime.local.json

`qa` 报告语速异常的轮次（疑似重复/长停顿或漏读）、句内长静音（`long_internal_pause`，默认 ≥1.3 秒，`--long-pause` 可调）、削波、峰值、主讲有效发言占比和粤语/繁体/口播定位符；标记是该去听的线索，`listening_verified` 始终为 false。`asr-check` 用模型目录里已缓存的 faster-whisper 逐轮转写（读 `out/work/NNN.wav`），写 `asr.json`：相似度最低的轮次（多半是数字写法和同音字，读一遍找真漏读/重复）与 `buy_sell_listen`（并列“买…卖”被同化的句子，留给人听）。一分钟系列的 `split-series`、`render-series`、`source-map` 见 [shorts.md](shorts.md)。`package-chapters` 按 manifest 章节时间从 episode.wav 切出 `chapters/NN-章节名.mp3` 与 `chapters.json`，整集母带不变。

预览实际时长不在 30–60 秒时仍写出全部文件，manifest 记 `duration_ok: false`，CLI 在 stderr 警告并以退出码 3 结束：先试听，再用缓存精简或补充台词，不当成已合格短样。
