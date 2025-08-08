# backend/workflows/config_driven_workflow.py
"""
Config-Driven ControlFlow Workflow

Completely replaces hardcoded workflows with configuration-driven execution.
Uses proper ControlFlow patterns for task orchestration and dependency management.
"""

import controlflow as cf
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Any, Optional, Literal
from pydantic import BaseModel, Field

from .base import BaseWorkflow, WorkflowResult as BaseWorkflowResult
from .config_loader import get_workflow_config_loader
from ..utils.logging import setup_logging
from ..utils.monitoring import WorkflowMonitor

logger = setup_logging()

class InvestmentAnalysis(BaseModel):
    """Structured result model for investment analysis"""
    ticker: str = Field(description="Stock ticker symbol")
    market_analysis: str = Field(description="Market analysis summary")
    sentiment: Literal["positive", "negative", "neutral"] = Field(description="Overall sentiment")
    recommendation: str = Field(description="Investment recommendation")
    confidence: float = Field(description="Confidence level (0-1)", ge=0, le=1)
    key_insights: List[str] = Field(description="Key insights", min_items=1, max_items=5)
    risk_assessment: str = Field(description="Risk assessment summary")

class MarketAnalysisResult(BaseModel):
    """Result from market analysis task"""
    ticker: str
    current_price: Optional[float] = None
    market_data: str
    company_overview: str
    analysis_summary: str

class RiskAssessmentResult(BaseModel):
    """Result from risk assessment task"""
    ticker: str
    risk_level: Literal["Low", "Medium", "High"]
    risk_factors: List[str]
    risk_summary: str

class ConfigDrivenWorkflow(BaseWorkflow):
    """
    ControlFlow-native workflow that builds itself from configuration.
    Completely replaces hardcoded workflow implementations.
    """
    
    def __init__(self, workflow_type: str = "quick_stock_analysis"):
        """Initialize workflow with configuration validation"""
        
        self.workflow_type = workflow_type
        super().__init__(
            name=f"config_driven_{workflow_type}",
            description=f"Config-driven {workflow_type} workflow using ControlFlow patterns"
        )
        
        # Initialize core components
        self.config_loader = get_workflow_config_loader()
        
        # Import registry manager and agent factory here to avoid circular imports
        from ..registry.manager import get_registry_manager
        from ..agents.factory import get_agent_factory
        
        self.registry_manager = get_registry_manager()
        self.agent_factory = get_agent_factory()
        
        # Load and validate workflow configuration
        self.workflow_config = self._load_and_validate_config()
        
        # Workflow execution state
        self.execution_context = {}
        self.task_results = {}
        self.status_callbacks = []
        self.tasks: Dict[str, cf.Task] = {}
        self.task_statuses: Dict[str, str] = {}
        
        # Initialize workflow status for tracking
        self.workflow_status = {
            'status': 'initialized',
            'nodes': [],
            'edges': [],
            'result': None,
            'enhanced_result': None,
            'execution_time': 0,
            'workflow_name': self.name,
            'workflow_type': workflow_type
        }
        
        logger.info(f"Initialized config-driven workflow: {workflow_type}")
    
    def _load_and_validate_config(self) -> Dict[str, Any]:
        """Load and strictly validate workflow configuration"""
        
        config = self.config_loader.get_workflow_config(self.workflow_type)
        if not config:
            raise ValueError(f"Workflow type '{self.workflow_type}' not found in configuration")
        
        # Validate required configuration sections
        required_sections = ['agents']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Workflow configuration missing required section: {section}")
        
        # Validate that we have at least one required agent
        agents = config.get('agents', [])
        required_agents = [agent for agent in agents if agent.get('required', False)]
        if not required_agents:
            raise ValueError(f"Workflow '{self.workflow_type}' must have at least one required agent")
        
        logger.info(f"Configuration validated for workflow: {self.workflow_type}")
        return config
    
    def add_status_callback(self, callback):
        """Add callback for status updates"""
        self.status_callbacks.append(callback)
    
    def _update_status(self, update: Dict[str, Any]):
        """Update workflow status and notify callbacks with enhanced live inspection data"""
        self.execution_context.update(update)
        
        # Add timestamp
        update['timestamp'] = datetime.now().isoformat()
        
        # Enhanced live inspection data
        if 'current_task' in update:
            task_details = {
                'task_name': update['current_task'],
                'task_progress': self._get_task_progress(update['current_task']),
                'agent_reasoning': self._get_current_agent_reasoning(),
                'tool_calls': self._get_recent_tool_calls(),
                'execution_context': self.execution_context.copy()
            }
            update['live_details'] = task_details
        
        # Add workflow-level metrics
        update['workflow_metrics'] = self._get_workflow_metrics()
        
        # Generate workflow graph for frontend visualization
        try:
            workflow_graph = self._generate_workflow_graph()
            update['nodes'] = workflow_graph['nodes']
            update['edges'] = workflow_graph['edges']
            update['hasNodes'] = True if workflow_graph['nodes'] else False
        except Exception as e:
            logger.error(f"Error generating workflow graph: {e}", exc_info=True)
            update['nodes'] = []
            update['edges'] = []
            update['hasNodes'] = False
        
        # Notify all callbacks
        for callback in self.status_callbacks:
            try:
                callback(update)
            except Exception as e:
                logger.error(f"Status callback error: {e}")
    
    def _get_task_progress(self, task_name: str) -> Dict[str, Any]:
        """Get detailed progress information for a specific task"""
        return {
            'task_name': task_name,
            'status': 'running',
            'start_time': self.execution_context.get(f'{task_name}_start_time'),
            'current_step': self.execution_context.get(f'{task_name}_current_step', 'initializing'),
            'steps_completed': self.execution_context.get(f'{task_name}_steps_completed', 0),
            'total_steps': self.execution_context.get(f'{task_name}_total_steps', 1)
        }
    
    def _get_current_agent_reasoning(self) -> Optional[str]:
        """Get the most recent agent reasoning from the event handler"""
        try:
            if hasattr(self, 'event_handler') and self.event_handler:
                if hasattr(self.event_handler, 'get_events_by_type'):
                    events = self.event_handler.get_events_by_type('agent_message')
                    if events:
                        latest_event = events[-1]
                        return latest_event.get('message_content', 'No reasoning available')
        except Exception as e:
            logger.warning(f"Could not retrieve agent reasoning: {e}")
        return None
    
    def _get_recent_tool_calls(self) -> List[Dict[str, Any]]:
        """Get recent tool calls for live inspection"""
        try:
            if hasattr(self, 'event_handler') and self.event_handler:
                if hasattr(self.event_handler, 'get_events_by_type'):
                    tool_events = self.event_handler.get_events_by_type('agent_tool_call')
                    return tool_events[-3:] if tool_events else []
        except Exception as e:
            logger.warning(f"Could not retrieve tool calls: {e}")
        return []

    def _get_tools_used_by_agent(self, agent_name: str) -> List[str]:
        """Derive the list of tools actually used by a given agent so far.

        Filters out ControlFlow completion tools (e.g., mark_task_*_successful).
        """
        try:
            if not agent_name:
                return []
            if hasattr(self, 'event_handler') and self.event_handler and hasattr(self.event_handler, 'get_events_by_type'):
                events = self.event_handler.get_events_by_type('agent_tool_call') or []
                used = []
                for e in events:
                    if e.get('agent_name') != agent_name:
                        continue
                    tool_name = e.get('tool_name') or ''
                    if not tool_name or tool_name.startswith('mark_task_'):
                        # Skip completion tools
                        continue
                    used.append(tool_name)
                # Deduplicate preserving order
                seen = set()
                ordered = []
                for name in used:
                    if name not in seen:
                        seen.add(name)
                        ordered.append(name)
                return ordered
        except Exception as e:
            logger.warning(f"Could not derive tools for agent '{agent_name}': {e}")
        return []
    
    def _extract_ticker_from_query(self, query: str) -> str:
        """Extract ticker symbol using AI-powered detection; raise if not found."""
        try:
            from ..tools.builtin_tools import _detect_ticker_with_ai
            
            detection_result = _detect_ticker_with_ai(query)
            self.execution_context['ticker_detection'] = detection_result
            
            if detection_result.get("status") == "success" and detection_result.get("ticker") and detection_result.get("ticker") != "UNKNOWN":
                logger.info(f"AI detected ticker: {detection_result['ticker']}")
                return str(detection_result["ticker"])  # type: ignore[index]
            else:
                logger.warning("AI ticker detection failed or returned UNKNOWN")
                raise ValueError("TickerNotDetected: Could not detect a valid ticker from the query.")
                
        except Exception as e:
            logger.error(f"Ticker detection error: {e}")
            # Preserve error for UI to show why input is needed
            self.execution_context['ticker_detection'] = {"status": "error", "error": str(e)}
            raise
    
    def _should_include_agent_for_query(self, agent_config: Dict[str, Any], query: str) -> bool:
        """Determine if agent should be included based on query analysis"""
        if agent_config.get('required', False):
            return True
        
        role = agent_config.get('role')
        return self.config_loader.should_include_agent(self.workflow_type, role, query)
    
    @cf.flow
    def execute(self, query: str, provider: str = "openai", **kwargs) -> BaseWorkflowResult:
        """
        Main workflow execution using ControlFlow patterns
        """
        start_time = datetime.now()
        workflow_id = kwargs.get('workflow_id', 'unknown')
        
        self.execution_context['start_time'] = start_time
        
        try:
            logger.info(f"Starting config-driven workflow {workflow_id}: {self.workflow_type}")
            
            self._update_status({
                'status': 'initializing',
                'workflow_id': workflow_id,
                'workflow_type': self.workflow_type,
                'query': query,
                'provider': provider
            })
            
            # Allow explicit override from caller when user provides it
            ticker_override = kwargs.get('ticker_override')
            if ticker_override and isinstance(ticker_override, str) and ticker_override.strip():
                ticker = ticker_override.strip().upper()
                self.execution_context['ticker_detection'] = {
                    'status': 'override',
                    'ticker': ticker,
                    'reason': 'User provided ticker override'
                }
            else:
                try:
                    ticker = self._extract_ticker_from_query(query)
                except Exception:
                    # Ask user for ticker; surface friendly message
                    message = "I couldn't detect a ticker in your question. Please reply with a stock symbol, e.g., AAPL or MSFT."
                    self._update_status({'status': 'failed', 'error': message})
                    raise
            self.execution_context['ticker'] = ticker
            
            self._update_status({'status': 'creating_agents', 'ticker': ticker})
            
            agents = self.agent_factory.create_agents_for_workflow(self.workflow_type, provider)
            
            self._update_status({
                'status': 'executing_tasks',
                'agents_created': len(agents),
                'available_agents': list(agents.keys())
            })
            
            result = self._execute_workflow_tasks(query, ticker, agents)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self._update_status({
                'status': 'completed',
                'execution_time': execution_time,
                'result_summary': f"Analysis completed for {ticker}"
            })
            
            return BaseWorkflowResult(
                success=True,
                result=result.dict(),
                trace=self._build_execution_trace(),
                agent_invocations=self._build_agent_invocations(),
                execution_time=execution_time,
                workflow_name=self.name
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_message = f"Config-driven workflow failed: {str(e)}"
            logger.error(f"Workflow {workflow_id} failed: {e}", exc_info=True)
            
            self._update_status({
                'status': 'failed',
                'error': error_message,
                'execution_time': execution_time
            })
            
            return BaseWorkflowResult(
                success=False,
                result="",
                trace={'error': error_message, 'context': self.execution_context},
                agent_invocations=self._build_agent_invocations(),
                execution_time=execution_time,
                workflow_name=self.name,
                error=error_message
            )
    
    def _execute_workflow_tasks(self, query: str, ticker: str, agents: Dict[str, cf.Agent]) -> InvestmentAnalysis:
        """
        Execute workflow tasks using a dynamically constructed ControlFlow DAG.
        Honors optional 'dependencies' declared in the workflow configuration.
        """
        workflow_context = {"query": query, "ticker": ticker, "workflow_type": self.workflow_type}

        from ..utils.monitoring import FintelEventHandler
        self.event_handler = FintelEventHandler()

        agent_configs: List[Dict[str, Any]] = self.workflow_config.get('agents', [])

        # 1) Create Task objects for all configured roles that exist in the agent mapping
        tasks: Dict[str, cf.Task] = {}
        role_to_result_type: Dict[str, Any] = {}

        for agent_config in agent_configs:
            role = agent_config.get('role')
            if not role or role not in agents:
                continue

            # Map known roles to structured result models; default to str for intermediates
            if role == 'market_analysis':
                result_type = MarketAnalysisResult
            elif role == 'risk_assessment':
                result_type = RiskAssessmentResult
            elif role == 'synthesis':
                result_type = InvestmentAnalysis
            else:
                result_type = str

            role_to_result_type[role] = result_type

            prompt = f"Perform {role.replace('_', ' ')} for {ticker} based on the query: {query}"
            # Build role-aware instructions that include upstream context keys and result schema hint
            upstream_keys = agent_config.get('dependencies', []) or []
            upstream_hint = f" Use prior results from: {', '.join(upstream_keys)}." if upstream_keys else ""
            result_type_name = result_type.__name__ if hasattr(result_type, '__name__') else 'ResultModel'
            tool_names = agent_config.get('tools', []) or []
            tools_hint = f" Available tools: {', '.join(tool_names)}." if tool_names else ""
            instructions = agent_config.get('instructions', '') or (
                f"Complete the {role.replace('_', ' ')} task using available tools.{upstream_hint}{tools_hint} "
                f"The current query is '{query}' for ticker {ticker}. "
                f"Return output strictly as valid JSON matching the {result_type_name} schema."
            )

            tasks[role] = cf.Task(
                objective=prompt,
                instructions=instructions,
                agents=[agents[role]],
                context=workflow_context,
                result_type=result_type,
                name=f"task_{role}"
            )

        # Expose tasks mapping on the instance for downstream status/graph building
        self.tasks = tasks

        # 2) Configure dependencies
        any_explicit_dependencies = False
        for agent_config in agent_configs:
            role = agent_config.get('role')
            if role not in tasks:
                continue
            dependencies = agent_config.get('dependencies', []) or []
            if dependencies:
                any_explicit_dependencies = True
            for dep_role in dependencies:
                if dep_role in tasks:
                    try:
                        # Use ControlFlow's official API for dependencies
                        tasks[role].add_dependency(tasks[dep_role])
                    except Exception as e:
                        logger.warning(f"Failed to set dependency: {role} depends_on {dep_role}: {e}")
                else:
                    logger.warning(f"Invalid dependency '{dep_role}' for task '{role}'")

        # If no dependencies are defined anywhere, fall back to a linear chain in config order
        if not any_explicit_dependencies:
            ordered_roles = [ac.get('role') for ac in agent_configs if ac.get('role') in tasks]
            for i in range(1, len(ordered_roles)):
                prev_role = ordered_roles[i - 1]
                current_role = ordered_roles[i]
                try:
                    tasks[current_role].add_dependency(tasks[prev_role])
                except Exception as e:
                    logger.warning(f"Failed to set linear dependency: {current_role} depends_on {prev_role}: {e}")

        # 3) Build levelized execution plan (parallel waves) using dependencies
        roles_in_graph = [r for r in [ac.get('role') for ac in agent_configs] if r in tasks]
        role_deps: Dict[str, set] = {r: set() for r in roles_in_graph}
        for agent_config in agent_configs:
            r = agent_config.get('role')
            if r in role_deps:
                for dep in (agent_config.get('dependencies', []) or []):
                    if dep in tasks:
                        role_deps[r].add(dep)

        indegree: Dict[str, int] = {r: len(role_deps[r]) for r in roles_in_graph}
        dependents: Dict[str, List[str]] = {r: [] for r in roles_in_graph}
        for r, deps in role_deps.items():
            for d in deps:
                if d in dependents:
                    dependents[d].append(r)

        # Collect roles by levels
        levels: List[List[str]] = []
        ready = [r for r, deg in indegree.items() if deg == 0]
        visited = set()
        while ready:
            current_level = [r for r in ready if r not in visited]
            if not current_level:
                break
            levels.append(current_level)
            for r in current_level:
                visited.add(r)
                for child in dependents.get(r, []):
                    indegree[child] -= 1
            ready = [r for r, deg in indegree.items() if deg == 0 and r not in visited]

        # Fallback linear level if graph malformed
        if not levels:
            levels = [[r] for r in roles_in_graph]

        # 4) Execute level by level (parallel per level)
        final_result: Optional[InvestmentAnalysis] = None
        for level_index, level_roles in enumerate(levels):
            # Update status for the first role of the level
            try:
                display_role = level_roles[0]
                self._update_status({'status': 'running', 'current_task': display_role, 'task_details': f"Executing {', '.join(level_roles)}..."})
            except Exception:
                pass

            # Execute tasks in this level concurrently using threads
            try:
                with ThreadPoolExecutor(max_workers=max(1, len(level_roles))) as executor:
                    future_to_role = {}
                    for r in level_roles:
                        if r in tasks:
                            task_obj = tasks[r]
                            # If any dependency failed, skip this task and mark SKIPPED
                            deps = role_deps.get(r, set())
                            if any(self.task_statuses.get(d) == 'failed' for d in deps):
                                try:
                                    task_obj.mark_skipped()
                                except Exception:
                                    pass
                                self.task_statuses[r] = 'skipped'
                                continue
                            # Submit direct run of the task to ensure execution
                            self.execution_context[f'{r}_start_time'] = datetime.now().isoformat()
                            if hasattr(self, 'event_handler') and self.event_handler:
                                future_to_role[executor.submit(task_obj.run, handlers=[self.event_handler])] = r
                            else:
                                future_to_role[executor.submit(task_obj.run)] = r
                    for future in as_completed(future_to_role):
                        r = future_to_role[future]
                        try:
                            res = future.result()
                            if res is not None:
                                self.task_results[r] = res
                                self._log_task_result(r, res)
                            # Record end time and status
                            self.execution_context[f'{r}_end_time'] = datetime.now().isoformat()
                            # Normalize ControlFlow status to UI labels
                            try:
                                raw = tasks[r].status.name.lower()
                            except Exception:
                                raw = 'successful' if r in self.task_results else 'failed'
                            status_map = {
                                'successful': 'completed',
                                'failed': 'failed',
                                'running': 'running',
                                'skipped': 'skipped',
                                'pending': 'pending',
                            }
                            self.task_statuses[r] = status_map.get(raw, raw)
                        except Exception as e:
                            logger.error(f"Task '{r}' failed during level {level_index+1} execution: {e}", exc_info=True)
                            self.task_statuses[r] = 'failed'
                            self.execution_context[f'{r}_end_time'] = datetime.now().isoformat()
            except Exception as e:
                logger.error(f"Level {level_index+1} thread execution failed: {e}", exc_info=True)

            # Record results for all tasks in this level and inject into shared context
            for r in level_roles:
                try:
                    task_obj = tasks[r]
                    task_result_value = getattr(task_obj, 'result', None)
                    if task_result_value is not None:
                        self.task_results[r] = task_result_value
                        self._log_task_result(r, task_result_value)
                        # Make upstream results available to downstream tasks via shared context
                        try:
                            if hasattr(task_result_value, 'dict'):
                                workflow_context[r] = task_result_value.dict()
                            else:
                                workflow_context[r] = str(task_result_value)
                        except Exception:
                            workflow_context[r] = str(task_result_value)
                        if r == 'synthesis' and isinstance(task_result_value, InvestmentAnalysis):
                            final_result = task_result_value
                    # Ensure we have a status recorded for the role
                    if r not in self.task_statuses:
                        try:
                            raw = task_obj.status.name.lower()
                        except Exception:
                            raw = 'pending'
                        self.task_statuses[r] = {'successful': 'completed'}.get(raw, raw)
                except Exception:
                    continue

        if final_result is None:
            # Attempt to construct InvestmentAnalysis from upstream results if available
            try:
                market_summary = self.task_results.get('market_analysis')
                risk_summary = self.task_results.get('risk_assessment')
                final_result = InvestmentAnalysis(
                    ticker=ticker,
                    market_analysis=str(getattr(market_summary, 'analysis_summary', market_summary) or ''),
                    sentiment='neutral',
                    recommendation='No specific recommendation provided',
                    confidence=0.5,
                    key_insights=["Automated synthesis placeholder"],
                    risk_assessment=str(getattr(risk_summary, 'risk_summary', risk_summary) or '')
                )
            except Exception as e:
                logger.error(f"Failed to construct fallback InvestmentAnalysis: {e}")
                # Return a minimal safe object rather than raising to avoid user-facing failures
                final_result = InvestmentAnalysis(
                    ticker=ticker,
                    market_analysis='',
                    sentiment='neutral',
                    recommendation='No specific recommendation provided',
                    confidence=0.5,
                    key_insights=["Automated synthesis placeholder"],
                    risk_assessment=''
                )

        # Ensure final result is recorded under 'synthesis' for downstream consumers
        self.task_results['synthesis'] = final_result
        return final_result
    
    def _build_execution_trace(self) -> Dict[str, Any]:
        """Build execution trace for debugging and monitoring"""
        return {
            'workflow_type': self.workflow_type,
            'execution_context': self.execution_context,
            'task_results': {
                task_name: (result.dict() if hasattr(result, 'dict') else str(result))
                for task_name, result in self.task_results.items()
            },
            'configuration_used': self.workflow_config
        }
    
    def _build_agent_invocations(self) -> List[Dict[str, Any]]:
        """Build agent invocation history for monitoring"""
        configured_roles = [agent.get('role') for agent in self.workflow_config.get('agents', []) if agent.get('role')]
        return [
            {
                'task': role,
                'status': self.task_statuses.get(role, 'pending'),
                'timestamp': datetime.now().isoformat()
            }
            for role in configured_roles
        ]
    
    def _get_task_status(self, task_role: str, workflow_status: str, current_task: Optional[str]) -> str:
        """Determine status from real ControlFlow Task status when available."""
        status = self.task_statuses.get(task_role)
        if status:
            # normalize to UI-friendly values
            mapping = {
                'successful': 'completed',
                'failed': 'failed',
                'running': 'running',
                'skipped': 'skipped',
                'pending': 'pending'
            }
            return mapping.get(status, status)
        if task_role == current_task:
            return 'running'
        return 'pending'

    def _get_task_summary(self, role: str) -> Optional[str]:
        """Derive a concise summary string for a task's result, if available."""
        res = self.task_results.get(role)
        try:
            if isinstance(res, BaseModel):
                if role == 'market_analysis' and hasattr(res, 'analysis_summary'):
                    return getattr(res, 'analysis_summary')
                if role == 'risk_assessment' and hasattr(res, 'risk_summary'):
                    return getattr(res, 'risk_summary')
                if role == 'synthesis':
                    # Richer synthesis summary: recommendation + up to 2 insights + sentiment/confidence
                    rec = getattr(res, 'recommendation', None) or ''
                    insights = list(getattr(res, 'key_insights', []) or [])
                    sentiment = getattr(res, 'sentiment', None)
                    confidence = getattr(res, 'confidence', None)
                    parts = []
                    if rec:
                        parts.append(str(rec))
                    if insights:
                        parts.append("; ".join(insights[:2]))
                    tail_bits = []
                    if sentiment:
                        tail_bits.append(str(sentiment).title())
                    if isinstance(confidence, (int, float)):
                        tail_bits.append(f"{int(confidence*100)}%")
                    if tail_bits:
                        parts.append(", ".join(tail_bits))
                    return " — ".join(parts) if parts else None
            elif res is not None:
                s = str(res)
                return s[:200] + ('...' if len(s) > 200 else '')
        except Exception:
            pass
        # If still running, surface latest agent message snippet as a provisional summary
        if self.execution_context.get('current_task') == role and hasattr(self, 'event_handler') and self.event_handler:
            try:
                msgs = self.event_handler.get_events_by_type('agent_message')
                if msgs:
                    content = msgs[-1].get('message_content') or ''
                    return (content or '')[:200]
            except Exception:
                pass
        return None

    def _generate_workflow_graph(self) -> Dict[str, List[Dict[str, Any]]]:
        """Dynamically generate workflow nodes and edges for frontend visualization from config and dependencies."""
        nodes, edges = [], []
        agent_configs = self.workflow_config.get('agents', [])
        current_task = self.execution_context.get('current_task')
        workflow_status = self.execution_context.get('status', 'initializing')

        if not agent_configs:
            return {"nodes": [], "edges": []}

        node_width, x_pos, y_pos = 280, 0, 100

        # Input Node with ticker detection summary and tool
        detection = self.execution_context.get('ticker_detection') or {}
        summary_parts = []
        try:
            det_ticker = detection.get('ticker')
            conf = detection.get('confidence')
            if det_ticker and detection.get('status') in ('success', 'override'):
                if isinstance(conf, (int, float)):
                    summary_parts.append(f"Ticker detected: {det_ticker} ({int(conf*100)}%)")
                else:
                    summary_parts.append(f"Ticker detected: {det_ticker}")
            elif detection:
                summary_parts.append("No ticker detected; please provide a ticker symbol (e.g., AAPL)")
        except Exception:
            pass
        input_summary = "; ".join(summary_parts) if summary_parts else None
        nodes.append({
            "id": "input", "type": "input", "position": {"x": x_pos, "y": y_pos},
            "data": {
                "label": "User Query",
                "status": "completed",
                "description": self.execution_context.get('query', ''),
                "summary": input_summary,
                "tools": ["detect_stock_ticker"],
                "detection": detection
            }
        })
        x_pos += node_width

        # Build mapping for dependencies
        role_to_config = {ac.get('role'): ac for ac in agent_configs if ac.get('role')}
        roles = list(role_to_config.keys())

        # Agent/Task Nodes
        for idx, role in enumerate(roles):
            status = self._get_task_status(role, workflow_status, current_task)
            task_id = None
            try:
                if hasattr(self, 'tasks') and self.tasks and role in self.tasks:
                    task_id = getattr(self.tasks[role], 'id', None)
            except Exception:
                task_id = None
            # Determine tools to display: prefer actually used tools; fall back to configured capability list
            agent_name_for_role = role_to_config[role].get('name', 'N/A')
            used_tools = self._get_tools_used_by_agent(agent_name_for_role)
            try:
                configured_tool_objects = self.registry_manager.get_tools_for_agent(role)
                configured_tools = [t.get('name', '') for t in configured_tool_objects]
            except Exception:
                configured_tools = []
            tools_to_show = used_tools if used_tools else configured_tools
            nodes.append({
                "id": f"task_{role}", "type": "task", "position": {"x": x_pos + idx * node_width, "y": y_pos},
                "data": {
                    "label": role_to_config[role].get('label', role.replace('_', ' ').title()),
                    "status": status,
                    "description": role_to_config[role].get('description', ''),
                    "agentName": agent_name_for_role,
                    "tools": tools_to_show,
                    "liveDetails": self._get_live_details_for_agent(role) if status == 'running' else None,
                    "summary": self._get_task_summary(role),
                    "taskId": task_id,
                }
            })

        # Helper to get node id
        def node_id(role_name: str) -> str:
            return f"task_{role_name}"

        # Create edges based on dependencies; connect input to roles without deps
        dependents = set()
        for role in roles:
            deps = role_to_config[role].get('dependencies', []) or []
            if deps:
                for dep in deps:
                    if dep in roles:
                        edges.append({
                            "id": f"edge_{node_id(dep)}_to_{node_id(role)}",
                            "source": node_id(dep),
                            "target": node_id(role),
                            "type": "depends_on"
                        })
                        dependents.add(role)
            else:
                edges.append({
                    "id": f"edge_input_to_{node_id(role)}",
                    "source": "input",
                    "target": node_id(role),
                    "type": "depends_on"
                })

        # Output Node
        output_status = "completed" if workflow_status == "completed" else "pending"
        # Determine terminal roles (no one depends on them)
        terminal_roles = [r for r in roles if all(r not in (role_to_config.get(other, {}).get('dependencies', []) or []) for other in roles)]
        if not terminal_roles and roles:
            terminal_roles = [roles[-1]]
        # Prefer synthesis for result data
        final_role_for_result = 'synthesis' if 'synthesis' in roles else terminal_roles[0]
        result_data = self.task_results.get(final_role_for_result)
        if isinstance(result_data, BaseModel):
            result_data = result_data.dict()

        nodes.append({
            "id": "output", "type": "output", "position": {"x": x_pos + (len(roles) + 1) * node_width, "y": y_pos},
            "data": {"label": "Final Report", "status": output_status, "result": result_data}
        })
        for role in terminal_roles:
            edges.append({
                "id": f"edge_{node_id(role)}_to_output",
                "source": node_id(role),
                "target": "output",
                "type": "produces"
            })

        return {"nodes": nodes, "edges": edges}


    def _get_live_details_for_agent(self, agent_role: str) -> Optional[Dict[str, Any]]:
        """Get live details for a specific agent if it's the current task."""
        if self.execution_context.get('current_task') == agent_role:
            return {
                'task_name': agent_role,
                'task_progress': self._get_task_progress(agent_role),
                'agent_reasoning': self._get_current_agent_reasoning(),
                'tool_calls': self._get_recent_tool_calls()
            }
        return None
    
    def _get_workflow_metrics(self) -> Dict[str, Any]:
        """Get current workflow metrics"""
        start_time = self.execution_context.get('start_time')
        execution_time = (datetime.now() - start_time).total_seconds() if start_time else 0
        
        # Count based on actual tasks executed or defined
        tasks_in_config = self.workflow_config.get('agents', [])
        total_tasks = len(tasks_in_config) # Add 1 for synthesis

        return {
            'total_tasks': total_tasks,
            'completed_tasks': len(self.task_results),
            'execution_time': execution_time
        }

    # --- Logging helpers ---
    def _log_task_result(self, role: str, result: Any) -> None:
        """Log a concise, safe preview of a task's result for diagnostics."""
        try:
            if hasattr(result, 'dict'):
                payload = result.dict()
            else:
                payload = result
            if isinstance(payload, (dict, list)):
                preview = json.dumps(payload, default=str)
            else:
                preview = str(payload)
            if len(preview) > 400:
                preview = preview[:400] + '...'
            logger.info(f"Task '{role}' completed. Result preview: {preview}")
        except Exception as e:
            logger.warning(f"Could not log result for task '{role}': {e}")

def create_config_driven_workflow(workflow_type: str = "quick_stock_analysis") -> ConfigDrivenWorkflow:
    """
    Factory function to create config-driven workflow instances
    """
    return ConfigDrivenWorkflow(workflow_type)
