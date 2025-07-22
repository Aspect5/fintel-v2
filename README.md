# FINTEL: Flexible Agentic Environment

FINTEL is a sophisticated, web-based workflow development environment for creating, visualizing, and executing multi-agent financial analysis tasks. It features a dual-architecture design for robust A/B testing and comparative analysis:

1.  **Gemini (Visual):** A lightweight, client-side engine using Google's Gemini API directly from the browser. It provides a visual, step-by-step representation of the agent workflow, making it ideal for debugging and understanding agentic processes.
2.  **ControlFlow (Python):** A powerful, server-side engine that uses the `controlflow` library. It orchestrates a team of specialized agents that can be powered by multiple LLM providers (OpenAI, Gemini, or local models) to handle complex financial analysis tasks.

All API keys and secrets are managed exclusively by the secure Python backend.

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
    *   **Windows:** `backendenv\Scripts\activate`
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

1.  **Select Execution Engine:** In the UI, choose between `Gemini (Visual)` or `ControlFlow (Python)`.
2.  **Configure `ControlFlow` Provider:** If you selected `ControlFlow`, choose your desired LLM provider (OpenAI, Gemini, or Local) and enter a base URL if needed.
3.  **Submit Query:** Type your financial analysis request and send the message. The selected engine will handle the workflow.

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
