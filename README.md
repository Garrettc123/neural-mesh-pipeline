# Neural Mesh Pipeline

**Production-ready self-healing neural mesh pipeline with AI-powered code repair, retry logic, and state persistence for Termux**

## Features

✅ **Exponential Backoff Retry Logic** - Handles transient failures gracefully  
✅ **Persistent State Management** - Survives interruptions and device resets  
✅ **AI-Powered Code Repair** - LangChain agents automatically fix failing tests  
✅ **Structured Logging** - File and console output with timestamps  
✅ **Advanced Test Execution** - Timeout protection and metrics collection  
✅ **Zero-Trust Networking** - OpenZiti deployment integration  
✅ **Termux Optimized** - Designed for Android mobile development  

## Quick Start (5 Minutes)

### Automated Deployment (Recommended)

```bash
# Clone repository
git clone https://github.com/Garrettc123/neural-mesh-pipeline.git
cd neural-mesh-pipeline

# Run deployment script
./deploy.sh

# Or use Docker
./deploy-docker.sh
```

### Manual Setup (Termux)

```bash
# 1. Install prerequisites
pkg update && pkg upgrade -y
pkg install python python-pip -y
termux-setup-storage

# 2. Create directory structure
mkdir -p ~/neural-mesh/{src/tests,logs,storage}
cd ~/neural-mesh

# 3. Clone or download files
# Copy pipeline_enhanced.py and requirements-termux.txt to ~/neural-mesh

# 4. Install dependencies
pip install -r requirements-termux.txt

# 5. Configure
export OPENAI_API_KEY="sk-your-key"

# 6. Run!
python pipeline_enhanced.py
```

For detailed deployment options (Docker, Cloud, CI/CD), see **[DEPLOYMENT.md](DEPLOYMENT.md)**

## Documentation

- **[Deployment Guide](DEPLOYMENT.md)** - Complete deployment instructions
- **[Quick Reference](QUICK_REFERENCE.md)** - Commands and common tasks
- **[Implementation Guide](IMPLEMENTATION_GUIDE.md)** - Full technical documentation
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

## Architecture

```
NeuralMeshPipeline
├── State Persistence (JSON)
├── Retry Logic (Exponential Backoff + Jitter)
├── Test Execution (Subprocess + Timeout)
├── AI Code Repair (LangChain ReAct Agent)
│   ├── ReadSourceCode Tool
│   ├── AnalyzeError Tool
│   └── WriteFixedCode Tool
└── Continuous Orchestration
```

## Usage Examples

```bash
# Single cycle
python pipeline_enhanced.py --mode single

# Continuous with 30-min interval
python pipeline_enhanced.py --interval 1800

# View current state
python pipeline_enhanced.py --show-state

# Watch logs
tail -f logs/pipeline_*.log
```

## Configuration

Create `.env` file:

```bash
OPENAI_API_KEY=sk-your-key-here
AI_MODEL=gpt-4
MAX_RETRIES=3
TEST_TIMEOUT=300
```

## Key Features Explained

### Retry Logic

Uses exponential backoff with jitter to prevent thundering herd:
- Attempt 1: immediate
- Attempt 2: ~1s delay
- Attempt 3: ~2s delay  
- Attempt 4: ~4s delay

### State Persistence

Automatically saves:
- Cycle count and timestamps
- Test metrics (passes/failures)
- Repair success rates
- Code checksums
- Backup locations

### AI Repair

LangChain agent with specialized tools:
1. Reads failing source code
2. Analyzes test error output
3. Generates corrected code
4. Verifies fix with re-test

## Requirements

- Python 3.8+
- Termux (Android) or Linux
- OpenAI API key
- ~50MB storage

## Project Structure

```
~/neural-mesh/
├── pipeline_enhanced.py      # Main orchestrator (500+ lines)
├── requirements-termux.txt   # Dependencies
├── .env                      # API keys (create this)
├── src/
│   ├── tests/               # Test files (test_*.py)
│   └── *.py                 # Your source code
├── logs/                    # Rotating logs
└── storage/                 # State persistence
    └── pipeline_state.json
```

## License

MIT License - See LICENSE file for details

## Contributing

Pull requests welcome! See IMPLEMENTATION_GUIDE.md for architecture details.

## Support

For issues, see TROUBLESHOOTING.md or open a GitHub issue.

---

**Built for production use on Termux with love ❤️**
