# backend/agents/templates.py
from typing import Dict, Any, List
from pathlib import Path
import yaml
import controlflow as cf
from backend.tools.registry import get_tool_registry

class AgentTemplate:
    """Template for creating agents with predefined configurations"""
    
    def __init__(self, template_data: Dict[str, Any]):
        self.name = template_data['name']
        self.base_instructions = template_data.get('base_instructions', '')
        self.required_tools = template_data.get('required_tools', [])
        self.optional_tools = template_data.get('optional_tools', [])
        self.model_preference = template_data.get('model_preference', 'gpt-4o-mini')
        self.parameters = template_data.get('parameters', {})
    
    def create_agent(
        self, 
        name: str = None,
        additional_instructions: str = "",
        additional_tools: List[str] = None,
        model: str = None,
        **kwargs
    ) -> cf.Agent:
        """Create an agent instance from this template"""
        tool_registry = get_tool_registry()
        
        # Combine tools
        all_tool_names = self.required_tools.copy()
        if additional_tools:
            all_tool_names.extend(additional_tools)
        
        # Get actual tool objects
        tools = tool_registry.get_tools(all_tool_names)
        
        # Combine instructions
        full_instructions = self.base_instructions
        if additional_instructions:
            full_instructions += f"\nAdditional Instructions: {additional_instructions}"
        
        # Fill in any template parameters
        for key, value in kwargs.items():
            if key in self.parameters:
                full_instructions = full_instructions.replace(f"{{{key}}}", str(value))
        
        return cf.Agent(
            name=name or self.name,
            instructions=full_instructions,
            tools=tools,
            model=model or self.model_preference
        )

class AgentTemplateRegistry:
    """Registry for agent templates"""
    
    def __init__(self):
        self.templates: Dict[str, AgentTemplate] = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load templates from YAML files"""
        template_dir = Path(__file__).parent.parent / "config" / "agent_templates"
        if not template_dir.exists():
            template_dir.mkdir(parents=True)
            self._create_default_templates(template_dir)
        
        for template_file in template_dir.glob("*.yaml"):
            with open(template_file, 'r') as f:
                data = yaml.safe_load(f)
                if 'templates' in data:
                    for template_data in data['templates']:
                        template = AgentTemplate(template_data)
                        self.templates[template.name] = template
    
    def _create_default_templates(self, template_dir: Path):
        """Create default agent templates"""
        default_templates = {
            "templates": [
                {
                    "name": "DataAnalyst",
                    "base_instructions": """You are a data analyst specializing in {domain}.
                    
Your core responsibilities:
1. Analyze data using the provided tools
2. Identify patterns and insights
3. Provide clear, actionable recommendations
4. Support conclusions with data

Domain expertise: {domain}
Focus area: {focus_area}""",
                    "required_tools": ["get_market_data", "calculate_pe_ratio"],
                    "optional_tools": ["analyze_cash_flow", "get_competitor_analysis"],
                    "model_preference": "gpt-4o-mini",
                    "parameters": {
                        "domain": "financial markets",
                        "focus_area": "equity analysis"
                    }
                },
                {
                    "name": "ResearchAnalyst",
                    "base_instructions": """You are a research analyst focused on {research_type}.
                    
Your approach:
1. Gather comprehensive data from multiple sources
2. Synthesize information into coherent insights
3. Identify trends and correlations
4. Provide evidence-based conclusions

Research type: {research_type}
Methodology: {methodology}""",
                    "required_tools": ["get_economic_data_from_fred"],
                    "optional_tools": ["get_market_data", "get_company_overview"],
                    "model_preference": "gpt-4o",
                    "parameters": {
                        "research_type": "macroeconomic trends",
                        "methodology": "quantitative analysis"
                    }
                }
            ]
        }
        
        with open(template_dir / "default_templates.yaml", 'w') as f:
            yaml.dump(default_templates, f, default_flow_style=False)
    
    def create_agent_from_template(
        self,
        template_name: str,
        **kwargs
    ) -> cf.Agent:
        """Create an agent from a template"""
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        return self.templates[template_name].create_agent(**kwargs)
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """Get information about a template"""
        if template_name not in self.templates:
            return None
        
        template = self.templates[template_name]
        return {
            "name": template.name,
            "required_tools": template.required_tools,
            "optional_tools": template.optional_tools,
            "parameters": template.parameters,
            "model_preference": template.model_preference
        }