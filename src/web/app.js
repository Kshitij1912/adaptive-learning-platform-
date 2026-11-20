/**
 * Edoo Adaptive Learning Platform - Interactive Client Application
 * Clean EdTech Style (Deep Forest Green, Mint Green & Pure White)
 * Connecting Modern Frontend UI to FastAPI Backend & ML Models.
 */

const API_BASE = window.location.origin;

// State Variables
let currentLearnerId = "SYN-A-101";
let currentLearnerData = null;
let currentTimeline = [];
let currentRecs = null;
let allLearners = [];

// DOM Element Selectors
const learnerNameEl = document.getElementById("learner-name");
const learnerCohortEl = document.getElementById("learner-cohort-badge");
const learnerEduEl = document.getElementById("learner-education");
const learnerSpeedEl = document.getElementById("learner-speed");
const learnerMethodEl = document.getElementById("learner-method");
const learnerAvatarEl = document.getElementById("learner-badge-avatar");

const kpiScoreEl = document.getElementById("kpi-score");
const kpiEngagementEl = document.getElementById("kpi-engagement");
const kpiRiskEl = document.getElementById("kpi-risk");

const checkpointLabelEl = document.getElementById("curr-checkpoint-label");
const predOutcomePillEl = document.getElementById("pred-outcome-pill");

const probDistEl = document.getElementById("prob-dist");
const probDistValEl = document.getElementById("prob-dist-val");
const probPassEl = document.getElementById("prob-pass");
const probPassValEl = document.getElementById("prob-pass-val");
const probFailEl = document.getElementById("prob-fail");
const probFailValEl = document.getElementById("prob-fail-val");
const probWithdrawnEl = document.getElementById("prob-withdrawn");
const probWithdrawnValEl = document.getElementById("prob-withdrawn-val");

const inferencesListEl = document.getElementById("inferences-list");
const pathwayBadgeEl = document.getElementById("pathway-badge");
const pathwayTitleEl = document.getElementById("pathway-title");
const recsSummaryListEl = document.getElementById("recommendations-summary");
const topicsContainerEl = document.getElementById("topics-container");
const customLearnersListEl = document.getElementById("custom-learners-list");

// Modals
const quizModal = document.getElementById("quiz-modal");
const customLearnerModal = document.getElementById("custom-learner-modal");
const toastEl = document.getElementById("toast");

// Canvas
const canvas = document.getElementById("trajectory-canvas");
const ctx = canvas.getContext("2d");

// ----------------- Initialization -----------------
async function init() {
  bindEvents();
  await refreshLearnerList();
  await loadLearner(currentLearnerId);
}

function bindEvents() {
  // Mobile nav toggle
  const mobileBtn = document.getElementById("btn-mobile-nav");
  if (mobileBtn) {
    mobileBtn.addEventListener("click", () => {
      document.querySelector(".nav-menu").classList.toggle("open");
    });
  }

  // Quiz Modal Events
  document.getElementById("btn-open-quiz").addEventListener("click", () => quizModal.classList.remove("hidden"));
  document.getElementById("btn-close-quiz").addEventListener("click", () => quizModal.classList.add("hidden"));
  document.getElementById("quiz-form").addEventListener("submit", handleQuizSubmit);

  // Custom Learner Modal Events
  document.getElementById("btn-new-learner").addEventListener("click", () => customLearnerModal.classList.remove("hidden"));
  document.getElementById("btn-close-custom").addEventListener("click", () => customLearnerModal.classList.add("hidden"));
  document.getElementById("custom-learner-form").addEventListener("submit", handleCustomLearnerSubmit);

  // Simulation Controls
  document.getElementById("btn-simulate-step").addEventListener("click", handleSimulateStep);
  document.getElementById("btn-simulate-all").addEventListener("click", handleSimulateAll);

  // Recommendation Feedback
  document.getElementById("btn-adopt-recs").addEventListener("click", () => handleFeedback("ADOPT_RECOMMENDATIONS", "Learner adopted adaptive pathway", true));
  document.getElementById("btn-need-help").addEventListener("click", () => handleFeedback("REQUEST_SCAFFOLDING", "Learner requested extra practice and hints", false));

  // Canonical Buttons in Studio
  document.querySelectorAll(".student-pill-btn").forEach(tab => {
    tab.addEventListener("click", (e) => {
      const targetTab = e.currentTarget;
      document.querySelectorAll(".student-pill-btn").forEach(t => t.classList.remove("active"));
      targetTab.classList.add("active");
      const id = targetTab.getAttribute("data-id");
      loadLearner(id);
    });
  });
}

// Global helper for archetype card clicks
window.selectCanonicalLearner = function(learnerId) {
  document.querySelectorAll(".student-pill-btn").forEach(t => {
    if (t.getAttribute("data-id") === learnerId) {
      t.classList.add("active");
    } else {
      t.classList.remove("active");
    }
  });
  loadLearner(learnerId);
};

// ----------------- API Integration -----------------
async function refreshLearnerList() {
  try {
    const res = await fetch(`${API_BASE}/api/learners`);
    allLearners = await res.json();
    renderCustomLearnersList();
  } catch (err) {
    showToast("Error connecting to backend API: " + err.message);
  }
}

async function loadLearner(learnerId) {
  currentLearnerId = learnerId;
  try {
    const [profileRes, journeyRes, recsRes] = await Promise.all([
      fetch(`${API_BASE}/api/learners/${learnerId}`),
      fetch(`${API_BASE}/api/learners/${learnerId}/journey`),
      fetch(`${API_BASE}/api/learners/${learnerId}/recommendations`)
    ]);

    currentLearnerData = await profileRes.json();
    const journeyData = await journeyRes.json();
    currentTimeline = journeyData.timeline || [];
    currentRecs = await recsRes.json();

    renderUI();
  } catch (err) {
    showToast("Error loading learner profile: " + err.message);
  }
}

// ----------------- Dynamic Rendering -----------------
function renderUI() {
  if (!currentLearnerData) return;
  const learner = currentLearnerData.learner;
  const latest = currentLearnerData.latest_checkpoint || currentTimeline[currentTimeline.length - 1] || {};

  // Profile Information
  learnerNameEl.textContent = learner.name;
  learnerCohortEl.textContent = latest.cluster_cohort || `${learner.archetype} Cohort`;
  learnerEduEl.textContent = learner.education;
  learnerSpeedEl.textContent = `${learner.learning_speed}x`;
  learnerMethodEl.textContent = learner.preferred_learning_method;

  // Avatar Styling
  const initial = learner.archetype === "Advanced" ? "A" : learner.archetype === "Average" ? "B" : learner.archetype === "Struggling" ? "C" : "S";
  learnerAvatarEl.textContent = initial;
  learnerAvatarEl.className = "profile-avatar-circle " + (
    learner.archetype === "Advanced" ? "avatar-a" :
    learner.archetype === "Average" ? "avatar-b" :
    learner.archetype === "Struggling" ? "avatar-c" : "avatar-custom"
  );

  // KPIs
  const score = latest.assessment_score !== undefined ? latest.assessment_score.toFixed(1) : learner.initial_knowledge.toFixed(1);
  const engagement = latest.engagement_pct !== undefined ? latest.engagement_pct.toFixed(1) : (learner.engagement_baseline * 100).toFixed(1);
  const risk = latest.risk_score_pct !== undefined ? latest.risk_score_pct.toFixed(1) : "30.0";

  kpiScoreEl.textContent = `${score}%`;
  kpiEngagementEl.textContent = `${engagement}%`;
  kpiRiskEl.textContent = `${risk}%`;
  kpiRiskEl.className = `kpi-val ${parseFloat(risk) >= 50 ? "text-risk-high" : parseFloat(risk) >= 20 ? "text-risk-med" : "text-risk-low"}`;

  checkpointLabelEl.textContent = latest.week ? `Week ${latest.week}` : "Week 1";

  // Outcome Pill
  const outcome = latest.predicted_outcome || "Pass";
  predOutcomePillEl.textContent = outcome;
  predOutcomePillEl.className = `badge-outcome-${outcome.toLowerCase()}`;

  // Outcome Probabilities
  const probs = latest.probabilities || { "Distinction": 0.25, "Pass": 0.55, "Fail": 0.15, "Withdrawn": 0.05 };
  updateProgressBar(probDistEl, probDistValEl, probs["Distinction"] || 0);
  updateProgressBar(probPassEl, probPassValEl, probs["Pass"] || 0);
  updateProgressBar(probFailEl, probFailValEl, probs["Fail"] || 0);
  updateProgressBar(probWithdrawnEl, probWithdrawnValEl, probs["Withdrawn"] || 0);

  // Pattern Inferences (from research PDF)
  inferencesListEl.innerHTML = "";
  const inferences = latest.patterns && latest.patterns.length > 0 ? latest.patterns : ["Consistent progress along baseline"];
  inferences.forEach(inf => {
    const li = document.createElement("li");
    li.textContent = "• " + inf;
    inferencesListEl.appendChild(li);
  });

  // Render Syllabus & Canvas
  renderCurriculum();
  renderTrajectoryChart();
}

function updateProgressBar(barEl, valEl, prob) {
  const pct = (prob * 100).toFixed(1);
  barEl.style.width = `${pct}%`;
  valEl.textContent = `${pct}%`;
}

function renderCurriculum() {
  if (!currentRecs) return;
  pathwayBadgeEl.textContent = currentRecs.pathway_name || "Standard Pathway";
  pathwayTitleEl.textContent = `Personalized Syllabus: ${currentRecs.pathway_name}`;

  recsSummaryListEl.innerHTML = "";
  (currentRecs.recommendations || []).forEach(r => {
    const li = document.createElement("li");
    li.textContent = r;
    recsSummaryListEl.appendChild(li);
  });

  topicsContainerEl.innerHTML = "";
  const curriculum = currentRecs.custom_curriculum || [];
  curriculum.forEach(topic => {
    const box = document.createElement("div");
    box.className = "topic-box";

    let diffClass = "diff-easy";
    if (topic.difficulty === "Medium") diffClass = "diff-med";
    if (topic.difficulty === "Hard") diffClass = "diff-hard";

    let stClass = "st-standard";
    if (topic.status && topic.status.includes("Skipped")) stClass = "st-skipped";
    if (topic.status && topic.status.includes("Active")) stClass = "st-active";
    if (topic.status && topic.status.includes("Foundational")) stClass = "st-review";

    box.innerHTML = `
      <div class="topic-box-top">
        <span class="topic-header-title">${topic.topic_id}: ${topic.title}</span>
        <span class="diff-badge ${diffClass}">${topic.difficulty}</span>
      </div>
      <p style="font-size: 11.5px; color: #64748b; line-height: 1.4;">${topic.description}</p>
      <div class="topic-status-pill ${stClass}">${topic.status || "Standard Track"}</div>
      <p style="font-size: 10.5px; color: #2563EB; font-weight: 600; margin-top: 6px;">${topic.custom_note || ""}</p>
    `;
    topicsContainerEl.appendChild(box);
  });
}

function renderTrajectoryChart() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const width = canvas.width;
  const height = canvas.height;
  const padding = { left: 45, right: 30, top: 25, bottom: 35 };
  const graphWidth = width - padding.left - padding.right;
  const graphHeight = height - padding.top - padding.bottom;

  // Grid Lines & Y Axis
  ctx.strokeStyle = "#E2E8F0";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#94A3B8";
  ctx.font = "10px JetBrains Mono";
  ctx.textAlign = "right";

  for (let yVal = 0; yVal <= 100; yVal += 25) {
    const yPos = padding.top + graphHeight - (yVal / 100 * graphHeight);
    ctx.beginPath();
    ctx.moveTo(padding.left, yPos);
    ctx.lineTo(width - padding.right, yPos);
    ctx.stroke();
    ctx.fillText(`${yVal}%`, padding.left - 8, yPos + 3);
  }

  // Pass Threshold Line (50%)
  const passY = padding.top + graphHeight - (50 / 100 * graphHeight);
  ctx.strokeStyle = "rgba(239, 68, 68, 0.4)";
  ctx.setLineDash([4, 4]);
  ctx.beginPath();
  ctx.moveTo(padding.left, passY);
  ctx.lineTo(width - padding.right, passY);
  ctx.stroke();
  ctx.setLineDash([]);

  if (currentTimeline.length === 0) return;

  // Calculate Data Points
  const xStep = graphWidth / Math.max(1, currentTimeline.length - 1);
  const points = currentTimeline.map((step, idx) => {
    const x = currentTimeline.length === 1 ? padding.left + graphWidth / 2 : padding.left + (idx * xStep);
    const yScore = padding.top + graphHeight - (Math.min(100, step.assessment_score) / 100 * graphHeight);
    const yEng = padding.top + graphHeight - (Math.min(100, step.engagement_pct) / 100 * graphHeight);
    return { x, yScore, yEng, week: step.week };
  });

  // Draw X Axis Labels
  ctx.fillStyle = "#4b5563";
  ctx.textAlign = "center";
  points.forEach(p => {
    ctx.fillText(`Week ${p.week}`, p.x, height - 10);
  });

  // Draw Assessment Curve (Brand Blue #2563EB)
  drawLineSeries(points.map(p => ({ x: p.x, y: p.yScore })), "#2563EB", "rgba(37, 99, 235, 0.10)");

  // Draw Engagement Curve (Purple #8B5CF6)
  drawLineSeries(points.map(p => ({ x: p.x, y: p.yEng })), "#8B5CF6", "rgba(139, 92, 246, 0.08)");
}

function drawLineSeries(coords, strokeColor, fillColor) {
  if (coords.length === 0) return;

  // Area Fill
  ctx.fillStyle = fillColor;
  ctx.beginPath();
  ctx.moveTo(coords[0].x, canvas.height - 35);
  coords.forEach(pt => ctx.lineTo(pt.x, pt.y));
  ctx.lineTo(coords[coords.length - 1].x, canvas.height - 35);
  ctx.closePath();
  ctx.fill();

  // Stroke
  ctx.strokeStyle = strokeColor;
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  coords.forEach((pt, i) => {
    if (i === 0) ctx.moveTo(pt.x, pt.y);
    else ctx.lineTo(pt.x, pt.y);
  });
  ctx.stroke();

  // Highlight Dots
  coords.forEach(pt => {
    ctx.fillStyle = strokeColor;
    ctx.beginPath();
    ctx.arc(pt.x, pt.y, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(pt.x, pt.y, 2, 0, Math.PI * 2);
    ctx.fill();
  });
}

function renderCustomLearnersList() {
  customLearnersListEl.innerHTML = "";
  const nonCanonical = allLearners.filter(l => !["SYN-A-101", "SYN-B-102", "SYN-C-103"].includes(l.learner_id));
  if (nonCanonical.length === 0) return;

  const header = document.createElement("p");
  header.className = "card-caption-sm mt-2";
  header.textContent = "Custom Spawned Students:";
  customLearnersListEl.appendChild(header);

  nonCanonical.forEach(l => {
    const tab = document.createElement("button");
    tab.className = `student-pill-btn ${l.learner_id === currentLearnerId ? "active" : ""}`;
    tab.innerHTML = `
      <div class="student-avatar-badge avatar-custom">S</div>
      <div class="student-pill-info">
        <strong>${l.name}</strong>
        <span>${l.archetype} • ${l.preferred_learning_method}</span>
      </div>
    `;
    tab.addEventListener("click", () => {
      document.querySelectorAll(".student-pill-btn").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      loadLearner(l.learner_id);
    });
    customLearnersListEl.appendChild(tab);
  });
}

// ----------------- Actions -----------------
async function handleSimulateStep() {
  const adaptationActive = document.getElementById("toggle-adaptation").checked;
  try {
    const res = await fetch(`${API_BASE}/api/learners/${currentLearnerId}/simulate-step?adaptation_active=${adaptationActive}`, {
      method: "POST"
    });
    const data = await res.json();
    showToast(data.message || `Advanced to Week ${data.new_checkpoint.week}`);
    await loadLearner(currentLearnerId);
  } catch (err) {
    showToast("Simulation error: " + err.message);
  }
}

async function handleSimulateAll() {
  const adaptationActive = document.getElementById("toggle-adaptation").checked;
  try {
    const res = await fetch(`${API_BASE}/api/learners/${currentLearnerId}/simulate-all?adaptation_active=${adaptationActive}`, {
      method: "POST"
    });
    await res.json();
    showToast("Successfully simulated full 8-week trajectory!");
    await loadLearner(currentLearnerId);
  } catch (err) {
    showToast("Simulation error: " + err.message);
  }
}

async function handleQuizSubmit(e) {
  e.preventDefault();
  const topicId = document.getElementById("quiz-topic-select").value;
  const score = parseFloat(document.getElementById("quiz-score-input").value);

  try {
    const res = await fetch(`${API_BASE}/api/learners/${currentLearnerId}/submit-quiz`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic_id: topicId, score: score })
    });
    await res.json();
    quizModal.classList.add("hidden");
    showToast(`Quiz score ${score}% recorded! Recalibrating journey.`);
    await loadLearner(currentLearnerId);
  } catch (err) {
    showToast("Quiz submission error: " + err.message);
  }
}

async function handleCustomLearnerSubmit(e) {
  e.preventDefault();
  const name = document.getElementById("cust-name").value;
  const archetype = document.getElementById("cust-archetype").value;
  const edu = document.getElementById("cust-edu").value;
  const format = document.getElementById("cust-format").value;
  const initK = parseFloat(document.getElementById("cust-init-k").value);
  const speed = parseFloat(document.getElementById("cust-speed").value);

  try {
    const res = await fetch(`${API_BASE}/api/learners`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        archetype,
        education: edu,
        preferred_learning_method: format,
        initial_knowledge: initK,
        learning_speed: speed,
        engagement_baseline: speed * 0.9
      })
    });
    const data = await res.json();
    customLearnerModal.classList.add("hidden");
    showToast(`Learner ${name} spawned!`);
    await refreshLearnerList();
    loadLearner(data.learner.learner_id);
  } catch (err) {
    showToast("Creation error: " + err.message);
  }
}

async function handleFeedback(feedbackType, notes, applied) {
  try {
    await fetch(`${API_BASE}/api/learners/${currentLearnerId}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ feedback_type: feedbackType, notes: notes, applied: applied })
    });
    showToast(applied ? "Adaptive curriculum confirmed!" : "Feedback logged for review.");
    await loadLearner(currentLearnerId);
  } catch (err) {
    showToast("Feedback error: " + err.message);
  }
}

function showToast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.remove("hidden");
  setTimeout(() => toastEl.classList.add("hidden"), 3500);
}

window.addEventListener("DOMContentLoaded", init);
