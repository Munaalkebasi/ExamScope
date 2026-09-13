# ExamScope

> **See what is most likely to hurt your exam grade before it happens.**

ExamScope is an academic study planning tool that visualizes exam risk by combining confidence, practice performance, review recency, and exam proximity. Instead of treating study planning like a generic to-do list, flashcard app, or Pomodoro timer, ExamScope projects your course topics onto an **interactive Radar Scanner** interface to visually answer one core question: *"What should I study next?"*

---

## Main Features

- **Interactive Exam Radar Scanner**: Projects course topics onto concentric risk rings (**Critical**, **High Risk / Needs Attention**, **Moderate Risk**, and **Safe Zone**) with polar coordinate mapping and an animated sweep line.
- **Deterministic Python Risk Engine**: Pure mathematical risk calculation executed entirely in Python without external or paid APIs.
- **Automated "Study Next" Recommendation**: Identifies the single highest-risk topic and generates targeted practice recommendations.
- **Multi-Course & Multi-Exam Support**: Manage and switch between multiple exams (e.g., `MATH 232 Midterm 1`, `PHYS 101 Final Exam`).
- **Comprehensive Topic Management**: Full CRUD capabilities with real-time risk score updates, searching, filtering by risk level, and sorting by risk, confidence, practice score, and review date.
- **Progress Analytics**: Visual readiness score trend chart, risk distribution breakdown, and activity log.
- **SQLite Data Management**: Local SQLite database storage (`database/examscope.db`), validated JSON import/export, and a one-click demo data loader.
- **Light / Dark Theme Support**: Seamless switching between Dark Navy, Light, and System Default themes.

---

## How the Risk Score Works

ExamScope calculates a transparent Risk Score $R \in [0, 100]$ for every topic using four deterministic inputs:

$$\text{Base Risk} = \left(0.40 \times \frac{100 - P}{100} + 0.35 \times \frac{100 - C}{100} + 0.25 \times \min\left(1.0, \frac{D}{12}\right)\right) \times 100$$

Where:
- **$P$**: Latest practice score (%)
- **$C$**: Self-reported confidence level (%)
- **$D$**: Days since last review date

### Exam Proximity Urgency Amplifier
If the exam date is within **14 days** and the topic's Base Risk is $\ge 25$, an urgency multiplier is applied:

$$\text{Urgency Multiplier} = 1.0 + 0.25 \times \max\left(0, 1 - \frac{\text{Days Until Exam}}{14}\right)$$

### Risk Bands & Radar Zones
- **Critical ($75 - 100$)**: Center Zone — Immediate study focus required.
- **High Risk ($50 - 74$)**: Inner/Middle Zone — Needs attention before exam day.
- **Moderate ($25 - 49$)**: Middle/Outer Zone — Periodic review.
- **Safe ($0 - 24$)**: Outer Zone — High retention and strong performance.

---

## Tech Stack

- **Python 3**: Application routing, database interactions, risk engine calculations, readiness scoring, and import/export logic.
- **Flask**: Lightweight WSGI web framework.
- **SQLite 3**: Embedded relational database.
- **Jinja2**: Templating engine for server-side HTML rendering.
- **HTML5 & CSS3**: Responsive UI styling with Tailwind CSS.
- **JavaScript (Vanilla)**: Minimal browser-side interactions for SVG radar rendering, modals, theme toggling, and blip click events.

---

## Project Structure

```text
examscope/
├── app.py                  # Main Flask application & routes
├── database/
│   └── schema.sql          # SQLite schema definitions
├── static/
│   ├── css/
│   │   └── styles.css      # Custom styles and radar animations
│   └── js/
│       ├── app.js          # Core app JS (theme & modal handling)
│       └── radar.js        # Interactive SVG radar blip handler
├── templates/
│   ├── base.html           # Base Jinja template & modal dialogs
│   ├── radar.html          # Main Radar Scanner dashboard
│   ├── topics.html         # Topic management, search & filter page
│   ├── progress.html       # Analytics & progress trend page
│   └── settings.html       # Theme & data management page
├── utils/
│   ├── db.py               # SQLite database helper functions
│   ├── risk_calculator.py  # Python Risk Engine & polar coordinates
│   ├── analytics.py        # Progress snapshots & activity logging
│   ├── recommendations.py  # Study Next recommendation logic
│   └── demo_data.py        # Pre-populated demo dataset loader
├── test_app.py             # Automated unit & integration tests
├── requirements.txt        # Python dependency manifest
├── .gitignore              # Git ignore rules
└── README.md               # Project documentation
```

---

## Installation & Running Locally

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Steps

1. **Clone or navigate to the project directory**:
   ```bash
   cd examscope
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Flask server**:
   ```bash
   python app.py
   ```

4. **Access the web app**:
   Open your browser and go to `http://127.0.0.1:5000`

---

## Testing Instructions

ExamScope includes a comprehensive automated test suite in `test_app.py` covering route rendering, risk engine calculations, exam CRUD, topic CRUD, demo data loading, JSON import validation, and theme settings.

To execute the test suite:

```bash
python test_app.py
```

---

## Vercel deployment

Import `Munaalkebasi/ExamScope` into Vercel and select the Flask framework.
The existing `app.py` exports the application; no separate server is needed.
`vercel.json` runs `build_vercel.py` to publish the existing static assets at
their unchanged `/static/` URLs. Dependencies come from `requirements.txt`.

On Vercel, SQLite uses `/tmp/examscope/examscope.db` and the existing startup
code initializes and seeds demo data. This storage is ephemeral: changes may
disappear on cold starts, redeployments, or when requests use another instance.
Visitors using the same instance share demo data. Do not use this deployment
for private records or reliable progress storage. Export any data you want to
keep. Local and Render deployments retain the existing database path.

Keep Render available until the Vercel deployment and all four main pages
have been verified. Durable storage requires a separate database decision.

## Future Improvements

- **Sub-Topic Breakdowns**: Support nested sub-topics under major exam units.
- **Study Session Timer Integration**: Track time spent studying specific high-risk topics.
- **Calendar Export**: Export study recommendations to iCal/Google Calendar formats.
- **Multi-Exam Comparison**: Side-by-side radar overlay comparing risk distributions across different courses.
