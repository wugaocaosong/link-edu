# xzr 课堂视频分析结果

- 课题：算法的三要素（IPO）与三大结构
- 视频时长：507.1 秒

## 动作记录

- MM-TBA 事件行：186
- 分类条数：Writing 115, Pointing 5, Normal 66
- 各类平均置信度：Writing 0.537, Pointing 0.523, Normal 0.523
- GPU：CUDA RTX 5060

## 声学线索

- 0.2 秒窗：2536
- RMS 中位数：-40.06 dBFS；10–90 分位：-48.47–-34.85 dBFS
- 高于 -45 dBFS 的窗：2008（只作信号阈值参考，不代表语音占比）
- 本次未运行转写或中文声音情绪识别。

## 面部模型输出

- YuNet 人脸检测：508/508 秒（100.0%）
- LibreFace 有效输出：389/508 帧
- 表情最高分标签条数：Neutral 331, Sadness 41, Anger 8, Surprise 4, Fear 1, Happiness 4
- 原始表情分数均值：Anger 0.117, Contempt 0.095, Disgust 0.096, Fear 0.100, Happiness 0.098, Neutral 0.249, Sadness 0.142, Surprise 0.103

## 使用边界

- 行为、表情与声学值都是模型/信号输出，需回放抽查；不可直接等同教学质量或真实情绪。
- 音量阈值不是经过验证的语音活动检测；本次未运行ASR、教学话语识别或中文SER。
- 表情类别和AU值未在这批视频上做人工校准；缺失帧不补值。
- MM-TBA动作类别置信度偏低时须人工复核，Normal/Writing/Pointing均不应直接用于评分。
