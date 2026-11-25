import re

from extensions import db


TOPICS = ('人际关系', '综合分析', '组织管理', '计划组织', '应急应变', '自我认知', '教育教学',
          '课堂管理', '时事政治', '家校沟通', '学生支持', '班级管理', '试讲', '答辩')
VALUES = {
    'weaknesses': TOPICS,
    'mistake_types': TOPICS,
    'preferences': ('逐题练习', '模拟面试', '先给提示', '先出题再点评', '限时练习'),
    'goals': ('教资面试', '结构化面试', '试讲', '答辩', *TOPICS),
}


class AssistantProfile(db.Model):
    __tablename__ = 'assistant_profiles'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    labels = db.Column(db.JSON, nullable=False)


def normalize(labels):
    if not isinstance(labels, dict):
        labels = {}
    return {
        field: list(dict.fromkeys(label for label in labels.get(field, []) if label in allowed))[-8:]
        if isinstance(labels.get(field), list) else []
        for field, allowed in VALUES.items()
    }


def read_profile(uid):
    row = db.session.get(AssistantProfile, uid)
    return normalize(row.labels if row else {})


def merge_labels(profile, changes):
    return normalize({field: profile[field] + changes.get(field, []) for field in VALUES})


def update_profile(uid, changes):
    changes = normalize(changes)
    if not any(changes.values()):
        return read_profile(uid)
    row = db.session.get(AssistantProfile, uid)
    if row is None:
        row = AssistantProfile(user_id=uid, labels=changes)
        db.session.add(row)
    else:
        row.labels = merge_labels(normalize(row.labels), changes)
    db.session.commit()
    return row.labels


def learning_signals(text, questions):
    changes = {}
    for clause in re.split(r'[。！？!?；;，,\n]', text):
        if re.search(r'不是|并非|不再|不想|不打算|不计划|不喜欢|假如|例如|他说|她说|举例|引用|[“”「」]', clause):
            continue
        topics = [topic for topic in TOPICS if topic in clause]
        if re.match(r'^\s*我.{0,24}(总卡|老卡|总是卡|总答错|经常答错|反复答错|总做错|经常做错)', clause):
            changes.setdefault('weaknesses', []).extend(topics)
            if re.search(r'答错|做错', clause):
                changes.setdefault('mistake_types', []).extend(topics)
        if re.match(r'^\s*(我.{0,12}(目标是|打算|计划|准备通过|想通过|想练好)|目标是)', clause):
            for label in VALUES['goals']:
                if label in clause:
                    changes.setdefault('goals', []).append(label)
        if re.match(r'^\s*我.{0,8}(更喜欢|偏好|希望以后)', clause):
            changes.setdefault('preferences', []).extend(label for label in VALUES['preferences'] if label in clause)
        if topics and re.search(r'怎么答|怎么练|如何答|如何练|不会答|帮我练', clause):
            for topic in topics:
                questions.setdefault(topic, set()).add(clause.strip())
                if len(questions[topic]) >= 2:
                    changes.setdefault('preferences', []).append('逐题练习')
                    changes.setdefault('goals', []).append(topic)
    return normalize(changes)
