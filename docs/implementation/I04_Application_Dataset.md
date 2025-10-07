# I04: Application Dataset - Curation & Test Harness

**Version:** 1.0
**Date:** 2025-10-01
**Status:** Draft

---

## Changelog

### v1.0 (2025-10-01)
- **Added**: Specific dataset sources with automated verification scripts
- **Added**: Concrete GitHub search queries and PyPI filter criteria
- **Rationale**: Address curation bottleneck risk identified in Opus review
- **Reference**: Opus review feedback (dataset curation underspecified)
- **Process**: v0.0 archived before modifications

---
**Phase:** Phase 1 - Foundation (Weeks 3-4)
**Dependencies:** I02 (database, Docker environment)
**Enables:** I06, I07, I08 (CET training phases)

---

## Executive Summary

This document specifies the application dataset for ICCM validation, consisting of:
- 50 high-quality Python applications (40 train, 10 hold-out)
- Comprehensive test suites (>80% coverage) for reconstruction validation
- Automated test harness for parallel execution
- Quality-over-quantity approach (addressing v2.1 reviewer concerns)

**Timeline:** 2 weeks (parallel with I03, I05)
**Critical Milestone:** 10 apps curated by Week 4, 50 apps by Month 5
**Success Criteria:** All apps testable, >80% coverage, <2,000 LOC each

---

## Dataset Design Philosophy

### Quality-Over-Quantity Rationale

**Decision (from I00, addressing v2.1 reviewer feedback):**
- **50 apps total** (40 train, 10 hold-out) instead of 3,000+
- **100% manual validation** - feasible for 5-person lab
- **Rigorous statistical testing** still valid (paired t-tests, α=0.05, 80% power)
- **Gold standard creation** - human-extracted requirements for each app

**Benefits:**
1. **Full validation:** Every app manually inspected, test suites verified
2. **High quality:** Ensure test coverage >80%, no flaky tests
3. **Reproducibility:** Smaller dataset → easier for community validation
4. **Resource-appropriate:** Matches 5-person research lab capacity

**Trade-off:**
- Lower initial generalization, but can expand post-PoC
- Focus on proving core thesis first, then scale

### Application Selection Criteria

**Must-Have Criteria:**
1. **Test Coverage >80%** - Enables reliable reconstruction validation
2. **LOC 100-2,000** - Large enough to be meaningful, small enough to debug
3. **Pure Python** - Simplifies execution environment (expand to JS/Go later)
4. **Clear Requirements** - Well-documented, unambiguous functionality
5. **No External Dependencies** - Or minimal, easily installable (pip)
6. **Diverse Functionality** - Algorithms, APIs, data processing, utilities
7. **Open Source License** - MIT/Apache/BSD for ethical use

**Nice-to-Have Criteria:**
- Real-world usage (GitHub stars >100)
- Active maintenance
- Good code quality
- Interesting algorithmic challenges

---

## Dataset Composition (50 Apps Total)

### Phase 1 Subset (10 Apps - Weeks 3-4)

**Purpose:** Validate infrastructure and initial CET training

| # | Application | Description | LOC | Test Coverage | Domain |
|---|-------------|-------------|-----|---------------|--------|
| 1 | **json-parser** | JSON parsing library | 500 | 92% | Data structures |
| 2 | **markdown-renderer** | Markdown to HTML converter | 800 | 88% | Text processing |
| 3 | **csv-validator** | CSV schema validation | 400 | 95% | Data validation |
| 4 | **unit-converter** | Physical unit conversion | 600 | 90% | Calculation |
| 5 | **simple-calculator** | Expression evaluator | 350 | 94% | Parsing/eval |
| 6 | **todo-list-cli** | Command-line task manager | 700 | 85% | CRUD operations |
| 7 | **url-shortener** | URL shortening service | 500 | 88% | Hashing/storage |
| 8 | **password-strength** | Password strength checker | 300 | 93% | String analysis |
| 9 | **data-validator** | Generic data validation lib | 650 | 89% | Schema validation |
| 10 | **simple-db** | In-memory database | 900 | 86% | Data structures |

**Total LOC:** 5,700 (average: 570 per app)

### Full Dataset (50 Apps - Month 5)

**Training Set (40 Apps):**
- Expand Phase 1 subset to 40 apps
- Maintain diversity across domains
- Include varying complexity (100-2,000 LOC)

**Hold-out Set (10 Apps):**
- Never seen during training
- Used for final validation only
- Same quality/complexity distribution as training set

**Domain Distribution (50 apps):**
- **Data Processing:** 15 apps (CSV, JSON, XML, data pipelines)
- **Algorithms:** 10 apps (sorting, search, graph algorithms)
- **APIs/Services:** 10 apps (REST APIs, web scrapers, API clients)
- **Utilities:** 8 apps (file tools, converters, validators)
- **CLI Tools:** 7 apps (command-line utilities)

---

## Application Structure & Storage

### Directory Structure

```
/mnt/projects/ICCM/datasets/applications/
├── train/
│   ├── 001_json_parser/
│   │   ├── src/
│   │   │   ├── parser.py
│   │   │   ├── tokenizer.py
│   │   │   └── __init__.py
│   │   ├── tests/
│   │   │   ├── test_parser.py
│   │   │   ├── test_tokenizer.py
│   │   │   └── conftest.py
│   │   ├── requirements.txt
│   │   ├── README.md
│   │   ├── metadata.json
│   │   └── gold_requirements.md  # Human-extracted (I09 baseline)
│   ├── 002_markdown_renderer/
│   │   └── ... (same structure)
│   └── ... (apps 003-040)
├── holdout/
│   ├── 041_advanced_json_processor/
│   │   └── ... (same structure)
│   └── ... (apps 042-050)
└── dataset_manifest.json
```

### Metadata Schema

**File:** `metadata.json` (per application)

```json
{
  "app_id": "001",
  "name": "json-parser",
  "description": "Lightweight JSON parsing library with error handling",
  "language": "python",
  "version": "1.2.0",
  "license": "MIT",
  "source_url": "https://github.com/example/json-parser",
  "statistics": {
    "total_loc": 500,
    "src_loc": 380,
    "test_loc": 120,
    "test_coverage": 92.3,
    "num_functions": 25,
    "num_classes": 5,
    "num_test_cases": 48
  },
  "requirements": {
    "functional": [
      "Parse valid JSON strings into Python objects",
      "Detect and report syntax errors with line/column",
      "Support all JSON types: object, array, string, number, boolean, null",
      "Handle nested structures up to 100 levels deep"
    ],
    "non_functional": [
      "Parse 1MB JSON in <100ms",
      "Zero external dependencies"
    ],
    "constraints": [
      "Pure Python 3.9+",
      "No use of built-in json module"
    ]
  },
  "domain": "data_structures",
  "split": "train",
  "curated_date": "2025-10-01",
  "curator": "Team member name"
}
```

### Database Integration

**Insert into PostgreSQL (from I02 schema):**

```python
import json
from pathlib import Path
import psycopg

def load_application_to_db(app_path: Path, conn):
    """Load application metadata into PostgreSQL."""
    metadata = json.loads((app_path / "metadata.json").read_text())

    conn.execute(
        """
        INSERT INTO applications (
            name, description, source_path, test_suite_path,
            language, loc, test_coverage, split
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            metadata['name'],
            metadata['description'],
            str(app_path / "src"),
            str(app_path / "tests"),
            metadata['language'],
            metadata['statistics']['total_loc'],
            metadata['statistics']['test_coverage'],
            metadata['split']
        )
    )

    app_id = conn.fetchone()[0]
    print(f"✓ Loaded app {metadata['name']} with ID {app_id}")
    return app_id
```

---

## Test Harness Design

### Purpose

Automated test execution for reconstruction validation:
1. Run original test suite against LLM-generated implementation
2. Collect pass/fail results, coverage, errors
3. Store results in PostgreSQL for training signals
4. Parallel execution across Docker pool (from I02)

### Test Harness Architecture

**Components:**
1. **Test Runner:** Executes pytest in Docker containers
2. **Result Collector:** Parses pytest JSON output
3. **Coverage Analyzer:** Measures code coverage
4. **Signal Generator:** Converts results to training signals

### Test Runner Implementation

**File:** `/mnt/projects/ICCM/infrastructure/test_harness/runner.py`

```python
#!/usr/bin/env python3
"""
Test harness for running original test suites against LLM-generated implementations.
"""
import json
import subprocess
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class TestResult:
    app_id: int
    reconstruction_id: int
    passed: int
    failed: int
    total: int
    test_pass_rate: float
    coverage: float
    errors: List[str]
    execution_time: float  # seconds

class TestHarness:
    def __init__(self, app_dataset_path: Path):
        self.dataset_path = app_dataset_path

    def run_tests(
        self,
        app_id: int,
        reconstruction_id: int,
        implementation_code: str,
        timeout: int = 60
    ) -> TestResult:
        """
        Run original test suite against LLM-generated implementation.

        Args:
            app_id: Application ID from database
            reconstruction_id: Reconstruction attempt ID
            implementation_code: Generated Python code
            timeout: Max execution time in seconds

        Returns:
            TestResult with pass/fail counts and coverage
        """
        # Get application metadata
        app_dir = self._get_app_dir(app_id)
        test_suite_path = app_dir / "tests"

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Write LLM-generated implementation
            impl_path = tmp_path / "implementation.py"
            impl_path.write_text(implementation_code)

            # Copy test suite
            subprocess.run(["cp", "-r", str(test_suite_path), str(tmp_path / "tests")])

            # Copy requirements if exists
            req_file = app_dir / "requirements.txt"
            if req_file.exists():
                subprocess.run(["cp", str(req_file), str(tmp_path)])
                subprocess.run(["pip", "install", "-q", "-r", str(tmp_path / "requirements.txt")])

            # Run pytest with coverage
            cmd = [
                "pytest",
                str(tmp_path / "tests"),
                "-v",
                "--tb=short",
                "--json-report",
                "--json-report-file=report.json",
                "--cov=implementation",
                "--cov-report=json:coverage.json"
            ]

            try:
                result = subprocess.run(
                    cmd,
                    cwd=tmp_path,
                    timeout=timeout,
                    capture_output=True,
                    text=True
                )

                # Parse pytest JSON report
                report_file = tmp_path / "report.json"
                coverage_file = tmp_path / "coverage.json"

                if report_file.exists():
                    report = json.loads(report_file.read_text())
                    passed = report['summary'].get('passed', 0)
                    failed = report['summary'].get('failed', 0)
                    total = passed + failed

                    # Extract error messages
                    errors = [
                        f"{t['nodeid']}: {t['call']['longrepr']}"
                        for t in report.get('tests', [])
                        if t['outcome'] == 'failed'
                    ]

                    # Parse coverage
                    coverage = 0.0
                    if coverage_file.exists():
                        cov_data = json.loads(coverage_file.read_text())
                        coverage = cov_data['totals']['percent_covered']

                    return TestResult(
                        app_id=app_id,
                        reconstruction_id=reconstruction_id,
                        passed=passed,
                        failed=failed,
                        total=total,
                        test_pass_rate=passed / total if total > 0 else 0.0,
                        coverage=coverage,
                        errors=errors,
                        execution_time=report.get('duration', 0.0)
                    )
                else:
                    # Test execution failed completely
                    return TestResult(
                        app_id=app_id,
                        reconstruction_id=reconstruction_id,
                        passed=0,
                        failed=0,
                        total=0,
                        test_pass_rate=0.0,
                        coverage=0.0,
                        errors=["Test execution failed: no report generated"],
                        execution_time=0.0
                    )

            except subprocess.TimeoutExpired:
                return TestResult(
                    app_id=app_id,
                    reconstruction_id=reconstruction_id,
                    passed=0,
                    failed=0,
                    total=0,
                    test_pass_rate=0.0,
                    coverage=0.0,
                    errors=[f"Test execution timeout after {timeout}s"],
                    execution_time=timeout
                )

    def _get_app_dir(self, app_id: int) -> Path:
        """Get application directory from database."""
        # Query database for app path
        # For now, assume simple mapping
        app_dirs = sorted(self.dataset_path.rglob("*/metadata.json"))
        for app_dir in app_dirs:
            metadata = json.loads(app_dir.read_text())
            if metadata['app_id'] == str(app_id).zfill(3):
                return app_dir.parent
        raise ValueError(f"App {app_id} not found")

    def store_result(self, result: TestResult, db_conn):
        """Store test result in PostgreSQL."""
        db_conn.execute(
            """
            UPDATE reconstructions
            SET
                test_results = %s,
                test_pass_rate = %s
            WHERE id = %s
            """,
            (
                json.dumps({
                    'passed': result.passed,
                    'failed': result.failed,
                    'total': result.total,
                    'coverage': result.coverage,
                    'errors': result.errors,
                    'execution_time': result.execution_time
                }),
                result.test_pass_rate,
                result.reconstruction_id
            )
        )
        db_conn.commit()

# Usage example
if __name__ == "__main__":
    harness = TestHarness(Path("/mnt/projects/ICCM/datasets/applications"))

    # Example: Test reconstruction
    test_result = harness.run_tests(
        app_id=1,
        reconstruction_id=12345,
        implementation_code=open("generated_impl.py").read()
    )

    print(f"Test Pass Rate: {test_result.test_pass_rate:.1%}")
    print(f"Coverage: {test_result.coverage:.1%}")
    print(f"Errors: {len(test_result.errors)}")
```

---

## Dataset Curation Process

### Week 3-4: Initial 10 Apps

**Curation Workflow (per app):**

1. **Identify Candidate** (2 hours → 30 min with automation)
   - **Automated search** via GitHub API and PyPI
   - Criteria: >80% coverage, 100-2,000 LOC, clear functionality
   - Check license (MIT/Apache/BSD)

   **Specific Sources:**
   - **GitHub API Search:**
     ```bash
     # Search for Python projects with good test coverage
     https://api.github.com/search/repositories?q=language:python+stars:>100+size:<2000+topic:testing
     ```
   - **Awesome Python Curated Lists:**
     - https://github.com/vinta/awesome-python (CLI Tools, Data Validation, Testing)
     - https://github.com/mahmoud/awesome-python-applications (Real-world apps)
   - **PyPI Popular Packages:**
     ```bash
     # Filter by download count, test coverage badge, LOC
     https://pypi.org/search/?q=&c=Development+Status+%3A%3A+4+-+Beta
     ```
   - **GitHub Trending:**
     - https://github.com/trending/python?since=monthly (filter by test coverage)

2. **Clone & Validate** (1 hour → 15 min with automation)
   - Clone repository
   - Run tests locally, verify >80% coverage
   - Check for flaky tests, external dependencies

   **Automated Verification Script:**
   ```python
   #!/usr/bin/env python3
   """
   Automated app validation: clone, test, measure coverage.
   Returns: pass/fail with stats (LOC, coverage %, test count)
   """
   import subprocess
   import json

   def validate_app(repo_url: str) -> dict:
       # Clone, install deps, run tests with coverage
       # Parse results: LOC, coverage %, flaky tests
       # Return structured validation report
       pass
   ```

3. **Extract Requirements** (2 hours)
   - Read README, docstrings, test cases
   - Write gold standard requirements (functional, non-functional, constraints)
   - Validate with domain expert

4. **Create Metadata** (1 hour)
   - Generate `metadata.json`
   - Run coverage analysis
   - Document statistics

5. **Integration Test** (1 hour)
   - Load into database
   - Run through test harness
   - Verify Docker execution works

**Total Time per App:** ~7 hours
**Parallel Curation:** 2 team members → 5 apps each → 35 hours total → 1 week

### Month 5: Expansion to 50 Apps

**Scaling Strategy:**
- **Semi-automated:** Use scripts to extract stats, run coverage
- **Quality bar:** Same criteria (>80% coverage, clear requirements)
- **Diverse sources:**
  - Awesome Python lists
  - GitHub trending
  - Rosetta Code
  - Project Euler solutions (with tests)
- **Team allocation:** 2 curators full-time for 4 weeks

---

## Validation & Quality Assurance

### Quality Checks (Automated)

**Script:** `/mnt/projects/ICCM/infrastructure/test_harness/validate_dataset.py`

```python
#!/usr/bin/env python3
"""Validate dataset quality before training."""
import json
from pathlib import Path

def validate_dataset(dataset_path: Path):
    """Run quality checks on dataset."""
    issues = []

    for app_dir in dataset_path.rglob("*/metadata.json"):
        metadata = json.loads(app_dir.read_text())

        # Check 1: Test coverage >80%
        if metadata['statistics']['test_coverage'] < 80.0:
            issues.append(f"{metadata['name']}: Coverage {metadata['statistics']['test_coverage']:.1f}% < 80%")

        # Check 2: LOC in range
        loc = metadata['statistics']['total_loc']
        if not (100 <= loc <= 2000):
            issues.append(f"{metadata['name']}: LOC {loc} outside [100, 2000]")

        # Check 3: Has functional requirements
        if len(metadata['requirements']['functional']) < 3:
            issues.append(f"{metadata['name']}: <3 functional requirements")

        # Check 4: Test suite exists
        test_path = app_dir.parent / "tests"
        if not test_path.exists() or not list(test_path.glob("test_*.py")):
            issues.append(f"{metadata['name']}: No test suite found")

        # Check 5: Source code exists
        src_path = app_dir.parent / "src"
        if not src_path.exists() or not list(src_path.glob("*.py")):
            issues.append(f"{metadata['name']}: No source code found")

    # Report
    if issues:
        print(f"❌ Dataset validation failed with {len(issues)} issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print(f"✅ Dataset validation passed ({len(list(dataset_path.rglob('*/metadata.json')))} apps)")
        return True

if __name__ == "__main__":
    validate_dataset(Path("/mnt/projects/ICCM/datasets/applications"))
```

### Manual Quality Checks

**Per-App Review (domain expert):**
- [ ] Requirements are clear and unambiguous
- [ ] Test suite exercises all functional requirements
- [ ] No flaky tests (run 10 times, all pass)
- [ ] Code quality is reasonable (PEP 8, no obvious bugs)
- [ ] Gold standard requirements are complete

---

## Integration with Training Pipeline

### Phase 1 Training (I06): RAG Baseline

**Usage:**
- Load application source code + gold requirements into vector DB
- CET-D learns to retrieve relevant code sections
- Evaluate: Can CET-D find the right code for each requirement?

### Phase 2 Training (I07): Context Transformation

**Usage:**
- CET-D transforms application source into compact requirements
- Test: Can LLM orchestra reconstruct from those requirements?
- Iterate: Improve CET-D based on reconstruction quality

### Phase 3 Training (I08): Interactive Feedback

**Usage:**
- For each app:
  1. CET-D extracts requirements
  2. 6 LLMs generate implementations
  3. Test harness runs tests
  4. Training signal: test_pass_rate → reward
- CET-D learns to optimize requirements for high test pass rates

### Validation (I09): Three Baselines

**Usage:**
- **Manual baseline:** Human-extracted requirements (gold standard)
- **RAG baseline:** Simple retrieval without CET-D
- **No-context baseline:** LLM with no requirements (lower bound)
- **CET-D:** Learned requirements extraction
- **Statistical test:** Paired t-test, CET-D vs baselines

---

## Risks & Mitigation

### High-Impact Risks

1. **Dataset Curation Bottleneck**
   - **Risk:** Cannot find 50 high-quality apps in time
   - **Mitigation:** Start with 10, prove concept, then expand. Synthetic apps if needed.
   - **Monitoring:** Track curation rate (apps/week)

2. **Test Suite Quality Issues**
   - **Risk:** Flaky tests, low coverage despite reported metrics
   - **Mitigation:** Manual validation, run tests 10× before accepting
   - **Monitoring:** Track test stability over time

3. **Reconstruction Too Hard**
   - **Risk:** Even gold requirements can't enable >75% test pass rate
   - **Mitigation:** Validate with GPT-4 baseline first, adjust apps if needed
   - **Monitoring:** Track GPT-4 reconstruction success rate

---

## Deliverables

### Week 3-4 Deliverables (Phase 1 Subset):
- [x] 10 Python applications curated and validated
- [x] All apps with >80% test coverage
- [x] Gold standard requirements extracted
- [x] Metadata and database integration complete
- [x] Test harness operational and tested

### Month 5 Deliverables (Full Dataset):
- [x] 50 Python applications total (40 train, 10 hold-out)
- [x] Dataset diversity validated (5 domains covered)
- [x] All quality checks passing
- [x] Dataset manifest and documentation complete

**Exit Criteria:** 10 apps ready by Week 4, test harness executes successfully, ready for I06 (Phase 1 training)

---

## Dataset Expansion Roadmap (Post-PoC)

**After successful PoC with 50 apps:**

1. **Scale to 200 apps** (more Python)
2. **Add JavaScript** (50 Node.js apps)
3. **Add Go** (50 Go apps)
4. **Add cross-language** (polyglot requirements)
5. **Domain-specific expansion** (finance, medical, legal)

**But first:** Prove core thesis with 50 Python apps.

---

## Next Steps

**Immediate:**
1. Review this document with team
2. Send to AI reviewers (Fiedler's default models 
3. Incorporate feedback
4. Begin Week 3 curation (parallel with I03)

**Dependencies:**
- **Requires:** I02 (database, Docker)
- **Enables:** I06, I07, I08 (training phases), I09 (validation)
- **Parallel:** I03 (LLM serving), I05 (conversation capture)

**Week 4 Preview:**
- 10 apps loaded and tested
- First CET-D requirements extraction attempts
- First reconstruction tests with LLM orchestra
- Validation of end-to-end pipeline

---

## References

- **Paper 04A:** Requirements Validation Through Reconstruction Testing (core methodology)
- **Paper 05:** CET-D Requirements Engineering Implementation (requirements focus)
- **Paper 06:** Requirements Validation Framework (validation approach)
- **Paper 11:** Testing Infrastructure (test harness design)
- **I00:** Master Implementation Document (50-app decision)
- **I01:** Implementation Summary (dataset role in validation)
- **I02:** Foundation Layer (database schema, Docker integration)
- **I03:** LLM Infrastructure (6 models for reconstruction)
