# Contributing to Vibe Finance

Thank you for your interest in contributing to **Vibe Finance**! We welcome community contributions, bug fixes, algorithmic improvements, and feature proposals.

---

## 🛠️ Development Setup

### 1. Prerequisites
- **Python**: 3.11 or higher
- **Node.js**: 18.0 or higher (with npm)
- **Docker & Docker Compose** (optional, recommended for isolated testing)

### 2. Fork and Clone
```bash
git clone https://github.com/YOUR_USERNAME/Vibe-Finance.git
cd Vibe-Finance
```

### 3. Backend Setup (FastAPI)
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt  # or backend/requirements.txt

# Configure environment
cp .env.example .env
```

### 4. Frontend Setup (React + Vite)
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Testing & Quality Assurance

Before submitting any Pull Request, ensure that all 21 test scenarios pass with zero regressions:

```bash
# From repository root
python -u backend/test_suite.py
```

### Pull Request Checklist:
- [ ] All 21 tests in `backend/test_suite.py` pass.
- [ ] New functionality or financial indicators include corresponding test scenarios.
- [ ] No hardcoded API keys or private credentials in commits.
- [ ] Code adheres to PEP 8 for Python and standard ESLint rules for TypeScript/React.

---

## 🌿 Git Branching & Commits

- Create feature branches from `main`:
  ```bash
  git checkout -b feature/your-feature-name
  ```
- Use conventional commit messages:
  - `feat(quant): add stochastic oscillator indicator`
  - `fix(rag): resolve document chunk boundary overlap`
  - `docs: update API contracts for portfolio rebalancer`
  - `test: add unit coverage for behavioral risk drawdown`

---

## 📄 License
By contributing to Vibe Finance, you agree that your contributions will be licensed under the project's [Apache 2.0 License](LICENSE).
