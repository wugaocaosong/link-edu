-- Lab5 ONLY. Run with the restricted link_lab5 account.

USE link_lab5;

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS adaptive_skills (
	id VARCHAR(24) NOT NULL, 
	name VARCHAR(64) NOT NULL, 
	description TEXT NOT NULL, 
	ordinal INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (ordinal)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS classroom_api_usage (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	session_id INTEGER, 
	service VARCHAR(20) NOT NULL, 
	reserved_cny FLOAT NOT NULL, 
	charged_cny FLOAT, 
	units JSON, 
	state VARCHAR(20) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id),
  INDEX `ix_classroom_api_usage_session_id` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS classroom_credit_usage (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	account VARCHAR(16) NOT NULL, 
	service VARCHAR(16) NOT NULL, 
	model VARCHAR(80) NOT NULL, 
	session_id INTEGER, 
	reserved_usd FLOAT NOT NULL, 
	charged_usd FLOAT, 
	units JSON, 
	state VARCHAR(20) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id),
  INDEX `ix_classroom_credit_usage_account` (`account`),
  INDEX `ix_classroom_credit_usage_session_id` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS classroom_tickets (
	digest VARCHAR(64) NOT NULL, 
	session_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	expires_at DATETIME NOT NULL, 
	used BOOL NOT NULL, 
	PRIMARY KEY (digest)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS courses (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	title VARCHAR(128) NOT NULL, 
	category VARCHAR(64) NOT NULL, 
	description TEXT, 
	lesson_count INTEGER NOT NULL, 
	cover_url VARCHAR(255), 
	stage VARCHAR(32), 
	outline TEXT, 
	source VARCHAR(128), 
	source_url VARCHAR(255), 
	is_active BOOL NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS resources (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	title VARCHAR(128) NOT NULL, 
	category VARCHAR(64), 
	description VARCHAR(255), 
	file_url VARCHAR(255), 
	is_active BOOL NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS users (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	account VARCHAR(64) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	name VARCHAR(64) NOT NULL, 
	`role` VARCHAR(32) NOT NULL, 
	avatar_url VARCHAR(255), 
	bio TEXT, 
	school VARCHAR(128), 
	major VARCHAR(128), 
	grade VARCHAR(32), 
	level INTEGER NOT NULL, 
	xp INTEGER NOT NULL, 
	badges_json TEXT, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id),
  UNIQUE INDEX `ix_users_account` (`account`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS adaptive_mastery (
	user_id INTEGER NOT NULL, 
	skill_id VARCHAR(24) NOT NULL, 
	quiz_score FLOAT, 
	training_score FLOAT, 
	score FLOAT, 
	evidence JSON NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (user_id, skill_id), 
	CHECK (score IS NULL OR (score >= 0 AND score <= 100)), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(skill_id) REFERENCES adaptive_skills (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS adaptive_paths (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	fingerprint VARCHAR(64) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id, fingerprint), 
	FOREIGN KEY(user_id) REFERENCES users (id),
  INDEX `ix_adaptive_paths_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS adaptive_questions (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	code VARCHAR(48) NOT NULL, 
	skill_id VARCHAR(24) NOT NULL, 
	level INTEGER NOT NULL, 
	prompt TEXT NOT NULL, 
	options JSON NOT NULL, 
	answer VARCHAR(1) NOT NULL, 
	explanation TEXT NOT NULL, 
	active BOOL NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (level BETWEEN 1 AND 3), 
	UNIQUE (code), 
	FOREIGN KEY(skill_id) REFERENCES adaptive_skills (id),
  INDEX `ix_adaptive_questions_skill_id` (`skill_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS adaptive_quizzes (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	request_key VARCHAR(64) NOT NULL, 
	skill_id VARCHAR(24), 
	status VARCHAR(16) NOT NULL, 
	scores JSON, 
	created_at DATETIME NOT NULL, 
	submitted_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (user_id, request_key), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(skill_id) REFERENCES adaptive_skills (id),
  INDEX `ix_adaptive_quizzes_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS adaptive_skill_materials (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	skill_id VARCHAR(24) NOT NULL, 
	resource_id INTEGER NOT NULL, 
	course_id INTEGER NOT NULL, 
	level INTEGER NOT NULL, 
	content TEXT NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (skill_id, level), 
	CHECK (level BETWEEN 1 AND 3), 
	FOREIGN KEY(skill_id) REFERENCES adaptive_skills (id), 
	FOREIGN KEY(resource_id) REFERENCES resources (id), 
	FOREIGN KEY(course_id) REFERENCES courses (id),
  INDEX `ix_adaptive_skill_materials_skill_id` (`skill_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS kb_documents (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	title VARCHAR(200) NOT NULL, 
	filename VARCHAR(255) NOT NULL, 
	file_type VARCHAR(16) NOT NULL, 
	category VARCHAR(32) NOT NULL, 
	tags JSON NOT NULL, 
	source VARCHAR(255), 
	description TEXT, 
	sha256 VARCHAR(64) NOT NULL, 
	size_bytes INTEGER NOT NULL, 
	storage_path VARCHAR(255) NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	error VARCHAR(255), 
	page_count INTEGER, 
	chunk_count INTEGER NOT NULL, 
	embedding_model VARCHAR(128), 
	is_active BOOL NOT NULL, 
	uploaded_by INTEGER, 
	content_version VARCHAR(32) NOT NULL, 
	license_note VARCHAR(255), 
	valid_until VARCHAR(10), 
	last_audited_at DATETIME, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (sha256), 
	FOREIGN KEY(uploaded_by) REFERENCES users (id),
  INDEX `ix_kb_documents_category` (`category`),
  INDEX `ix_kb_documents_status` (`status`),
  INDEX `ix_kb_documents_uploaded_by` (`uploaded_by`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS training_journals (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	entry_date VARCHAR(10) NOT NULL, 
	body TEXT NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id),
  INDEX `ix_training_journals_entry_date` (`entry_date`),
  INDEX `ix_training_journals_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS training_sessions (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	course_id INTEGER NOT NULL, 
	status VARCHAR(32) NOT NULL, 
	progress_percent INTEGER NOT NULL, 
	duration_minutes INTEGER NOT NULL, 
	started_at DATETIME, 
	last_trained_at DATETIME, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(course_id) REFERENCES courses (id),
  INDEX `ix_training_sessions_course_id` (`course_id`),
  INDEX `ix_training_sessions_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS adaptive_answers (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	quiz_id INTEGER NOT NULL, 
	question_id INTEGER NOT NULL, 
	ordinal INTEGER NOT NULL, 
	snapshot JSON NOT NULL, 
	selected VARCHAR(1), 
	correct BOOL, 
	PRIMARY KEY (id), 
	UNIQUE (quiz_id, question_id), 
	UNIQUE (quiz_id, ordinal), 
	FOREIGN KEY(quiz_id) REFERENCES adaptive_quizzes (id), 
	FOREIGN KEY(question_id) REFERENCES adaptive_questions (id),
  INDEX `ix_adaptive_answers_quiz_id` (`quiz_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ai_feedbacks (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	session_id INTEGER, 
	overall_score INTEGER NOT NULL, 
	clarity_score INTEGER, 
	pace_score INTEGER, 
	interaction_score INTEGER, 
	suggestion TEXT, 
	report_json TEXT, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(session_id) REFERENCES training_sessions (id),
  INDEX `ix_ai_feedbacks_session_id` (`session_id`),
  INDEX `ix_ai_feedbacks_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS classrooms (
	session_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	mode VARCHAR(16) NOT NULL, 
	topic VARCHAR(128) NOT NULL, 
	state VARCHAR(24) NOT NULL, 
	students JSON NOT NULL, 
	started_at DATETIME NOT NULL, 
	ended_at DATETIME, 
	cloud_vision BOOL NOT NULL, 
	report_state VARCHAR(24) NOT NULL, 
	report JSON, 
	report_error VARCHAR(160), 
	report_version INTEGER NOT NULL, 
	correction TEXT, 
	PRIMARY KEY (session_id), 
	FOREIGN KEY(session_id) REFERENCES training_sessions (id), 
	FOREIGN KEY(user_id) REFERENCES users (id),
  INDEX `ix_classrooms_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS kb_audit_logs (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	document_id INTEGER, 
	action VARCHAR(32) NOT NULL, 
	actor_id INTEGER, 
	detail JSON NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(document_id) REFERENCES kb_documents (id) ON DELETE SET NULL,
  INDEX `ix_kb_audit_logs_actor_id` (`actor_id`),
  INDEX `ix_kb_audit_logs_document_id` (`document_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS kb_chunks (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	document_id INTEGER NOT NULL, 
	ordinal INTEGER NOT NULL, 
	kind VARCHAR(16) NOT NULL, 
	text TEXT NOT NULL, 
	heading_path JSON NOT NULL, 
	page_start INTEGER, 
	page_end INTEGER, 
	char_count INTEGER NOT NULL, 
	content_hash VARCHAR(64) NOT NULL, 
	embedding BLOB NOT NULL, 
	embedding_model VARCHAR(128) NOT NULL, 
	embedding_dim INTEGER NOT NULL, 
	extra JSON NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_kb_chunk_ordinal UNIQUE (document_id, ordinal), 
	FOREIGN KEY(document_id) REFERENCES kb_documents (id) ON DELETE CASCADE,
  INDEX `ix_kb_chunks_document_id` (`document_id`),
  INDEX `ix_kb_chunks_embedding_model` (`embedding_model`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS classroom_events (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	session_id INTEGER NOT NULL, 
	event_key VARCHAR(96) NOT NULL, 
	kind VARCHAR(40) NOT NULL, 
	at_ms INTEGER NOT NULL, 
	payload JSON NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (session_id, event_key), 
	FOREIGN KEY(session_id) REFERENCES classrooms (session_id),
  INDEX `ix_classroom_events_session_id` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS classroom_practice_plans (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	source_session_id INTEGER NOT NULL, 
	source_report_version INTEGER NOT NULL, 
	dimension VARCHAR(24) NOT NULL, 
	target_kind VARCHAR(40) NOT NULL, 
	task_text TEXT NOT NULL, 
	basis VARCHAR(24) NOT NULL, 
	source_event_ids JSON NOT NULL, 
	criteria JSON NOT NULL, 
	status VARCHAR(24) NOT NULL, 
	retest_session_id INTEGER, 
	comparison JSON, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (source_session_id, source_report_version, target_kind), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(source_session_id) REFERENCES classrooms (session_id), 
	UNIQUE (retest_session_id), 
	FOREIGN KEY(retest_session_id) REFERENCES classrooms (session_id),
  INDEX `ix_classroom_practice_plans_source_session_id` (`source_session_id`),
  INDEX `ix_classroom_practice_plans_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS adaptive_path_steps (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	path_id INTEGER NOT NULL, 
	skill_id VARCHAR(24) NOT NULL, 
	ordinal INTEGER NOT NULL, 
	kind VARCHAR(16) NOT NULL, 
	title VARCHAR(160) NOT NULL, 
	reason JSON NOT NULL, 
	material_id INTEGER, 
	practice_plan_id INTEGER, 
	status VARCHAR(16) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (path_id, ordinal), 
	FOREIGN KEY(path_id) REFERENCES adaptive_paths (id), 
	FOREIGN KEY(skill_id) REFERENCES adaptive_skills (id), 
	FOREIGN KEY(material_id) REFERENCES adaptive_skill_materials (id), 
	FOREIGN KEY(practice_plan_id) REFERENCES classroom_practice_plans (id),
  INDEX `ix_adaptive_path_steps_path_id` (`path_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS adaptive_progress (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER NOT NULL, 
	step_id INTEGER NOT NULL, 
	completed_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (step_id), 
	FOREIGN KEY(step_id) REFERENCES adaptive_path_steps (id),
  INDEX `ix_adaptive_progress_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
