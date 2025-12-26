# Neural Mesh Pipeline - Implementation Guide

## Overview

This guide provides comprehensive documentation for implementing and extending the Neural Mesh Pipeline in Termux.

## Architecture

### Core Components

1. **Configuration Management** (`Config` class)
   - Centralized settings
   - Path management
   - Retry parameters
   - AI model configuration

2. **State Persistence** (`PipelineState` class)
   - Cycle tracking
   - Metrics collection
   - Recovery points
   - JSON serialization

3. **Retry Logic** (Exponential Backoff)
   - Prevents thundering herd
   - Configurable delays
   - Jitter for randomness

4. **Test Execution**
   - Subprocess isolation
   - Timeout protection
   - Output capture

5. **AI Code Repair** (`AICodeRepairer` class)
   - LangChain agent
   - Tool-based architecture
   - Error analysis
   - Code generation

6. **Pipeline Orchestrator** (`NeuralMeshPipeline` class)
   - Cycle management
   - Test processing
   - Failure handling
   - Continuous operation

## Key Patterns

### Exponential Backoff with Jitter

```python
def exponential_backoff_with_jitter(attempt: int) -> float:
    base_delay = Config.BASE_DELAY * (2 ** attempt)
    delay = min(Config.MAX_DELAY, base_delay)
    jitter = delay * Config.JITTER_RANGE * (2 * random.random() - 1)
    return max(0, delay + jitter)
```

**When to use:**
- Network requests
- External API calls
- Resource contention scenarios

**Benefits:**
- Prevents synchronized retries
- Reduces server load
- Improves overall system stability

### State Persistence Pattern

```python
# Save state
self.state.cycle_count += 1
self.state.save()

# Load state on restart
state = PipelineState.load()
print(f"Resuming from cycle {state.cycle_count}")
```

**Use cases:**
- Recovery from crashes
- Audit trails
- Performance tracking
- Long-running processes

### AI Agent Integration

The pipeline uses LangChain's ReAct agent pattern:

```python
tools = [
    Tool(name="ReadSourceCode", func=read_func, description="..."),
    Tool(name="AnalyzeError", func=analyze_func, description="..."),
    Tool(name="WriteFixedCode", func=write_func, description="...")
]

agent = create_react_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
```

## Configuration

### Environment Variables

Create a `.env` file in `~/neural-mesh/`:

```bash
# Required for AI repair
OPENAI_API_KEY=sk-your-key-here

# Optional: Override defaults
AI_MODEL=gpt-4
AI_TEMPERATURE=0.1
MAX_RETRIES=3
TEST_TIMEOUT=300
```

Load in code:

```python
from dotenv import load_dotenv
load_dotenv()
```

### Custom Configuration

Extend the `Config` class:

```python
class Config:
    # Add custom settings
    SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
    EMAIL_ALERTS = os.getenv("EMAIL_ALERTS", "false").lower() == "true"
    
    # Custom paths
    CUSTOM_DIR = BASE_DIR / "custom"
```

## Extending the Pipeline

### Adding New Test Types

```python
def run_integration_tests(self):
    """Run integration tests separately."""
    test_files = Config.TEST_DIR.glob("integration_*.py")
    for test_file in test_files:
        self._process_test_file(test_file)
```

### Custom AI Tools

Add tools to the AI agent:

```python
Tool(
    name="CheckDependencies",
    func=lambda x: subprocess.check_output(["pip", "list"]).decode(),
    description="Check installed Python packages"
)
```

### Notification Integration

```python
def notify_failure(self, test_file: Path, error: str):
    """Send notification on test failure."""
    if Config.SLACK_WEBHOOK:
        requests.post(Config.SLACK_WEBHOOK, json={
            "text": f"Test failed: {test_file}\n{error[:200]}"
        })
```

### Metrics Export

```python
def export_metrics(self, format: str = "json"):
    """Export metrics to file."""
    metrics_file = Config.LOG_DIR / f"metrics_{datetime.now():%Y%m%d}.{format}"
    
    if format == "json":
        with open(metrics_file, 'w') as f:
            json.dump(self.state.metrics, f, indent=2)
    elif format == "csv":
        # Export to CSV
        pass
```

## Integration Examples

### With OpenZiti

```python
import openziti

class SecurePipeline(NeuralMeshPipeline):
    def __init__(self, ziti_config: str):
        super().__init__()
        self.ziti = openziti.load(ziti_config)
    
    def deploy_to_mesh(self, artifact: Path):
        """Deploy via zero-trust network."""
        with self.ziti.connect("deployment-service") as conn:
            conn.send_file(artifact)
```

### With CI/CD

```yaml
# .github/workflows/neural-mesh.yml
name: Neural Mesh Pipeline

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours

jobs:
  run-pipeline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements-termux.txt
      - name: Run pipeline
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: python pipeline_enhanced.py --mode single
      - name: Upload logs
        uses: actions/upload-artifact@v3
        with:
          name: pipeline-logs
          path: logs/
```

### With Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements-termux.txt .
RUN pip install --no-cache-dir -r requirements-termux.txt

COPY pipeline_enhanced.py .
COPY src/ ./src/

CMD ["python", "pipeline_enhanced.py", "--mode", "continuous"]
```

## Best Practices

### Error Handling

```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Specific error: {e}")
    # Handle specifically
except Exception as e:
    logger.exception("Unexpected error")  # Logs stack trace
    # Generic fallback
finally:
    cleanup()
```

### Logging

```python
# Structured logging
logger.info("Test started", extra={
    "test_file": test_file,
    "cycle": self.state.cycle_count
})

# Use appropriate levels
logger.debug("Detailed info for debugging")
logger.info("Normal operation info")
logger.warning("Recoverable issue")
logger.error("Error requiring attention")
logger.critical("System failure")
```

### Resource Management

```python
# Use context managers
with open(file_path, 'r') as f:
    data = f.read()

# Clean up temporary files
import tempfile
with tempfile.TemporaryDirectory() as tmpdir:
    # Work with temporary files
    pass  # Automatically cleaned up
```

### Testing

```python
import pytest

def test_exponential_backoff():
    """Test retry logic."""
    delay = exponential_backoff_with_jitter(attempt=0)
    assert 0 <= delay <= Config.BASE_DELAY * 1.5

def test_state_persistence(tmp_path):
    """Test state save/load."""
    state = PipelineState(cycle_count=5)
    state_file = tmp_path / "state.json"
    state.save(state_file)
    
    loaded = PipelineState.load(state_file)
    assert loaded.cycle_count == 5
```

## Performance Optimization

### Parallel Test Execution

```python
from concurrent.futures import ThreadPoolExecutor

def run_tests_parallel(self, test_files: List[Path]):
    """Run tests in parallel."""
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(self._process_test_file, tf) for tf in test_files]
        results = [f.result() for f in futures]
    return results
```

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_analysis(code: str) -> Dict:
    """Cache expensive operations."""
    # Perform analysis
    return result
```

## Security Considerations

1. **Never commit API keys** - Use environment variables
2. **Validate file paths** - Prevent directory traversal
3. **Sanitize inputs** - Especially for AI-generated code
4. **Use secure connections** - HTTPS, TLS for external services
5. **Implement rate limiting** - Prevent abuse of AI APIs

## Troubleshooting

See `TROUBLESHOOTING.md` for common issues and solutions.

## Further Reading

- [LangChain Documentation](https://python.langchain.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Python Logging Guide](https://docs.python.org/3/howto/logging.html)
- [Termux Wiki](https://wiki.termux.com/)
