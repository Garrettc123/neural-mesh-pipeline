# Neural Mesh Pipeline - Quick Reference

## Installation

```bash
# One-time setup
pkg update && pkg upgrade -y
pkg install python python-pip -y
termux-setup-storage
mkdir -p ~/neural-mesh/{src/tests,logs,storage}
cd ~/neural-mesh
pip install -r requirements-termux.txt
```

## Configuration

```bash
# Set API key
export OPENAI_API_KEY="sk-your-key"

# Or create .env file
cat > .env << EOF
OPENAI_API_KEY=sk-your-key
AI_MODEL=gpt-4
EOF
```

## Running

```bash
# Single cycle
python pipeline_enhanced.py --mode single

# Continuous (default)
python pipeline_enhanced.py

# Continuous with custom interval (seconds)
python pipeline_enhanced.py --interval 1800  # 30 min

# Show current state
python pipeline_enhanced.py --show-state
```

## File Structure

```
~/neural-mesh/
├── pipeline_enhanced.py      # Main orchestrator
├── requirements-termux.txt   # Dependencies
├── .env                      # Environment vars (create this)
├── src/                      # Source code
│   ├── tests/               # Test files (test_*.py)
│   └── *.py                 # Your modules
├── logs/                    # Log files
│   └── pipeline_YYYYMMDD.log
└── storage/                 # Persistent state
    └── pipeline_state.json
```

## Common Commands

```bash
# View logs
tail -f ~/neural-mesh/logs/pipeline_*.log

# Check state
cat ~/neural-mesh/storage/pipeline_state.json | python -m json.tool

# Find backups
ls ~/neural-mesh/src/*_backup_*

# Clean old logs (>7 days)
find ~/neural-mesh/logs -name '*.log' -mtime +7 -delete

# Test single file
python ~/neural-mesh/src/tests/test_example.py
```

## Key Configuration Parameters

```python
# In pipeline_enhanced.py > Config class

MAX_RETRIES = 3              # Retry attempts
BASE_DELAY = 1.0             # Initial retry delay (seconds)
MAX_DELAY = 10.0             # Max retry delay
TEST_TIMEOUT = 300           # Test timeout (5 min)
AI_MODEL = "gpt-4"           # OpenAI model
MAX_REPAIR_ATTEMPTS = 2      # AI repair attempts
```

## State File Format

```json
{
  "cycle_count": 5,
  "last_run": "2024-12-26T10:30:00",
  "total_repairs": 2,
  "total_errors": 0,
  "code_hash": "abc123...",
  "last_backup": "/path/to/backup.py",
  "metrics": {
    "test_passes": 10,
    "test_failures": 2,
    "repair_successes": 2,
    "repair_failures": 0,
    "avg_test_time": 1.5
  }
}
```

## Troubleshooting Quick Fixes

```bash
# Module not found
pip install langchain langchain-openai openai

# Permission denied
termux-setup-storage
chmod +x pipeline_enhanced.py

# API key error
export OPENAI_API_KEY="sk-your-key"
echo $OPENAI_API_KEY  # Verify

# Corrupted state
mv ~/neural-mesh/storage/pipeline_state.json{,.bak}

# Clear everything
rm -rf ~/neural-mesh && mkdir -p ~/neural-mesh/{src/tests,logs,storage}
```

## Monitoring

```bash
# Watch logs in real-time
tail -f ~/neural-mesh/logs/pipeline_*.log | grep -i error

# Check process
ps aux | grep pipeline

# Monitor resources
top | grep python

# Disk usage
du -sh ~/neural-mesh/*
```

## Integration Snippets

### Custom Test

```python
# ~/neural-mesh/src/tests/test_example.py
import unittest

class TestExample(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(1 + 1, 2)

if __name__ == "__main__":
    unittest.main()
```

### Environment Variables

```python
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
```

### Custom Notification

```python
import requests

def notify_slack(message: str):
    webhook = os.getenv("SLACK_WEBHOOK")
    if webhook:
        requests.post(webhook, json={"text": message})
```

## Useful One-Liners

```bash
# Count test files
find ~/neural-mesh/src/tests -name 'test_*.py' | wc -l

# Total cycles run
jq '.cycle_count' ~/neural-mesh/storage/pipeline_state.json

# Success rate
jq '.metrics | .test_passes / (.test_passes + .test_failures) * 100' \
  ~/neural-mesh/storage/pipeline_state.json

# Recent errors
grep ERROR ~/neural-mesh/logs/pipeline_*.log | tail -10

# Backup everything
tar -czf neural-mesh-backup-$(date +%Y%m%d).tar.gz ~/neural-mesh
```

## Performance Tuning

```python
# Faster but cheaper model
Config.AI_MODEL = "gpt-3.5-turbo"

# Reduce retries for speed
Config.MAX_RETRIES = 2

# Shorter timeouts
Config.TEST_TIMEOUT = 60

# Less aggressive repairs
Config.MAX_REPAIR_ATTEMPTS = 1
```

## Security Checklist

- [ ] API key in `.env`, not code
- [ ] `.env` in `.gitignore`
- [ ] Logs don't contain secrets
- [ ] File permissions restricted (`chmod 600 .env`)
- [ ] Regular backups of state

## Exit Codes

- `0` - Success
- `1` - General error
- `2` - Configuration error
- `130` - Interrupted (Ctrl+C)

## Keyboard Shortcuts

- `Ctrl+C` - Stop pipeline (saves state)
- `Ctrl+Z` - Suspend (not recommended)
- `Ctrl+D` - Exit shell

## Resources

- Full docs: `IMPLEMENTATION_GUIDE.md`
- Troubleshooting: `TROUBLESHOOTING.md`
- GitHub: https://github.com/Garrettc123/neural-mesh-pipeline
