"""Synthetic course catalogue (application layer): Introduction to Python Programming."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ContentItem, ContentType as C, Course, Difficulty as D, Topic

COURSE_CODE = "PY101"

# (topic, difficulty, [(title, type, difficulty)])
_TOPICS = [
    ("Python Basics", D.EASY, [("Introductory video", C.VIDEO, D.EASY), ("Reading material", C.READING, D.EASY),
                               ("Basics quiz", C.QUIZ, D.EASY)]),
    ("Variables", D.EASY, [("Variables walkthrough", C.VIDEO, D.EASY), ("Practice exercises", C.EXERCISE, D.EASY),
                           ("Variables quiz", C.QUIZ, D.EASY)]),
    ("Conditional Statements", D.MEDIUM, [("Video + examples", C.VIDEO_EXAMPLES, D.MEDIUM),
                                          ("Conditionals reading", C.READING, D.MEDIUM),
                                          ("Conditionals exercises", C.EXERCISE, D.MEDIUM)]),
    ("Loops", D.MEDIUM, [("Loops video", C.VIDEO, D.MEDIUM), ("Practice quiz", C.QUIZ, D.MEDIUM),
                         ("Loop exercises", C.EXERCISE, D.MEDIUM)]),
    ("Functions", D.HARD, [("Functions reading", C.READING, D.HARD), ("Advanced exercises", C.EXERCISE, D.HARD),
                           ("Functions quiz", C.QUIZ, D.HARD)]),
]


def ensure_seed_course(db: Session) -> Course:
    existing = db.scalar(select(Course).where(Course.code == COURSE_CODE))
    if existing:
        return existing
    course = Course(code=COURSE_CODE, title="Introduction to Python Programming",
                    description="Synthetic course used to demonstrate adaptive guidance.")
    topics = []
    for i, (name, diff, items) in enumerate(_TOPICS, start=1):
        t = Topic(name=name, order_index=i, difficulty=diff)
        for j, (title, ctype, idiff) in enumerate(items, start=1):
            t.content_items.append(ContentItem(title=title, content_type=ctype, difficulty=idiff, order_index=j))
        topics.append(t)
    for prev, nxt in zip(topics, topics[1:]):
        nxt.prerequisites.append(prev)
    course.topics = topics
    db.add(course)
    db.commit()
    return course
