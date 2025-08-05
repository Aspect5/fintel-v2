#!/usr/bin/env python3
"""
FinTel v2 - YAML Configuration Demo
This script demonstrates how easy it is to configure agents using YAML files
"""

import sys
import os
from pathlib import Path
import yaml
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """Load and parse a YAML configuration file"""
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}

def demonstrate_agent_configuration():
    """Demonstrate how easy it is to configure agents"""
    print("🤖 FinTel v2 - YAML Agent Configuration Demo")
    print("=" * 60)
    
    # Load agent configuration
    agents_config = load_yaml_config("backend/config/agents_demo.yaml")
    
    print("\n📋 Available Agents:")
    print("-" * 30)
    
    if 'agents' in agents_config:
        for agent_name, config in agents_config['agents'].items():
            print(f"\n🔹 {agent_name}")
            print(f"   Description: {config.get('description', 'N/A')}")
            print(f"   Provider: {config.get('provider', 'N/A')}")
            print(f"   Model: {config.get('model', 'N/A')}")
            print(f"   Tools: {', '.join(config.get('tools', []))}")
            print(f"   Capabilities: {', '.join(config.get('capabilities', []))}")
            print(f"   Enabled: {config.get('settings', {}).get('enabled', True)}")
    
    print("\n🔧 Easy Configuration Changes:")
    print("-" * 35)
    print("• Change provider: Just modify 'provider: openai' to 'provider: google'")
    print("• Change model: Update 'model: gpt-4o-mini' to any supported model") 
    print("• Add tools: Add tool names to the 'tools' list")
    print("• Disable agent: Set 'enabled: false' in settings")
    print("• Adjust temperature: Modify 'temperature: 0.1' for creativity control")

def demonstrate_workflow_configuration():
    """Demonstrate workflow configuration flexibility"""
    print("\n\n🔄 Workflow Configuration Demo")
    print("=" * 60)
    
    # Load workflow configuration  
    workflow_config = load_yaml_config("backend/config/workflow_config_demo.yaml")
    
    if 'workflows' in workflow_config:
        print("\n📊 Available Workflows:")
        print("-" * 25)
        
        for workflow_name, config in workflow_config['workflows'].items():
            print(f"\n🔸 {workflow_name}")
            print(f"   Name: {config.get('name', 'N/A')}")
            print(f"   Description: {config.get('description', 'N/A')}")
            
            if 'steps' in config:
                print(f"   Steps: {len(config['steps'])} total")
                for i, step in enumerate(config['steps'], 1):
                    print(f"     {i}. {step.get('task', 'N/A')} (Agent: {step.get('agent', 'N/A')})")
            
            settings = config.get('settings', {})
            print(f"   Max Time: {settings.get('max_execution_time', 'N/A')}s")
            print(f"   Parallel: {settings.get('parallel_execution', False)}")
    
    print("\n🎯 Dynamic Workflow Selection:")
    print("-" * 35)
    
    if 'workflow_selection' in workflow_config:
        rules = workflow_config['workflow_selection'].get('rules', [])
        for rule in rules:
            if 'keywords' in rule:
                keywords = ', '.join(rule['keywords'])
                workflow = rule['workflow']
                print(f"• Keywords '{keywords}' → {workflow}")
            elif 'default' in rule:
                print(f"• Default workflow: {rule['default']}")

def demonstrate_customization_examples():
    """Show practical customization examples"""
    print("\n\n✨ Customization Examples")
    print("=" * 60)
    
    print("\n🔄 Switching LLM Providers:")
    print("-" * 25)
    print("# For OpenAI (default):")
    print("provider: 'openai'")
    print("model: 'gpt-4o-mini'")
    print("")
    print("# For Google Gemini:")
    print("provider: 'google'") 
    print("model: 'gemini-1.5-flash'")
    print("")
    print("# For Local Model:")
    print("provider: 'local'")
    print("model: 'local-model'")
    
    print("\n🛠️  Adding New Tools:")
    print("-" * 20)
    print("tools:")
    print("  - 'get_market_data'")
    print("  - 'get_company_overview'")
    print("  - 'new_custom_tool'      # <-- Just add here!")
    
    print("\n👥 Creating Agent Teams:")
    print("-" * 23)
    print("teams:")
    print("  quick_analysis:")
    print("    agents:")
    print("      - 'MarketAnalyst'")
    print("      - 'FinancialAnalyst'")
    print("    coordination: 'MarketAnalyst'")
    
    print("\n⚙️  Workflow Modifications:")
    print("-" * 26)
    print("# Make step optional:")
    print("- step: 'economic_analysis'")
    print("  required: false           # <-- Easy toggle!")
    print("")
    print("# Change execution order:")
    print("  depends_on: ['step1', 'step2']  # <-- Define dependencies")
    print("")
    print("# Add parallel processing:")
    print("  parallel_execution: true        # <-- Speed boost!")

def main():
    """Main demonstration function"""
    try:
        demonstrate_agent_configuration()
        demonstrate_workflow_configuration() 
        demonstrate_customization_examples()
        
        print("\n\n🎉 Configuration Demo Complete!")
        print("=" * 60)
        print("Key Benefits:")
        print("• No code changes needed for most customizations")
        print("• Easy A/B testing of different configurations") 
        print("• Simple agent and workflow swapping")
        print("• Modular design for maximum flexibility")
        print("• Production-ready with fallback mechanisms")
        
        print("\n💡 Next Steps:")
        print("1. Copy backend/config/agents_demo.yaml to agents.yaml")
        print("2. Modify the configuration to your needs")
        print("3. Restart the application to see changes")
        print("4. Monitor performance and adjust as needed")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())