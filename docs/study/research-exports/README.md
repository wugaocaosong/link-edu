# 《认识几分之一》研究导出验收材料

此目录仅放核查样例、空白表及明确标注的合成数据。没有复制真实参与者资料。第35节来自普通 demo 课堂、没有正式实验场次关联，只用于核查采集链；原始 PDF 和录像仍按获准研究存储管理。

## 交付件

- [第35节协调员核查样例](lesson35-coordinator-check.md)：来源、分母、播放时序、可追溯师生片段及待录像核验项。
- [匿名盲评空白表及评分说明](blind-scoring-form.md)：与匿名 5 分钟录像逐行核对，两次机会、四项评分、缺失原因栏。
- [双评分者合成汇总样例](synthetic-two-rater-example.md)：包含两次机会完整、缺机会和缺第二位评分者；合成分数不代表真实教师。
- [逐行 CSV 空白模板](blind-scoring-template.csv)：可复制为每名评分者、每个匿名片段的一份独立文件。
- [合成评分 JSON](synthetic-two-rater-example.json)：用于命令行回归。
- [合成汇总 JSON/CSV](synthetic-two-rater-aggregate.json)：由导出命令按公式实际计算得到。
- 第35节普通课堂核查 JSON：[lesson35-coordinator-check.json](lesson35-coordinator-check.json)。

## 命令

从仓库根目录运行，输入文件由协调员在获准研究存储里导出；不要把真实参与者文件复制到本仓库。

```powershell
python scripts/study_export.py blind --input "E:\approved-study\anonymous-clip.json" --out-dir "E:\approved-study\blind-packs\K7M4Q2"
python scripts/study_export.py aggregate --input "E:\approved-study\submitted-ratings.json" --out "E:\approved-study\coordinator\rating-summary.json"
python scripts/study_export.py coordinator --input "E:\approved-study\coordinator\two-round-record.json" --out "E:\approved-study\coordinator\P03-export.json"
python scripts/study_export.py generate-report --packet "E:\approved-study\sealed-packet.json" --events "E:\approved-study\source-events.json" --out "E:\approved-study\draft-report.json"
python scripts/study_export.py issue-report --input "E:\approved-study\issue-payload.json" --out "E:\approved-study\issued-report.json"
python scripts/study_export.py seal-input --input "E:\approved-study\source-events.json" --group transcript --session-id STUDY-ROUND --model deepseek-v4-flash --rubric fraction-formative-1 --template fraction-narrative-1 --out "E:\approved-study\sealed-packet.json"
python scripts/study_export.py seal-input --input "E:\approved-study\source-events.json" --group multimodal --session-id STUDY-ROUND --model deepseek-v4-flash --rubric fraction-formative-1 --template fraction-narrative-1 --motion "E:\approved-study\reviewed-motion.json" --out "E:\approved-study\sealed-packet.json"
```

`seal-input` 输出外层包含组别、场次标识和输入 SHA-256。**送模型时只发送 `input` 对象**。转写组只含最终转写；多模态组在完全相同的转写上附加播放回执及经筛选的教师动作摘要。未播完、失败或被打断的虚拟学生发言不进入两组转写。评分脚本不接受 0 分；机会缺失时要求记录原因，场次总分保持空值。

`generate-report` 调用冻结模型生成草稿，按事件原文回填引文，并核实学生播放完成和后续教师定稿事件；草稿不自动发放。`issue-report` 强制先有独立自评，要求实际发放文本保留已核实的学生与教师原句、回应解释及下一步建议，并保存原文、发放时间、输入摘要和冻结版本；报告长度须为 280–900 字符。其输出应直接写入获准研究存储。协调员负责把生成的两个评分 JSON 分开收齐后，再运行 `aggregate`。

`coordinator` 输出供协调员使用，接受两轮的原始场次字段、自评、原样已发放报告、修订目标、输入摘要和模型/量规/模板版本，并从事件计算生成、开始、完成以及动作样本分母。缺值保留为 null；跨轮状态枚举分别保留“无机会”“给了机会但教师跳过”“无法判断”。此文件含研究编号与组别，只能留在获准研究存储，绝不可提供给盲评者或参与者。

## 当前集成边界

本仓库现有课堂表是普通 `classrooms/classroom_events`；当前代码中没有交接报告声称的 `study packet/generate/issue` 命令，也没有正式实验场次、报告发放审计、参与者自评/修订目标持久化或研究导出表。此交付增加了封存输入、匿名盲评包与评分汇总的可测试服务/CLI；没有把普通课堂或 demo 账号自动认作正式实验场次，也没有实现真实参与者场次的管理 UI/持久化。正式采集前需由研究团队在获准存储配置场次清单，并现场核验两名评分者文件确实互相隔离。
