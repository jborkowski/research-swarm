# Getting Started with Research Swarm

**Welcome!** This guide will help you start using Research Swarm in minutes.

## What is Research Swarm?

Research Swarm is an AI-powered system that takes your ideas and automatically:
1. Researches the best approaches
2. Creates implementation plans
3. Generates working code with tests
4. Documents everything in Git

All autonomously, using multi-agent AI orchestration.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.11 or higher (`python --version`)
- [ ] Redis installed (`redis-cli --version`)
- [ ] OpenAI API key (get from https://platform.openai.com/api-keys)
- [ ] Git installed (`git --version`)

## 5-Minute Setup

### 1. Install Dependencies (1 minute)

```bash
cd research-swarm-claude
pip install -r requirements.txt
```

### 2. Configure API Keys (2 minutes)

```bash
# Copy the template
cp config/.env.template config/.env

# Edit with your API key
nano config/.env  # or use your favorite editor
```

Minimum required setting:
```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

### 3. Initialize (1 minute)

```bash
python scripts/init_db.py
```

This will verify your setup and create the output repository.

### 4. Start Services (1 minute)

**Option A: Quick Start Script**
```bash
./scripts/run_local.sh
```

**Option B: Docker (if you have Docker)**
```bash
docker-compose up -d
```

**Option C: Manual (3 terminals)**
```bash
# Terminal 1
redis-server

# Terminal 2
python -m uvicorn api.main:app --reload

# Terminal 3
python orchestrator/worker.py
```

## Your First Idea

### Submit an Idea

```bash
curl -X POST http://localhost:8000/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{
    "idea": "Create a simple weather checker that emails me the forecast"
  }'
```

You'll get back:
```json
{
  "idea_id": "abc-123-def-456",
  "status": "queued",
  "estimated_completion": "2025-11-01T12:30:00",
  "tracking_url": "http://localhost:8000/ideas/abc-123-def-456"
}
```

### Watch the Magic Happen

The system will now:
1. ✓ Analyze your idea (2 mins)
2. ✓ Research weather APIs (5 mins)
3. ✓ Plan the implementation (3 mins)
4. ✓ Generate code with tests (10 mins)
5. ✓ Run tests (2 mins)
6. ✓ Create documentation (1 min)

**Total**: ~20-30 minutes

### Check Status

```bash
# Use the idea_id from above
curl http://localhost:8000/api/v1/ideas/abc-123-def-456/status
```

### View Results

When complete, check:
```bash
ls outputs/research-repository/ideas/

# Open the summary
cat outputs/research-repository/ideas/2025-11-01-simple-weather-checker/SUMMARY.md
```

## What You'll Get

For each idea, you receive:

### 📊 Research Report
- Feasibility analysis
- Recommended APIs and tools
- Technical approach
- Potential blockers

### 📝 Implementation Plan
- Step-by-step tasks
- Complexity assessment
- Time estimates
- Dependencies

### 💻 Working Code
- Source files
- Test files
- Dependencies (`requirements.txt` or `package.json`)
- README with setup instructions

### ✅ Test Results
- Unit test results
- Code coverage report
- E2E test status

### 📚 Documentation
- Implementation summary
- Setup instructions
- Usage examples

All organized in Git with commits for each phase!

## Example Ideas to Try

### Starter Ideas (Simple)
```bash
# Python script
curl -X POST http://localhost:8000/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{"idea": "Create a script that downloads my GitHub stars to a CSV"}'

# Web app
curl -X POST http://localhost:8000/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{"idea": "Build a markdown preview tool with Streamlit"}'
```

### Intermediate Ideas (Medium)
```bash
# API integration
curl -X POST http://localhost:8000/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{"idea": "Create a Slack bot that posts daily standup reminders"}'

# Data processing
curl -X POST http://localhost:8000/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{"idea": "Build a tool to analyze CSV files and generate charts"}'
```

### Advanced Ideas (Complex)
```bash
# Full application
curl -X POST http://localhost:8000/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{"idea": "Create a personal finance tracker with FastAPI backend and React frontend"}'
```

## Explore the API

Visit http://localhost:8000/docs for:
- Interactive API documentation
- Try different endpoints
- See request/response schemas

## Enable Notifications (Optional)

### Email Notifications

Edit `config/.env`:
```bash
EMAIL_FROM=your-email@gmail.com
EMAIL_TO=your-email@gmail.com
EMAIL_PASSWORD=your-app-specific-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

For Gmail, create an App Password: https://myaccount.google.com/apppasswords

### Discord Notifications

1. Create a Discord webhook in your server settings
2. Add to `config/.env`:
```bash
DISCORD_WEBHOOK=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
```

Restart services after configuration changes.

## Tips for Better Results

### 1. Be Specific
❌ "Make an app"
✓ "Create a TODO app with FastAPI backend and simple HTML frontend"

### 2. Mention Constraints
✓ "Build a website using only Python and Streamlit"
✓ "Create a script that runs without external dependencies"

### 3. Provide Context
```bash
curl -X POST http://localhost:8000/api/v1/ideas \
  -H "Content-Type: application/json" \
  -d '{
    "idea": "Build a note-taking app",
    "context": "Should save notes to local files, support markdown, and have a search feature"
  }'
```

### 4. Set Priority
```bash
-d '{
  "idea": "Your idea",
  "priority": "high"  # or "medium", "low"
}'
```

## Monitoring

### Check Queue Status
```bash
curl http://localhost:8000/api/v1/queue/stats
```

### View Logs
```bash
# Application logs
tail -f logs/research-swarm.log

# Docker logs
docker-compose logs -f
```

### Metrics
```bash
# Prometheus metrics
curl http://localhost:9090/metrics
```

## Common Questions

### How long does it take?
- Simple ideas: 15-20 minutes
- Medium ideas: 20-40 minutes
- Complex ideas: 40-60 minutes

### What languages are supported?
Currently:
- Python (best support)
- JavaScript/Node.js (good support)
- More coming in Phase 2

### Can I cancel an idea?
```bash
curl -X DELETE http://localhost:8000/api/v1/ideas/{idea_id}
```

### Can I run multiple ideas at once?
Yes! Scale workers:
```bash
docker-compose up -d --scale worker=3
```

### What if something fails?
The system will:
1. Retry up to 10 times
2. Save partial progress
3. Document what worked and what failed
4. Send you a notification

## Troubleshooting

### "Redis connection failed"
```bash
# Start Redis
redis-server

# Or with Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### "OpenAI API error"
```bash
# Check your key
echo $OPENAI_API_KEY

# Verify it works
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### "Port 8000 already in use"
```bash
# Change port in config/.env
API_PORT=8001

# Or kill the process
lsof -ti:8000 | xargs kill -9
```

### Still stuck?
1. Check logs: `tail -f logs/research-swarm.log`
2. See full troubleshooting: [README.md](README.md#troubleshooting)
3. Open an issue on GitHub

## Next Steps

Now that you're up and running:

1. **Try Different Ideas**: Experiment with various project types
2. **Review the Code**: Look at generated implementations
3. **Customize Settings**: Adjust timeouts, models, etc. in `config/.env`
4. **Set Up Mobile**: Create iOS Shortcut for on-the-go ideas
5. **Deploy to Cloud**: Move to production for 24/7 operation

## Learn More

- **Full Documentation**: [README.md](README.md)
- **Quick Reference**: [QUICKSTART.md](QUICKSTART.md)
- **Implementation Details**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Original PRD**: [docs/research-swarm-prd.md](docs/research-swarm-prd.md)

## Get Help

- 📖 Documentation in `README.md`
- 🐛 Issues on GitHub
- 💬 Discussions on GitHub
- 📧 Email: support@example.com

---

**Happy building! 🚀**

Remember: Research Swarm is your AI research assistant. Give it ideas, and it will research, plan, and build autonomously!
