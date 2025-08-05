# AGGRESSIVE REPOSITORY CLEANUP PROMPT

You are an aggressive repository cleanup agent. Your mission is to ruthlessly eliminate unused files, duplicate code, redundant documentation, and test files that are cluttering this financial intelligence repository. This is a production codebase that needs to be lean and maintainable.

## CRITICAL CLEANUP TARGETS

### 1. WORKFLOW DUPLICATION ELIMINATION
The `backend/workflows/` directory contains multiple workflow implementations. After testing, I found that **BOTH workflows are actually being used** by the application:

**KEEP BOTH WORKING WORKFLOW IMPLEMENTATIONS:**
- **PRIMARY**: `simplified_workflow.py` (655 lines) - Used for "Comprehensive Analysis" workflow
- **SECONDARY**: `enhanced_simplified_workflow.py` (532 lines) - Used for "Enhanced Simplified Analysis" workflow
- **KEEP**: `base.py` (35 lines) - Required by both workflows
- **KEEP**: `config_loader.py` (170 lines) - Used by `app.py` for workflow configs
- **DELETE**: All other workflow files:
  - `controlflow_enhanced_workflow.py` (394 lines) - REDUNDANT
  - `enhanced_orchestrator.py` (488 lines) - REDUNDANT
  - `dependency_workflow.py` (480 lines) - REDUNDANT
  - `orchestrator.py` (99 lines) - OBSOLETE
  - `templates.py` (103 lines) - UNUSED

**RATIONALE**: The application uses both workflows through the configuration system in `workflow_config.yaml`. Users can choose between "Comprehensive Analysis" and "Enhanced Simplified Analysis" in the frontend. Both workflows are functional and provide different analysis approaches.

### 2. TEST FILE ELIMINATION
**DELETE ALL TEST FILES** - They are development artifacts cluttering production:

```
test_adaptive_workflow.py
test_workflow_orchestration_diagnosis.py
test_detailed_workflow.py
test_enhanced_workflow.py
test_event_handling.py
test_agent_creation.py
test_minimal_workflow.py
test_simplified_workflow.py
test_workflow_diagnosis.py
test_api_endpoints.py
test_enhanced_system.py
backend/test_auto_discovery.py
test_retry_scenario.md
```

**RATIONALE**: These are development/testing artifacts that don't belong in a production repository. They reference outdated workflow patterns and create confusion.

### 3. DOCUMENTATION CLEANUP
**DELETE REDUNDANT DOCUMENTATION FILES:**

**KEEP ONLY:**
- `README.md` - Main project documentation
- `docs/help.md` - User help documentation
- `docs/ARCHITECTURAL_BLUEPRINT_FOR_PRODUCTION.md` - Production architecture guide

**DELETE ALL OTHERS:**
```
CONTROLFLOW_BEST_PRACTICES_IMPLEMENTATION.md
ENHANCED_WORKFLOW_INTEGRATION_FIXES_SUMMARY.md
IMMEDIATE_ISSUES_ANALYSIS.md
GOOGLE_ADK_INTEGRATION_GUIDE.md
CODING_LLM_AGENT_PROMPT.md
DEBUG_ENHANCED_WORKFLOW_ISSUES_PROMPT.md
CONTROLFLOW_INTEGRATION_GUIDE.md
WORKFLOW_DIAGNOSIS_SUMMARY.md
docs/FUTURE_RESEARCH_PROMPTS.md
docs/API_INTEGRATION_STRATEGY.md
docs/api_research_prompt.md
docs/RESEARCH_PROMPT_FOR_GOOGLE.md
docs/ARCHITECTURAL_GUIDANCE_FOR_ADVANCED_FEATURES.md
AGENT_ANALYSIS_PROMPT.md
COORDINATOR_DELEGATION_FIX_SUMMARY.md
ADAPTIVE_COORDINATOR_IMPROVEMENTS.md
AI_AGENT_DIAGNOSTIC_PROMPT.md
RETRY_ANALYSIS_FIX_SUMMARY.md
ENHANCED_WORKFLOW_IMPLEMENTATION_SUMMARY.md
prompt.md
```

**RATIONALE**: These are development notes, research prompts, and temporary documentation that clutters the repository. Only production-ready documentation should remain.

### 4. BACKUP FILE ELIMINATION
**DELETE ALL BACKUP FILES:**
```
frontend/src/components/ToolkitPanel.tsx.backup
backend/agents/registry.py.backup
docs/Copy of ControlFlow Multi-Agent Architecture Best Practices.txt
```

### 5. REPORT CLEANUP
**DELETE DEVELOPMENT REPORTS:**
```
reports/I_analysis_2025-07-31_12-22-15.md
```

### 6. DEVELOPMENT SCRIPTS CLEANUP
**DELETE DEVELOPMENT SCRIPTS:**
```
manual_test_enhanced_system.py
debug_tool_instances.py
troubleshoot_controlflow.py
```

## CLEANUP EXECUTION STRATEGY

### PHASE 1: SAFETY CHECKS
1. **Verify Dependencies**: Before deleting any file, check if it's imported or referenced anywhere
2. **Backup Critical Files**: Create a temporary backup of files you're unsure about
3. **Check Git History**: Ensure important code isn't lost

### PHASE 2: AGGRESSIVE DELETION
1. **Delete Test Files First**: These are clearly development artifacts
2. **Delete Redundant Workflows**: Keep only `enhanced_simplified_workflow.py`
3. **Delete Documentation**: Remove all development notes and research prompts
4. **Delete Backup Files**: Remove all `.backup` and `Copy of` files
5. **Delete Development Scripts**: Remove manual test and debug scripts

### PHASE 3: CODE CLEANUP
1. **Update Imports**: Fix any broken imports after deletion
2. **Remove Dead Code**: Eliminate any code that referenced deleted files
3. **Update Documentation**: Ensure remaining docs are accurate

### PHASE 4: VERIFICATION
1. **Test Core Functionality**: Ensure the main application still works
2. **Check for Broken References**: Verify no broken imports or references
3. **Validate Workflow**: Test that the remaining workflow works correctly

## SUCCESS CRITERIA

After cleanup, the repository should have:
- **Two working workflow implementations**:
  - `simplified_workflow.py` for "Comprehensive Analysis"
  - `enhanced_simplified_workflow.py` for "Enhanced Simplified Analysis"
- **No test files** in the root or backend directories
- **Minimal documentation** (only production-ready docs)
- **No backup files** or duplicate files
- **Clean import structure** with no broken references
- **`npm run dev` works perfectly** with both workflow options available
- **Reduced repository size** by at least 30%

## EXECUTION COMMANDS

Use these commands to execute the cleanup:

```bash
# 1. Delete test files
find . -name "test_*.py" -not -path "./backend/venv/*" -delete
find . -name "test_*.md" -not -path "./backend/venv/*" -delete

# 2. Delete redundant workflows (keep both working workflows)
cd backend/workflows
rm controlflow_enhanced_workflow.py enhanced_orchestrator.py dependency_workflow.py orchestrator.py templates.py

# 3. Delete backup files
find . -name "*.backup" -delete
find . -name "Copy of *" -delete

# 4. Delete development documentation
# (List all the .md files to delete)

# 5. Delete development scripts
rm manual_test_enhanced_system.py debug_tool_instances.py troubleshoot_controlflow.py

# 6. Clean up reports
rm -rf reports/

# 7. Update imports and fix broken references
# (Check and fix any import statements that reference deleted files)
```

## IMPORTANT NOTES

- **PRIORITY: `npm run dev` MUST WORK**: This is the primary requirement - everything else is secondary
- **BE CONSERVATIVE**: Don't delete anything that might break the application
- **FOCUS ON PRODUCTION**: Remove everything that's not needed for production
- **MAINTAIN FUNCTIONALITY**: Ensure the core application still works after cleanup
- **TEST AFTER EACH STEP**: Run `npm run dev` after each major deletion to verify it still works
- **DOCUMENT CHANGES**: Update any remaining documentation to reflect the cleanup

## EXPECTED OUTCOME

A clean, maintainable repository with:
- Two working workflow implementations providing different analysis approaches
- No development artifacts
- Minimal, focused documentation
- Reduced complexity and maintenance burden
- **`npm run dev` works perfectly** - users can choose between "Comprehensive Analysis" and "Enhanced Simplified Analysis"
- Faster development cycles due to reduced clutter

Execute this cleanup conservatively and test frequently. The primary goal is ensuring `npm run dev` continues to work perfectly with both workflow options available. 