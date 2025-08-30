# Agent Transparency System

Complete guide to the agent transparency features in Trajectory.AI, providing visibility into multi-agent operations while maintaining a clean user experience.

## Overview & Quick Start

The agent transparency system provides real-time monitoring of agent activities, workflow coordination, and performance metrics. Features are hidden by default in production but easily accessible for development and debugging.

**Quick Enable:**
- Development mode: Features auto-enabled
- Production: `localStorage.setItem('show-agent-dashboard', 'true')`
- Keyboard shortcuts: `Ctrl+Shift+A` (Dashboard), `Ctrl+Shift+L` (Logs)

## Features Implemented

### 1. Agent Status Monitoring

**Backend Components:**
- `AgentOrchestratorService.get_status()` - Provides real-time agent status
- `BaseAgent.get_status()` - Individual agent status and metrics
- `/api/agents/status` - REST endpoint for agent status

**Frontend Components:**
- `AgentStatusIndicator` - Minimal status indicator showing active agents
- Shows processing state with animated indicators
- Only visible in development mode or when explicitly enabled

**Usage:**
```typescript
<AgentStatusIndicator showDetails={false} />
```

### 2. Workflow Collaboration Visualization

**Backend Components:**
- `AgentWorkflow` model - Tracks multi-agent workflows
- `WorkflowStep` tracking - Individual step progress
- `/api/agents/workflows` - Workflow status endpoint

**Frontend Components:**
- `AgentCollaborationViewer` - Shows active workflows and agent coordination
- Displays workflow steps, participating agents, and progress
- Real-time updates every 3 seconds

**Features:**
- Visual workflow progress indicators
- Agent collaboration chains
- Step-by-step execution tracking
- Workflow status (created, running, completed, failed)

### 3. Agent Contribution Indicators

**Backend Components:**
- Enhanced response metadata with agent contributions
- Confidence scores and processing times
- Agent-specific contribution tracking

**Frontend Components:**
- `AgentContributionIndicator` - Shows which agents contributed to responses
- Minimal mode: Shows agent icons (🎯📊📚📄👨‍🏫)
- Detailed mode: Shows confidence scores and processing times

**Integration:**
- Embedded in chat messages for AI responses
- Shows agent collaboration on roadmap generation
- Confidence scoring for each agent's contribution

### 4. Agent Activity Logging

**Backend Components:**
- `AgentLogger` - Centralized logging system
- Structured logging with metadata
- Activity types: request_received, request_processed, workflow_started, etc.
- `/api/agents/logs` - Log retrieval endpoint

**Frontend Components:**
- `AgentLogViewer` - Real-time log viewer (Ctrl+Shift+L to toggle)
- Filtering by agent, activity type, and log level
- Live updates every 5 seconds

**Log Types:**
- Request processing events
- Workflow coordination
- Agent collaboration messages
- Error tracking
- Performance metrics

### 5. Agent Dashboard

**Frontend Components:**
- `AgentDashboard` - Comprehensive monitoring dashboard (Ctrl+Shift+A to toggle)
- System metrics (registered agents, active workflows)
- Agent performance metrics
- Real-time status indicators

**Features:**
- Collapsible interface
- Performance statistics
- System load monitoring
- Agent utilization tracking

## Visibility Controls

### Development Mode
All agent transparency features are visible by default in development mode (`NODE_ENV === 'development'`).

### Production Mode
In production, features are hidden by default but can be enabled via localStorage:

```javascript
// Enable specific components
localStorage.setItem('show-agent-status', 'true')
localStorage.setItem('show-agent-collaboration', 'true')
localStorage.setItem('show-agent-contributions', 'true')
localStorage.setItem('show-agent-dashboard', 'true')
localStorage.setItem('show-agent-logs', 'true')
```

### Keyboard Shortcuts
- `Ctrl+Shift+A` - Toggle Agent Dashboard
- `Ctrl+Shift+L` - Toggle Agent Log Viewer

## API Endpoints

### Agent Status
```
GET /api/agents/status
```
Returns current status of all registered agents including load, capabilities, and health.

### Workflow Information
```
GET /api/agents/workflows
```
Returns active workflows and recent workflow history with step details.

### Performance Metrics
```
GET /api/agents/metrics
```
Returns system-wide and agent-specific performance metrics.

### Activity Logs
```
GET /api/agents/logs?limit=100&agent_id=&activity_type=&level=
```
Returns filtered agent activity logs with statistics.

## Integration Points

### Chat Interface
- Agent status indicator in chat header
- Agent contribution indicators on AI responses
- Workflow progress for complex requests

### Roadmap Generation
- Multi-agent workflow visualization
- Agent contribution breakdown
- Performance metrics for roadmap quality

### Error Handling
- Agent error logging and reporting
- Fallback mechanisms when agents fail
- Error recovery workflows

## Configuration

### Backend Configuration
```python
# In main.py or service initialization
from api.agents import set_orchestrator
from services.agent_orchestrator_service import AgentOrchestratorService

# Initialize orchestrator
orchestrator = AgentOrchestratorService(ai_service)
set_orchestrator(orchestrator)

# Register agents
orchestrator.register_agent(career_strategy_agent)
orchestrator.register_agent(skills_analysis_agent)
# ... other agents
```

### Frontend Configuration
```typescript
// In layout.tsx or app initialization
import { AgentDashboard, AgentLogViewer } from '@/components/agent'

export default function Layout({ children }) {
  return (
    <div>
      {children}
      <AgentDashboard />
      <AgentLogViewer />
    </div>
  )
}
```

## Performance Considerations

### Minimal Impact
- Components only render when explicitly enabled
- Efficient polling intervals (3-10 seconds)
- Lightweight data structures
- Client-side filtering and caching

### Resource Usage
- Log entries limited to 10,000 in memory
- Automatic cleanup of old workflow data
- Minimal network overhead
- No impact on core agent performance

## Security Considerations

### Data Privacy
- No sensitive user data in logs
- Agent IDs are anonymized in production
- Workflow details exclude personal information
- Configurable log retention policies

### Access Control
- Development-only features by default
- No sensitive system information exposed
- Rate limiting on monitoring endpoints
- Optional authentication for admin features

## Future Enhancements

### Planned Features
- Agent performance analytics dashboard
- Workflow optimization suggestions
- Agent load balancing visualization
- Custom monitoring alerts
- Export capabilities for logs and metrics

### Integration Opportunities
- Integration with external monitoring tools
- Custom agent performance dashboards
- Workflow optimization recommendations
- Automated agent scaling based on load

## Troubleshooting

### Common Issues

**Agent status not showing:**
- Check if development mode is enabled
- Verify localStorage settings
- Ensure backend agents are registered

**Workflows not visible:**
- Confirm orchestrator is properly initialized
- Check if agents are processing requests
- Verify API endpoints are accessible

**Logs not updating:**
- Check network connectivity
- Verify backend logging is enabled
- Confirm API endpoints are responding

### Debug Commands

```bash
# Test agent transparency system
cd backend
python test_agent_transparency.py

# Check frontend compilation
cd frontend
npx tsc --noEmit

# Verify API endpoints
curl http://localhost:8000/agents/status
curl http://localhost:8000/agents/workflows
curl http://localhost:8000/agents/metrics
```

## Implementation Summary

The agent transparency system successfully provides:

✅ **Minimalistic UI** - Hidden by default, developer-friendly controls
✅ **Real-time Monitoring** - Live updates of agent status and workflows  
✅ **Performance Tracking** - Comprehensive metrics and analytics
✅ **Activity Logging** - Structured logging with filtering capabilities
✅ **Workflow Visualization** - Multi-agent coordination display
✅ **Contribution Indicators** - Agent-specific response attribution
✅ **Error Tracking** - Comprehensive error logging and reporting
✅ **Security Conscious** - No sensitive data exposure, configurable access

The system maintains the core requirement of being "minimalistic and not too visible for end users" while providing comprehensive monitoring capabilities for development and debugging purposes.
## Syst
em Status

Your system currently has:
- ✅ **5 Agents Registered**: career_strategy, learning_resource, skills_analysis, resume_optimization, career_mentor
- ✅ **Multi-Agent Service**: Running and initialized
- ✅ **Agent Orchestrator**: Available for workflow coordination
- ✅ **Activity Logging**: Working and capturing agent interactions
- ✅ **API Endpoints**: All transparency APIs functional

## Testing the Features

1. **Start services**: `cd backend && python main.py` + `cd frontend && npm run dev`
2. **Open application**: http://localhost:3000
3. **Enable features**: Press `Ctrl+Shift+A` for Dashboard, `Ctrl+Shift+L` for Logs
4. **Interact with AI**: Ask questions, generate roadmaps, watch agents work in real-time

## Troubleshooting

**Dashboard not showing**: Check development mode or localStorage settings, refresh page
**No agent activity**: Ensure backend running, interact with AI features
**Logs not updating**: Verify backend on port 8000, check network tab for API failures