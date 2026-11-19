# 实验五：数据库与自适应学习

本次新增功能在独立 MySQL 实验库验收，不修改原 SQLite 数据库，不覆盖 `.env`，不迁移当前服务。平台新增功能默认关闭。

## 启动

需要 Docker Desktop（Linux 容器）、Python、Node.js，以及项目已有依赖。实验辅助脚本额外使用 `sqlparse`、`requests`。

```powershell
docker compose -f deploy/lab5.compose.yml up -d
# 等待容器健康后执行，首次建表与后续重复导入使用相同命令。
python scripts/lab5.py setup
./scripts/start-lab5.ps1
```

界面：`http://127.0.0.1:5195/adaptive`；后端：`http://127.0.0.1:5015`。
合成账号 `lab5_student` / `Lab5-demo-2026`，另有 `lab5_peer` 用于权限与并发验收。
MySQL：`127.0.0.1:13316`，库名、用户名均为 `link_lab5`，实验密码 `lab5-local-only`。这些固定凭据只用于本机隔离实验，不用于公网。

启动器检查 5015、5195 端口，冲突时停止，不结束已有服务。MySQL 只绑定回环地址；账户权限限定在实验库。运行后端使用独立的源码副本和锁目录，避免旧服务硬编码的证据目录和进程锁相互影响；修改后端代码后需重启实验后端刷新副本。

关闭实验可停止对应 5015/5195 服务并运行 `docker compose -f deploy/lab5.compose.yml stop`，保留独立实验数据卷。不要使用原项目数据库的初始化或清理命令。

## 数据与规则

SQL 位于 `backend/sql/lab5/`。`00_database.sql` 是可选 DBA 建库语句，Compose 已自动完成建库。`01_schema.sql` 包含当前 ORM 所需表与索引，`02_seed.sql` 仅插入合成账号、六项技能、36 道原创题目、18 张学习卡及六门技能研习课程，`03_verify.sql` 提供连接、表结构、题库和关联查询。

所有脚本显式使用 `link_lab5`。数据脚本使用主键/唯一键冲突时不覆盖记录的写法。SQL 的生成来源是当前 ORM，在 `python scripts/lab5.py export` 中以临时内存数据库生成，不读取原业务数据库。

九张新增表包括技能、技能材料关联、题目、测验、题目快照/作答、掌握度、学习路径、路径步骤、学习进度。核心业务字段关系化；选项、不可变题目快照和推荐依据使用 JSON。已有训练、课堂及 PracticePlan 继续复用。

掌握度按六维分别计算，最近三次该技能测验的平均分与最新有效课堂报告各占 50%；只有一类时仅用该类。无证据保持 NULL。训练必须是已完成报告、有效数值且引用同一课堂存在的证据事件；演示、合成报告、失败状态和证据不足数据不参与。版本更新重新计算，不累加旧报告。

阈值：低于 60 基础学习，60–79 专项巩固，80 及以上提升练习。它们是平台学习规则，不代表标准化教师评价。资源阅读与自行练习只增加进度；测验步骤由真实提交完成，关联课堂训练步骤由已有 PracticePlan 完成状态同步。资源停用后拒绝完成并在重新生成的路径中排除。

## 接口

后端 `ADAPTIVE_ENABLED=true` 才注册 `/api/adaptive`；前端 `VITE_ADAPTIVE_ENABLED=true` 才显示导航及路由。实验启动脚本设置这两个开关，原启动方式默认关闭。

| 方法与路径 | 用途 |
|---|---|
| GET `/api/adaptive/overview` | 六维掌握度、最近20份测验、最新路径 |
| POST `/api/adaptive/quizzes` | `request_key`（1–64字符），可选 `skill_id`；无技能时12题，有技能时6题 |
| GET `/api/adaptive/quizzes/{id}` | 读取自己测验；提交前隐藏答案、解析 |
| POST `/api/adaptive/quizzes/{id}/submit` | `answers` 为题目ID字符串到 A/B/C/D 的映射；必须完整作答 |
| POST `/api/adaptive/paths` | 根据当前证据与资源生成路径；相同证据返回同一条路径 |
| GET `/api/adaptive/paths/{id}` | 读取自己的路径及步骤 |
| POST `/api/adaptive/steps/{id}/complete` | 完成阅读或无课堂关联的自练；不能手动冒充完成测验/课堂训练 |

用户身份只来自 JWT。按用户行锁序列化学习事务，提交结果、作答和掌握度在一个事务内完成。相同请求编号不同测验范围、已提交后改答案返回409；无权访问按404处理。

## 验证与材料

```powershell
python -m pytest backend/tests/test_adaptive.py backend/tests/test_classroom_practice.py backend/tests/test_classroom_base.py -q
npm test --prefix frontend
$env:VITE_ADAPTIVE_ENABLED='true'
npm run build --prefix frontend
python scripts/verify_lab5.py
```

`verify_lab5.py` 仅操作实验库；并发验收会为 `lab5_peer` 新增合成测验记录。原始数据库文件与 `.env` 在 setup 前后进行 SHA-256 核对，验收时再次核对；日志不包含原有凭据。

提交目录为 `output/lab5/submission/`，包含 Word/PDF、SQL、截图、ER 图、完整数据字典及验收记录。数据库截图来自实际查询结果的只读展示页，不伪装为 Navicat 或其他管理软件。组号、姓名、学号和实际分工留给成员补充。

已完成的浏览器验收使用合成账号，未进行真实摄像头、麦克风、真人授课或付费模型调用，不将自动化验证描述为真实教学效果评价。

CodeGraph 已初始化并在 `.codex/config.toml` 配置本项目 MCP；本轮通过 CLI 查询索引。MCP 工具需在后续客户端会话加载配置后可用。

本次验收后，Docker Desktop 的管理接口出现 `stopping` 状态及超时；已建立的实验 MySQL 连接仍正常，未为恢复管理接口而重启其他容器。后续重新启动实验容器前，需先确认 Docker Desktop 引擎已恢复运行。此状态不计作 SQL 执行成功的证据。
