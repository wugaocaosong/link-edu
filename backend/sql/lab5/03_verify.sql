USE link_lab5;
SELECT VERSION() AS mysql_version, DATABASE() AS lab_database, CURRENT_USER() AS restricted_user;
SHOW TABLES;
SHOW CREATE TABLE adaptive_answers;
SELECT s.name, COUNT(q.id) AS question_count FROM adaptive_skills s JOIN adaptive_questions q ON q.skill_id=s.id GROUP BY s.id,s.name;
SELECT s.name, m.level, c.title AS course, r.title AS resource FROM adaptive_skill_materials m JOIN adaptive_skills s ON s.id=m.skill_id JOIN courses c ON c.id=m.course_id JOIN resources r ON r.id=m.resource_id ORDER BY s.ordinal,m.level;
