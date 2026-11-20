"""
Course Catalog and Content Management Module.
Maintains course configurations, modular learning topics, content types, and difficulty ratings.
"""

import json
from typing import Dict, Any, List, Optional


class CourseCatalog:
    def __init__(self, catalog_filepath: str):
        self.catalog_filepath = catalog_filepath
        self.courses: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self):
        with open(self.catalog_filepath, "r", encoding="utf-8") as f:
            course_list = json.load(f)
            self.courses = {c["id"]: c for c in course_list}

    def get_course(self, course_id: str) -> Optional[Dict[str, Any]]:
        return self.courses.get(course_id)

    def list_courses(self) -> List[Dict[str, Any]]:
        return list(self.courses.values())

    def get_topics(self, course_id: str) -> List[Dict[str, Any]]:
        course = self.get_course(course_id)
        return course.get("topics", []) if course else []

    def get_topic(self, course_id: str, topic_id: str) -> Optional[Dict[str, Any]]:
        topics = self.get_topics(course_id)
        for t in topics:
            if t["topic_id"] == topic_id:
                return t
        return None
