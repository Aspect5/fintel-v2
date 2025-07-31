export interface RetryAnalysisData {
  agentsEncounteringErrors: string[];
  specificErrors: string[];
  retryAttempts: number;
  adaptationStrategies: string[];
  adaptationSuccess: boolean;
  impactOnAnalysis: string;
  retryDetails: RetryDetail[];
}

export interface RetryDetail {
  agent: string;
  specialization: string;
  tool: string;
  totalAttempts: number;
  finalStatus: 'success' | 'failed';
  retrySequence: RetryAttempt[];
  adaptationStrategy?: string;
}

export interface RetryAttempt {
  attemptNumber: number;
  status: 'success' | 'error';
  input: any;
  errorType?: string;
  errorMessage?: string;
  receivedData?: any;
  expectedFormat?: string;
}

export interface ParsedReport {
  executiveSummary: string;
  investmentRecommendation: string;
  keyFindings: string[];
  riskAssessment: string;
  actionItems: string[];
  retryAnalysis?: RetryAnalysisData;
  confidenceLevel: number;
  queryAnalysis?: string;
  executionTime?: string;
}

export function parseReportContent(content: string): ParsedReport {
  const lines = content.split('\n');
  const sections: { [key: string]: string[] } = {};
  let currentSection = '';
  let currentLines: string[] = [];

  // Parse sections based on markdown headers
  for (const line of lines) {
    if (line.startsWith('## ')) {
      // Save previous section
      if (currentSection && currentLines.length > 0) {
        sections[currentSection] = currentLines;
      }
      
      // Start new section
      currentSection = line.replace('## ', '').trim();
      currentLines = [];
    } else if (line.startsWith('### ')) {
      // Handle subsections (like in retry analysis)
      if (currentSection && currentLines.length > 0) {
        sections[currentSection] = currentLines;
      }
      currentSection = line.replace('### ', '').trim();
      currentLines = [];
    } else {
      currentLines.push(line);
    }
  }
  
  // Save last section
  if (currentSection && currentLines.length > 0) {
    sections[currentSection] = currentLines;
  }

  // Extract sections
  const executiveSummary = extractSectionContent(sections, ['Executive Summary', '📊 Investment Analysis Report']);
  const investmentRecommendation = extractSectionContent(sections, ['Investment Recommendation']);
  const keyFindings = extractKeyFindings(sections);
  const riskAssessment = extractSectionContent(sections, ['Risk Assessment', '⚠️ Risk Assessment']);
  const actionItems = extractActionItems(sections);
  const retryAnalysis = extractRetryAnalysis(sections);
  const confidenceLevel = extractConfidenceLevel(content);
  const queryAnalysis = extractSectionContent(sections, ['Query Analysis', 'Fintel Query Analysis']);
  const executionTime = extractExecutionTime(content);

  return {
    executiveSummary,
    investmentRecommendation,
    keyFindings,
    riskAssessment,
    actionItems,
    retryAnalysis,
    confidenceLevel,
    queryAnalysis,
    executionTime
  };
}

function extractSectionContent(sections: { [key: string]: string[] }, possibleNames: string[]): string {
  for (const name of possibleNames) {
    if (sections[name]) {
      return sections[name].join('\n').trim();
    }
  }
  return '';
}

function extractKeyFindings(sections: { [key: string]: string[] }): string[] {
  const keyFindingsSection = extractSectionContent(sections, ['Key Findings']);
  if (!keyFindingsSection) return [];

  const lines = keyFindingsSection.split('\n');
  const findings: string[] = [];
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('-') || trimmed.startsWith('•') || trimmed.startsWith('*')) {
      findings.push(trimmed.substring(1).trim());
    }
  }
  
  return findings;
}

function extractActionItems(sections: { [key: string]: string[] }): string[] {
  const actionItemsSection = extractSectionContent(sections, ['Action Items', '📋 Action Items']);
  if (!actionItemsSection) return [];

  const lines = actionItemsSection.split('\n');
  const items: string[] = [];
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('-') || trimmed.startsWith('•') || trimmed.startsWith('*')) {
      items.push(trimmed.substring(1).trim());
    }
  }
  
  return items;
}

function extractRetryAnalysis(sections: { [key: string]: string[] }): RetryAnalysisData | undefined {
  const retrySection = extractSectionContent(sections, ['🔄 Agent Adaptation & Retry Analysis', '🔄 Retry Analysis']);
  if (!retrySection) return undefined;

  const lines = retrySection.split('\n');
  const retryDetails: RetryDetail[] = [];
  let currentAgent = '';
  let currentSpecialization = '';
  let currentTool = '';
  let currentTotalAttempts = 0;
  let currentFinalStatus: 'success' | 'failed' = 'failed';
  let currentRetrySequence: RetryAttempt[] = [];
  let currentAdaptationStrategy = '';

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    // Check for agent header
    if (line.startsWith('### ') && !line.includes('Tool:') && !line.includes('Total Attempts:')) {
      // Save previous agent data if exists
      if (currentAgent && currentTool) {
        retryDetails.push({
          agent: currentAgent,
          specialization: currentSpecialization,
          tool: currentTool,
          totalAttempts: currentTotalAttempts,
          finalStatus: currentFinalStatus,
          retrySequence: currentRetrySequence,
          adaptationStrategy: currentAdaptationStrategy
        });
      }
      
      // Parse new agent
      const agentMatch = line.match(/### (.+?) \((.+?)\)/);
      if (agentMatch) {
        currentAgent = agentMatch[1];
        currentSpecialization = agentMatch[2];
        currentTool = '';
        currentTotalAttempts = 0;
        currentFinalStatus = 'failed';
        currentRetrySequence = [];
        currentAdaptationStrategy = '';
      }
    }
    
    // Check for tool information
    if (line.startsWith('**Tool:**')) {
      currentTool = line.replace('**Tool:**', '').replace(/`/g, '').trim();
    }
    
    // Check for total attempts
    if (line.startsWith('**Total Attempts:**')) {
      const attemptsMatch = line.match(/\*\*Total Attempts:\*\* (\d+)/);
      if (attemptsMatch) {
        currentTotalAttempts = parseInt(attemptsMatch[1]);
      }
    }
    
    // Check for final status
    if (line.startsWith('**Final Status:**')) {
      if (line.includes('✅ Success')) {
        currentFinalStatus = 'success';
      } else {
        currentFinalStatus = 'failed';
      }
    }
    
    // Check for adaptation strategy
    if (line.startsWith('**Adaptation Strategy:**')) {
      currentAdaptationStrategy = line.replace('**Adaptation Strategy:**', '').trim();
    }
    
    // Parse retry sequence
    if (line.startsWith('**Attempt ')) {
      const attemptMatch = line.match(/\*\*Attempt (\d+)\*\* (✅|❌)/);
      if (attemptMatch) {
        const attemptNumber = parseInt(attemptMatch[1]);
        const status = attemptMatch[2] === '✅' ? 'success' : 'error';
        
        const attempt: RetryAttempt = {
          attemptNumber,
          status,
          input: 'N/A'
        };
        
        // Look ahead for input and error details
        for (let j = i + 1; j < lines.length && j < i + 10; j++) {
          const nextLine = lines[j].trim();
          if (nextLine.startsWith('- **Input:**')) {
            attempt.input = nextLine.replace('- **Input:**', '').replace(/`/g, '').trim();
          } else if (nextLine.startsWith('- **Error Type:**')) {
            attempt.errorType = nextLine.replace('- **Error Type:**', '').trim();
          } else if (nextLine.startsWith('- **Error Message:**')) {
            attempt.errorMessage = nextLine.replace('- **Error Message:**', '').trim();
          } else if (nextLine.startsWith('- **Received Data:**')) {
            attempt.receivedData = nextLine.replace('- **Received Data:**', '').replace(/`/g, '').trim();
          } else if (nextLine.startsWith('- **Expected Format:**')) {
            attempt.expectedFormat = nextLine.replace('- **Expected Format:**', '').trim();
          } else if (nextLine === '' || nextLine.startsWith('**')) {
            break;
          }
        }
        
        currentRetrySequence.push(attempt);
      }
    }
  }
  
  // Add the last agent
  if (currentAgent && currentTool) {
    retryDetails.push({
      agent: currentAgent,
      specialization: currentSpecialization,
      tool: currentTool,
      totalAttempts: currentTotalAttempts,
      finalStatus: currentFinalStatus,
      retrySequence: currentRetrySequence,
      adaptationStrategy: currentAdaptationStrategy
    });
  }

  if (retryDetails.length === 0) return undefined;

  // Aggregate retry analysis data
  const agentsEncounteringErrors = [...new Set(retryDetails.map(d => d.agent))];
  const specificErrors = [...new Set(retryDetails.flatMap(d => 
    d.retrySequence.filter(r => r.status === 'error').map(r => r.errorType || 'Unknown error')
  ))];
  const retryAttempts = retryDetails.reduce((sum, d) => sum + d.totalAttempts, 0);
  const adaptationStrategies = [...new Set(retryDetails.map(d => d.adaptationStrategy).filter(Boolean))];
  const adaptationSuccess = retryDetails.some(d => d.finalStatus === 'success');
  const impactOnAnalysis = adaptationSuccess 
    ? 'Agents successfully adapted to tool errors, ensuring analysis completion'
    : 'Some tool errors may have impacted analysis quality';

  return {
    agentsEncounteringErrors,
    specificErrors,
    retryAttempts,
    adaptationStrategies,
    adaptationSuccess,
    impactOnAnalysis,
    retryDetails
  };
}

function extractConfidenceLevel(content: string): number {
  const confidenceMatch = content.match(/confidence.*?(\d+)/i);
  if (confidenceMatch) {
    const level = parseInt(confidenceMatch[1]);
    return Math.min(Math.max(level / 10, 0), 1); // Convert to 0-1 scale
  }
  return 0.85; // Default confidence
}

function extractExecutionTime(content: string): string {
  const timeMatch = content.match(/\*\*Analysis Time:\*\* ([\d.]+) seconds/);
  return timeMatch ? timeMatch[1] : '';
} 