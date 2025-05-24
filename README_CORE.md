<div align="center">
  <img src="assets/ii.png" width="200"/>




# II Agent

[![GitHub stars](https://img.shields.io/github/stars/Intelligent-Internet/ii-agent?style=social)](https://github.com/Intelligent-Internet/ii-agent/stargazers)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Blog](https://img.shields.io/badge/Blog-II--Agent-blue)](https://ii.inc/web/blog/post/ii-agent)
[![GAIA Benchmark](https://img.shields.io/badge/GAIA-Benchmark-green)](https://ii-agent-gaia.ii.inc/)
</div>

II-Agent is an open-source intelligent assistant designed to streamline and enhance workflows across multiple domains. It represents a significant advancement in how we interact with technology—shifting from passive tools to intelligent systems capable of independently executing complex tasks.



## Introduction
https://github.com/user-attachments/assets/d0eb7440-a6e2-4276-865c-a1055181bb33


## Overview

II Agent is built around providing an agentic interface to Anthropic Claude models. It offers:

- A CLI interface for direct command-line interaction
- A WebSocket server that powers a modern React-based frontend
- Integration with Google Cloud's Vertex AI for API access to Anthropic models

The backend, primarily driven by `ws_server.py`, serves as the main entry point for frontend interactions. It utilizes WebSockets to establish persistent, bidirectional communication. A key aspect of the agent lifecycle is that a new, distinct agent instance is created for each WebSocket connection. This ensures that each user session is isolated and maintains its own state. The agent interacts with various tools by calling them as needed to fulfill user requests or execute planned steps. These tools are integrated into the agent's workflow, allowing it to perform a wide range of actions.

## Core Capabilities

II-Agent is a versatile open-source assistant built to elevate your productivity across domains:

| Domain | What II‑Agent Can Do | Backend Support |
|--------|----------------------|-----------------|
| Research & Fact‑Checking | Multistep web search, source triangulation, structured note‑taking, rapid summarization | Supported by tools for web searching (e.g., Tavily, SerpAPI), browser automation for accessing and parsing web content, and file system tools for saving research. |
| Content Generation | Blog & article drafts, lesson plans, creative prose, technical manuals, Website creations | Enabled by the core LLM's generative capabilities, combined with tools for writing and editing files in the workspace. |
| Data Analysis & Visualization | Cleaning, statistics, trend detection, charting, and automated report generation | Facilitated by code execution tools (e.g., running Python scripts with libraries like Pandas, Matplotlib) and file system access for data input/output. |
| Software Development | Code synthesis, refactoring, debugging, test‑writing, and step‑by‑step tutorials across multiple languages | Achieved through tools that allow file creation, reading, modification, and deletion, as well as shell command execution for running linters, compilers, and tests. |
| Workflow Automation | Script generation, browser automation, file management, process optimization | Realized via a combination of browser automation tools, file system operations, and the ability to execute scripts (e.g., Bash, Python) to interact with other systems or automate sequences of tasks. |
| Problem Solving | Decomposition, alternative‑path exploration, stepwise guidance, troubleshooting | Fundamentally driven by the agent's interaction with the LLM for reasoning and planning, augmented by tools that allow it to gather information or test hypotheses. |

## Methods

The II-Agent system represents a sophisticated approach to building versatile AI agents. Our methodology centers on:

1. **Core Agent Architecture and LLM Interaction**
   - System prompting with dynamically tailored context
   - Comprehensive interaction history management
   - Intelligent context management to handle token limitations
   - Systematic LLM invocation and capability selection
   - Iterative refinement through execution cycles

2. **Planning and Reflection**
   - Structured reasoning for complex problem-solving
   - Problem decomposition and sequential thinking
   - Transparent decision-making process
   - Hypothesis formation and testing

3. **Execution Capabilities**
   - File system operations with intelligent code editing
   - Command line execution in a secure environment
   - Advanced web interaction and browser automation
   - Task finalization and reporting
   - Specialized capabilities for various modalities (Experimental) (PDF, audio, image, video, slides)
   - Deep research integration

4. **Context Management**
   - Token usage estimation and optimization
   - Strategic truncation for lengthy interactions
   - File-based archival for large outputs

5. **Real-time Communication**
   - WebSocket-based interface for interactive use
   - Isolated agent instances per client
   - Streaming operational events for responsive UX

## GAIA Benchmark Evaluation

II-Agent has been evaluated on the GAIA benchmark, which assesses LLM-based agents operating within realistic scenarios across multiple dimensions including multimodal processing, tool utilization, and web searching.

We identified several issues with the GAIA benchmark during our evaluation:

- **Annotation Errors**: Several incorrect annotations in the dataset (e.g., misinterpreting date ranges, calculation errors)
- **Outdated Information**: Some questions reference websites or content no longer accessible
- **Language Ambiguity**: Unclear phrasing leading to different interpretations of questions

Despite these challenges, II-Agent demonstrated strong performance on the benchmark, particularly in areas requiring complex reasoning, tool use, and multi-step planning.

![GAIA Benchmark](assets/gaia.jpg)
You can view the full traces of some samples here: [GAIA Benchmark Traces](https://ii-agent-gaia.ii.inc/)

## Requirements

- Python 3.10+
- Node.js 18+ (for frontend)
- Google Cloud project with Vertex AI API enabled or Anthropic API key

## Environment

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# Image and Video Generation Tool
OPENAI_API_KEY=your_openai_key
OPENAI_AZURE_ENDPOINT=your_azure_endpoint
# Search Provider
TAVILY_API_KEY=your_tavily_key
#JINA_API_KEY=your_jina_key
#FIRECRAWL_API_KEY=your_firecrawl_key
# For Image Search and better search results use SerpAPI
#SERPAPI_API_KEY=your_serpapi_key 

STATIC_FILE_BASE_URL=http://localhost:8000/

#If you are using Anthropic client
ANTHROPIC_API_KEY=
#If you are using Goolge Vertex (recommended if you have permission extra throughput)
#GOOGLE_APPLICATION_CREDENTIALS=
```

### Frontend Environment Variables

For the frontend, create a `.env` file in the frontend directory:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Installation

1. Clone the repository
2. Set up Python environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .
   ```

3. Set up frontend (optional):
   ```bash
   cd frontend
   npm install
   ```

## Usage

### Command Line Interface

The Command Line Interface (CLI) allows for direct, interactive sessions with an II-Agent. To start an interactive session, run:

```bash
python cli.py [OPTIONS]
```

Ensure your `.env` file is configured with the necessary API keys (e.g., `ANTHROPIC_API_KEY` for direct Anthropic access, or `GOOGLE_APPLICATION_CREDENTIALS` for Vertex AI).

**Key Command-Line Arguments:**

*   `--project-id YOUR_PROJECT_ID`: (Optional) Your Google Cloud Project ID. Required if using Vertex AI and `GOOGLE_APPLICATION_CREDENTIALS` is not set or needs to be overridden for the session.
*   `--region YOUR_REGION`: (Optional) The Google Cloud region for Vertex AI services (e.g., `us-east5`).
*   `--workspace PATH`: (Optional) Specifies the path to the directory where the agent can store files and perform file-based operations. Defaults to `./workspace`. A unique subdirectory will be created within this path for each session.
*   `--needs-permission`: (Optional) If set, the agent will prompt for user permission before executing potentially impactful commands (like shell commands or file modifications).
*   `--minimize-stdout-logs`: (Optional) Reduces the verbosity of logs printed to the standard output during the session. Detailed logs are still typically saved to a file.
*   `--context-manager CONTEXT_MANAGER_NAME`: (Optional) Specifies the context management strategy. For example, `claude_retrieval` might be an option. Defaults to a standard context manager.
*   `--logs-path DIRECTORY_PATH`: (Optional) Specifies the directory where log files should be stored. Defaults to the current directory.
*   `--debug`: (Optional) Enables debug mode, which usually increases log verbosity.
*   `--session-id SESSION_ID`: (Optional) Allows resuming a previous session if the session ID is provided and history is persisted.

### Web Interface

The Web Interface provides a user-friendly GUI to interact with the agent. It consists of a backend server and a frontend application.

1.  **Start the Backend Server:**

    The backend is powered by `ws_server.py`, which handles WebSocket connections from the frontend.

    ```bash
    python ws_server.py [OPTIONS]
    ```

    Ensure your `.env` file is configured. The `STATIC_FILE_BASE_URL` environment variable (e.g., `http://localhost:8000`) should also be set if you plan to use file upload/download features via the server itself.

    **Key Command-Line Arguments for `ws_server.py`:**

    *   `--host HOST_IP`: (Optional) The IP address the WebSocket server will listen on. Defaults to `0.0.0.0` (all available interfaces).
    *   `--port PORT_NUMBER`: (Optional) The port the WebSocket server will listen on. Defaults to `8000`.
    *   `--project-id YOUR_PROJECT_ID`: (Optional) Your Google Cloud Project ID for Vertex AI.
    *   `--region YOUR_REGION`: (Optional) The Google Cloud region for Vertex AI (e.g., `us-east5`).
    *   `--certfile CERT_FILE_PATH` and `--keyfile KEY_FILE_PATH`: (Optional) Paths to SSL certificate and key files if you want to run the server over HTTPS/WSS.
    *   `--db-path DB_FILE_PATH`: (Optional) Path to the SQLite database file for storing session information if using SQLite. For MongoDB, connection is usually configured via environment variables or within `MongoManager`.
    *   `--logs-path DIRECTORY_PATH`: (Optional) Specifies the directory where log files should be stored.
    *   `--debug`: (Optional) Enables debug mode.
    *   `--uvicorn`: (Optional) Runs the server using Uvicorn instead of the default `websockets` library server, which might be preferred for production or specific deployment needs.

2.  **Start the Frontend Application:**

    The frontend is typically a React application.

```bash
cd frontend
npm run dev
```

3. Open your browser to http://localhost:3000

## Logging

Backend logging provides crucial insights into the agent's operations, decision-making processes, and potential issues.

*   **File-based Logs:**
    *   Both `cli.py` and `ws_server.py` are configured to save detailed logs to files.
    *   By default, `cli.py` saves logs to `agent.log` in the current working directory. This can be overridden using the `--logs-path` argument to specify a different directory or filename.
    *   `ws_server.py` also supports the `--logs-path` argument. When sessions are used, it often creates session-specific log files (e.g., `workspace/<session_id>/agent.log`).
*   **Console Output:**
    *   Both scripts also output logs to `stdout` and `stderr`. The verbosity of console logs can often be controlled (e.g., using `--minimize-stdout-logs` in `cli.py` or `--debug` to increase verbosity).
*   **Log Content:**
    *   Logs typically contain:
        *   Agent's internal thoughts and reasoning steps.
        *   Tool selection and invocation details (tool name, arguments).
        *   The output or result from each tool execution.
        *   Errors and exceptions encountered during processing.
        *   Key events in the agent or server lifecycle.
        *   Timestamps for tracking the sequence and duration of operations.
    *   This information is invaluable for debugging, understanding agent behavior, and auditing actions performed by the agent.

## Project Structure

- `cli.py`: Command-line interface for direct interaction with the agent.
- `ws_server.py`: WebSocket server that powers the web frontend and manages agent instances.
- `src/ii_agent/`: Core agent implementation.
  - `agents/`: Contains different agent implementations. A key example is `anthropic_fc.py`, which orchestrates the interaction with Anthropic models and tools.
  - `browser/`: Provides tools and utilities for web browser automation, enabling the agent to interact with websites.
  - `core/`: Includes core components like `event.py`, which defines the structure for WebSocket messages exchanged between the backend and frontend.
  - `db/`: Manages database interactions, primarily for storing session information and event history. This includes `manager.py` for database operations and `models.py` for data schemas (e.g., using MongoDB).
  - `llm/`: Contains interfaces for interacting with Large Language Models (LLMs), including context management strategies to handle token limits and format model prompts.
  - `prompts/`: Stores system prompts that guide the behavior and persona of the agents.
  - `tools/`: A collection of various tools that the agent can utilize. These include tools for bash command execution, file editing, web search, image generation, and more. Each tool is typically a class designed to perform a specific action.
  - `utils/`: Contains utility functions and classes used across the project, such as `workspace_manager.py` for managing isolated file environments for each agent session.

## Key Components

This section details some of the most important modules and classes that make up the II-Agent backend.

-   **`ws_server.py`**: This script is the primary interface for clients (like the React frontend). It manages WebSocket connections, handling incoming messages and broadcasting outgoing events. For each new WebSocket connection, it typically instantiates an agent and a session. It also exposes HTTP endpoints for auxiliary functions, such as `/api/upload` for file uploads to an agent's workspace and `/api/sessions/{session_id}/events` for retrieving event history for a specific session.

-   **`cli.py`**: This provides a command-line interface for interacting directly with an agent. It's a valuable tool for development, testing, or running agents in environments without a graphical interface. It initializes an agent and allows users to send commands or queries through the terminal.

-   **`AnthropicFC` Agent (`src/ii_agent/agents/anthropic_fc.py`)**: This is a core agent implementation responsible for the main logic loop. Its duties include:
    *   Managing the overall conversation flow with the user.
    *   Interacting with the configured Large Language Model (LLM), specifically Anthropic Claude models, either via Google Vertex AI or a direct Anthropic API key.
    *   Processing user input and LLM responses.
    *   Selecting appropriate tools from the available toolset based on the LLM's suggestions or a predefined plan.
    *   Executing these tools and incorporating their outputs back into the conversation or plan.
    *   Managing the context window for the LLM, ensuring relevant information is included without exceeding token limits.

-   **Tools (`src/ii_agent/tools/`)**: The agent's capabilities are extended by a suite of tools located in this directory. Each tool is generally implemented as a class with a specific `run` method (or similar) that performs a distinct action. Examples include:
    *   `Bash`: Executes shell commands.
    *   `EditFile`: Creates, modifies, or deletes files.
    *   `TavilySearch`: Performs web searches using the Tavily API.
    *   `ImageGeneration`: Generates images using models like DALL-E.
    The agent, guided by the LLM, decides which tool to use and with what arguments. The output from the tool is then returned to the agent to inform subsequent steps.

-   **Workspace Management (`src/ii_agent/utils/workspace_manager.py`)**: To maintain isolation and organization, each agent session is provided with a unique workspace. The `WorkspaceManager` class handles the creation and management of these workspaces. Typically, a root `workspace/` directory is created (if it doesn't exist), and within it, subdirectories named with unique identifiers (e.g., UUIDs) are generated for each session. This allows agents to read, write, and list files, execute code, and perform other file system operations specific to their current task without interfering with other sessions.

-   **Database Interaction (`src/ii_agent/db/`)**: The system uses a database to persist session information and the history of events for each session. Based on imports in `ws_server.py` (like `MongoManager`), MongoDB is the backend database. The `DatabaseManager` class (e.g., `MongoManager` in `src/ii_agent/db/manager.py`) encapsulates the logic for connecting to the database and performing operations like saving new events, retrieving session history, and managing session metadata. The `src/ii_agent/db/models.py` file likely defines the schema for the data stored in the database.

## Conclusion

The II-Agent framework, architected around the reasoning capabilities of large language models like Claude 3.7 Sonnet, presents a comprehensive and robust methodology for building versatile AI agents. Through its synergistic combination of a powerful LLM, a rich set of execution capabilities, an explicit mechanism for planning and reflection, and intelligent context management strategies, II-Agent is well-equipped to address a wide spectrum of complex, multi-step tasks. Its open-source nature and extensible design provide a strong foundation for continued research and development in the rapidly evolving field of agentic AI.

## Acknowledgement

We would like to express our sincere gratitude to the following projects and individuals for their invaluable contributions that have helped shape this project:

- **AugmentCode**: We have incorporated and adapted several key components from the [AugmentCode project](https://github.com/augmentcode/augment-swebench-agent). AugmentCode focuses on SWE-bench, a benchmark that tests AI systems on real-world software engineering tasks from GitHub issues in popular open-source projects. Their system provides tools for bash command execution, file operations, and sequential problem-solving capabilities designed specifically for software engineering tasks.

- **Manus**: Our system prompt architecture draws inspiration from Manus's work, which has helped us create more effective and contextually aware AI interactions.

- **Index Browser Use**: We have built upon and extended the functionality of the [Index Browser Use project](https://github.com/lmnr-ai/index/tree/main), particularly in our web interaction and browsing capabilities. Their foundational work has enabled us to create more sophisticated web-based agent behaviors.

We are committed to open source collaboration and believe in acknowledging the work that has helped us build this project. If you feel your work has been used in this project but hasn't been properly acknowledged, please reach out to us.
