from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ContentItem, ContentType, Difficulty, Topic

DIFF = {Difficulty.EASY: 0, Difficulty.MEDIUM: 1, Difficulty.HARD: 2}


@dataclass(frozen=True)
class Item:
    id: int
    topic_id: int
    topic_order: int
    topic_name: str
    content_type: ContentType
    difficulty: Difficulty
    title: str


class Catalogue:
    """Flattened, ordered view of a course's content (topic order, then item order)."""

    def __init__(self, items: list[Item]):
        self.items = items
        self._idx = {it.id: i for i, it in enumerate(items)}

    def __bool__(self) -> bool:
        return bool(self.items)

    def index_of(self, item_id: int | None) -> int:
        return self._idx.get(item_id, -1) if item_id is not None else -1

    def next_item(self, idx: int) -> Item | None:
        return self.items[idx + 1] if idx + 1 < len(self.items) else None

    def foundational(self, idx: int, pref: ContentType | None) -> Item:
        """Earliest easy item up to the current position, preferring the learner's format."""
        pool = [it for it in self.items[: max(idx, 0) + 1] if it.difficulty == Difficulty.EASY] or self.items[:1]
        for want in (pref, ContentType.VIDEO):
            for it in pool:
                if want is not None and it.content_type == want:
                    return it
        return pool[0]

    def practice(self, idx: int) -> Item | None:
        cur = self.items[max(idx, 0)]
        pool = [it for it in self.items
                if it.content_type in (ContentType.EXERCISE, ContentType.QUIZ)
                and it.topic_order <= cur.topic_order and DIFF[it.difficulty] <= DIFF[cur.difficulty]]
        return pool[-1] if pool else None

    def quiz(self, idx: int) -> Item | None:
        cur = self.items[max(idx, 0)]
        pool = [it for it in self.items if it.content_type == ContentType.QUIZ and it.topic_order <= cur.topic_order]
        return pool[-1] if pool else next((it for it in self.items if it.content_type == ContentType.QUIZ), None)

    def first_at_least(self, idx: int, level: Difficulty) -> Item | None:
        return next((it for it in self.items[idx + 1:] if DIFF[it.difficulty] >= DIFF[level]), None)

    def harder(self, idx: int) -> Item | None:
        cur = self.items[max(idx, 0)]
        return next((it for it in self.items[idx + 1:] if DIFF[it.difficulty] > DIFF[cur.difficulty]), None) \
            or self.next_item(idx)


def load_catalogue(db: Session, course_id: int | None) -> Catalogue | None:
    if course_id is None:
        return None
    rows = db.execute(
        select(ContentItem, Topic).join(Topic, ContentItem.topic_id == Topic.id)
        .where(Topic.course_id == course_id).order_by(Topic.order_index, ContentItem.order_index)
    ).all()
    items = [Item(ci.id, t.id, t.order_index, t.name, ci.content_type, ci.difficulty, ci.title) for ci, t in rows]
    return Catalogue(items) if items else None
