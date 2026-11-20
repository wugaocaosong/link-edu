# lkr 课堂视频分析结果

- 课题：程序语句与程序结构：顺序、分支及代码规范
- 视频时长：595.0 秒

## 动作记录

- MM-TBA 事件行：149
- 分类条数：Normal 102, Writing 47
- 各类平均置信度：Normal 0.536, Writing 0.568
- GPU：CUDA RTX 5060

## 声学线索

- 0.2 秒窗：2975
- RMS 中位数：-25.34 dBFS；10–90 分位：-34.28–-20.83 dBFS
- 高于 -45 dBFS 的窗：2975（只作信号阈值参考，不代表语音占比）
- 本次未运行转写或中文声音情绪识别。

## 面部模型输出

- YuNet 人脸检测：595/595 秒（100.0%）
- LibreFace 有效输出：238/595 帧
- 表情最高分标签条数：Neutral 95, Happiness 29, Surprise 28, Anger 3, Fear 18, Sadness 64, Disgust 1
- 原始表情分数均值：Anger 0.098, Contempt 0.089, Disgust 0.092, Fear 0.123, Happiness 0.114, Neutral 0.188, Sadness 0.165, Surprise 0.131

## 使用边界

- 行为、表情与声学值都是模型/信号输出，需回放抽查；不可直接等同教学质量或真实情绪。
- 音量阈值不是经过验证的语音活动检测；本次未运行ASR、教学话语识别或中文SER。
- 表情类别和AU值未在这批视频上做人工校准；缺失帧不补值。
- MM-TBA动作类别置信度偏低时须人工复核，Normal/Writing/Pointing均不应直接用于评分。
