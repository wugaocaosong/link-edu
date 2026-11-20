# ckh 课堂视频分析结果

- 课题：算法概念与特征：地铁换乘路线及流程图
- 视频时长：795.0 秒

## 动作记录

- MM-TBA 事件行：693
- 分类条数：Normal 688, Pointing 1, Writing 4
- 各类平均置信度：Normal 0.622, Pointing 0.503, Writing 0.516
- GPU：CUDA RTX 5060

## 声学线索

- 0.2 秒窗：3975
- RMS 中位数：-39.37 dBFS；10–90 分位：-41.08–-35.99 dBFS
- 高于 -45 dBFS 的窗：3975（只作信号阈值参考，不代表语音占比）
- 本次未运行转写或中文声音情绪识别。

## 面部模型输出

- YuNet 人脸检测：795/795 秒（100.0%）
- LibreFace 有效输出：491/795 帧
- 表情最高分标签条数：Neutral 292, Surprise 53, Sadness 53, Anger 55, Disgust 22, Happiness 16
- 原始表情分数均值：Anger 0.131, Contempt 0.089, Disgust 0.112, Fear 0.095, Happiness 0.104, Neutral 0.207, Sadness 0.144, Surprise 0.119

## 使用边界

- 行为、表情与声学值都是模型/信号输出，需回放抽查；不可直接等同教学质量或真实情绪。
- 音量阈值不是经过验证的语音活动检测；本次未运行ASR、教学话语识别或中文SER。
- 表情类别和AU值未在这批视频上做人工校准；缺失帧不补值。
- MM-TBA动作类别置信度偏低时须人工复核，Normal/Writing/Pointing均不应直接用于评分。
