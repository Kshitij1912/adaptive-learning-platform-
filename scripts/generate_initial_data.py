import json
import csv
import random
import os

def generate_oulad_historical(filepath: str, n_records: int = 2000):
    random.seed(42)
    regions = ["London", "South Region", "Scotland", "North Western Region", "West Midlands", "South West Region", "East Anglia"]
    education_levels = ["No Formal quals", "Lower Than A Level", "A Level or Equivalent", "HE Qualification", "Post Graduate Qualification"]
    age_bands = ["0-35", "35-55", "55<="]
    genders = ["M", "F"]
    modules = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG"]

    records = []
    for i in range(1, n_records + 1):
        student_id = 10000 + i
        code_module = random.choice(modules)
        gender = random.choice(genders)
        region = random.choice(regions)
        education = random.choices(education_levels, weights=[0.05, 0.30, 0.40, 0.20, 0.05])[0]
        age_band = random.choices(age_bands, weights=[0.65, 0.30, 0.05])[0]
        studied_credits = random.choice([30, 60, 90, 120, 150, 180])
        prev_attempts = random.choices([0, 1, 2, 3], weights=[0.80, 0.14, 0.05, 0.01])[0]

        # Latent archetype to model real-world learning behavior:
        archetype = random.choices(
            ["advanced", "consistent", "struggling_engaged", "disengaged_dropout", "improving"],
            weights=[0.18, 0.32, 0.20, 0.18, 0.12]
        )[0]

        if archetype == "advanced":
            total_clicks = random.randint(1200, 3500)
            avg_assessment = round(random.uniform(78.0, 98.0), 1)
            score_trend = round(random.uniform(0.02, 0.15), 3) # positive improvement
            inactivity_rate = round(random.uniform(0.02, 0.12), 2)
            final_result = random.choices(["Distinction", "Pass"], weights=[0.75, 0.25])[0]
        elif archetype == "consistent":
            total_clicks = random.randint(700, 1600)
            avg_assessment = round(random.uniform(55.0, 78.0), 1)
            score_trend = round(random.uniform(-0.02, 0.08), 3)
            inactivity_rate = round(random.uniform(0.05, 0.20), 2)
            final_result = random.choices(["Pass", "Distinction", "Fail"], weights=[0.82, 0.12, 0.06])[0]
        elif archetype == "struggling_engaged":
            total_clicks = random.randint(900, 2200) # high clicks, poor scores! (PDF: High engagement + poor assessment scores)
            avg_assessment = round(random.uniform(32.0, 52.0), 1)
            score_trend = round(random.uniform(-0.08, 0.05), 3)
            inactivity_rate = round(random.uniform(0.05, 0.22), 2)
            final_result = random.choices(["Pass", "Fail"], weights=[0.40, 0.60])[0]
        elif archetype == "disengaged_dropout":
            total_clicks = random.randint(50, 450) # low clicks, declining scores, increasing inactivity
            avg_assessment = round(random.uniform(15.0, 42.0), 1)
            score_trend = round(random.uniform(-0.35, -0.05), 3)
            inactivity_rate = round(random.uniform(0.35, 0.85), 2)
            final_result = random.choices(["Withdrawn", "Fail"], weights=[0.65, 0.35])[0]
        else: # improving
            total_clicks = random.randint(600, 1500)
            avg_assessment = round(random.uniform(48.0, 72.0), 1)
            score_trend = round(random.uniform(0.12, 0.35), 3) # strong positive trajectory
            inactivity_rate = round(random.uniform(0.08, 0.25), 2)
            final_result = random.choices(["Pass", "Distinction"], weights=[0.85, 0.15])[0]

        records.append({
            "id_student": student_id,
            "code_module": code_module,
            "gender": gender,
            "region": region,
            "highest_education": education,
            "age_band": age_band,
            "studied_credits": studied_credits,
            "num_of_prev_attempts": prev_attempts,
            "total_clicks": total_clicks,
            "avg_assessment_score": avg_assessment,
            "score_trend": score_trend,
            "inactivity_rate": inactivity_rate,
            "final_result": final_result
        })

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
    print(f"Generated {len(records)} historical OULAD records at {filepath}")

def generate_course_catalog(filepath: str):
    courses = [
        {
            "id": "CS101",
            "name": "Introduction to Python Programming",
            "description": "Comprehensive foundational programming course with modular adaptive pathways.",
            "topics": [
                {
                    "topic_id": "T1",
                    "title": "Python Basics",
                    "description": "Language syntax, REPL, execution model, and basic I/O.",
                    "difficulty": "Easy",
                    "contents": [
                        {"content_id": "C1_VID", "title": "Introductory Video: Hello Python", "type": "Video", "duration_min": 12, "difficulty": "Easy"},
                        {"content_id": "C1_TXT", "title": "Interactive Reading: Syntax & Comments", "type": "Reading", "duration_min": 15, "difficulty": "Easy"},
                        {"content_id": "C1_QZ", "title": "Concept Check Quiz", "type": "Quiz", "duration_min": 10, "difficulty": "Easy"}
                    ]
                },
                {
                    "topic_id": "T2",
                    "title": "Variables & Data Types",
                    "description": "Integers, floats, strings, booleans, type conversion, and state management.",
                    "difficulty": "Easy",
                    "contents": [
                        {"content_id": "C2_VID", "title": "Video: Memory, Variables & Types", "type": "Video", "duration_min": 14, "difficulty": "Easy"},
                        {"content_id": "C2_EX", "title": "Practice Exercises: Manipulating Data Types", "type": "Practice", "duration_min": 25, "difficulty": "Easy"},
                        {"content_id": "C2_QZ", "title": "Variables Mastery Quiz", "type": "Quiz", "duration_min": 15, "difficulty": "Easy"}
                    ]
                },
                {
                    "topic_id": "T3",
                    "title": "Conditional Statements",
                    "description": "Branching logic, if-elif-else constructs, Boolean algebra, and nested conditions.",
                    "difficulty": "Medium",
                    "contents": [
                        {"content_id": "C3_VID", "title": "Video + Worked Examples: Decision Making", "type": "Video", "duration_min": 18, "difficulty": "Medium"},
                        {"content_id": "C3_TXT", "title": "Reading: Truth Tables & Short-circuiting", "type": "Reading", "duration_min": 15, "difficulty": "Medium"},
                        {"content_id": "C3_EX", "title": "Coding Challenge: Decision Trees in Code", "type": "Practice", "duration_min": 30, "difficulty": "Medium"},
                        {"content_id": "C3_QZ", "title": "Conditionals Checkpoint Assessment", "type": "Quiz", "duration_min": 20, "difficulty": "Medium"}
                    ]
                },
                {
                    "topic_id": "T4",
                    "title": "Loops & Iteration",
                    "description": "Definite (for) and indefinite (while) loops, break, continue, and iterations over collections.",
                    "difficulty": "Medium",
                    "contents": [
                        {"content_id": "C4_VID", "title": "Video: Iterating Effectively with For & While", "type": "Video", "duration_min": 20, "difficulty": "Medium"},
                        {"content_id": "C4_EX", "title": "Interactive Lab: Pattern Generation & Algorithms", "type": "Practice", "duration_min": 35, "difficulty": "Medium"},
                        {"content_id": "C4_QZ", "title": "Practice Quiz: Loop Control & Edge Cases", "type": "Quiz", "duration_min": 20, "difficulty": "Medium"}
                    ]
                },
                {
                    "topic_id": "T5",
                    "title": "Functions & Modularity",
                    "description": "Function definition, parameters, return values, scope, closures, and modular design.",
                    "difficulty": "Hard",
                    "contents": [
                        {"content_id": "C5_VID", "title": "Video: Decomposing Problems with Functions", "type": "Video", "duration_min": 22, "difficulty": "Hard"},
                        {"content_id": "C5_EX1", "title": "Foundational Practice: Function Signatures & Scope", "type": "Practice", "duration_min": 25, "difficulty": "Medium"},
                        {"content_id": "C5_EX2", "title": "Advanced Exercises: Recursion & High-Order Functions", "type": "Advanced", "duration_min": 45, "difficulty": "Hard"},
                        {"content_id": "C5_QZ", "title": "Functions Mastery Assessment", "type": "Quiz", "duration_min": 25, "difficulty": "Hard"}
                    ]
                },
                {
                    "topic_id": "T6",
                    "title": "Object-Oriented Programming & Real-World Projects",
                    "description": "Classes, objects, inheritance, encapsulation, and building a modular application.",
                    "difficulty": "Hard",
                    "contents": [
                        {"content_id": "C6_VID", "title": "Video: Thinking in Objects and Data Abstraction", "type": "Video", "duration_min": 25, "difficulty": "Hard"},
                        {"content_id": "C6_EX", "title": "Capstone Mini-Project: Student Gradebook System", "type": "Advanced", "duration_min": 60, "difficulty": "Hard"},
                        {"content_id": "C6_QZ", "title": "Comprehensive Final Assessment", "type": "Quiz", "duration_min": 30, "difficulty": "Hard"}
                    ]
                }
            ]
        }
    ]

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, mode="w", encoding="utf-8") as f:
        json.dump(courses, f, indent=2)
    print(f"Generated Course Catalog at {filepath}")

if __name__ == "__main__":
    generate_oulad_historical("C:/Users/mehta/.gemini/antigravity/scratch/adaptive-learning-platform/data/oulad_historical.csv")
    generate_course_catalog("C:/Users/mehta/.gemini/antigravity/scratch/adaptive-learning-platform/data/courses.json")
