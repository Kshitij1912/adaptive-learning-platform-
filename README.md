# ML-Powered Adaptive Learning Platform

> An intelligent, multi-layer educational platform combining historical learning analytics (OULAD), synthetic learner simulation, and dynamic syllabus personalization. Developed under an Agile/Lean MVP methodology with modular architecture, continuous testing, and real-time user feedback loops.

---

## 🎯 Executive Summary & Research Insights

This project translates the core educational data science principles outlined in the **OULAD Adaptive Learning Specification** into an enterprise-ready, modular system:

1. **Clicks $\ne$ Learning**: Avoids treating raw click counts as learning. Instead, it extracts normalized engagement indexes, assessment improvement trajectories, and inactivity risk.
2. **3 Distinct Architectural Layers**:
   - **Layer 1: Intelligence Layer** (Historical OULAD Data $\rightarrow$ Outcome Classification, K-Means Clustering, Pattern Detection).
   - **Layer 2: Simulation Layer** (Agent-based Synthetic Learners $\rightarrow$ Multi-checkpoint trajectories across Weeks 1, 3, 5, 8).
   - **Layer 3: Application Layer** (Personalized Course Delivery $\rightarrow$ Dynamic syllabus adaptation for *Introduction to Python Programming*).
3. **Canonical Learner Archetypes**:
   - **Learner A (Advanced)**: High engagement + high scores $\rightarrow$ Skipped introductory revision, unlocked OOP capstone challenge.
   - **Learner B (Average)**: Consistent effort + moderate scores $\rightarrow$ Standard sequential progression with reinforced practice.
   - **Learner C (Struggling)**: High/declining effort + low initial scores $\rightarrow$ Remedial foundational review, video format prioritization, and hint scaffolding turning fail risk into a pass.

---

## 🚀 Quick Start Guide

### 1. Open Project in VS Code
Open your terminal and launch VS Code directly in this project directory:
```powershell
code "C:\Users\mehta\Desktop\Final year project"
```

### 2. Run the Full-Stack Web Application
Run the one-click launcher:
```cmd
run.bat
```
*Or execute with Python:*
```powershell
python scripts/run_server.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

- **Interactive Dashboard**: `http://localhost:8000/`
- **Swagger REST API Docs**: `http://localhost:8000/docs`

---

## 💻 VS Code Integration

Pre-configured `.vscode` configurations are included:

- **Run / Debug Configurations (`F5`)**:
  - `FastAPI Web Server`: Starts the development server with live reload.
  - `Simulation CLI Demo (Learners A, B, C)`: Runs the multi-checkpoint trajectory comparison in your terminal.
  - `Train & Evaluate ML Pipeline`: Retrains Softmax and K-Means models from scratch on OULAD CSV data.
  - `Run All Tests (Unittest)`: Runs the test suite in the integrated debug terminal.
- **VS Code Tasks (`Ctrl+Shift+B` or `Terminal -> Run Task`)**:
  - `Start Adaptive Learning Platform`
  - `Run Continuous Tests`
  - `Run Simulation CLI Demo`

---

## 🧪 Continuous Testing

All 19 unit and integration tests execute in under 200ms without requiring heavy third-party runners:
```powershell
python -m unittest discover tests
```
Output:
```
...................
----------------------------------------------------------------------
Ran 19 tests in 0.168s

OK
```

---

## 📂 Project Architecture

```
Final year project/
├── .vscode/                 # Pre-configured launch, settings & tasks for VS Code
│   ├── launch.json
│   ├── settings.json
│   └── tasks.json
├── data/                    # Historical OULAD records, courses & model weights
│   ├── oulad_historical.csv
│   ├── courses.json
│   ├── classifier_model.json
│   └── clusterer_model.json
├── docs/                    # Agile planning, architecture & API specs
│   ├── AGILE_PLANNING.md
│   ├── ARCHITECTURE.md
│   └── API_SPEC.md
├── scripts/                 # Executable scripts
│   ├── generate_initial_data.py
│   ├── train_models.py
│   ├── run_simulation_demo.py
│   └── run_server.py
├── src/
│   ├── intelligence/        # Layer 1: OULAD loader, Softmax Classifier, K-Means
│   ├── simulation/          # Layer 2: Synthetic learners & interaction simulator
│   ├── adaptive/            # Layer 3: Course catalog & recommendation engine
│   ├── api/                 # FastAPI backend application
│   └── web/                 # Interactive HTML5/Canvas/CSS/JS frontend
├── tests/                   # 19 automated tests
│   ├── test_intelligence.py
│   ├── test_simulation.py
│   ├── test_adaptive_engine.py
│   └── test_api.py
├── project_overview.pdf     # Original research specification
├── requirements.txt
├── README.md
└── run.bat
```

---

## 📊 Live Trajectory Comparison

When running `python scripts/run_simulation_demo.py`:
- **Learner A**: Starts at 87% $\rightarrow$ Distinction (0.4% risk) $\rightarrow$ *Accelerated Mastery Pathway*.
- **Learner B**: Starts at 59% $\rightarrow$ Pass (4.2% risk) $\rightarrow$ *Standard Balanced Pathway*.
- **Learner C**: Starts at 39% (71.6% fail/withdrawal risk) $\rightarrow$ With adaptive guidance climbs to 64% (5.7% risk) $\rightarrow$ *Remedial & Foundational Support Pathway*.
