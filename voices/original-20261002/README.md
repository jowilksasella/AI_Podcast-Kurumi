# 原始音色与中文情绪库（original-chat-20261002）

`original-chat-20261002` 配方的八个原始文件。每个文件的 sha256 与大小都与公开配方 [recipes/original-chat-20261002.json](../../recipes/original-chat-20261002.json) 记录的身份一致，可直接绑定：

    .\scripts\run.ps1 bind-original --assets voices/original-20261002 --index-home "YOUR_EXISTING_INDEXTTS_DIRECTORY" --out config.local.json

| 文件 | 用途 |
|---|---|
| `kurumi_ja.wav` | 久留美音色：铃木爱奈公开日语演员样本 |
| `mochiko_ja.wav` | 萌智子音色：濑户麻沙美公开日语演员样本 |
| `kurumi_explain.wav` | 久留美中文 explain / comment 情绪 |
| `kurumi_question.wav` | 久留美中文 question 情绪 |
| `kurumi_joke.wav` | 久留美中文 joke；原正文也供萌智子 joke 使用 |
| `mochiko_explain.wav` | 萌智子中文 explain 情绪 |
| `mochiko_comment.wav` | 萌智子中文 comment 情绪 |
| `mochiko_question.wav` | 萌智子中文 question 情绪 |

中文片段是原始 AI 聊天的表演参考，不是演员本人的中文录音。动画音色定稿（[../anime-20261022/](../anime-20261022/)）只换日语音色参考，中文情绪仍用这里的文件。

演员样本版权归配音演员及其事务所；按仓库所有者的决定（2026-10-24）放在这里供本工作流复用，不适用 MIT。
