const fs=require('fs'),path=require('path'),{createRequire}=require('module');
const out=path.resolve(__dirname,'../output/lab5');
const load=createRequire(path.join(out,'tooling/package.json'));
const dict=JSON.parse(fs.readFileSync(path.join(out,'data-dictionary.json'),'utf8'));
const labels={users:'用户',courses:'课程',resources:'资源',classroom_practice_plans:'课堂训练计划',adaptive_skills:'技能目录',adaptive_skill_materials:'分层学习材料',adaptive_questions:'题库',adaptive_quizzes:'测验',adaptive_answers:'题目快照与作答',adaptive_mastery:'技能掌握度',adaptive_paths:'学习路径',adaptive_path_steps:'路径步骤',adaptive_progress:'学习进度'};
const names=new Set(Object.keys(labels));
let dot='digraph ER { graph [rankdir=LR, bgcolor="white", nodesep=0.3, ranksep=0.7, pad=0.3, splines=polyline]; node [shape=record, style="filled", fillcolor="#EDF3FC", color="#7992B3", fontname="Microsoft YaHei", fontsize=13, margin="0.16,0.12"]; edge [color="#6F829C", arrowsize=0.6, fontname="Microsoft YaHei", fontsize=9];\n';
for(const name of names){
 const pk=dict[name].filter(c=>c.primary_key).map(c=>c.name).join(', ');
 dot+=`"${name}" [label="${labels[name]}|${name}|PK: ${pk}", fillcolor="${name.startsWith('adaptive_')?'#EDF3FC':'#F1F4F3'}"];\n`;
}
for(const name of names) for(const col of dict[name]) for(const fk of col.references){
 const parent=fk.split('.')[0];
 if(names.has(parent))dot+=`"${parent}" -> "${name}" [label="1:N", tooltip="${col.name} references ${fk}"];\n`;
}
dot+='}';
fs.writeFileSync(path.join(out,'er-diagram.dot'),dot);
load('@viz-js/viz').instance().then(viz=>{fs.writeFileSync(path.join(out,'er-diagram.svg'),viz.renderString(dot,{format:'svg'}));console.log('ER diagram rendered from actual foreign keys.');});
