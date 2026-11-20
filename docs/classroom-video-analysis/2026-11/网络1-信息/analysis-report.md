# 网络1-信息 课堂视频分析结果

- 课题：信息的基本特征
- 视频时长：658.1 秒

## 动作记录

- MM-TBA 事件行：130
- 分类条数：Normal 115, Writing 15
- 各类平均置信度：Normal 0.516, Writing 0.522
- GPU：CUDA RTX 5060

## 声学线索

- 0.2 秒窗：3290
- RMS 中位数：-20.79 dBFS；10–90 分位：-33.71–-15.57 dBFS
- 高于 -45 dBFS 的窗：3287（只作信号阈值参考，不代表语音占比）
- 本次未运行转写或中文声音情绪识别。

## 面部模型输出

- YuNet 人脸检测：655/659 秒（99.4%）
- LibreFace 有效输出：545/659 帧
- 表情最高分标签条数：Neutral 311, Happiness 200, Sadness 29, Surprise 2, Disgust 3
- 原始表情分数均值：Anger 0.103, Contempt 0.093, Disgust 0.097, Fear 0.094, Happiness 0.177, Neutral 0.217, Sadness 0.122, Surprise 0.097

## 使用边界

- 行为、表情与声学值都是模型/信号输出，需回放抽查；不可直接等同教学质量或真实情绪。
- 音量阈值不是经过验证的语音活动检测；本次未运行ASR、教学话语识别或中文SER。
- 表情类别和AU值未在这批视频上做人工校准；缺失帧不补值。
- MM-TBA动作类别置信度偏低时须人工复核，Normal/Writing/Pointing均不应直接用于评分。
