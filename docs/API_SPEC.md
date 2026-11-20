# REST API Specification

The platform exposes an interactive OpenAPI (Swagger) interface at `http://localhost:8000/docs` when the server is running.

## Base URL
```
http://localhost:8000/api
```

---

## 1. System & Historical Intelligence Endpoints

### `GET /api/health`
Returns system status, active models, and total registered learners.
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "service": "Adaptive Learning Platform",
  "models_loaded": {
    "classifier": true,
    "clusterer": true
  },
  "registered_learners_count": 3
}
```

### `GET /api/stats`
Returns summary statistics and outcome distributions from the historical OULAD dataset.
- **Response `200 OK`**:
```json
{
  "total_students": 2000,
  "outcome_distribution": {
    "Pass": 48.1,
    "Distinction": 18.6,
    "Fail": 20.3,
    "Withdrawn": 12.9
  },
  "avg_clicks": 1270.4,
  "avg_assessment_score": 57.0
}
```

---

## 2. Learner & Simulation Endpoints

### `GET /api/learners`
Lists all registered learners (including canonical subjects A, B, C and dynamically spawned synthetic learners).

### `POST /api/learners`
Creates and registers a custom synthetic learner.
- **Request Body**:
```json
{
  "name": "Alex Johnson",
  "archetype": "Average",
  "age": 23,
  "education": "Undergraduate",
  "initial_knowledge": 50.0,
  "learning_speed": 0.65,
  "engagement_baseline": 0.60,
  "preferred_learning_method": "Practice"
}
```

### `GET /api/learners/{learner_id}`
Returns the comprehensive profile, latest checkpoint, and active guidance pathway for a learner.

### `GET /api/learners/{learner_id}/journey`
Returns the sequential multi-week timeline (Weeks 1, 3, 5, 8...) tracking evolving scores, engagement, and risk %.

### `POST /api/learners/{learner_id}/simulate-step?adaptation_active=true`
Advances the learner simulation by 2 weeks. Dynamically recalibrates ML predictions and adaptive recommendations.

### `POST /api/learners/{learner_id}/simulate-all?adaptation_active=true`
Simulates the full 8-week learning trajectory and updates final recommendations.

---

## 3. Adaptive Personalization & Feedback Endpoints

### `GET /api/learners/{learner_id}/recommendations`
Returns personalized syllabus modifications, exempted modules, enriched challenges, and pedagogical rationales.

### `POST /api/learners/{learner_id}/submit-quiz`
Records an assessment score on a topic, updating learner knowledge and triggering trajectory evolution.
- **Request Body**:
```json
{
  "topic_id": "T2",
  "score": 88.0
}
```

### `POST /api/learners/{learner_id}/feedback`
Records continuous feedback from the learner or educator, adjusting pacing and engagement parameters.
- **Request Body**:
```json
{
  "feedback_type": "PACING",
  "notes": "Pacing is optimal, ready for functions module.",
  "applied": true
}
```

---

## 4. Course Catalog Endpoints

### `GET /api/courses`
Lists available modular courses and topic breakdowns.

### `GET /api/courses/{course_id}`
Returns details for a specific course (e.g. `CS101`).
