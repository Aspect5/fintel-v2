# FINTEL v2: Refactored Multi-Agent Financial Intelligence Assistant

FINTEL v2 is a sophisticated, web-based workflow development environment for creating, visualizing, and executing multi-agent financial analysis tasks. It is built on a robust, backend-driven architecture that ensures a single source of truth for all business logic, including agent capabilities and tool definitions.

The system uses a unified, declarative workflow model powered by the `controlflow` library. This model orchestrates a team of specialized agents to handle complex financial analysis tasks, with a Directed Acyclic Graph (DAG) of tasks being defined and executed by the `controlflow` library.

## Key Architectural Principles

*   **Backend as a Single Source of Truth**: The Python backend is the sole authority for all business logic, including agent capabilities and tool definitions. The frontend is a "dumb" client that renders data and forwards user input, dynamically learning about capabilities from the backend's API.
*   **Unified, Declarative Workflow**: The system uses a single, consistent pattern for agent orchestration. The chosen pattern is a Dependency-Driven Workflow, where a Directed Acyclic Graph (DAG) of tasks is defined and executed by the `controlflow` library.

## Getting Started

Follow these instructions to set up and run the complete FINTEL application locally.

### 1. Prerequisites

*   **Node.js** (v18 or higher)
*   **Python** (v3.9 or higher) and `pip`

### 2. One-Time Setup

These steps only need to be performed once to prepare the project.

**A. Configure the Backend:**

1.  **Create a Python Virtual Environment:** From the project root, run:
    ```bash
    python3 -m venv backend/venv
    ```
2.  **Activate the Virtual Environment:**
    *   **macOS/Linux:** `source backend/venv/bin/activate`
    *   **Windows:** `backend env\Scripts\activate`
3.  **Install Python Dependencies:** With the virtual environment active, run:
    ```bash
    pip install -r backend/requirements.txt
    ```
4.  **Configure API Keys:** All secrets are managed in a single file.
    *   Navigate to the `backend` directory.
    *   Create a `.env` file by copying the example: `cp .env.example .env`.
    *   Open `backend/.env` and add your API keys. At least one provider (OpenAI or Google) is required.

**B. Configure the Frontend:**

1.  **Install Node.js Dependencies:** From the project root, run:
    ```bash
    npm install
    ```

### 3. Running the Application

After the one-time setup, you can start the entire application with a single command from the **project root**.

```bash
npm run dev
```

This command uses `concurrently` to:
*   Start the Vite frontend development server (on `http://localhost:5173`).
*   Start the Python Flask backend server (on `http://localhost:5001`) using the correct virtual environment.

You can now open your browser to `http://localhost:5173`.

### How to Use

1.  **Configure LLM Provider:** Choose your desired LLM provider (OpenAI, Gemini, or Local) and enter a base URL if needed.
2.  **Submit Query:** Type your financial analysis request and send the message. The backend will handle the workflow.

---
### **Advanced: Manual Server Startup**

For debugging, you can run the frontend and backend servers independently.

*   **To run the backend only:**
    ```bash
    # Make sure your virtual environment is active
    source backend/venv/bin/activate
    flask run --port=5001
    ```
*   **To run the frontend only:**
    ```bash
    npm run vite
    ```
