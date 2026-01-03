#!/usr/bin/env python3
"""
Health Check Script for Neural Mesh Pipeline
Verifies deployment status and reports any issues.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header():
    print(f"\n{Colors.BOLD}{'='*50}")
    print("Neural Mesh Pipeline - Health Check")
    print(f"{'='*50}{Colors.END}\n")

def check_status(name, condition, details=""):
    status = f"{Colors.GREEN}✓ OK{Colors.END}" if condition else f"{Colors.RED}✗ FAIL{Colors.END}"
    print(f"  {name}: {status}")
    if details:
        print(f"    {details}")
    return condition

def main():
    print_header()
    
    all_checks_passed = True
    
    # Check 1: Python version
    print(f"{Colors.BLUE}1. System Requirements{Colors.END}")
    python_version = sys.version_info
    python_ok = python_version >= (3, 8)
    all_checks_passed &= check_status(
        "Python Version",
        python_ok,
        f"Version: {python_version.major}.{python_version.minor}.{python_version.micro}"
    )
    
    # Check 2: Required directories
    print(f"\n{Colors.BLUE}2. Directory Structure{Colors.END}")
    base_dir = Path.home() / "neural-mesh"
    required_dirs = [
        base_dir,
        base_dir / "src",
        base_dir / "src" / "tests",
        base_dir / "logs",
        base_dir / "storage"
    ]
    
    dirs_ok = True
    for directory in required_dirs:
        exists = directory.exists()
        dirs_ok &= exists
        check_status(str(directory), exists)
    all_checks_passed &= dirs_ok
    
    # Check 3: Required files
    print(f"\n{Colors.BLUE}3. Required Files{Colors.END}")
    required_files = [
        base_dir / "pipeline_enhanced.py",
        base_dir / "requirements-termux.txt"
    ]
    
    files_ok = True
    for file_path in required_files:
        exists = file_path.exists()
        files_ok &= exists
        check_status(str(file_path), exists)
    all_checks_passed &= files_ok
    
    # Check 4: Environment configuration
    print(f"\n{Colors.BLUE}4. Environment Configuration{Colors.END}")
    api_key = os.getenv("OPENAI_API_KEY")
    api_key_ok = api_key is not None and api_key.startswith("sk-")
    all_checks_passed &= check_status(
        "OPENAI_API_KEY",
        api_key_ok,
        "Set" if api_key_ok else "Not set or invalid"
    )
    
    # Check 5: Pipeline state
    print(f"\n{Colors.BLUE}5. Pipeline State{Colors.END}")
    state_file = base_dir / "storage" / "pipeline_state.json"
    
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            check_status("State File", True, "Found and readable")
            
            # Check last run time
            if "last_run" in state:
                last_run = datetime.fromisoformat(state["last_run"])
                time_since = datetime.now() - last_run
                recent = time_since < timedelta(hours=24)
                check_status(
                    "Last Run",
                    recent,
                    f"{time_since.total_seconds() / 3600:.1f} hours ago"
                )
            
            # Check metrics
            if "metrics" in state:
                metrics = state["metrics"]
                print(f"\n    {Colors.BOLD}Metrics:{Colors.END}")
                print(f"      Cycle count: {state.get('cycle_count', 0)}")
                print(f"      Test passes: {metrics.get('test_passes', 0)}")
                print(f"      Test failures: {metrics.get('test_failures', 0)}")
                print(f"      Repair successes: {metrics.get('repair_successes', 0)}")
                print(f"      Repair failures: {metrics.get('repair_failures', 0)}")
        except json.JSONDecodeError:
            all_checks_passed &= check_status("State File", False, "Corrupted JSON")
        except Exception as e:
            all_checks_passed &= check_status("State File", False, str(e))
    else:
        check_status("State File", False, "Not found (pipeline not run yet)")
    
    # Check 6: Dependencies
    print(f"\n{Colors.BLUE}6. Python Dependencies{Colors.END}")
    try:
        import langchain
        check_status("langchain", True)
    except ImportError:
        all_checks_passed &= check_status("langchain", False, "Not installed")
    
    try:
        from langchain_openai import ChatOpenAI
        check_status("langchain_openai", True)
    except ImportError:
        all_checks_passed &= check_status("langchain_openai", False, "Not installed")
    
    # Check 7: Logs
    print(f"\n{Colors.BLUE}7. Logs{Colors.END}")
    log_dir = base_dir / "logs"
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log"))
        check_status(
            "Log Files",
            len(log_files) > 0,
            f"{len(log_files)} log file(s) found"
        )
        
        # Check for recent errors
        if log_files:
            latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
            print(f"    Latest log: {latest_log.name}")
    else:
        check_status("Log Directory", False, "Directory not found")
    
    # Summary
    print(f"\n{Colors.BOLD}{'='*50}")
    if all_checks_passed:
        print(f"{Colors.GREEN}✓ All checks passed!{Colors.END}")
        print(f"{'='*50}{Colors.END}\n")
        return 0
    else:
        print(f"{Colors.YELLOW}⚠ Some checks failed{Colors.END}")
        print(f"{'='*50}{Colors.END}\n")
        print("Please fix the issues above before running the pipeline.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
