# lm 课堂视频分析结果

- 课题：信息获取与辨识：检索策略和信息可信度
- 视频时长：580.7 秒

## 动作记录

- MM-TBA 事件行：202
- 分类条数：Normal 172, Writing 30
- 各类平均置信度：Normal 0.543, Writing 0.580
- GPU：CUDA RTX 5060

## 声学线索

- 0.2 秒窗：2903
- RMS 中位数：-34.24 dBFS；10–90 分位：-44.03–-29.15 dBFS
- 高于 -45 dBFS 的窗：2644（只作信号阈值参考，不代表语音占比）
- 本次未运行转写或中文声音情绪识别。

## 面部模型输出

- YuNet 人脸检测：580/581 秒（99.8%）
- LibreFace 有效输出：475/581 帧
- 表情最高分标签条数：Happiness 159, Surprise 61, Neutral 226, Sadness 24, Fear 1, Anger 4
- 原始表情分数均值：Anger 0.098, Contempt 0.091, Disgust 0.092, Fear 0.095, Happiness 0.169, Neutral 0.218, Sadness 0.115, Surprise 0.121

## 使用边界

- 行为、表情与声学值都是模型/信号输出，需回放抽查；不可直接等同教学质量或真实情绪。
- 音量阈值不是经过验证的语音活动检测；本次未运行ASR、教学话语识别或中文SER。
- 表情类别和AU值未在这批视频上做人工校准；缺失帧不补值。
- MM-TBA动作类别置信度偏低时须人工复核，Normal/Writing/Pointing均不应直接用于评分。
