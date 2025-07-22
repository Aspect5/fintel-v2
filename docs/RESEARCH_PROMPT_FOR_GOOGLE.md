# Architectural Guidance for Deploying a Gemini Tool-Using Web App on Google Cloud Run

**To:** Google Cloud & Gemini API Expert Teams
**From:** FINTEL Application Development
**Subject:** Seeking best practices for deploying a client-side, tool-using Gemini web application from an AI Studio prototype to a production environment on Google Cloud Run.

## 1. High-Level Context

We are developing **FINTEL**, a sophisticated Financial Intelligence Assistant. It's a modular, multi-agent AI system built with a modern web stack (React, TypeScript, Vite) and a Node.js/Express backend. The application leverages the Google Gemini API (`gemini-2.5-flash`) to orchestrate complex financial analysis tasks.

### Core Application Workflow

The workflow is inspired by a ReAct-style agentic framework:

1.  **User Query**: A user submits a complex financial query (e.g., "What is the impact of a 10% tariff on the automotive industry in the USA and Eurozone?").
2.  **Coordinator Planner**: An initial Gemini API call analyzes the query and constructs a plan. This plan involves selecting several specialized agents (e.g., `MarketAnalyst`, `EconomicForecaster`) to handle discrete parts of the query.
3.  **Agent Execution**: The client-side application "invokes" these agents. Each agent is another instance of a Gemini call, given a specific persona, a task, and a list of available "tools" (e.g., `get_market_data`, `get_economic_data`).
4.  **Tool Reasoning & Execution**: The agent reasons about which tools to use for its task. It returns a JSON object specifying the tool and parameters. The client-side code then parses this and executes the actual tool function, which calls a third-party API (e.g., Alpha Vantage, FRED).
5.  **Synthesis**: The results from the tool execution are sent back to the agent in a subsequent Gemini call. The agent then synthesizes a final answer for its sub-task.
6.  **Final Report Generation**: Finally, all the synthesized findings from the individual agents are collected and sent to a "Report Synthesizer" (a final Gemini call) to create a single, cohesive, user-facing report.

## 2. The Deployment Challenge

The application works perfectly in a local development environment and in sandboxes like Google AI Studio. However, upon deployment to **Google Cloud Run**, we encounter a critical, blocking error during the very first Gemini API call from the client:

```json
{
  "error": "Proxying failed",
  "details": "ReadableStream uploading is not supported",
  "name": "NotSupportedError",
  "proxiedUrl": "https://fintel-financial-intelligence-assistant-....run.app/api-proxy/v1beta/models/gemini-2.5-flash:generateContent"
}
```

This error indicates that the Gemini Web SDK's use of `fetch` with a `ReadableStream` body is incompatible with the proxy or networking environment within our deployed Google Cloud Run service.

### Current Architectural Solution

To mitigate this, we have implemented a **Backend-for-Frontend (BFF)** pattern. The Cloud Run container runs our Node.js/Express server, which performs two roles:
1.  Serves the static assets for the React single-page application.
2.  Exposes a local API endpoint (e.g., `/api/gemini/generateContent`).

The client-side React application has been refactored to **never call the Gemini API directly**. Instead, all requests that would have gone to the Gemini API are now directed to our own backend endpoint. The Node.js server then securely calls the Gemini API using the server-side SDK and pipes the response back to the client.

## 3. Core Questions for Google Experts

While the BFF pattern appears to solve the immediate error, we want to ensure we are following the canonical, most robust, and future-proof patterns.

1.  **Recommended Architecture**: Is the Backend-for-Frontend (BFF)/proxy pattern the officially recommended architecture for deploying a web app that uses the Gemini Web SDK on Google Cloud Run? Are there specific configurations for either the SDK or Cloud Run that would make direct client-side calls more reliable, or is the BFF pattern considered the best practice?

2.  **Manual Agents vs. Native Tool Calling**: Our application uses a manual, multi-step agent loop (LLM plans -> client executes -> client sends results). How does this compare to using Gemini's native `tools` and `FunctionDeclaration` features? Would adopting native tool calling simplify our architecture or offer better performance/reliability in a deployed environment? Does the underlying SDK communication method change when using native tools in a way that might avoid the `ReadableStream` issue?

3.  **Third-Party API Key Management**: Google AI Studio provides a seamless UI for managing API keys for external tools. When moving to a self-hosted application on Cloud Run, what is the recommended pattern for managing these third-party keys (e.g., `ALPHA_VANTAGE_API_KEY`)? Should they be stored in Google Secret Manager and accessed exclusively by our backend proxy when it executes a tool call on behalf of the client?

4.  **Bridging AI Studio and Cloud Run**: What are the key environmental and networking differences between the AI Studio sandbox and a standard Google Cloud Run container that developers should be aware of when prototyping tool-using applications? Is there documentation that covers best practices for this transition?

Thank you for your time and expertise. Clear guidance on these points will be invaluable for us and likely for many other developers building on the Gemini platform.
