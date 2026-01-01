# AI Agent Reliability - Course Demos

This folder contains all demo files for the "AI Agent Reliability" course.

## Setup Instructions

1. **Install Python 3.12+**
   Ensure you have Python 3.12 or higher installed.

2. **Create Virtual Environment**
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API Key**
   - Copy `env.example` to `.env`
   - Add your OpenAI API key to the `.env` file
   ```bash
   cp env.example .env
   # Edit .env and add your API key
   ```

## Module Structure

### Module 1: Understanding Agent Failures
**Location**: `m1-agent-failures/`

Demonstrates common failure modes in AI agents:
- `01_failure_scenarios.py` - Planning, grounding, and invocation failures
- `02_cascading_errors.py` - Multi-step workflow error propagation

### Module 2: Building Reliable Agents
**Location**: `m2-reliable-agents/`

Shows strategies to improve agent reliability:
- `01_improved_prompts.py` - Better prompt engineering for tool selection
- `02_fallback_logic.py` - Error recovery and graceful degradation
- `03_stress_testing.py` - Automated testing framework for agents

## Running the Demos

Each demo can be run independently:

```bash
# Module 1 demos
python m1-agent-failures/01_failure_scenarios.py
python m1-agent-failures/02_cascading_errors.py

# Module 2 demos
python m2-reliable-agents/01_improved_prompts.py
python m2-reliable-agents/02_fallback_logic.py
python m2-reliable-agents/03_stress_testing.py
```

## Notes

- All demos use the Globomantics e-commerce scenario
- Tool functions are simulated (no real API calls to external services)
- Test data is embedded in the demo files for easy execution