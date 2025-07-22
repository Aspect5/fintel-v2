
# Architectural Guidance: Implementing Advanced FINTEL Capabilities

This document provides architectural patterns and best practices for implementing the advanced features outlined in the FINTEL roadmap. The guidance is tailored for a Google Cloud serverless environment, leveraging the Gemini API and related services.

---

### **1. Stateful Conversations & Long-Term Memory**

**Challenge:** Evolve from stateless workflows to conversations that maintain context and have long-term memory.

**Architectural Recommendations:**

*   **1.1. Context Management (Short-Term Memory):**
    *   **Pattern:** Use a "Summarization and Re-injection" strategy. Passing the entire raw chat history with every API call is inefficient and costly, quickly exceeding token limits.
    *   **Implementation:**
        1.  **Store Raw History:** Persist the full conversation log in a fast, key-value store like **Firestore** or **Memorystore (Redis)**, keyed by a session ID.
        2.  **Generate Summary:** Before executing the main agent logic, make a dedicated, lightweight Gemini call (`gemini-2.5-flash` is ideal for this) with the prompt: `"Summarize this conversation history into a concise context object containing key entities, user intent, previous results, and follow-up questions. History: [Last N messages]"`.
        3.  **Inject Context:** Inject this summarized context object into the main prompt for your Coordinator and Agent LLM calls. This keeps the primary prompt lean and focused while retaining essential context.
    *   **Benefit:** Balances context preservation with token efficiency and lower latency.

*   **1.2. Long-Term Memory (RAG with Vector Search):**
    *   **Pattern:** Implement a Retrieval-Augmented Generation (RAG) pipeline using **Vertex AI Vector Search** (formerly Matching Engine). This is the canonical Google Cloud solution for this use case.
    *   **Implementation:**
        1.  **Document Chunking:** After a report is generated, chunk its content into meaningful sections (e.g., Executive Summary, individual Agent Findings, Recommendations). Each chunk becomes a document for embedding.
        2.  **Embedding Generation:** Use a text embedding model (e.g., `text-embedding-004` from the Gemini family) to convert each document chunk into a vector.
        3.  **Indexing:** Store these vectors in a Vertex AI Vector Search index. Crucially, store metadata alongside each vector, such as `report_id`, `section_title`, `agent_name`, and `timestamp`.
        4.  **Retrieval:** When a new query comes in, first embed the query using the same model. Then, perform an Approximate Nearest Neighbor (ANN) search against the Vector Search index to find the most relevant document chunks from past reports.
        5.  **Augmentation:** Inject the retrieved text from these chunks as context into the main LLM prompt. The prompt becomes: `"Based on the following relevant information from past analyses, answer the user's query. Relevant Info: [Retrieved Chunks]. User Query: [Query]"`.
    *   **Structure:** Documents in Vector Search should have a clear ID and a `metadata` payload. Example: `{"id": "report123_summary", "embedding": [...], "restricts": [{"namespace": "agent_name", "allow": ["MarketAnalyst"]}, {"namespace": "year", "allow": ["2024"]}]}`. Use namespaces for efficient filtering.

*   **1.3. RAG vs. Fine-Tuning:**
    *   **RAG is almost always the starting point.** It's cheaper, faster to implement, and doesn't suffer from knowledge cutoffs. It's ideal for incorporating new information on the fly.
    *   **Consider Fine-Tuning only when you need to change the model's *behavior*, *style*, or *formatting*, not just its knowledge.** For example, if you want FINTEL to consistently adopt a specific institutional tone of voice or always structure its output in a unique, complex JSON format that prompting alone cannot achieve reliably, then fine-tuning is appropriate. Do not use fine-tuning to "teach" the model facts; that is the job of RAG.

---

### **2. Proactive Agent Monitoring & Alerting**

**Challenge:** Transition agents from being purely reactive to running autonomously in the background to monitor data and send alerts.

**Architectural Recommendations:**

*   **2.1. Triggering Mechanism:**
    *   **Pattern:** A combination of **Cloud Scheduler** and **Cloud Functions** (2nd gen) is the most robust and scalable serverless approach.
    *   **Implementation:**
        1.  **Scheduler Job:** Create a Cloud Scheduler job that runs on a defined cron schedule (e.g., every 15 minutes for a stock monitor, daily for an economic data check).
        2.  **Pub/Sub Target:** Configure the scheduler's target to be a **Pub/Sub topic** (e.g., `agent-triggers`). This decouples the scheduler from the execution logic.
        3.  **Event-Driven Function:** Create a Cloud Function that is triggered by messages on the `agent-triggers` Pub/Sub topic. The message payload can contain the agent configuration (e.g., `{"agentName": "MarketAnalyst", "task": "Check NVDA price against threshold of $850"}`).
        4.  **Agent Logic:** The Cloud Function contains the logic to run the specified agent task (call the tool, check the data, and decide if an alert is needed).
    *   **Benefit:** This is highly scalable, resilient (Pub/Sub provides at-least-once delivery), and cost-effective, as you only pay for the function's execution time.

*   **2.2. Managing State & Cost:**
    *   **State Management:** Store the "state" of the monitor (e.g., the last checked price, the alert threshold) in **Firestore**. The Cloud Function reads the current state from Firestore before executing and updates it afterward. This prevents duplicate alerts and provides a history.
    *   **Cost Control:**
        1.  **Function Timeouts:** Set a hard timeout on your Cloud Function (e.g., 60 seconds) to prevent runaway executions.
        2.  **Budget Alerts:** Use **Google Cloud Billing budget alerts** to get notified if costs are approaching a specified threshold.
        3.  **Smart Scheduling:** Don't run monitors more frequently than the data source updates. For market data, 5-15 minutes might be fine. For daily economic data, run the job once a day.
        4.  **Disable Thinking:** For these simple, automated check-and-alert tasks, you can significantly reduce cost and latency by disabling the model's "thinking" feature. In your Gemini call within the function, set `config: { thinkingConfig: { thinkingBudget: 0 } }`.

*   **2.3. Proactive Communication:**
    *   **Pattern:** Use a dedicated notification service triggered from your agent's Cloud Function.
    *   **Implementation:** Once the agent logic in the Cloud Function determines an alert is necessary, it can:
        *   **Send an email:** Use an API service like **SendGrid** or **Mailgun**.
        *   **Send a push notification:** If you have a mobile app or PWA, use **Firebase Cloud Messaging (FCM)**.
        *   **Send a Slack/Teams message:** Call the respective webhook APIs.
    *   The Cloud Function should format the LLM's output into the required payload for the chosen notification service.

---

### **3. Advanced Tool Orchestration & Self-Correction**

**Challenge:** Build more resilient agents that can handle errors and execute complex, multi-step tasks.

**Architectural Recommendations:**

*   **3.1. Self-Correction Loops (ReAct Pattern):**
    *   **Pattern:** Implement the loop logic within your server-side code (e.g., in a dedicated Cloud Function or your Express server). Do not try to make the LLM loop internally.
    *   **Implementation:**
        1.  Wrap your agent execution in a `for` loop with a maximum number of attempts (e.g., 3-5 iterations to prevent infinite loops).
        2.  **Initial Call:** The agent makes its first tool call request.
        3.  **Execute & Observe:** Your code executes the tool. `try...catch` this execution robustly.
        4.  **Feedback:** Construct a "feedback" payload.
            *   On success: `{"tool_name": "...", "status": "success", "output": "..."}`.
            *   On failure: `{"tool_name": "...", "status": "error", "error_message": "API returned 404 Not Found"}`.
        5.  **Next Iteration:** Send this feedback payload back to the agent in the next LLM call. The prompt should be: `"You are performing a task. You previously called a tool and here is the result: [Feedback Payload]. Analyze the result. If it was successful, proceed with synthesizing your final answer. If it failed, decide on your next step: either call the same tool with corrected parameters, call a different tool, or admit failure if you cannot proceed. Your original task was: [Task]"`.
        6.  The loop continues until the agent returns a final answer instead of another tool call, or the max attempts are reached.

*   **3.2. Sequential Tool-Chaining:**
    *   **Pattern:** The orchestration logic should reside in your server-side TypeScript code. Delegating multi-step reasoning to a single LLM call is brittle and hard to debug.
    *   **Implementation:** Define complex tasks as a sequence of steps in your code.
        ```typescript
        // Example in server-side code
        async function runComplexAnalysis(company: string) {
          // Step 1: Get market data
          const marketDataResult = await runAgent('MarketAnalyst', `Get market data for ${company}`);
          
          // Step 2: Use market data to inform economic analysis
          const gdpGrowthResult = await runAgent('EconomicForecaster', `Given that ${company}'s volume is ${marketDataResult.volume}, what is the current GDP growth?`);

          // Step 3: Synthesize
          return synthesizeResults([marketDataResult, gdpGrowthResult]);
        }
        ```
    *   **Rationale:** This approach is more reliable, debuggable, and allows for stronger typing and error handling between steps. It treats the LLM as a powerful function to be called within a classical programming paradigm, which is more robust than treating the LLM as the main orchestrator.

*   **3.3. Dynamic Tool Generation:**
    *   **This is a highly advanced and risky capability.** Executing dynamically generated code is a significant security risk.
    *   **Pattern:** If absolutely necessary, use a severely sandboxed execution environment. Do not use Node.js's `eval()` or `new Function()`.
    *   **Implementation (High-Security Sandbox):**
        1.  **Generation:** An LLM call generates a snippet of JavaScript code based on the user's request.
        2.  **Sandboxing:** Use a dedicated, isolated execution environment like **Cloud Run** with `gVisor` (a container sandbox) or a WebAssembly-based runtime (like `Wasmtime`). The environment should have **NO network access** except to pre-approved APIs and **NO file system access**.
        3.  **Invocation:** The main application invokes this sandboxed environment via an HTTP call, passing the code and necessary data.
        4.  **Execution & Return:** The sandboxed environment executes the code and returns the result. The entire environment is ephemeral and destroyed after execution.
    *   **Recommendation:** Avoid this pattern unless it is a core, unavoidable feature. The security and implementation complexity are extremely high. A better approach is to expand your static tool library and improve the agent's ability to combine existing tools.

---

### **4. Security & Governance for Internal Data Tools**

**Challenge:** Securely allow agents to access and process sensitive, internal company data.

**Architectural Recommendations:**

*   **4.1. Data Sandboxing & The "Gatekeeper" Pattern:**
    *   **Pattern:** Never let the LLM directly query a production database. The `executeTool` function on your server acts as a secure "Gatekeeper".
    *   **Implementation:**
        1.  **LLM Request:** The agent requests a tool call: `analyze_spending_trends` with parameters `{"department": "R&D", "period": "Q3 2024"}`.
        2.  **Gatekeeper Validation:** Your server-side `executeTool` function receives this. Before executing, it validates the parameters against a strict allow-list. E.g., `department` must be one of `['R&D', 'Marketing', 'Sales']`. If the LLM hallucinates a department like `'All Departments'` or attempts an injection attack, the validation fails and an error is returned to the agent.
        3.  **Secure Execution:** The Gatekeeper function, now with validated parameters, connects to the internal database using a dedicated, read-only service account.
        4.  **Sanitized Summary:** The Gatekeeper retrieves the raw data but **does not** return it to the LLM. Instead, it computes a summary (e.g., total spend, top 3 categories).
        5.  **Return Summary to LLM:** Only the sanitized, aggregated summary (`{ "total_spend": 250000, ... }`) is returned to the LLM for its final synthesis. The raw, row-level data never leaves your secure backend.

*   **4.2. Principle of Least Privilege:**
    *   **IAM is Key:** The service account used by the Gatekeeper function to query the database must have the absolute minimum permissions required. It should have **read-only access** and only to the specific tables/views needed for the FINTEL tools.
    *   **Gatekeeper Logic as Policy:** The validation logic in the Gatekeeper function (as described above) is your primary enforcement mechanism. It ensures the LLM cannot request data outside its authorized scope.
    *   **Parameter Sanitization:** In addition to validation, always sanitize parameters to prevent SQL injection or other attacks, even though the LLM is the source.

*   **4.3. Identity and Access Management:**
    *   **Pattern:** Use **Workload Identity Federation** on Google Cloud. This is the recommended practice.
    *   **Implementation:**
        1.  Create a dedicated **Google Service Account (GSA)** for your FINTEL backend (e.g., `fintel-backend-sa@...`).
        2.  Grant this GSA IAM permissions to access necessary Google Cloud resources (Firestore, Vector Search, etc.) and the necessary permissions on your internal database (assuming it's accessible within your VPC).
        3.  Configure your Cloud Run service to run *as* this service account.
    *   **Benefit:** This avoids managing or distributing service account keys. All actions taken by your backend are auditable under the identity of that specific service account. This provides a clear audit trail and a single point for managing access control.
