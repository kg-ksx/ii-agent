#!/usr/bin/env python3
"""
FastAPI WebSocket Server for the Agent.

This script provides a WebSocket interface for interacting with the Agent,
allowing real-time communication with a frontend application.
"""

import os
import argparse
import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Dict, List, Set, Any
from dotenv import load_dotenv

load_dotenv()

import uvicorn
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Request,
    HTTPException,
)

from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import anyio
import base64
import httpx
from sqlalchemy import asc, text

from ii_agent.core.event import RealtimeEvent, EventType
from ii_agent.db.models import Event # This model is likely for SQLAlchemy, might be unused with MongoDB
from ii_agent.utils.constants import DEFAULT_MODEL, UPLOAD_FOLDER_NAME
from utils import parse_common_args # create_workspace_manager_for_connection will be moved here
from ii_agent.agents.anthropic_fc import AnthropicFC
from ii_agent.agents.base import BaseAgent
from ii_agent.llm.base import LLMClient
from ii_agent.utils import WorkspaceManager
from ii_agent.llm import get_client
from ii_agent.utils.prompt_generator import enhance_user_prompt

from fastapi.staticfiles import StaticFiles

from ii_agent.llm.context_manager.file_based import FileBasedContextManager
from ii_agent.llm.context_manager.standard import StandardContextManager
from ii_agent.llm.token_counter import TokenCounter
from ii_agent.db.manager import DatabaseManager
from ii_agent.tools import get_system_tools
from ii_agent.prompts.system_prompt import SYSTEM_PROMPT

MAX_OUTPUT_TOKENS_PER_TURN = 32768
MAX_TURNS = 200


app = FastAPI(title="Agent WebSocket API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# Create a logger
logger = logging.getLogger("websocket_server")
logger.setLevel(logging.INFO)

# Active WebSocket connections
active_connections: Set[WebSocket] = set()

# Active agents for each connection
active_agents: Dict[WebSocket, BaseAgent] = {}

# Active agent tasks
active_tasks: Dict[WebSocket, asyncio.Task] = {}

# Store message processors for each connection
message_processors: Dict[WebSocket, asyncio.Task] = {}

# Store global args for use in endpoint
global_args = None


async def fetch_user_id(
    token: str | None,
    api_key: str | None,
    client_key: str | None,
    device_id: str | None,
) -> str | None:
    """Fetches user_id from an external service."""
    payload = {
        "token": token,
        "api_key": api_key,
        "client_key": client_key,
        "device_id": device_id,
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://example.com/fetchuser", json=payload, timeout=10.0
            )
        response.raise_for_status()  # Raise an exception for bad status codes
        response_json = response.json()
        user_id = response_json.get("user_id")
        if user_id:
            logger.info(f"Successfully fetched user_id: {user_id}")
            return user_id
        else:
            logger.error("user_id not found in response")
            return None
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
        return None
    except httpx.RequestError as e:
        logger.error(f"Request error occurred: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return None


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Read headers
    authorization_header = websocket.headers.get("Authorization")
    api_key_header = websocket.headers.get("X-API-Key")
    client_key_header = websocket.headers.get("X-Client-Key")
    device_id_header = websocket.headers.get("X-Device-ID")

    logger.info(f"Authorization Header: {authorization_header}")
    logger.info(f"X-API-Key Header: {api_key_header}")
    logger.info(f"X-Client-Key Header: {client_key_header}")
    logger.info(f"X-Device-ID Header: {device_id_header}")

    # Fetch user_id
    user_id = await fetch_user_id(
        token=authorization_header,
        api_key=api_key_header,
        client_key=client_key_header,
        device_id=device_id_header,
    )

    if user_id is None:
        await websocket.send_json(
            RealtimeEvent(
                type=EventType.ERROR,
                content={"message": "User authentication failed."},
            ).model_dump()
        )
        await websocket.close()
        return

    logger.info(f"Successfully authenticated user_id: {user_id}")

    # Determine device_id (already done with device_id_header)
    # Ensure device_id is present for composite session ID
    if not device_id_header:
        logger.error("X-Device-ID header is missing, cannot create composite session ID.")
        await websocket.send_json(
            RealtimeEvent(
                type=EventType.ERROR,
                content={"message": "X-Device-ID header is required and was not found."},
            ).model_dump()
        )
        await websocket.close()
        return

    composite_session_id = f"{user_id}_{device_id_header}"
    logger.info(f"Using composite session ID: {composite_session_id}")
    
    active_connections.add(websocket)

    # workspace_session_uuid is the UUID for the directory name
    workspace_manager, workspace_session_uuid = create_workspace_manager_for_connection(
        global_args.workspace, global_args.use_container_workspace # use_container_workspace needs to be from global_args
    )
    logger.info(f"Workspace manager created: {workspace_manager}, Directory UUID: {workspace_session_uuid}")

    try:
        # Initialize LLM client
        client = get_client(
            "anthropic-direct",
            model_name=DEFAULT_MODEL,
            use_caching=False,
            project_id=global_args.project_id,
            region=global_args.region,
        )
        
        # Initial connection message with session info
        await websocket.send_json(
            RealtimeEvent(
                type=EventType.CONNECTION_ESTABLISHED,
                content={
                    "message": "Connected to Agent WebSocket Server",
                    "workspace_path": str(workspace_manager.root),
                },
            ).model_dump()
        )

        # Process messages from the client
        while True:
            # Receive and parse message
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                msg_type = message.get("type")
                content = message.get("content", {})

                if msg_type == "init_agent":
                    # Create a new agent for this connection
                    tool_args = content.get("tool_args", {})
                    agent = create_agent_for_connection(
                        client=client,
                        workspace_session_uuid=workspace_session_uuid,
                        workspace_manager=workspace_manager,
                        websocket=websocket,
                        tool_args=tool_args,
                        user_id=user_id,
                        device_id=device_id_header, # Pass the determined device_id
                        composite_session_id=composite_session_id
                    )
                    active_agents[websocket] = agent

                    # Start message processor for this connection
                    message_processor = agent.start_message_processing()
                    message_processors[websocket] = message_processor
                    await websocket.send_json(
                        RealtimeEvent(
                            type=EventType.AGENT_INITIALIZED,
                            content={"message": "Agent initialized"},
                        ).model_dump()
                    )

                elif msg_type == "query":
                    # Check if there's an active task for this connection
                    if websocket in active_tasks and not active_tasks[websocket].done():
                        await websocket.send_json(
                            RealtimeEvent(
                                type=EventType.ERROR,
                                content={
                                    "message": "A query is already being processed"
                                },
                            ).model_dump()
                        )
                        continue

                    # Process a query to the agent
                    user_input = content.get("text", "")
                    resume = content.get("resume", False)
                    files = content.get("files", [])

                    # Send acknowledgment
                    await websocket.send_json(
                        RealtimeEvent(
                            type=EventType.PROCESSING,
                            content={"message": "Processing your request..."},
                        ).model_dump()
                    )

                    # Run the agent with the query in a separate task
                    task = asyncio.create_task(
                        run_agent_async(websocket, user_input, resume, files)
                    )
                    active_tasks[websocket] = task

                elif msg_type == "workspace_info":
                    # Send information about the current workspace
                    if workspace_manager:
                        await websocket.send_json(
                            RealtimeEvent(
                                type=EventType.WORKSPACE_INFO,
                                content={
                                    "path": str(workspace_manager.root),
                                },
                            ).model_dump()
                        )
                    else:
                        await websocket.send_json(
                            RealtimeEvent(
                                type=EventType.ERROR,
                                content={"message": "Workspace not initialized"},
                            ).model_dump()
                        )

                elif msg_type == "ping":
                    # Simple ping to keep connection alive
                    await websocket.send_json(
                        RealtimeEvent(type=EventType.PONG, content={}).model_dump()
                    )

                elif msg_type == "cancel":
                    # Cancel the current agent task if one exists
                    if websocket in active_tasks and not active_tasks[websocket].done():
                        active_tasks[websocket].cancel()
                        await websocket.send_json(
                            RealtimeEvent(
                                type=EventType.SYSTEM,
                                content={"message": "Query canceled"},
                            ).model_dump()
                        )
                    else:
                        await websocket.send_json(
                            RealtimeEvent(
                                type=EventType.ERROR,
                                content={"message": "No active query to cancel"},
                            ).model_dump()
                        )

                elif msg_type == "enhance_prompt":
                    # Process a request to enhance a prompt using an LLM
                    user_input = content.get("text", "")
                    files = content.get("files", [])
                    
                    # Call the enhance_prompt function from the module
                    success, message, enhanced_prompt = await enhance_user_prompt(
                        client=client,
                        user_input=user_input,
                        files=files,
                    )
                    
                    if success and enhanced_prompt:
                        # Send the enhanced prompt back to the client
                        await websocket.send_json(
                            RealtimeEvent(
                                type=EventType.PROMPT_GENERATED,
                                content={
                                    "result": enhanced_prompt,
                                    "original_request": user_input,
                                },
                            ).model_dump()
                        )
                    else:
                        # Send error message
                        await websocket.send_json(
                            RealtimeEvent(
                                type=EventType.ERROR,
                                content={"message": message},
                            ).model_dump()
                        )

                else:
                    # Unknown message type
                    await websocket.send_json(
                        RealtimeEvent(
                            type=EventType.ERROR,
                            content={"message": f"Unknown message type: {msg_type}"},
                        ).model_dump()
                    )

            except json.JSONDecodeError:
                await websocket.send_json(
                    RealtimeEvent(
                        type=EventType.ERROR, content={"message": "Invalid JSON format"}
                    ).model_dump()
                )
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                await websocket.send_json(
                    RealtimeEvent(
                        type=EventType.ERROR,
                        content={"message": f"Error processing request: {str(e)}"},
                    ).model_dump()
                )

    except WebSocketDisconnect:
        # Handle disconnection
        logger.info("Client disconnected")
        cleanup_connection(websocket)
    except Exception as e:
        # Handle other exceptions
        logger.error(f"WebSocket error: {str(e)}")
        cleanup_connection(websocket)


async def run_agent_async(
    websocket: WebSocket, user_input: str, resume: bool = False, files: List[str] = []
):
    """Run the agent asynchronously and send results back to the websocket."""
    agent = active_agents.get(websocket)

    if not agent:
        await websocket.send_json(
            RealtimeEvent(
                type=EventType.ERROR,
                content={"message": "Agent not initialized for this connection"},
            ).model_dump()
        )
        return

    try:
        # Add user message to the event queue to save to database
        agent.message_queue.put_nowait(
            RealtimeEvent(type=EventType.USER_MESSAGE, content={"text": user_input})
        )
        # Run the agent with the query
        await anyio.to_thread.run_sync(agent.run_agent, user_input, files, resume)

    except Exception as e:
        logger.error(f"Error running agent: {str(e)}")
        import traceback

        traceback.print_exc()
        await websocket.send_json(
            RealtimeEvent(
                type=EventType.ERROR,
                content={"message": f"Error running agent: {str(e)}"},
            ).model_dump()
        )
    finally:
        # Clean up the task reference
        if websocket in active_tasks:
            del active_tasks[websocket]


def cleanup_connection(websocket: WebSocket):
    """Clean up resources associated with a websocket connection."""
    # Remove from active connections
    if websocket in active_connections:
        active_connections.remove(websocket)

    # Set websocket to None in the agent but keep the message processor running
    if websocket in active_agents:
        agent = active_agents[websocket]
        agent.websocket = (
            None  # This will prevent sending to websocket but keep processing
        )
        # Don't cancel the message processor - it will continue saving to database
        if websocket in message_processors:
            del message_processors[websocket]  # Just remove the reference

    # Cancel any running tasks
    if websocket in active_tasks and not active_tasks[websocket].done():
        active_tasks[websocket].cancel()
        del active_tasks[websocket]

    # Remove agent for this connection
    if websocket in active_agents:
        del active_agents[websocket]


def create_agent_for_connection(
    client: LLMClient,
    workspace_session_uuid: uuid.UUID, # This is for the directory name
    workspace_manager: WorkspaceManager,
    websocket: WebSocket,
    tool_args: Dict[str, Any],
    user_id: str,
    device_id: str, # This is the X-Device-ID header value
    composite_session_id: str,
):
    """Create a new agent instance for a websocket connection."""
    global global_args
    # device_id is now passed directly
    # Setup logging
    logger_for_agent_logs = logging.getLogger(f"agent_logs_{id(websocket)}")
    logger_for_agent_logs.setLevel(logging.DEBUG)
    # Prevent propagation to root logger to avoid duplicate logs
    logger_for_agent_logs.propagate = False

    # Ensure we don't duplicate handlers
    if not logger_for_agent_logs.handlers:
        logger_for_agent_logs.addHandler(logging.FileHandler(global_args.logs_path))
        if not global_args.minimize_stdout_logs:
            logger_for_agent_logs.addHandler(logging.StreamHandler())

    # Initialize database manager
    db_manager = DatabaseManager()

    # Create a new session in the database
    db_manager.create_session(
        composite_session_id=composite_session_id,
        workspace_session_uuid=workspace_session_uuid, # UUID for the directory
        workspace_path=workspace_manager.root,    # Path based on workspace_session_uuid
        user_id=user_id,
        device_id=device_id,
    )
    logger_for_agent_logs.info(
        f"DB Session created with composite_id {composite_session_id} for user {user_id}, device {device_id}, workspace at {workspace_manager.root}"
    )

    # Initialize token counter
    token_counter = TokenCounter()

    # Create context manager based on argument
    if global_args.context_manager == "file-based":
        context_manager = FileBasedContextManager(
            workspace_manager=workspace_manager,
            token_counter=token_counter,
            logger=logger_for_agent_logs,
            token_budget=120_000,
        )
    else:  # standard
        context_manager = StandardContextManager(
            token_counter=token_counter,
            logger=logger_for_agent_logs,
            token_budget=120_000,
        )

    # Initialize agent with websocket
    queue = asyncio.Queue()
    tools = get_system_tools(
        client=client,
        workspace_manager=workspace_manager,
        message_queue=queue,
        container_id=global_args.docker_container_id,
        ask_user_permission=global_args.needs_permission,
        tool_args=tool_args,
    )
    agent = AnthropicFC(
        system_prompt=SYSTEM_PROMPT,
        client=client,
        tools=tools,
        workspace_manager=workspace_manager,
        message_queue=queue,
        logger_for_agent_logs=logger_for_agent_logs,
        context_manager=context_manager,
        max_output_tokens_per_turn=MAX_OUTPUT_TOKENS_PER_TURN,
        max_turns=MAX_TURNS,
        websocket=websocket,
        session_id=composite_session_id,  # Agent uses the composite session ID
        user_id=user_id,
        device_id=device_id, # Pass device_id to the agent constructor
    )

    # Store the composite session ID, user ID, and device_id in the agent
    agent.session_id = composite_session_id
    agent.user_id = user_id
    agent.device_id = device_id # For event saving via agent._process_messages

    return agent


def setup_workspace(app, workspace_path):
    try:
        app.mount(
            "/workspace",
            StaticFiles(directory=workspace_path, html=True),
            name="workspace",
        )
    except RuntimeError:
        # Directory might not exist yet
        os.makedirs(workspace_path, exist_ok=True)
        app.mount(
            "/workspace",
            StaticFiles(directory=workspace_path, html=True),
            name="workspace",
        )


def main():
    """Main entry point for the WebSocket server."""
    global global_args

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="WebSocket Server for interacting with the Agent"
    )
    parser = parse_common_args(parser)
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to run the server on",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on",
    )
    args = parser.parse_args()
    global_args = args

    setup_workspace(app, args.workspace)

    # Start the FastAPI server
    logger.info(f"Starting WebSocket server on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)


@app.post("/api/upload")
async def upload_file_endpoint(request: Request):
    """API endpoint for uploading a single file to the workspace.

    Expects a JSON payload with:
    - session_id: UUID of the session/workspace
    - file: Object with path and content properties
    """
    try:
        data = await request.json()
        session_id = data.get("session_id")
        file_info = data.get("file")

        if not session_id:
            return JSONResponse(
                status_code=400, content={"error": "session_id is required"}
            )

        if not file_info:
            return JSONResponse(
                status_code=400, content={"error": "No file provided for upload"}
            )

        # Find the workspace path for this session
        workspace_path = Path(global_args.workspace).resolve() / session_id
        if not workspace_path.exists():
            return JSONResponse(
                status_code=404,
                content={"error": f"Workspace not found for session: {session_id}"},
            )

        # Create the upload directory if it doesn't exist
        upload_dir = workspace_path / UPLOAD_FOLDER_NAME
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = file_info.get("path", "")
        file_content = file_info.get("content", "")

        if not file_path:
            return JSONResponse(
                status_code=400, content={"error": "File path is required"}
            )

        # Ensure the file path is relative to the workspace
        if Path(file_path).is_absolute():
            file_path = Path(file_path).name

        # Create the full path within the upload directory
        original_path = upload_dir / file_path
        full_path = original_path

        # Handle filename collision by adding a suffix
        if full_path.exists():
            base_name = full_path.stem
            extension = full_path.suffix
            counter = 1

            # Keep incrementing counter until we find a unique filename
            while full_path.exists():
                new_filename = f"{base_name}_{counter}{extension}"
                full_path = upload_dir / new_filename
                counter += 1

            # Update the file_path to reflect the new name
            file_path = f"{full_path.relative_to(upload_dir)}"

        # Ensure any subdirectories exist
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if content is base64 encoded (for binary files)
        if file_content.startswith("data:"):
            # Handle data URLs (e.g., "data:application/pdf;base64,...")
            # Split the header from the base64 content
            header, encoded = file_content.split(",", 1)

            # Decode the content
            decoded = base64.b64decode(encoded)

            # Write binary content
            with open(full_path, "wb") as f:
                f.write(decoded)
        else:
            # Write text content
            with open(full_path, "w") as f:
                f.write(file_content)

        # Log the upload
        logger.info(f"File uploaded to {full_path}")

        # Return the path relative to the workspace for client use
        relative_path = f"/{UPLOAD_FOLDER_NAME}/{file_path}"

        return {
            "message": "File uploaded successfully",
            "file": {"path": relative_path, "saved_path": str(full_path)},
        }

    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return JSONResponse(
            status_code=500, content={"error": f"Error uploading file: {str(e)}"}
        )


# Function moved from utils.py and adapted
def create_workspace_manager_for_connection(
    base_workspace_path: str, use_container_workspace: bool = False
) -> tuple[WorkspaceManager, uuid.UUID]: # Returns UUID for directory name
    """Create a new workspace manager instance for a websocket connection."""
    # Create unique UUID for the directory name for this connection
    workspace_session_uuid = uuid.uuid4() # This UUID is for the directory name
    workspace_path = Path(base_workspace_path).resolve()
    connection_workspace = workspace_path / str(workspace_session_uuid)
    connection_workspace.mkdir(parents=True, exist_ok=True)

    # Initialize workspace manager with connection-specific subdirectory
    # The WorkspaceManager's root will be the UUID-based path.
    actual_workspace_path_for_manager = connection_workspace
    if use_container_workspace:
        # Simplified container path logic (adjust if complex mapping is needed)
        parts = Path(base_workspace_path).parts
        if "app" in parts:
            idx = parts.index("app")
            container_path_parts = parts[idx + 1 :]
            actual_workspace_path_for_manager = Path("/") / Path(*container_path_parts) / str(workspace_session_uuid)
        else:
            # Fallback or specific logic if /app isn't in host path structure
            actual_workspace_path_for_manager = connection_workspace
            
    workspace_manager = WorkspaceManager(
        root=actual_workspace_path_for_manager,
        # container_workspace needs to be the path *inside* the container if different
        # For now, assuming WorkspaceManager handles this or paths are consistent
    )
    # Return the manager and the UUID used for the directory name
    return workspace_manager, workspace_session_uuid


@app.get("/api/sessions/{device_id}")
async def get_sessions_by_device_id(device_id: str):
    """Get all sessions for a specific device ID, sorted by creation time descending.
    For each session, also includes the first user message if available.

    Args:
        device_id: The device identifier to look up sessions for

    Returns:
        A list of sessions with their details and first user message, sorted by creation time descending
    """
    try:
        db_manager = DatabaseManager()
        # This method now directly returns a list of dicts from MongoDB
        # pymongo needs to be imported if not already at the top of the file for sort_order
        # For now, assuming it's available or DatabaseManager handles it.
        # Let's ensure pymongo is imported in this file if using pymongo constants.
        import pymongo # Added import for pymongo.ASCENDING

        sessions_data = db_manager.get_sessions_by_device_id(device_id)
        
        processed_sessions = []
        for session_doc in sessions_data:
            first_message_text = ""
            # Fetch the first user message for this session using the new filter
            first_user_events = db_manager.get_events_for_session(
                session_id=session_doc["_id"], # Use composite ID from session document
                limit=1,
                sort_order=pymongo.ASCENDING,
                event_type_filter=EventType.USER_MESSAGE.value
            )
            
            if first_user_events:
                first_user_event_payload = first_user_events[0].get("event_payload")
                if isinstance(first_user_event_payload, dict):
                    first_message_text = first_user_event_payload.get("content", {}).get("text", "")

            processed_sessions.append({
                "id": session_doc["_id"],
                "workspace_dir": session_doc["workspace_dir"],
                "created_at": session_doc["created_at"].isoformat(),
                "last_activated_at": session_doc.get("last_activated_at", session_doc["created_at"]).isoformat(), # Fallback to created_at if not present
                "device_id": session_doc["device_id"],
                "user_id": session_doc["user_id"],
                "is_active": session_doc.get("is_active", False), # Default to False if not present
                "workspace_session_uuid": session_doc.get("workspace_session_uuid"),
                "first_message": first_message_text,
            })
        return {"sessions": processed_sessions}

    except Exception as e:
        logger.error(f"Error retrieving sessions for device_id {device_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Error retrieving sessions: {str(e)}"
        )


@app.get("/api/sessions/{session_id}/events") # session_id here is the composite ID
async def get_session_events(session_id: str): # session_id is composite
    """Get all events for a specific composite session ID, sorted by timestamp ascending.

    Args:
        session_id: The composite session identifier (user_id_device_id)

    Returns:
        A list of events with their details, sorted by timestamp ascending
    """
    try:
        db_manager = DatabaseManager()
        # get_events_for_session expects the composite session_id
        events_data = db_manager.get_events_for_session(session_id, sort_order=pymongo.ASCENDING)
        
        event_list = []
        for e_doc in events_data:
            event_list.append({
                # "_id" from MongoDB is typically an ObjectId, convert to str if not already
                "id": str(e_doc["_id"]), 
                "session_id": e_doc["session_id"], # Composite session ID
                "user_id": e_doc["user_id"],
                "device_id": e_doc.get("device_id"),
                "timestamp": e_doc["timestamp"].isoformat(),
                "event_type": e_doc["event_type"],
                "event_payload": e_doc["event_payload"],
                # workspace_dir is not directly on event, but on session. We can fetch session if needed.
                # For now, removing it from event list to avoid extra DB call per event.
            })
        return {"events": event_list}

    except Exception as e:
        logger.error(f"Error retrieving events for session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving events: {str(e)}"
        )


if __name__ == "__main__":
    main()
