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

For detailed information about the backend architecture, components, project structure, and advanced usage, please see our [Core Backend Documentation](README_CORE.md).

## Core Capabilities

II-Agent is a versatile open-source assistant capable of enhancing productivity across various domains including:
- Research & Fact-Checking
- Content Generation
- Data Analysis & Visualization
- Software Development
- Workflow Automation
- Problem Solving

For a detailed breakdown of capabilities and how the backend supports them, please refer to the [Core Backend Documentation](README_CORE.md#core-capabilities).

## Methods

Our methodology focuses on a robust Core Agent Architecture, LLM Interaction, structured Planning and Reflection, comprehensive Execution Capabilities, intelligent Context Management, and Real-time Communication. This approach enables II-Agent to handle complex, multi-step tasks effectively. For a deeper dive into our methods, see the [Core Backend Documentation](README_CORE.md#methods).

## GAIA Benchmark Evaluation

II-Agent has demonstrated strong performance on the GAIA benchmark, excelling in tasks requiring complex reasoning, tool use, and multi-step planning. More details on our evaluation and findings can be found in the [Core Backend Documentation](README_CORE.md#gaia-benchmark-evaluation).

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
Basic usage:
```bash
python cli.py [options]
```
For detailed CLI options and advanced usage, see the [Core Backend Documentation](README_CORE.md#command-line-interface).

### Web Interface
1. Start the WebSocket server:
   ```bash
   python ws_server.py [options]
   ```
2. Start the frontend (see `frontend/README.md`).

For detailed server options, see the [Core Backend Documentation](README_CORE.md#web-interface).
For developers looking to integrate a frontend (especially React) with the WebSocket server, please refer to the [Frontend Integration Guide](INTEGRATION_GUIDE.md).

## Project Structure

The project includes:
- `cli.py`: Command-line interface.
- `ws_server.py`: WebSocket server for the frontend.
- `src/ii_agent/`: Core agent Python implementation.
- `frontend/`: React-based frontend application.

For a detailed breakdown of the project structure, especially the backend components, please refer to the [Core Backend Documentation](README_CORE.md#project-structure).

## Conclusion

The II-Agent framework, architected around the reasoning capabilities of large language models like Claude 3.7 Sonnet, presents a comprehensive and robust methodology for building versatile AI agents. Through its synergistic combination of a powerful LLM, a rich set of execution capabilities, an explicit mechanism for planning and reflection, and intelligent context management strategies, II-Agent is well-equipped to address a wide spectrum of complex, multi-step tasks. Its open-source nature and extensible design provide a strong foundation for continued research and development in the rapidly evolving field of agentic AI.

## Acknowledgement

We would like to express our sincere gratitude to the following projects and individuals for their invaluable contributions that have helped shape this project:

- **AugmentCode**: We have incorporated and adapted several key components from the [AugmentCode project](https://github.com/augmentcode/augment-swebench-agent). AugmentCode focuses on SWE-bench, a benchmark that tests AI systems on real-world software engineering tasks from GitHub issues in popular open-source projects. Their system provides tools for bash command execution, file operations, and sequential problem-solving capabilities designed specifically for software engineering tasks.

- **Manus**: Our system prompt architecture draws inspiration from Manus's work, which has helped us create more effective and contextually aware AI interactions.

- **Index Browser Use**: We have built upon and extended the functionality of the [Index Browser Use project](https://github.com/lmnr-ai/index/tree/main), particularly in our web interaction and browsing capabilities. Their foundational work has enabled us to create more sophisticated web-based agent behaviors.

We are committed to open source collaboration and believe in acknowledging the work that has helped us build this project. If you feel your work has been used in this project but hasn't been properly acknowledged, please reach out to us.

