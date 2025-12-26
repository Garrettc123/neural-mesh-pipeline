# Neural Mesh Pipeline - Troubleshooting Guide

## Common Issues

### 1. Import Errors

**Symptom:**
```
ImportError: No module named 'langchain'
```

**Solution:**
```bash
pip install -r requirements-termux.txt

# If pip fails, try upgrading:
pip install --upgrade pip
pip install -r requirements-termux.txt

# For specific package:
pip install langchain langchain-openai
```

### 2. Permission Errors

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: '/storage/emulated/0/neural-mesh'
```

**Solution:**
```bash
# Grant storage permissions
termux-setup-storage

# Use home directory instead
mkdir -p ~/neural-mesh
cd ~/neural-mesh

# Verify permissions
ls -la ~/neural-mesh
```

### 3. OpenAI API Errors

**Symptom:**
```
openai.error.AuthenticationError: Invalid API key
```

**Solution:**
```bash
# Set environment variable
export OPENAI_API_KEY="sk-your-actual-key"

# Or create .env file
echo 'OPENAI_API_KEY=sk-your-key' > .env

# Verify it's set
echo $OPENAI_API_KEY

# Load in Python
from dotenv import load_dotenv
load_dotenv()
```

**Rate Limit Error:**
```
openai.error.RateLimitError: Rate limit exceeded
```

**Solution:**
- Increase retry delays in `Config.BASE_DELAY`
- Reduce concurrent requests
- Upgrade OpenAI plan for higher limits

### 4. Test Timeouts

**Symptom:**
```
Timeout after 300s
```

**Solution:**
```python
# Increase timeout in Config
class Config:
    TEST_TIMEOUT = 600  # 10 minutes

# Or pass custom timeout
run_tests(test_file, timeout=900)
```

### 5. State File Corruption

**Symptom:**
```
JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**Solution:**
```bash
# Backup corrupted file
mv ~/neural-mesh/storage/pipeline_state.json ~/neural-mesh/storage/pipeline_state.json.bak

# Pipeline will create fresh state
python pipeline_enhanced.py
```

### 6. Memory Issues on Android

**Symptom:**
```
MemoryError: Unable to allocate array
```

**Solution:**
```bash
# Reduce batch size
# Limit concurrent operations
# Clear Termux cache
pkg clean

# Monitor memory
top

# Restart Termux if needed
```

### 7. Network Connectivity

**Symptom:**
```
requests.exceptions.ConnectionError: Failed to establish connection
```

**Solution:**
```bash
# Check internet
ping 8.8.8.8

# Test API endpoint
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Use retry logic (already implemented)
# Check firewall/VPN settings
```

## Debugging Techniques

### Enable Debug Logging

```python
# In Config class
LOG_LEVEL = logging.DEBUG

# Or via command line
import logging
logger.setLevel(logging.DEBUG)
```

### Inspect State

```bash
# View current state
python pipeline_enhanced.py --show-state

# Or manually
cat ~/neural-mesh/storage/pipeline_state.json | python -m json.tool
```

### Test Individual Components

```python
# Test retry logic
from pipeline_enhanced import retry_with_backoff

def failing_func():
    raise ValueError("Test error")

try:
    retry_with_backoff(failing_func, max_retries=3)
except ValueError:
    print("Retries exhausted as expected")

# Test AI repair
repairer = AICodeRepairer()
result = repairer.repair(Path("test.py"), "error output")
```

### Check Logs

```bash
# View today's log
tail -f ~/neural-mesh/logs/pipeline_$(date +%Y%m%d).log

# Search for errors
grep -i error ~/neural-mesh/logs/*.log

# View last 100 lines
tail -100 ~/neural-mesh/logs/pipeline_*.log
```

## Performance Issues

### Slow Test Execution

**Solutions:**
- Parallelize tests (see Implementation Guide)
- Increase timeout only if necessary
- Optimize test code
- Use faster test frameworks

### High AI API Costs

**Solutions:**
```python
# Use cheaper model
Config.AI_MODEL = "gpt-3.5-turbo"

# Reduce repair attempts
Config.MAX_REPAIR_ATTEMPTS = 1

# Add caching
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_repair(code_hash, error_hash):
    # Only repair unique combinations
    pass
```

## Termux-Specific Issues

### Storage Access

**Problem:** Cannot write to `/storage/emulated/0`

**Solution:**
```bash
# Request permissions
termux-setup-storage

# Verify access
ls /storage/emulated/0/

# Use symlinks if needed
ln -s /storage/emulated/0/Documents ~/neural-mesh/docs
```

### Package Installation Failures

**Problem:** `pip install` fails with compilation errors

**Solution:**
```bash
# Install build dependencies
pkg install python python-dev clang

# Try binary wheels
pip install --only-binary :all: langchain

# Use conda-forge (alternative)
pkg install conda
conda install -c conda-forge langchain
```

### Python Version Mismatch

**Problem:** `SyntaxError` on f-strings or type hints

**Solution:**
```bash
# Check Python version (need 3.8+)
python --version

# Update if needed
pkg update python

# Or install specific version
pkg install python3.11
```

## Recovery Procedures

### Complete Reset

```bash
# Backup important data
cp -r ~/neural-mesh ~/neural-mesh-backup

# Remove everything
rm -rf ~/neural-mesh

# Reinstall
mkdir -p ~/neural-mesh/{src/tests,logs,storage}
cd ~/neural-mesh
# Copy files and reinstall
```

### Restore from Backup

```bash
# Find backup
ls ~/neural-mesh/src/*_backup_*

# Restore specific file
cp ~/neural-mesh/src/main_backup_20241226_101530.py ~/neural-mesh/src/main.py

# Restore state
cp ~/neural-mesh/storage/pipeline_state.json.bak ~/neural-mesh/storage/pipeline_state.json
```

## Getting Help

### Collect Diagnostic Information

```bash
# System info
uname -a
python --version
pip list

# Pipeline info
python pipeline_enhanced.py --show-state
ls -lah ~/neural-mesh/

# Recent logs
tail -50 ~/neural-mesh/logs/pipeline_*.log
```

### Report Issues

When reporting issues, include:
1. Error message (full traceback)
2. Python version
3. Termux version
4. Steps to reproduce
5. Relevant log excerpts
6. State file contents (sanitize API keys!)

## Known Limitations

1. **Android Battery Optimization** - May kill background processes
   - Solution: Disable battery optimization for Termux
   
2. **Limited CPU/Memory** - Slower than desktop
   - Solution: Reduce batch sizes, use simpler models

3. **Network Interruptions** - Mobile connectivity issues
   - Solution: Retry logic handles this (already implemented)

4. **Storage Constraints** - Limited space on mobile
   - Solution: Regular cleanup of logs and backups

## Preventive Measures

```bash
# Regular backups
crontab -e
# Add: 0 */6 * * * cp -r ~/neural-mesh ~/neural-mesh-backup

# Monitor disk space
df -h

# Clean old logs (keep 7 days)
find ~/neural-mesh/logs -name '*.log' -mtime +7 -delete

# Validate state periodically
python -c "import json; json.load(open('storage/pipeline_state.json'))"
```
