-- Synthetic accounts and original learning cards only.

USE link_lab5;

SET NAMES utf8mb4;

START TRANSACTION;

INSERT INTO `adaptive_skills` (`id`, `name`, `description`, `ordinal`) VALUES ('clarity', '表达清晰度', '用明确指令与可检验的例子解释概念。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skills` (`id`, `name`, `description`, `ordinal`) VALUES ('pace', '教学节奏', '为思考、回应和课堂回收分配时间。', 2) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skills` (`id`, `name`, `description`, `ordinal`) VALUES ('interaction', '互动设计', '让回应、反馈和课堂回收形成闭环。', 3) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skills` (`id`, `name`, `description`, `ordinal`) VALUES ('posture', '教态与站位', '让视线、站位和动作支持信息传递。', 4) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skills` (`id`, `name`, `description`, `ordinal`) VALUES ('questioning', '提问质量', '用具体问题、追问和证据促进思考。', 5) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skills` (`id`, `name`, `description`, `ordinal`) VALUES ('structure', '课堂结构', '让目标、活动、检查和小结相互衔接。', 6) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `courses` (`id`, `title`, `category`, `description`, `lesson_count`, `cover_url`, `stage`, `outline`, `source`, `source_url`, `is_active`, `created_at`) VALUES (96001, '表达清晰度研习（实验）', '表达清晰度', '用明确指令与可检验的例子解释概念。', 3, NULL, NULL, NULL, NULL, NULL, 1, '2026-11-05 02:23:05.764468') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `courses` (`id`, `title`, `category`, `description`, `lesson_count`, `cover_url`, `stage`, `outline`, `source`, `source_url`, `is_active`, `created_at`) VALUES (96002, '教学节奏研习（实验）', '教学节奏', '为思考、回应和课堂回收分配时间。', 3, NULL, NULL, NULL, NULL, NULL, 1, '2026-11-05 02:23:05.773838') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `courses` (`id`, `title`, `category`, `description`, `lesson_count`, `cover_url`, `stage`, `outline`, `source`, `source_url`, `is_active`, `created_at`) VALUES (96003, '互动设计研习（实验）', '互动设计', '让回应、反馈和课堂回收形成闭环。', 3, NULL, NULL, NULL, NULL, NULL, 1, '2026-11-05 02:23:05.779316') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `courses` (`id`, `title`, `category`, `description`, `lesson_count`, `cover_url`, `stage`, `outline`, `source`, `source_url`, `is_active`, `created_at`) VALUES (96004, '教态与站位研习（实验）', '教态与站位', '让视线、站位和动作支持信息传递。', 3, NULL, NULL, NULL, NULL, NULL, 1, '2026-11-05 02:23:05.785530') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `courses` (`id`, `title`, `category`, `description`, `lesson_count`, `cover_url`, `stage`, `outline`, `source`, `source_url`, `is_active`, `created_at`) VALUES (96005, '提问质量研习（实验）', '提问质量', '用具体问题、追问和证据促进思考。', 3, NULL, NULL, NULL, NULL, NULL, 1, '2026-11-05 02:23:05.791375') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `courses` (`id`, `title`, `category`, `description`, `lesson_count`, `cover_url`, `stage`, `outline`, `source`, `source_url`, `is_active`, `created_at`) VALUES (96006, '课堂结构研习（实验）', '课堂结构', '让目标、活动、检查和小结相互衔接。', 3, NULL, NULL, NULL, NULL, NULL, 1, '2026-11-05 02:23:05.797313') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `resources` (`id`, `title`, `category`, `description`, `file_url`, `is_active`, `created_at`) VALUES (97011, '表达清晰度·第1级学习卡', '表达清晰度', '用明确指令与可检验的例子解释概念。', NULL, 1, '2026-11-05 02:23:05.765886') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `resources` (`id`, `title`, `category`, `description`, `file_url`, `is_active`, `created_at`) VALUES (97012, '表达清晰度·第2级学习卡', '表达清晰度', '用明确指令与可检验的例子解释概念。', NULL, 1, '2026-11-05 02:23:05.768417') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `resources` (`id`, `title`, `category`, `description`, `file_url`, `is_active`, `created_at`) VALUES (97013, '表达清晰度·第3级学习卡', '表达清晰度', '用明确指令与可检验的例子解释概念。', NULL, 1, '2026-11-05 02:23:05.769197') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `resources` (`id`, `title`, `category`, `description`, `file_url`, `is_active`, `created_at`) VALUES (97021, '教学节奏·第1级学习卡', '教学节奏', '为思考、回应和课堂回收分配时间。', NULL, 1, '2026-11-05 02:23:05.774189') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `resources` (`id`, `title`, `category`, `description`, `file_url`, `is_active`, `created_at`) VALUES (97022, '教学节奏·第2级学习卡', '教学节奏', '为思考、回应和课堂回收分配时间。', NULL, 1, '2026-11-05 02:23:05.774911') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `resources` (`id`, `title`, `category`, `description`, `file_url`, `is_active`, `created_at`) VALUES (97023, '教学节奏·第3级学习卡', '教学节奏', '为思考、回应和课堂回收分配时间。', NULL, 1, '2026-11-05 02:23:05.775676') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `resources` (`id`, `title`, `category`, `description`, `file_url`, `is_active`, `created_at`) VALUES (97031, '互动设计·第1级学习卡', '互动设计', '让回应、反馈和课堂回收形成闭环。', NULL, 1, '2026-11-05 02:23:05.779710') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `resources` (`id`, `title`, `category`, `description`, `file_url`, `is_active`, `created_at`) VALUES (97032, '互动设计·第2级学习卡', '互动设计', '让回应、反馈和课堂回收形成闭环。', NULL, 1, '2026-11-05 02:23:05.780560') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `resources` (`id`, `title`, `category`, `description`, `file_url`, `is_active`, `created_at`) VALUES (97033, '互动设计·第3级学习卡', '互动设计', '让回应、反馈和课堂回收形成闭环。', NULL, 1, '2026-11-05 02:23:05.781522') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `resources` (`id`, `title`, `category`, `description`, `file_url`, `is_active`, `created_at`) VALUES (97041, '教态与站位·第1级学习卡', '教态与站位', '让视线、站位和动作支持信息传递。', NULL, 1, '2026-11-05 02:23:05.786035') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `resources` (`id`, `title`, `category`, `description`, `file_url`, `is_active`, `created_at`) VALUES (97042, '教态与站位·第2级学习卡', '教态与站位', '让视线、站位和动作支持信息传递。', NULL, 1, '2026-11-05 02:23:05.786911') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `resources` (`id`, `title`, `category`, `description`, `file_url`, `is_active`, `created_at`) VALUES (97043, '教态与站位·第3级学习卡', '教态与站位', '让视线、站位和动作支持信息传递。', NULL, 1, '2026-11-05 02:23:05.787719') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `resources` (`id`, `title`, `category`, `description`, `file_url`, `is_active`, `created_at`) VALUES (97051, '提问质量·第1级学习卡', '提问质量', '用具体问题、追问和证据促进思考。', NULL, 1, '2026-11-05 02:23:05.791734') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `resources` (`id`, `title`, `category`, `description`, `file_url`, `is_active`, `created_at`) VALUES (97052, '提问质量·第2级学习卡', '提问质量', '用具体问题、追问和证据促进思考。', NULL, 1, '2026-11-05 02:23:05.792527') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `resources` (`id`, `title`, `category`, `description`, `file_url`, `is_active`, `created_at`) VALUES (97053, '提问质量·第3级学习卡', '提问质量', '用具体问题、追问和证据促进思考。', NULL, 1, '2026-11-05 02:23:05.793328') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `resources` (`id`, `title`, `category`, `description`, `file_url`, `is_active`, `created_at`) VALUES (97061, '课堂结构·第1级学习卡', '课堂结构', '让目标、活动、检查和小结相互衔接。', NULL, 1, '2026-11-05 02:23:05.797782') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `resources` (`id`, `title`, `category`, `description`, `file_url`, `is_active`, `created_at`) VALUES (97062, '课堂结构·第2级学习卡', '课堂结构', '让目标、活动、检查和小结相互衔接。', NULL, 1, '2026-11-05 02:23:05.798699') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `resources` (`id`, `title`, `category`, `description`, `file_url`, `is_active`, `created_at`) VALUES (97063, '课堂结构·第3级学习卡', '课堂结构', '让目标、活动、检查和小结相互衔接。', NULL, 1, '2026-11-05 02:23:05.799487') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `users` (`id`, `account`, `password_hash`, `name`, `role`, `avatar_url`, `bio`, `school`, `major`, `grade`, `level`, `xp`, `badges_json`, `created_at`) VALUES (95001, 'lab5_student', 'scrypt:32768:8:1$LE12QlxqXnAuIPGN$8c29215647ffbccd16287bddafeacae0f6daf23b7f41480395e8cd8effed10b984172ec84d674d875a6f57c29f306a9cf1bcb89f53d300015672cd513a856245', '实验学习者（合成）', 'student', NULL, NULL, NULL, NULL, NULL, 1, 0, NULL, '2026-11-05 02:23:05.681078') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `users` (`id`, `account`, `password_hash`, `name`, `role`, `avatar_url`, `bio`, `school`, `major`, `grade`, `level`, `xp`, `badges_json`, `created_at`) VALUES (95002, 'lab5_peer', 'scrypt:32768:8:1$bvq2RmZgdjsXbA77$a7df71bbfd926a92cbe7335308c086977a19731aed79bbdad301a1fa409380c4841f447cc9146b302b64238d7fc7dcc8e7e59d61ce8c4a5fa315b77dab2efbe5', '实验学习者（合成）', 'student', NULL, NULL, NULL, NULL, NULL, 1, 0, NULL, '2026-11-05 02:23:05.761756') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (1, 'clarity-1', 'clarity', 1, '介绍分数时，哪种说法最明确？', '{"A": "把一个整体平均分成四份，其中一份是四分之一", "B": "分一下就是分数", "C": "越小的数越大", "D": "先背答案就可以"}', 'A', '先交代整体、平均分与所取份数，概念才完整。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (2, 'clarity-2', 'clarity', 1, '布置小组任务时应先说明什么？', '{"A": "与任务无关的故事", "B": "任务、产出和用时", "C": "教师个人喜好", "D": "下周全部安排"}', 'B', '清楚说明做什么、交什么、用多久，可以降低理解负担。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (3, 'clarity-3', 'clarity', 2, '学生混淆整体与部分，最合适的解释是？', '{"A": "让学生直接背结论", "B": "立即更换学习主题", "C": "用同一张纸标出整体，再标出其中一份", "D": "只提高音量重复术语"}', 'C', '保持整体不变，用可见的部分解释关系。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (4, 'clarity-4', 'clarity', 2, '如何检查学生是否理解“平均分”？', '{"A": "问“懂了吧”后继续讲", "B": "只询问是否喜欢课程", "C": "看学生是否抄完标题", "D": "让学生判断两组分法并说明理由"}', 'D', '辨别并解释比简单附和更能体现理解。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (5, 'clarity-5', 'clarity', 3, '解释分数大小时学生仍困惑，应如何调整？', '{"A": "保持整体相同，用图示比较并请学生复述", "B": "同时增加三种新术语", "C": "只延长独白时间", "D": "把困惑归为不认真"}', 'A', '控制比较条件，结合多种表征并检查理解。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (6, 'clarity-6', 'clarity', 3, '学生能背定义但解释错误，优先做什么？', '{"A": "删除所有示例", "B": "让其用反例区分定义条件", "C": "认定已完全掌握", "D": "只加快教学进度"}', 'B', '用反例检验必要条件，能揭示机械记忆背后的误解。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (7, 'pace-1', 'pace', 1, '提出问题后最合适的行为是？', '{"A": "根据问题难度留出思考时间", "B": "立即自己回答", "C": "马上换下一个问题", "D": "持续打断学生"}', 'A', '留出思考空间才能得到学生的真实回答。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (8, 'pace-2', 'pace', 1, '安排十分钟微格课，应优先考虑什么？', '{"A": "按课件页数平均切分", "B": "围绕目标分配环节并预留小结", "C": "把全部时间用于开场", "D": "忽略练习时间"}', 'B', '时间分配应服务学习目标而非材料数量。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (9, 'pace-3', 'pace', 2, '小组讨论超时但仍未聚焦，应如何处理？', '{"A": "直接否定所有讨论", "B": "不作回收立即下课", "C": "提示剩余时间和核心问题后组织回收", "D": "无限延长"}', 'C', '明确边界和目标，有助于有效结束讨论。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (10, 'pace-4', 'pace', 2, '多数学生已完成而少数仍在思考，应如何安排？', '{"A": "让所有人无目的等待", "B": "立刻收走所有材料", "C": "公开批评未完成者", "D": "给已完成者拓展任务并支持仍有困难者"}', 'D', '分层安排兼顾学习进度与参与机会。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (11, 'pace-5', 'pace', 3, '观察到连续讲授后学生回应减少，应优先调整？', '{"A": "插入短判断任务并依据反馈调整讲授", "B": "增加单向讲授密度", "C": "删除互动环节", "D": "仅提高语速"}', 'A', '短反馈环节帮助判断是否需要放慢或转换活动。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (12, 'pace-6', 'pace', 3, '评价节奏是否合理，最可靠的依据是？', '{"A": "只凭教师自我感觉", "B": "结合目标达成、等待时间与学生回应", "C": "只看是否准时讲完", "D": "只数幻灯片页数"}', 'B', '节奏质量需要学习证据支持，不能仅凭时长。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (13, 'interaction-1', 'interaction', 1, '学生回答后，教师应怎样反馈？', '{"A": "针对回答内容指出依据或需要修正之处", "B": "无论回答都只说很好", "C": "完全忽视回答", "D": "只评论声音大小"}', 'A', '具体反馈能帮助学生理解正确与错误的原因。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (14, 'interaction-2', 'interaction', 1, '小组讨论结束后应做什么？', '{"A": "取消所有反馈", "B": "组织分享并归纳共同结论", "C": "直接切换无关话题", "D": "只表扬最快小组"}', 'B', '全班回收使小组成果成为共同学习资源。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (15, 'interaction-3', 'interaction', 2, '只有少数学生发言时，怎样扩大参与？', '{"A": "把沉默等同于不懂", "B": "让教师包办回答", "C": "先独立思考，再同伴交流，最后分享", "D": "始终只请同一名学生"}', 'C', '分阶段交流降低参与门槛并增加准备时间。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (16, 'interaction-4', 'interaction', 2, '面对学生的错误回答，合适的互动是？', '{"A": "立刻嘲笑", "B": "不给解释机会直接否定", "C": "假装答案正确", "D": "追问其思路并用材料共同验证"}', 'D', '尊重思路并验证证据能够促进概念修正。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (17, 'interaction-5', 'interaction', 3, '两组观点相反，如何促进有效讨论？', '{"A": "让双方展示证据并比较适用条件", "B": "只按人数决定对错", "C": "由声音最大者决定", "D": "立即跳过争议"}', 'A', '讨论应围绕证据和条件，而不是人气。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (18, 'interaction-6', 'interaction', 3, '如何判断互动是否促进学习？', '{"A": "只统计教师提问数量", "B": "比较互动前后的解释与理解变化", "C": "只统计举手次数", "D": "只观察课堂是否热闹"}', 'B', '互动的价值应落到理解变化与学习成果。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (19, 'posture-1', 'posture', 1, '讲解时应如何面向学生？', '{"A": "尽量面向学生并保持自然交流", "B": "长时间背对学生", "C": "始终低头读稿", "D": "持续遮挡展示材料"}', 'A', '面向学生有利于建立交流并观察反馈。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (20, 'posture-2', 'posture', 1, '板书时站位的基本原则是什么？', '{"A": "全程背对学生讲话", "B": "避免遮挡关键内容并适时转向学生", "C": "站在内容正前方不动", "D": "尽量挡住学生视线"}', 'B', '站位应保障学生能看清内容和教师表达。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (21, 'posture-3', 'posture', 2, '巡视小组时，怎样做更有效？', '{"A": "不断打断所有小组", "B": "只检查桌面整齐", "C": "观察任务进展并提供针对性支持", "D": "只在讲台上不观察"}', 'C', '巡视的目标是获取学习证据并提供支持。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (22, 'posture-4', 'posture', 2, '演示教具时怎样保证可见性？', '{"A": "只朝第一排展示", "B": "快速晃动教具", "C": "把教具放在身体后方", "D": "确认不同位置学生都能看清再演示"}', 'D', '先确保可见性，再进行关键步骤演示。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (23, 'posture-5', 'posture', 3, '录像中无法看清教师全身，评价站位应如何处理？', '{"A": "明确证据边界，不推断不可见动作", "B": "直接给最低分", "C": "凭语气推断全部动作", "D": "复制其他教师的评价"}', 'A', '观测不足时应拒绝无依据的判断。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (24, 'posture-6', 'posture', 3, '教学动作频繁但学生分心，优先改进什么？', '{"A": "仅追求动作幅度", "B": "减少无关动作，让手势对应关键内容", "C": "增加随机走动", "D": "完全禁止自然动作"}', 'B', '动作应帮助注意聚焦，而不是制造额外干扰。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (25, 'questioning-1', 'questioning', 1, '哪种提问更能检查理解？', '{"A": "为什么这幅图表示四分之一？", "B": "大家都懂了吧？", "C": "是不是很简单？", "D": "你们喜欢我吗？"}', 'A', '要求解释依据的问题能呈现学生的思考。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (26, 'questioning-2', 'questioning', 1, '设计一个课堂核心问题时应注意什么？', '{"A": "只追求难倒学生", "B": "与目标一致且表述清楚", "C": "越长越复杂越好", "D": "同时包含许多无关要求"}', 'B', '问题应明确指向学习目标。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (27, 'questioning-3', 'questioning', 2, '学生说出正确答案后可以怎样追问？', '{"A": "重复公布答案即可", "B": "改问无关私人信息", "C": "请说明理由或举一个例子", "D": "立刻终止其表达"}', 'C', '追问理由能区分理解与猜测。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (28, 'questioning-4', 'questioning', 2, '学生回答偏离问题，应怎样追问？', '{"A": "连续抛出多个新问题", "B": "不听完就宣布失败", "C": "直接换到完全不同主题", "D": "重述核心条件并请其联系材料解释"}', 'D', '聚焦条件有助于学生调整推理。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (29, 'questioning-5', 'questioning', 3, '希望学生迁移“平均分”，哪种问题最好？', '{"A": "换一种材料后，判断是否平均分并说明依据", "B": "重复同一道题的答案", "C": "只背页码", "D": "只问是否见过图片"}', 'A', '变化情境并保持概念要求，可以检验迁移。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (30, 'questioning-6', 'questioning', 3, '怎样评价一个问题是否有价值？', '{"A": "只看教师是否满意", "B": "检查其是否引出与目标相关的推理证据", "C": "只看问题是否很难", "D": "只看回答是否整齐"}', 'B', '有价值的问题应使学生思考过程可观察。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (31, 'structure-1', 'structure', 1, '课程开场首先要让学生明确什么？', '{"A": "本节要解决的问题与学习目标", "B": "教师所有个人经历", "C": "教材全部章节名称", "D": "与本课无关的规则"}', 'A', '清晰目标为后续活动提供方向。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (32, 'structure-2', 'structure', 1, '课末小结应主要回顾什么？', '{"A": "仅重复作业页码", "B": "目标、关键概念和判断方法", "C": "所有无关细节", "D": "只说下课"}', 'B', '小结帮助学生组织本节学习所得。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (33, 'structure-3', 'structure', 2, '选择课堂活动时，应首先检查什么？', '{"A": "材料是否最多", "B": "能否占满所有时间", "C": "活动是否支持本节学习目标", "D": "活动是否足够热闹"}', 'C', '活动与目标一致才能形成有效课堂结构。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (34, 'structure-4', 'structure', 2, '从讲解过渡到练习时，最合适的做法是？', '{"A": "突然更换无关主题", "B": "省略全部任务说明", "C": "直接要求记住分数", "D": "说明练习如何检验刚学的概念"}', 'D', '明确衔接帮助学生理解活动的目的。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (35, 'structure-5', 'structure', 3, '小结发现多数学生未达目标，应如何安排后续？', '{"A": "依据错误类型设计补充学习和再检查", "B": "宣布所有人都已掌握", "C": "只增加无差别作业量", "D": "删除未达成目标"}', 'A', '后续安排应回应具体学习证据。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_questions` (`id`, `code`, `skill_id`, `level`, `prompt`, `options`, `answer`, `explanation`, `active`) VALUES (36, 'structure-6', 'structure', 3, '检查教学设计一致性时，应对照哪三项？', '{"A": "教师年龄、衣着和语速", "B": "学习目标、教学活动和评价任务", "C": "字体、页数和封面", "D": "座位、天气和铃声"}', 'B', '目标、活动、评价对齐是教学结构的核心。', 1) ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skill_materials` (`id`, `skill_id`, `resource_id`, `course_id`, `level`, `content`) VALUES (1, 'clarity', 97011, 96001, 1, '介绍分数时，哪种说法最明确？
建议：把一个整体平均分成四份，其中一份是四分之一。
说明：先交代整体、平均分与所取份数，概念才完整。

布置小组任务时应先说明什么？
建议：任务、产出和用时。
说明：清楚说明做什么、交什么、用多久，可以降低理解负担。

练习：以《分数的初步认识》为情境，写出一段教学设计；对照上述原则标注理由，完成技能复测检查理解。') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skill_materials` (`id`, `skill_id`, `resource_id`, `course_id`, `level`, `content`) VALUES (2, 'clarity', 97012, 96001, 2, '学生混淆整体与部分，最合适的解释是？
建议：用同一张纸标出整体，再标出其中一份。
说明：保持整体不变，用可见的部分解释关系。

如何检查学生是否理解“平均分”？
建议：让学生判断两组分法并说明理由。
说明：辨别并解释比简单附和更能体现理解。

练习：以《分数的初步认识》为情境，写出一段教学设计；对照上述原则标注理由，完成技能复测检查理解。') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skill_materials` (`id`, `skill_id`, `resource_id`, `course_id`, `level`, `content`) VALUES (3, 'clarity', 97013, 96001, 3, '解释分数大小时学生仍困惑，应如何调整？
建议：保持整体相同，用图示比较并请学生复述。
说明：控制比较条件，结合多种表征并检查理解。

学生能背定义但解释错误，优先做什么？
建议：让其用反例区分定义条件。
说明：用反例检验必要条件，能揭示机械记忆背后的误解。

练习：以《分数的初步认识》为情境，写出一段教学设计；对照上述原则标注理由，完成技能复测检查理解。') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skill_materials` (`id`, `skill_id`, `resource_id`, `course_id`, `level`, `content`) VALUES (4, 'pace', 97021, 96002, 1, '提出问题后最合适的行为是？
建议：根据问题难度留出思考时间。
说明：留出思考空间才能得到学生的真实回答。

安排十分钟微格课，应优先考虑什么？
建议：围绕目标分配环节并预留小结。
说明：时间分配应服务学习目标而非材料数量。

练习：以《分数的初步认识》为情境，写出一段教学设计；对照上述原则标注理由，完成技能复测检查理解。') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skill_materials` (`id`, `skill_id`, `resource_id`, `course_id`, `level`, `content`) VALUES (5, 'pace', 97022, 96002, 2, '小组讨论超时但仍未聚焦，应如何处理？
建议：提示剩余时间和核心问题后组织回收。
说明：明确边界和目标，有助于有效结束讨论。

多数学生已完成而少数仍在思考，应如何安排？
建议：给已完成者拓展任务并支持仍有困难者。
说明：分层安排兼顾学习进度与参与机会。

练习：以《分数的初步认识》为情境，写出一段教学设计；对照上述原则标注理由，完成技能复测检查理解。') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skill_materials` (`id`, `skill_id`, `resource_id`, `course_id`, `level`, `content`) VALUES (6, 'pace', 97023, 96002, 3, '观察到连续讲授后学生回应减少，应优先调整？
建议：插入短判断任务并依据反馈调整讲授。
说明：短反馈环节帮助判断是否需要放慢或转换活动。

评价节奏是否合理，最可靠的依据是？
建议：结合目标达成、等待时间与学生回应。
说明：节奏质量需要学习证据支持，不能仅凭时长。

练习：以《分数的初步认识》为情境，写出一段教学设计；对照上述原则标注理由，完成技能复测检查理解。') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skill_materials` (`id`, `skill_id`, `resource_id`, `course_id`, `level`, `content`) VALUES (7, 'interaction', 97031, 96003, 1, '学生回答后，教师应怎样反馈？
建议：针对回答内容指出依据或需要修正之处。
说明：具体反馈能帮助学生理解正确与错误的原因。

小组讨论结束后应做什么？
建议：组织分享并归纳共同结论。
说明：全班回收使小组成果成为共同学习资源。

练习：以《分数的初步认识》为情境，写出一段教学设计；对照上述原则标注理由，完成技能复测检查理解。') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skill_materials` (`id`, `skill_id`, `resource_id`, `course_id`, `level`, `content`) VALUES (8, 'interaction', 97032, 96003, 2, '只有少数学生发言时，怎样扩大参与？
建议：先独立思考，再同伴交流，最后分享。
说明：分阶段交流降低参与门槛并增加准备时间。

面对学生的错误回答，合适的互动是？
建议：追问其思路并用材料共同验证。
说明：尊重思路并验证证据能够促进概念修正。

练习：以《分数的初步认识》为情境，写出一段教学设计；对照上述原则标注理由，完成技能复测检查理解。') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skill_materials` (`id`, `skill_id`, `resource_id`, `course_id`, `level`, `content`) VALUES (9, 'interaction', 97033, 96003, 3, '两组观点相反，如何促进有效讨论？
建议：让双方展示证据并比较适用条件。
说明：讨论应围绕证据和条件，而不是人气。

如何判断互动是否促进学习？
建议：比较互动前后的解释与理解变化。
说明：互动的价值应落到理解变化与学习成果。

练习：以《分数的初步认识》为情境，写出一段教学设计；对照上述原则标注理由，完成技能复测检查理解。') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skill_materials` (`id`, `skill_id`, `resource_id`, `course_id`, `level`, `content`) VALUES (10, 'posture', 97041, 96004, 1, '讲解时应如何面向学生？
建议：尽量面向学生并保持自然交流。
说明：面向学生有利于建立交流并观察反馈。

板书时站位的基本原则是什么？
建议：避免遮挡关键内容并适时转向学生。
说明：站位应保障学生能看清内容和教师表达。

练习：以《分数的初步认识》为情境，写出一段教学设计；对照上述原则标注理由，完成技能复测检查理解。') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skill_materials` (`id`, `skill_id`, `resource_id`, `course_id`, `level`, `content`) VALUES (11, 'posture', 97042, 96004, 2, '巡视小组时，怎样做更有效？
建议：观察任务进展并提供针对性支持。
说明：巡视的目标是获取学习证据并提供支持。

演示教具时怎样保证可见性？
建议：确认不同位置学生都能看清再演示。
说明：先确保可见性，再进行关键步骤演示。

练习：以《分数的初步认识》为情境，写出一段教学设计；对照上述原则标注理由，完成技能复测检查理解。') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skill_materials` (`id`, `skill_id`, `resource_id`, `course_id`, `level`, `content`) VALUES (12, 'posture', 97043, 96004, 3, '录像中无法看清教师全身，评价站位应如何处理？
建议：明确证据边界，不推断不可见动作。
说明：观测不足时应拒绝无依据的判断。

教学动作频繁但学生分心，优先改进什么？
建议：减少无关动作，让手势对应关键内容。
说明：动作应帮助注意聚焦，而不是制造额外干扰。

练习：以《分数的初步认识》为情境，写出一段教学设计；对照上述原则标注理由，完成技能复测检查理解。') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skill_materials` (`id`, `skill_id`, `resource_id`, `course_id`, `level`, `content`) VALUES (13, 'questioning', 97051, 96005, 1, '哪种提问更能检查理解？
建议：为什么这幅图表示四分之一？。
说明：要求解释依据的问题能呈现学生的思考。

设计一个课堂核心问题时应注意什么？
建议：与目标一致且表述清楚。
说明：问题应明确指向学习目标。

练习：以《分数的初步认识》为情境，写出一段教学设计；对照上述原则标注理由，完成技能复测检查理解。') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skill_materials` (`id`, `skill_id`, `resource_id`, `course_id`, `level`, `content`) VALUES (14, 'questioning', 97052, 96005, 2, '学生说出正确答案后可以怎样追问？
建议：请说明理由或举一个例子。
说明：追问理由能区分理解与猜测。

学生回答偏离问题，应怎样追问？
建议：重述核心条件并请其联系材料解释。
说明：聚焦条件有助于学生调整推理。

练习：以《分数的初步认识》为情境，写出一段教学设计；对照上述原则标注理由，完成技能复测检查理解。') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skill_materials` (`id`, `skill_id`, `resource_id`, `course_id`, `level`, `content`) VALUES (15, 'questioning', 97053, 96005, 3, '希望学生迁移“平均分”，哪种问题最好？
建议：换一种材料后，判断是否平均分并说明依据。
说明：变化情境并保持概念要求，可以检验迁移。

怎样评价一个问题是否有价值？
建议：检查其是否引出与目标相关的推理证据。
说明：有价值的问题应使学生思考过程可观察。

练习：以《分数的初步认识》为情境，写出一段教学设计；对照上述原则标注理由，完成技能复测检查理解。') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skill_materials` (`id`, `skill_id`, `resource_id`, `course_id`, `level`, `content`) VALUES (16, 'structure', 97061, 96006, 1, '课程开场首先要让学生明确什么？
建议：本节要解决的问题与学习目标。
说明：清晰目标为后续活动提供方向。

课末小结应主要回顾什么？
建议：目标、关键概念和判断方法。
说明：小结帮助学生组织本节学习所得。

练习：以《分数的初步认识》为情境，写出一段教学设计；对照上述原则标注理由，完成技能复测检查理解。') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skill_materials` (`id`, `skill_id`, `resource_id`, `course_id`, `level`, `content`) VALUES (17, 'structure', 97062, 96006, 2, '选择课堂活动时，应首先检查什么？
建议：活动是否支持本节学习目标。
说明：活动与目标一致才能形成有效课堂结构。

从讲解过渡到练习时，最合适的做法是？
建议：说明练习如何检验刚学的概念。
说明：明确衔接帮助学生理解活动的目的。

练习：以《分数的初步认识》为情境，写出一段教学设计；对照上述原则标注理由，完成技能复测检查理解。') ON DUPLICATE KEY UPDATE `id`=`id`;

INSERT INTO `adaptive_skill_materials` (`id`, `skill_id`, `resource_id`, `course_id`, `level`, `content`) VALUES (18, 'structure', 97063, 96006, 3, '小结发现多数学生未达目标，应如何安排后续？
建议：依据错误类型设计补充学习和再检查。
说明：后续安排应回应具体学习证据。

检查教学设计一致性时，应对照哪三项？
建议：学习目标、教学活动和评价任务。
说明：目标、活动、评价对齐是教学结构的核心。

练习：以《分数的初步认识》为情境，写出一段教学设计；对照上述原则标注理由，完成技能复测检查理解。') ON DUPLICATE KEY UPDATE `id`=`id`;

COMMIT;
