"""
=============================================================================
PHASE 10 — PIPELINE AUTOMATION & ORCHESTRATION
=============================================================================
Script:   07_automation_pipeline.py
Purpose:  Orchestrate the complete ETL + Analytics pipeline end-to-end.
Usage:    python 07_automation_pipeline.py --full
          python 07_automation_pipeline.py --phase 1
=============================================================================
"""

import os
import sys
import time
import subprocess
import argparse
import logging
from datetime import datetime

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "outputs", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# Pipeline phases
PIPELINE_PHASES = {
    1: ("01_data_understanding.py", "Data Understanding & Profiling"),
    2: ("02_etl_pipeline.py", "ETL Pipeline (Extract, Transform, Load)"),
    3: ("03_eda_analysis.py", "Exploratory Data Analysis"),
    4: ("04_feature_engineering.py", "Feature Engineering & RFM"),
    5: ("05_kpi_dashboard.py", "KPI Generation & Visualizations"),
    6: ("06_advanced_analytics.py", "Advanced Analytics & ML"),
}

# Logging
log_path = os.path.join(PROJECT_ROOT, "outputs", "logs", "pipeline_run.log")
os.makedirs(os.path.dirname(log_path), exist_ok=True)

# Fix Windows console encoding for Unicode characters
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[
        logging.FileHandler(log_path, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("PipelineOrchestrator")


def run_phase(phase_num, script_name, description, max_retries=2):
    """Run a single pipeline phase with retry logic."""
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    
    if not os.path.exists(script_path):
        logger.warning(f"[WARN] Script not found: {script_path} -- SKIPPING")
        return False, 0, "Script not found"
    
    for attempt in range(1, max_retries + 1):
        logger.info(f"\n{'='*70}")
        logger.info(f"  PHASE {phase_num}: {description}")
        logger.info(f"  Script: {script_name} | Attempt: {attempt}/{max_retries}")
        logger.info(f"{'='*70}")
        
        start = time.time()
        try:
            result = subprocess.run(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=600,  # 10 minute timeout per phase
                cwd=SCRIPTS_DIR,
            )
            # Decode output safely
            stdout_text = (result.stdout or b"").decode('utf-8', errors='replace')
            stderr_text = (result.stderr or b"").decode('utf-8', errors='replace')
            elapsed = time.time() - start
            
            if result.returncode == 0:
                logger.info(f"[OK] Phase {phase_num} completed in {elapsed:.1f}s")
                # Log last 5 lines of stdout
                stdout_lines = stdout_text.strip().split('\n')
                for line in stdout_lines[-5:]:
                    logger.info(f"  | {line}")
                return True, elapsed, "Success"
            else:
                logger.error(f"[FAIL] Phase {phase_num} failed (exit code {result.returncode})")
                if stderr_text:
                    # Log last 10 lines of stderr
                    for line in stderr_text.strip().split('\n')[-10:]:
                        logger.error(f"  | {line}")
                if attempt < max_retries:
                    logger.info(f"  Retrying in 5 seconds...")
                    time.sleep(5)
                    
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start
            logger.error(f"[TIMEOUT] Phase {phase_num} timed out after {elapsed:.0f}s")
            if attempt < max_retries:
                logger.info("  Retrying...")
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"[ERROR] Phase {phase_num} error: {e}")
            if attempt < max_retries:
                logger.info("  Retrying...")
    
    return False, elapsed, "Failed after retries"


def generate_report(results, total_time):
    """Generate a final pipeline execution report."""
    report_path = os.path.join(REPORTS_DIR, "pipeline_report.txt")
    
    lines = []
    lines.append("=" * 80)
    lines.append("  E-COMMERCE DATA PIPELINE — EXECUTION REPORT")
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)
    lines.append("")
    
    # Phase results table
    lines.append(f"  {'Phase':<8} {'Status':<10} {'Time (s)':<10} {'Script':<35} {'Description'}")
    lines.append(f"  {'-'*8} {'-'*10} {'-'*10} {'-'*35} {'-'*30}")
    
    passed = 0
    failed = 0
    for phase_num, (success, elapsed, msg) in results.items():
        status = "[PASS]" if success else "[FAIL]"
        script = PIPELINE_PHASES[phase_num][0]
        desc = PIPELINE_PHASES[phase_num][1]
        lines.append(f"  {phase_num:<8} {status:<10} {elapsed:<10.1f} {script:<35} {desc}")
        if success:
            passed += 1
        else:
            failed += 1
    
    lines.append("")
    lines.append(f"  Total Phases: {len(results)} | Passed: {passed} | Failed: {failed}")
    lines.append(f"  Total Execution Time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    lines.append("")
    
    # Output inventory
    lines.append("  OUTPUT INVENTORY:")
    lines.append("  " + "-" * 70)
    
    output_dirs = [
        ("Data — Cleaned", os.path.join(PROJECT_ROOT, "data", "cleaned")),
        ("Data — Dashboard Ready", os.path.join(PROJECT_ROOT, "data", "dashboard_ready")),
        ("Charts", os.path.join(PROJECT_ROOT, "outputs", "charts")),
        ("KPIs", os.path.join(PROJECT_ROOT, "outputs", "kpis")),
        ("Reports", os.path.join(PROJECT_ROOT, "outputs", "reports")),
        ("Logs", os.path.join(PROJECT_ROOT, "outputs", "logs")),
    ]
    
    for label, dir_path in output_dirs:
        if os.path.exists(dir_path):
            files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
            total_size = sum(os.path.getsize(os.path.join(dir_path, f)) for f in files)
            lines.append(f"    {label:<25}: {len(files):>3} files ({total_size/1024:.0f} KB)")
        else:
            lines.append(f"    {label:<25}: Directory not found")
    
    lines.append("")
    lines.append("=" * 80)
    lines.append("  END OF PIPELINE REPORT")
    lines.append("=" * 80)
    
    report_text = "\n".join(lines)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    
    print("\n" + report_text)
    logger.info(f"\n[OK] Pipeline report saved to: {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description="E-Commerce Data Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python 07_automation_pipeline.py --full          Run all phases
  python 07_automation_pipeline.py --phase 1       Run phase 1 only
  python 07_automation_pipeline.py --phase 3 4 5   Run phases 3, 4, 5
        """
    )
    parser.add_argument("--full", action="store_true", help="Run all pipeline phases")
    parser.add_argument("--phase", nargs="+", type=int, help="Run specific phase(s)")
    parser.add_argument("--retries", type=int, default=2, help="Max retries per phase (default: 2)")
    
    args = parser.parse_args()
    
    if not args.full and not args.phase:
        # Default to full run
        args.full = True
    
    # Determine phases to run
    if args.full:
        phases_to_run = sorted(PIPELINE_PHASES.keys())
    else:
        phases_to_run = sorted(set(args.phase))
        invalid = [p for p in phases_to_run if p not in PIPELINE_PHASES]
        if invalid:
            logger.error(f"Invalid phase numbers: {invalid}. Valid: {list(PIPELINE_PHASES.keys())}")
            sys.exit(1)
    
    logger.info("=" * 66)
    logger.info("  E-COMMERCE DATA PIPELINE -- STARTING EXECUTION")
    logger.info(f"  Phases to run: {phases_to_run}")
    logger.info(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 66)
    
    total_start = time.time()
    results = {}
    
    for phase_num in phases_to_run:
        script_name, description = PIPELINE_PHASES[phase_num]
        success, elapsed, msg = run_phase(phase_num, script_name, description, args.retries)
        results[phase_num] = (success, elapsed, msg)
        
        if not success:
            logger.warning(f"Phase {phase_num} failed — continuing with next phase")
    
    total_time = time.time() - total_start
    
    # Generate report
    generate_report(results, total_time)
    
    # Exit code
    all_passed = all(s for s, _, _ in results.values())
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
