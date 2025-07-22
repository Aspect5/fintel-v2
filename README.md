# FINTEL: Dual-Backend Agentic Environment

FINTEL is a sophisticated, web-based workflow development environment for creating, visualizing, and executing multi-agent financial analysis tasks. It uniquely features a dual-backend architecture, allowing users to seamlessly switch between two distinct execution engines:

1.  **Gemini (In-Browser):** A lightweight, client-side engine that uses Google's Gemini API directly from the browser. It provides a visual, step-by-step representation of the agent workflow, making it ideal for debugging and understanding the agentic process.
2.  **ControlFlow (Python):** A powerful, server-side engine that uses the `controlflow` Python library. It orchestrates a team of specialized agents (powered by OpenAI models) to handle complex financial analysis tasks, returning a final, synthesized report.

This dual-backend approach offers the best of both worlds: the transparency and visual debugging of an in-browser solution and the power and extensibility of a Python-based multi-agent framework.

## Architecture Overview

*   **Frontend:** A React application built with Vite, using `reactflow` for workflow visualization and Zustand for state management.
*   **Gemini Backend:** A virtual, in-browser backend implemented in TypeScript. It coordinates agent tasks and displays the full multi-agent graph (Coordinator -> Agents -> Synthesizer) in the UI.
*   **Python Backend:** A Flask server that exposes a single API endpoint. It uses the `controlflow` library to manage a robust, multi-agent workflow based on the principles of the Coordinator-Service model.

## Getting Started

Follow these instructions to set up and run the complete FINTEL application locally.

### 1. Prerequisites

*   **Node.js** (v18 or higher)
*   **Python** (v3.9 or higher) and `pip`

### 2. Frontend Setup (Gemini Engine)

This setup is required for the core application and the in-browser Gemini engine.

1.  **Install Node.js Dependencies:**
    From the project root, run:
    ```bash
    npm install
    ```

2.  **Configure API Keys:**
    *   Create a `.env.local` file in the project root by copying the example: `cp .env.local.example .env.local`.
    *   Open `.env.local` and add your API keys.
        *   `VITE_GEMINI_API_KEY`: **Required** for the in-browser engine.
        *   `VITE_ALPHA_VANTAGE_API_KEY`: Optional, for stock data tools.
        *   `VITE_FRED_API_KEY`: Optional, for economic data tools.

    > **Note:** Environment variables for the Vite frontend **must** be prefixed with `VITE_`.

### 3. Backend Setup (ControlFlow Engine)

This setup is required to run the Python-based `controlflow` engine.

1.  **Create a Python Virtual Environment:**
    From the project root, run:
    ```bash
    python3 -m venv backend/venv
    source backend/venv/bin/activate
    ```
    *(On Windows, use `backendenv\Scripts\activate`)*

2.  **Install Python Dependencies:**
    With the virtual environment activated, run:
    ```bash
    pip install -r backend/requirements.txt
    ```

3.  **Configure API Keys:**
    *   Navigate to the `backend` directory.
    *   Create a `.env` file by copying the example: `cp .env.example .env`.
    *   Open `backend/.env` and add your API keys.
        *   `OPENAI_API_KEY`: **Required** for the Python agents.
        *   `ALPHA_VANTAGE_API_KEY`: Optional, for Python-based tools.
        *   `FRED_API_KEY`: Optional, for Python-based tools.

### 4. Running the Application

Once both the frontend and backend are configured, you can start the entire application with a single command from the project root.

```bash
npm run dev
```

This command uses `concurrently` to:
*   Start the Vite frontend development server (usually on `http://localhost:5173`).
*   Start the Python Flask backend server (on `http://localhost:5001`).

You can now open your browser to the Vite server address and begin using the FINTEL application.

## How to Use

1.  **Select Your Engine:** Use the "Execution Engine" dropdown in the side panel to choose between "Gemini (In-Browser)" and "ControlFlow (Python)".
2.  **Enter Your Query:** Type a financial analysis request into the chat input (e.g., "What is the current market outlook for Apple?").
3.  **Execute:**
    *   If using the **ControlFlow** engine, the analysis will run automatically, and the final report will be displayed.
    *   If using the **Gemini** engine, a visual workflow graph will be generated. Click the "Run Gemini Workflow" button to execute the plan and generate the report.
