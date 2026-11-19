/* Rebuild the deliverable from captured evidence, never fabricate screenshots. */
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const root = path.resolve(__dirname, '..');
const out = path.join(root, 'output/lab5');
const load = createRequire(path.join(out, 'tooling/package.json'));
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType, Footer, PageNumber, PageBreak } = load('docx');
const dictionary = JSON.parse(fs.readFileSync(path.join(out,'data-dictionary.json'),'utf8'));
const checks = JSON.parse(fs.readFileSync(path.join(out,'mysql-acceptance.json'),'utf8'));
const submission = path.join(out,'submission');
fs.mkdirSync(submission,{recursive:true});
const p = (text,options={}) => new Paragraph({spacing:{after:140,line:320},children:[new TextRun(text)],...options});
const heading = (text,level=1) => new Paragraph({text,heading:level===1?HeadingLevel.HEADING_1:HeadingLevel.HEADING_2});
const page = () => new Paragraph({pageBreakBefore:true,keepNext:true,spacing:{before:0,after:0,line:20},children:[new TextRun({text:'',size:2})]});
const border = {style:BorderStyle.SINGLE,size:4,color:'D7DFEA'};
function table(headers,rows,widths) {
 return new Table({width:{size:9906,type:WidthType.DXA},columnWidths:widths,rows:[headers,...rows].map((row,index)=>new TableRow({tableHeader:index===0,cantSplit:true,children:row.map((value,i)=>new TableCell({width:{size:widths[i],type:WidthType.DXA},borders:{top:border,bottom:border,left:border,right:border},margins:{top:90,bottom:90,left:110,right:110},shading:{type:ShadingType.CLEAR,fill:index===0?'E8EFF8':'FFFFFF'},children:[new Paragraph({spacing:{after:30,line:260},children:[new TextRun({text:String(value),bold:index===0,size:19})]})]}))}))});
}
function picture(file,caption,maxHeight=420) {
 const data=fs.readFileSync(path.join(out,file));
 const w=data.readUInt32BE(16),h=data.readUInt32BE(20),scale=Math.min(640/w,maxHeight/h);
 return [new Paragraph({alignment:AlignmentType.CENTER,children:[new ImageRun({type:'png',data,transformation:{width:Math.round(w*scale),height:Math.round(h*scale)},altText:{title:caption,name:caption,description:caption}})]}),p(caption,{alignment:AlignmentType.CENTER})];
}
const children = [
 p('数据库实验报告',{spacing:{before:400,after:200},alignment:AlignmentType.CENTER}),
 p('实验五  后端数据库设计',{alignment:AlignmentType.CENTER,children:[new TextRun({text:'实验五  后端数据库设计',bold:true,size:40,color:'203454'})]}),
 p('临客 LINK 智能学习平台',{alignment:AlignmentType.CENTER,children:[new TextRun({text:'临客 LINK 智能学习平台',size:30,color:'355E98'})]}),
 p('实验日期：2026年11月5日    实验学时：2学时',{alignment:AlignmentType.CENTER}),
 heading('（一）小组分工说明'),
 p('组号：［待补充］    班级：［待补充］'),
 table(['成员姓名','学号','实际分工'],[['［待补充］','［待补充］','［按实际参与情况填写］'],['［待补充］','［待补充］','［按实际参与情况填写］']],[2200,2500,5206]),
 p('说明：成员信息与实际分工由小组补充；不预设或编造个人贡献。技术内容、SQL 与截图已完成。'),
 heading('实验目标与需求描述',2),
 p('临客 LINK 面向师范生与职前教师，提供微格教学训练、课堂反馈、课程资源与成长记录。本实验在独立 MySQL 数据库中实现自适应学习：记录测验与训练证据，识别薄弱技能，生成可解释的学习路径，并持久化阅读、练习和复测进度。'),
 p('数据范围包括用户、课程、资源、训练与报告，以及技能目录、分层题库、测验作答、掌握度、学习路径及进度。六项技能为表达清晰度、教学节奏、互动设计、教态与站位、提问质量、课堂结构。'),
 p('实验环境：MySQL 8.4.11 / InnoDB / utf8mb4；Flask + SQLAlchemy 后端；Vue 3 前端。MySQL 端口13316，数据库link_lab5；前后端端口5015/5195。使用独立容器和数据卷，原 SQLite 数据库与 .env 不作修改。'),
 page(),heading('数据库需求与关系设计'),
 table(['需求','设计与约束'],[
 ['用户隔离','用户ID关联测验、掌握度与路径；接口从JWT取得身份，拒绝跨用户访问。'],
 ['题库与诊断','36道原创单选题，六技能各六题，三级难度；初次诊断每技能两题，专项复测六题。'],
 ['结果可追溯','作答表保存出题时的题干、选项、答案与解析快照；提交前隐藏答案与解析。'],
 ['训练证据','复用已有课堂及训练计划；有效报告必须引用同课堂真实存在的事件；合成和演示评分不计入。'],
 ['掌握度','每用户每技能一条记录；测验取最近三次均值，训练取最新有效报告；保留来源和报告版本。'],
 ['推荐路径','待诊断优先，之后按掌握度升序；关联技能、资源、训练计划，存储推荐理由与证据快照。'],
 ['学习进度','每步骤最多一条完成记录；阅读和自练只改变进度，不直接提高掌握度。'],
 ['数据一致性','外键、唯一约束、范围检查、事务及按用户行锁；重复提交与并发请求不重复计分。'],
 ],[2300,7606]),
 p('实体关系图展示九张新增自适应学习表与复用核心实体。箭头由父表指向子表，表示一对多；具体外键列在数据字典和 SQL 中列明。'),
 page(),heading('自适应学习实体关系图'),...picture('11-er-diagram.png','图1  自适应学习核心实体关系图',780),
 page(),heading('（二）数据库脚本执行完成截图'),
 p('安装步骤：启动独立 MySQL 8.4 容器，建立 link_lab5 数据库及限权实验账户；按顺序执行建表、演示数据与验证脚本。所有 SQL 显式使用实验库，原库不执行任何初始化或迁移。'),
 table(['脚本','用途'],[['00_database.sql','可选 DBA 建库；Compose 已自动建库。'],['01_schema.sql','依据当前 ORM 导出的24张表及索引，包含9张新增学习表。'],['02_seed.sql','合成账号、6项技能、6门研习课程、18张学习卡和36道题目；重复导入不覆盖。'],['03_verify.sql','版本、库名、表清单、表结构、题库分布和课程资源关联查询。']],[2800,7106]),
 p('执行命令：python scripts/lab5.py setup。脚本检查固定实验库目标，读取独立 SQL，并记录原数据库文件及 .env 的 SHA-256。重复执行后未覆盖已有数据。'),
 ...picture('08-mysql-install-execution.png','图2  MySQL版本、连接身份及脚本实际执行记录',440),
 p('截图说明：数据库证据通过只读网页展示实际 MySQL 查询结果与执行日志；不是数据库管理软件截图，也不是模拟终端。原始日志与查询结果 JSON 随提交包提供。'),
 page(),heading('SQL 设计要点'),
 p('数据库采用关系型设计：用户、课程、资源等基础实体独立建表；题目通过技能外键归类；测验和作答拆分，避免重复保存整次作答结果；路径与步骤拆分，支持多个步骤及独立进度。'),
 table(['约束或索引','作用'],[
 ['adaptive_quizzes(user_id, request_key) UNIQUE','同一用户的同一创建请求只产生一份测验。'],
 ['adaptive_answers(quiz_id, question_id) UNIQUE','同一测验中同一题只出现一次。'],
 ['adaptive_mastery(user_id, skill_id) PK','每位用户的每项技能只有一条当前掌握度。'],
 ['adaptive_paths(user_id, fingerprint) UNIQUE','相同证据与资源状态只生成一条路径。'],
 ['adaptive_progress(step_id) UNIQUE','重复完成操作不会重复新增进度。'],
 ['level BETWEEN 1 AND 3 / score范围','限定题目难度与掌握度的合理取值。'],
 ['用户、技能、路径、测验等外键索引','支持按用户、技能和父记录查询，同时维护引用完整性。'],
 ],[5100,4806]),
 p('选择 JSON 的边界：选项、出题快照、推荐解释及证据列表使用 JSON；用户、技能、关联目标、状态和时间仍使用结构化列。掌握度是可重新计算的结果表，用证据快照保留计算口径。'),
 p('事务边界：提交答案、判分、更新掌握度和完成测验步骤在同一事务中提交；校验失败回滚。MySQL 对用户行加锁，避免同一用户并发创建和提交造成重复结果。'),
 heading('自适应规则',2),
 p('最近三次该技能测验平均分与最新有效训练分各占50%；仅有一类证据时采用该类；无证据保持NULL并显示“待诊断”。训练报告修订后以新版本重新计算，不将旧版本重复累加。'),
 p('低于60分推荐基础学习，60–79分专项巩固，80分及以上提升练习；这些阈值是平台学习规则，不是标准化教师评价。每一步展示推荐理由。阅读和自行练习完成不会直接增加掌握度。'),
 page(),heading('（三）数据库截图'),
 ...picture('09-mysql-tables.png','图3  实验数据库表清单',500),
 p('实验数据库包含24张表：15张复用业务表与9张新增自适应学习表。新增部分通过外键连接既有用户、课程、资源及课堂训练计划，不复制建立另一套用户或训练体系。'),
 page(),heading('关键表结构与数据验证'),
 ...picture('10-mysql-structure.png','图4  作答表结构及关联数据的实际查询结果',490),
 p('表结构、外键、唯一约束、范围检查、中文数据与事务回滚已在 MySQL 实库验证。数据字典从 ORM 导出，并逐表与 MySQL 实际列名核对。合成实验账号与真实用户数据分离。'),
 page(),heading('平台功能验证：诊断与路径'),
 ...picture('04-learning-path.png','图5  合成账号完成诊断后生成的学习路径',420),
 p('登录后进入“自适应学习”，可查看六维掌握度、测验与训练分来源、推荐顺序及历史记录。截图中的分数来自自动化操作提交的合成测验，不代表真实师范生水平。'),
 ...picture('03-quiz-result.png','图6  服务端判分后的答案与解析',330),
 page(),heading('平台功能验证：学习与复测'),
 ...picture('05-resource-completed.png','图7  阅读学习卡并保存完成进度',380),
 ...picture('06-retest-path.png','图8  专项复测后更新掌握度与学习路径',380),
 p('已验证刷新后读取历史结果与完成记录；移动端390px宽度能够浏览技能概览和学习路径。真实课堂训练入口仍限定平台支持的“分数的初步认识”。'),
 page(),heading('（四）安装与设计过程中存在的问题'),
 table(['实际问题','解决方式'],[
 ['已有数据库与实验环境不同','原环境使用SQLite，实验使用独立MySQL；不覆盖原配置，不运行原初始化脚本。'],
 ['仓库旧SQL缺少当前ORM字段','从当前ORM导出独立完整DDL，并逐表核对实际数据库列。'],
 ['重复执行单独创建索引报错','将索引并入CREATE TABLE IF NOT EXISTS语句，重复执行脚本通过。'],
 ['旧服务有硬编码目录与进程锁','实验后端使用源码副本、独立运行目录和锁目录，隔离原服务文件。'],
 ['浏览器默认Chrome启动失败','改用已安装的Playwright Chromium，完成真实浏览器操作和截图。'],
 ['深色界面文字对比度不足','检查实际截图后调整自适应页面颜色，并验证移动端显示。'],
 ['Docker管理接口后续停止中并超时','原实验MySQL连接仍可用；未重启其他容器，后续重启实验前需确认Docker引擎恢复。'],
 ['CodeGraph命令不在当前PATH','安装包并以npx调用；建立本地索引和项目MCP配置。'],
 ],[3000,6906]),
 heading('验收结果与边界',2),
 table(['验收项目','结果'],[
 ['后端关联测试','11项通过：自适应学习、原有训练计划及基础服务。'],
 ['前端回归','206项通过；生产构建成功（有已有大文件分块提示）。'],
 ['MySQL实库验收',checks.length+'项通过，包含并发幂等、外键、唯一约束、回滚、中文读写与原文件哈希保护。'],
 ['浏览器闭环','登录→诊断→解析→路径→阅读完成→自练记录→专项复测→更新路径；刷新后保持记录。'],
 ['未进行的验收','真人授课、摄像头/麦克风、付费模型调用、教学成效研究与生产部署。'],
 ],[2800,7106]),
 p('实验结论：在保留原数据库与原配置的前提下，完成独立 MySQL 数据库设计与执行，打通测验、掌握度、推荐路径及进度闭环。报告中的执行结果均有对应脚本、日志或截图；提交前只需补充真实组号、成员信息和实际分工。'),
 page(),heading('附录：新增表数据字典'),
 p('完整24表数据字典见同目录“数据字典.md”及 data-dictionary.json；下表重点列出9张新增表。PK为主键，FK为外键，必填表示NOT NULL。'),
];
for(const [name, cols] of Object.entries(dictionary).filter(([name])=>name.startsWith('adaptive_'))) {
 children.push(heading(name,2));
 children.push(table(['字段','类型','约束/关联'],cols.map(c=>[c.name,c.type,[c.primary_key?'PK':'',!c.nullable?'必填':'可空',...c.references.map(r=>'FK→'+r)].filter(Boolean).join('；')]),[2600,2300,5006]));
 children.push(p(''));
}
const doc = new Document({creator:'临客 LINK',title:'实验五 后端数据库设计',description:'独立数据库实验与自适应学习验收报告',
 styles:{default:{document:{run:{font:'Microsoft YaHei',size:22,color:'26374D'}}},paragraphStyles:[
  {id:'Heading1',name:'Heading 1',basedOn:'Normal',next:'Normal',quickFormat:true,run:{font:'Microsoft YaHei',bold:true,size:30,color:'203454'},paragraph:{spacing:{before:240,after:180},keepNext:true,outlineLevel:0}},
  {id:'Heading2',name:'Heading 2',basedOn:'Normal',next:'Normal',quickFormat:true,run:{font:'Microsoft YaHei',bold:true,size:25,color:'355E98'},paragraph:{spacing:{before:220,after:140},keepNext:true,outlineLevel:1}},
 ]},sections:[{properties:{page:{size:{width:11906,height:16838},margin:{top:1000,bottom:1000,left:1000,right:1000}}},
 footers:{default:new Footer({children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:'临客 LINK · 实验五    ',size:18,color:'64748B'}),new TextRun({children:[PageNumber.CURRENT],size:18})]})]})},children}]});
Packer.toBuffer(doc).then(buffer=>{
 fs.writeFileSync(path.join(submission,'实验五-第X组-临客LINK.docx'),buffer);
 const md=Object.entries(dictionary).map(([name,cols])=>'## '+name+'\n\n| 字段 | 类型 | 可空 | 主键 | 外键 |\n|---|---|---|---|---|\n'+cols.map(c=>`| ${c.name} | ${c.type} | ${c.nullable?'是':'否'} | ${c.primary_key?'是':'否'} | ${c.references.join(', ')} |`).join('\n')).join('\n\n');
 fs.writeFileSync(path.join(submission,'数据字典.md'),'# 临客 LINK 实验数据库完整数据字典\n\n'+md,'utf8');
 for(const folder of ['SQL','截图','验收记录']) fs.mkdirSync(path.join(submission,folder),{recursive:true});
 for(const file of fs.readdirSync(path.join(root,'backend/sql/lab5'))) fs.copyFileSync(path.join(root,'backend/sql/lab5',file),path.join(submission,'SQL',file));
 for(const file of fs.readdirSync(out).filter(f=>/^\d\d-.*\.png$/.test(f))) fs.copyFileSync(path.join(out,file),path.join(submission,'截图',file));
 for(const file of ['mysql-acceptance.json','mysql-evidence.json','data-dictionary.json','sql-execution.txt','backend-tests.txt','frontend-tests.txt','build.log','original-files-before.json','original-files-after.json','browser-acceptance.md']) fs.copyFileSync(path.join(out,file),path.join(submission,'验收记录',file));
 fs.copyFileSync(path.join(root,'docs/lab5-delivery.md'),path.join(submission,'运行与验收说明.md'));
 fs.copyFileSync(path.join(out,'er-diagram.svg'),path.join(submission,'ER图.svg'));
 fs.copyFileSync(path.join(out,'er-diagram.dot'),path.join(submission,'ER图源文件.dot'));
 console.log('Report and submission package built:',submission);
});
