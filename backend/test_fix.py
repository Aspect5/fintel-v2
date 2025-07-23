# Add os to builtins so it's available everywhere
import os
import builtins
builtins.os = os

# Now try importing everything
import config
os.environ['OPENAI_API_KEY'] = config.OPENAI_API_KEY or ''

try:
    from agents import get_agents_from_config
    agents = get_agents_from_config(provider='openai')
    print('SUCCESS: Agents created successfully!')
    print('Agent names:', list(agents.keys()))
except Exception as e:
    print('ERROR:', e)
    import traceback
    traceback.print_exc()
