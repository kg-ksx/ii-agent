# Environment Variables

This document outlines the environment variables required for the application. These variables can be defined in a `.env` file in the root directory.

## Anthropic API Configuration

There are two ways to configure the Anthropic client:

1.  **Direct Anthropic API Key**:
    *   `ANTHROPIC_API_KEY`:
        *   **Purpose**: Your secret API key for accessing Anthropic's services directly.
        *   **Required**: Yes, if you are not using Google Cloud Vertex AI for Anthropic models.

2.  **Google Cloud Vertex AI for Anthropic**:
    *   `GOOGLE_PROJECT_ID`:
        *   **Purpose**: The Google Cloud Project ID where Vertex AI is enabled and configured to use Anthropic models.
        *   **Required**: Yes, if using Vertex AI for Anthropic models.
    *   `GOOGLE_REGION`:
        *   **Purpose**: The Google Cloud region (e.g., `us-central1`) where your Vertex AI services for Anthropic are located.
        *   **Required**: Yes, if using Vertex AI for Anthropic models.

**Relationship**:
*   If `GOOGLE_PROJECT_ID` and `GOOGLE_REGION` are provided and the client is configured to use Vertex AI, the `ANTHROPIC_API_KEY` is not used for the Anthropic Vertex client.
*   If `GOOGLE_PROJECT_ID` and `GOOGLE_REGION` are **not** provided, or the client is configured for direct Anthropic API access, then `ANTHROPIC_API_KEY` is mandatory.

## OpenAI API Configuration

### `OPENAI_API_KEY`

*   **Purpose**: Your secret API key for accessing OpenAI's services (e.g., GPT-4, GPT-3.5-turbo). This key is used to authenticate requests to the OpenAI API.
*   **Required**: This variable is necessary if the `OpenAIDirectClient` (or any similar component configured for direct OpenAI model usage) is initialized and utilized within the application. If the application is not configured to use OpenAI models, or uses them through a different mechanism that doesn't require a direct API key (e.g., a proxy or a managed service that handles authentication internally), then this variable might not be needed. Check the specific LLM client configuration in use.
