# System Architecture Specification

## 1. Architectural Overview: 3-Layer Decoupling

Following the architectural principles specified in **Section 7 & 8** of the research specification, the system strictly separates historical evidence, simulated experiments, and application-level delivery:

| Layer | Primary Source | Engineering Purpose | Key Modules |
| :--- | :--- | :--- | :--- |
| **Layer 1: Intelligence** | Historical OULAD Data | Understand learner behaviors, train classifiers & cluster archetypes | `oulad_loader.py`, `classifier.py`, `clusterer.py`, `pattern_analyzer.py` |
| **Layer 2: Simulation** | Synthetic Learners & Interactions | Stress-test learner profiles across multi-week checkpoints | `learner_generator.py`, `interaction_simulator.py` |
| **Layer 3: Application** | Course Catalogs & User Actions | Deliver personalized syllabi and process live feedback | `course_catalog.py`, `recommendation_engine.py`, `journey_tracker.py`, `app.py` |

---

## 2. Layer 1: Intelligence Layer

### A. Feature Engineering
The research emphasizes that **clicks do not equal learning** ($Clicks \ne Knowledge$). Therefore, raw clickstream data is processed alongside inactivity rates and assessment trajectories into an normalized feature space $\mathbf{x} \in \mathbb{R}^8$:
1. $x_1$: Normalized total click interactions
2. $x_2$: Normalized average assessment score ($[0, 1]$)
3. $x_3$: Assessment score trend / slope ($\Delta score / \Delta t$)
4. $x_4$: Inactivity rate ($[0, 1]$)
5. $x_5$: Educational attainment rank
6. $x_6$: Studied credits index
7. $x_7$: Previous course attempts
8. $x_8$: Engagement index:
   $$E = 0.5 \cdot x_1 + 0.5 \cdot (1 - x_4)$$

### B. Outcome Classifier (Softmax Regression with Momentum)
Outputs class probabilities for $K=4$ academic outcomes: $\mathcal{Y} = \{\text{Withdrawn}, \text{Fail}, \text{Pass}, \text{Distinction}\}$.
Logits:
$$z_k = \mathbf{w}_k^T \tilde{\mathbf{x}} + b_k$$
Probabilities:
$$P(y = k \mid \mathbf{x}) = \frac{e^{z_k}}{\sum_{j=1}^K e^{z_j}}$$
Academic Risk Index is formulated as:
$$\text{Risk}(\mathbf{x}) = \Big( P(y = \text{Withdrawn}) + P(y = \text{Fail}) \Big) \times 100\%$$

### C. Cohort Clustering (K-Means)
Partitions learners into $K=4$ behavioral cohorts using Euclidean distance optimization:
$$\arg\min_{\mathbf{S}} \sum_{i=1}^k \sum_{\mathbf{x} \in S_i} \|\mathbf{x} - \boldsymbol{\mu}_i\|^2$$

Discovered cohorts:
- **Cohort 0**: High Achiever / Fast Paced
- **Cohort 1**: Struggling / Guidance Needed
- **Cohort 2**: Steady Learner / Consistent Track
- **Cohort 3**: At-Risk / Disengaged

---

## 3. Layer 2: Simulation Layer

### Synthetic Learner Specification
Extends the platform beyond static records by modeling individual learning dynamics:
```python
@dataclass
class SyntheticLearner:
    learner_id: str
    name: str
    archetype: str
    age: int
    education: str
    initial_knowledge: float       # 0 - 100%
    learning_speed: float          # 0.1 - 1.0 multiplier
    engagement_baseline: float     # 0.1 - 1.0
    preferred_learning_method: str # 'Video' | 'Practice' | 'Reading'
    assessment_history: List[float]
    active_pathway: str
```

### Knowledge Gain & Checkpoint Progression
At each checkpoint $t \in \{1, 3, 5, 8\}$:
$$\Delta K_t = (\text{speed} \times \alpha) + (\text{engagement}_t \times \beta) + \gamma_{\text{adaptation}} + \epsilon$$

---

## 4. Layer 3: Application & Adaptive Guidance

### Adaptive Decision Matrix
Derived directly from **PDF Section 4**:

| Learner Archetype | Observed Metrics | Adaptive System Intervention | Syllabus Modifications |
| :--- | :--- | :--- | :--- |
| **Learner A (Advanced)** | High engagement ($\ge 80\%$), High scores ($\ge 80\%$), Fast pace | Fast-track to advanced exercises; introduce challenging topics | • Skip T1 (Basics)<br>• Enrich T5 (Recursion)<br>• Unlock T6 (OOP Capstone) |
| **Learner B (Average)** | Moderate engagement ($60-75\%$), Average scores ($55-75\%$) | Continue planned sequence; provide additional practice & quizzes | • Standard sequential pathway<br>• Periodic formative assessments |
| **Learner C (Struggling)** | Low performance ($<50\%$), Repeated topic difficulty | Revisit foundational concepts; simpler explanations; format adaptation | • Foundational review of T1 & T2<br>• Video explanations prioritized<br>• Hint scaffolding enabled |

---

## 5. Directory & File Organization

```
adaptive-learning-platform/
├── .vscode/                 # VS Code IDE launch configurations, tasks & settings
│   ├── launch.json
│   ├── settings.json
│   └── tasks.json
├── data/                    # Historical data, models & catalogs
│   ├── oulad_historical.csv
│   ├── courses.json
│   ├── classifier_model.json
│   └── clusterer_model.json
├── docs/                    # Architectural & project documentation
│   ├── AGILE_PLANNING.md
│   ├── ARCHITECTURE.md
│   └── API_SPEC.md
├── scripts/                 # CLI entrypoints & runners
│   ├── generate_initial_data.py
│   ├── train_models.py
│   ├── run_simulation_demo.py
│   └── run_server.py
├── src/
│   ├── intelligence/        # Layer 1: ML models & OULAD loaders
│   ├── simulation/          # Layer 2: Synthetic learners & checkpoint simulator
│   ├── adaptive/            # Layer 3: Recommendation engine & course catalog
│   ├── api/                 # REST API endpoints (FastAPI)
│   └── web/                 # Interactive Dashboard (HTML5/Canvas/CSS/JS)
├── tests/                   # Continuous testing suite (Unittest)
│   ├── test_intelligence.py
│   ├── test_simulation.py
│   ├── test_adaptive_engine.py
│   └── test_api.py
├── requirements.txt
├── README.md
└── run.bat
```
