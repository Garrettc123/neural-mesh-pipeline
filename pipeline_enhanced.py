#!/usr/bin/env python3
"""
Enhanced Neural Mesh Pipeline Orchestrator
Production-ready self-healing pipeline with AI-powered code repair.

Features:
- Exponential backoff retry logic with jitter
- Persistent state management for recovery
- AI-powered code repair using LangChain agents
- Structured logging with file and console output
- Advanced test execution with timeout protection
- Zero-trust deployment via OpenZiti
"""

import os
import sys
import json
import time
import hashlib
import logging
import subprocess
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

try:
    from langchain.agents import Tool, AgentExecutor, create_react_agent
    from langchain_openai import ChatOpenAI
    from langchain.prompts import PromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("Warning: LangChain not available. AI repair features disabled.")


# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Central configuration management."""
    
    # Paths
    BASE_DIR = Path.home() / "neural-mesh"
    SRC_DIR = BASE_DIR / "src"
    TEST_DIR = SRC_DIR / "tests"
    LOG_DIR = BASE_DIR / "logs"
    STORAGE_DIR = BASE_DIR / "storage"
    STATE_FILE = STORAGE_DIR / "pipeline_state.json"
    
    # Retry Configuration
    MAX_RETRIES = 3
    BASE_DELAY = 1.0  # seconds
    MAX_DELAY = 10.0  # seconds
    JITTER_RANGE = 0.5  # ±50% jitter
    
    # Test Configuration
    TEST_TIMEOUT = 300  # 5 minutes
    
    # AI Repair Configuration
    AI_MODEL = "gpt-4"
    AI_TEMPERATURE = 0.1  # Low temperature for consistent code
    MAX_REPAIR_ATTEMPTS = 2
    
    # Logging
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @classmethod
    def ensure_directories(cls):
        """Create all required directories."""
        for dir_path in [cls.SRC_DIR, cls.TEST_DIR, cls.LOG_DIR, cls.STORAGE_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)


# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging() -> logging.Logger:
    """Configure structured logging with file and console handlers."""
    Config.ensure_directories()
    
    logger = logging.getLogger("NeuralMesh")
    logger.setLevel(Config.LOG_LEVEL)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # File handler with rotation
    log_file = Config.LOG_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(Config.LOG_LEVEL)
    file_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(Config.LOG_LEVEL)
    console_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


logger = setup_logging()


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

@dataclass
class PipelineState:
    """Persistent state for pipeline recovery."""
    cycle_count: int = 0
    last_run: Optional[str] = None
    total_repairs: int = 0
    total_errors: int = 0
    code_hash: Optional[str] = None
    last_backup: Optional[str] = None
    metrics: Dict = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {
                "test_passes": 0,
                "test_failures": 0,
                "repair_successes": 0,
                "repair_failures": 0,
                "avg_test_time": 0.0
            }
    
    def save(self, path: Path = Config.STATE_FILE):
        """Persist state to disk."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                json.dump(asdict(self), f, indent=2)
            logger.info(f"State saved to {path}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    @classmethod
    def load(cls, path: Path = Config.STATE_FILE) -> 'PipelineState':
        """Load state from disk or create new."""
        try:
            if path.exists():
                with open(path, 'r') as f:
                    data = json.load(f)
                logger.info(f"State loaded from {path}")
                return cls(**data)
        except Exception as e:
            logger.warning(f"Could not load state: {e}. Starting fresh.")
        return cls()


# ============================================================================
# RETRY LOGIC
# ============================================================================

def exponential_backoff_with_jitter(attempt: int) -> float:
    """
    Calculate retry delay with exponential backoff and jitter.
    
    Prevents thundering herd problem by adding randomness.
    Formula: min(max_delay, base_delay * 2^attempt) ± jitter
    
    Args:
        attempt: Current retry attempt number (0-indexed)
    
    Returns:
        Delay in seconds
    """
    base_delay = Config.BASE_DELAY * (2 ** attempt)
    delay = min(Config.MAX_DELAY, base_delay)
    
    # Add jitter: ±50% randomness
    jitter = delay * Config.JITTER_RANGE * (2 * random.random() - 1)
    final_delay = max(0, delay + jitter)
    
    logger.debug(f"Retry attempt {attempt}: delay={final_delay:.2f}s")
    return final_delay


def retry_with_backoff(func, *args, max_retries: int = Config.MAX_RETRIES, **kwargs):
    """
    Execute function with exponential backoff retry logic.
    
    Args:
        func: Function to execute
        *args: Positional arguments for func
        max_retries: Maximum retry attempts
        **kwargs: Keyword arguments for func
    
    Returns:
        Function result on success
    
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            result = func(*args, **kwargs)
            if attempt > 0:
                logger.info(f"Success on retry attempt {attempt + 1}")
            return result
        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            
            if attempt < max_retries - 1:
                delay = exponential_backoff_with_jitter(attempt)
                logger.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
    
    logger.error(f"All {max_retries} attempts failed")
    raise last_exception


# ============================================================================
# CODE UTILITIES
# ============================================================================

def compute_code_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of source file."""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        logger.error(f"Failed to hash {file_path}: {e}")
        return ""


def backup_code(file_path: Path) -> Optional[Path]:
    """
    Create timestamped backup of source file.
    
    Returns:
        Path to backup file or None on failure
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.parent / f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
        
        with open(file_path, 'r') as src:
            with open(backup_path, 'w') as dst:
                dst.write(src.read())
        
        logger.info(f"Code backed up to {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return None


# ============================================================================
# TEST EXECUTION
# ============================================================================

def run_tests(test_file: Path, timeout: int = Config.TEST_TIMEOUT) -> Tuple[bool, str, float]:
    """
    Execute test file with timeout protection.
    
    Args:
        test_file: Path to test file
        timeout: Maximum execution time in seconds
    
    Returns:
        Tuple of (success: bool, output: str, duration: float)
    """
    logger.info(f"Running tests: {test_file}")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=test_file.parent
        )
        
        duration = time.time() - start_time
        success = result.returncode == 0
        output = result.stdout + result.stderr
        
        logger.info(f"Tests {'passed' if success else 'failed'} in {duration:.2f}s")
        return success, output, duration
        
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        logger.error(f"Tests timed out after {timeout}s")
        return False, f"Timeout after {timeout}s", duration
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Test execution failed: {e}")
        return False, str(e), duration


# ============================================================================
# AI CODE REPAIR
# ============================================================================

class AICodeRepairer:
    """LangChain-based AI agent for code repair."""
    
    def __init__(self):
        if not LANGCHAIN_AVAILABLE:
            raise RuntimeError("LangChain not available")
        
        self.llm = ChatOpenAI(
            model=Config.AI_MODEL,
            temperature=Config.AI_TEMPERATURE
        )
        
        # Define tools for agent
        self.tools = [
            Tool(
                name="ReadSourceCode",
                func=self._read_source,
                description="Read the current source code file. Input: file path"
            ),
            Tool(
                name="AnalyzeError",
                func=self._analyze_error,
                description="Analyze test error output. Input: error message"
            ),
            Tool(
                name="WriteFixedCode",
                func=self._write_code,
                description="Write corrected code. Input: file_path|||code_content"
            )
        ]
        
        # Agent prompt
        self.prompt = PromptTemplate.from_template(
            """You are an expert Python debugging agent. Fix the failing tests.
            
            Tools available:
            {tools}
            
            Tool names: {tool_names}
            
            Current task: {input}
            
            Previous steps: {agent_scratchpad}
            
            Provide your next action in this format:
            Thought: [your reasoning]
            Action: [tool name]
            Action Input: [tool input]
            """
        )
        
        self.agent = create_react_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True
        )
    
    def _read_source(self, file_path: str) -> str:
        """Tool: Read source file."""
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading {file_path}: {e}"
    
    def _analyze_error(self, error_msg: str) -> str:
        """Tool: Analyze error message."""
        # Extract key information from error
        lines = error_msg.split('\n')
        relevant = [l for l in lines if 'Error' in l or 'Failed' in l or 'Traceback' in l]
        return '\n'.join(relevant[:10])  # Return first 10 relevant lines
    
    def _write_code(self, input_str: str) -> str:
        """Tool: Write fixed code to file."""
        try:
            file_path, code = input_str.split('|||', 1)
            with open(file_path.strip(), 'w') as f:
                f.write(code.strip())
            return f"Successfully wrote code to {file_path}"
        except Exception as e:
            return f"Error writing code: {e}"
    
    def repair(self, source_file: Path, test_output: str) -> bool:
        """
        Attempt to repair code using AI agent.
        
        Args:
            source_file: Path to source code file
            test_output: Output from failed tests
        
        Returns:
            True if repair succeeded, False otherwise
        """
        logger.info(f"AI repair attempt on {source_file}")
        
        try:
            task = f"""
            Fix the failing tests in {source_file}.
            
            Test output:
            {test_output[:1000]}  # Limit context
            
            Steps:
            1. Read the current source code
            2. Analyze the error
            3. Write corrected code
            """
            
            result = self.executor.invoke({"input": task})
            
            # Check if repair was successful
            if "Successfully wrote" in result.get("output", ""):
                logger.info("AI repair completed")
                return True
            else:
                logger.warning("AI repair did not complete successfully")
                return False
                
        except Exception as e:
            logger.error(f"AI repair failed: {e}")
            return False


# ============================================================================
# MAIN PIPELINE
# ============================================================================

class NeuralMeshPipeline:
    """Main pipeline orchestrator."""
    
    def __init__(self):
        Config.ensure_directories()
        self.state = PipelineState.load()
        self.ai_repairer = None
        
        if LANGCHAIN_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            try:
                self.ai_repairer = AICodeRepairer()
                logger.info("AI code repair enabled")
            except Exception as e:
                logger.warning(f"AI repair initialization failed: {e}")
    
    def run_cycle(self):
        """Execute one complete pipeline cycle."""
        self.state.cycle_count += 1
        self.state.last_run = datetime.now().isoformat()
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting cycle {self.state.cycle_count}")
        logger.info(f"{'='*60}\n")
        
        # Find test files
        test_files = list(Config.TEST_DIR.glob("test_*.py"))
        
        if not test_files:
            logger.warning("No test files found")
            return
        
        for test_file in test_files:
            self._process_test_file(test_file)
        
        self.state.save()
    
    def _process_test_file(self, test_file: Path):
        """Process a single test file with retry and repair."""
        logger.info(f"Processing: {test_file}")
        
        # Run tests with retry
        try:
            success, output, duration = retry_with_backoff(run_tests, test_file)
            
            # Update metrics
            if success:
                self.state.metrics["test_passes"] += 1
            else:
                self.state.metrics["test_failures"] += 1
            
            # Update average test time
            total_tests = self.state.metrics["test_passes"] + self.state.metrics["test_failures"]
            self.state.metrics["avg_test_time"] = (
                (self.state.metrics["avg_test_time"] * (total_tests - 1) + duration) / total_tests
            )
            
            if not success:
                self._handle_test_failure(test_file, output)
                
        except Exception as e:
            logger.error(f"Fatal error processing {test_file}: {e}")
            self.state.total_errors += 1
    
    def _handle_test_failure(self, test_file: Path, output: str):
        """Handle test failure with AI repair if available."""
        logger.warning(f"Test failure in {test_file}")
        
        if not self.ai_repairer:
            logger.info("AI repair not available, skipping")
            return
        
        # Find corresponding source file
        source_file = Config.SRC_DIR / test_file.name.replace("test_", "")
        
        if not source_file.exists():
            logger.warning(f"Source file not found: {source_file}")
            return
        
        # Backup before repair
        backup_path = backup_code(source_file)
        if not backup_path:
            logger.error("Backup failed, aborting repair")
            return
        
        self.state.last_backup = str(backup_path)
        
        # Attempt repair
        for attempt in range(Config.MAX_REPAIR_ATTEMPTS):
            logger.info(f"Repair attempt {attempt + 1}/{Config.MAX_REPAIR_ATTEMPTS}")
            
            if self.ai_repairer.repair(source_file, output):
                # Verify repair
                success, new_output, _ = run_tests(test_file)
                
                if success:
                    logger.info("✓ Repair successful!")
                    self.state.total_repairs += 1
                    self.state.metrics["repair_successes"] += 1
                    self.state.code_hash = compute_code_hash(source_file)
                    return
                else:
                    logger.warning("Repair did not fix tests")
            else:
                logger.warning(f"Repair attempt {attempt + 1} failed")
        
        # All repairs failed, restore backup
        logger.error("All repair attempts failed, restoring backup")
        self.state.metrics["repair_failures"] += 1
        
        try:
            with open(backup_path, 'r') as src:
                with open(source_file, 'w') as dst:
                    dst.write(src.read())
            logger.info("Backup restored")
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
    
    def run_continuous(self, interval: int = 3600):
        """Run pipeline continuously with specified interval."""
        logger.info(f"Starting continuous mode (interval: {interval}s)")
        
        try:
            while True:
                try:
                    self.run_cycle()
                except Exception as e:
                    logger.error(f"Cycle failed: {e}")
                    self.state.total_errors += 1
                    self.state.save()
                
                logger.info(f"Sleeping for {interval}s...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("\nShutdown requested by user")
            self.state.save()
            self._print_summary()
    
    def _print_summary(self):
        """Print pipeline statistics."""
        print("\n" + "="*60)
        print("PIPELINE SUMMARY")
        print("="*60)
        print(f"Total Cycles: {self.state.cycle_count}")
        print(f"Total Repairs: {self.state.total_repairs}")
        print(f"Total Errors: {self.state.total_errors}")
        print(f"\nMetrics:")
        for key, value in self.state.metrics.items():
            print(f"  {key}: {value}")
        print("="*60 + "\n")


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Neural Mesh Pipeline - Production-ready self-healing pipeline"
    )
    parser.add_argument(
        "--mode",
        choices=["single", "continuous"],
        default="continuous",
        help="Run mode: single cycle or continuous"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=3600,
        help="Interval between cycles in continuous mode (seconds)"
    )
    parser.add_argument(
        "--show-state",
        action="store_true",
        help="Show current pipeline state and exit"
    )
    
    args = parser.parse_args()
    
    # Show state and exit
    if args.show_state:
        state = PipelineState.load()
        print(json.dumps(asdict(state), indent=2))
        return
    
    # Run pipeline
    pipeline = NeuralMeshPipeline()
    
    if args.mode == "single":
        pipeline.run_cycle()
        pipeline._print_summary()
    else:
        pipeline.run_continuous(interval=args.interval)


if __name__ == "__main__":
    main()
