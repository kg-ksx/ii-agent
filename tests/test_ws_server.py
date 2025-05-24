import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import httpx # Import httpx for RequestError

# Make sure ws_server is importable. This might require adjusting PYTHONPATH
# or the project structure if tests are not run from the project root.
# For now, assuming it can be imported.
# If ws_server.py is at the root of the project:
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ws_server import fetch_user_id, logger as ws_logger # Import the logger to check calls

# Disable logger propagation for tests to avoid cluttering test output,
# but allow checking calls to logger methods.
ws_logger.propagate = False


@pytest.mark.asyncio
async def test_fetch_user_id_success():
    """Test fetch_user_id successful call."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"user_id": "test_user_123"}

    async_mock_post = AsyncMock(return_value=mock_response)

    with patch('httpx.AsyncClient.post', new=async_mock_post) as mock_post:
        user_id = await fetch_user_id("token", "api_key", "client_key", "device_id")
        assert user_id == "test_user_123"
        mock_post.assert_called_once_with(
            "https://example.com/fetchuser",
            json={
                "token": "token",
                "api_key": "api_key",
                "client_key": "client_key",
                "device_id": "device_id",
            },
            timeout=10.0
        )
        # Check logger was called with success message (optional, depends on desired test depth)
        # For this, you might need to patch the logger object within ws_server.py if it's module-level
        # or pass logger as a dependency to fetch_user_id.
        # Example if logger was patched: ws_logger.info.assert_called_with("Successfully fetched user_id: test_user_123")


@pytest.mark.asyncio
async def test_fetch_user_id_api_error():
    """Test fetch_user_id with a non-200 API response."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    # Configure raise_for_status to raise an HTTPStatusError like httpx does
    mock_response.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError("Error", request=None, response=mock_response))


    async_mock_post = AsyncMock(return_value=mock_response)

    with patch('httpx.AsyncClient.post', new=async_mock_post):
        with patch.object(ws_logger, 'error') as mock_logger_error:
            user_id = await fetch_user_id("token", None, None, None)
            assert user_id is None
            mock_logger_error.assert_called_once()
            # More specific check on the log message if desired:
            # mock_logger_error.assert_called_with(f"HTTP error occurred: {mock_response.status_code} - {mock_response.text}")


@pytest.mark.asyncio
async def test_fetch_user_id_request_error():
    """Test fetch_user_id with an httpx.RequestError (network issue)."""
    async_mock_post = AsyncMock(side_effect=httpx.RequestError("Network error", request=None))

    with patch('httpx.AsyncClient.post', new=async_mock_post):
        with patch.object(ws_logger, 'error') as mock_logger_error:
            user_id = await fetch_user_id("token", "api_key", None, None)
            assert user_id is None
            mock_logger_error.assert_called_once()
            # mock_logger_error.assert_called_with("Request error occurred: Network error")


@pytest.mark.asyncio
async def test_fetch_user_id_invalid_json():
    """Test fetch_user_id with a successful response but invalid JSON."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.side_effect = json.JSONDecodeError("Error decoding JSON", "{}", 0)
    # Ensure raise_for_status does not raise for 200
    mock_response.raise_for_status = MagicMock()


    async_mock_post = AsyncMock(return_value=mock_response)

    with patch('httpx.AsyncClient.post', new=async_mock_post):
        with patch.object(ws_logger, 'error') as mock_logger_error:
            user_id = await fetch_user_id(None, "api_key", None, "device_id")
            assert user_id is None
            # This will log "An unexpected error occurred: Error decoding JSON" because json.JSONDecodeError is an Exception
            mock_logger_error.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_user_id_missing_user_id_in_response():
    """Test fetch_user_id with a successful response but missing 'user_id' key."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"some_other_key": "some_value"} # No user_id
    mock_response.raise_for_status = MagicMock()

    async_mock_post = AsyncMock(return_value=mock_response)

    with patch('httpx.AsyncClient.post', new=async_mock_post):
        with patch.object(ws_logger, 'error') as mock_logger_error:
            user_id = await fetch_user_id("token", None, "client_key", None)
            assert user_id is None
            mock_logger_error.assert_called_with("user_id not found in response")


@pytest.mark.asyncio
async def test_fetch_user_id_all_none_params():
    """Test fetch_user_id when all parameters are None."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"user_id": "test_user_none_params"}
    mock_response.raise_for_status = MagicMock()

    async_mock_post = AsyncMock(return_value=mock_response)

    with patch('httpx.AsyncClient.post', new=async_mock_post) as mock_post:
        user_id = await fetch_user_id(None, None, None, None)
        assert user_id == "test_user_none_params"
        mock_post.assert_called_once_with(
            "https://example.com/fetchuser",
            json={
                "token": None,
                "api_key": None,
                "client_key": None,
                "device_id": None,
            },
            timeout=10.0
        )

# Placeholder for WebSocket endpoint tests - to be developed further
# from fastapi.testclient import TestClient
# from ws_server import app # Assuming app is your FastAPI instance

# def test_websocket_auth_missing_user_id():
#     client = TestClient(app)
#     with patch('ws_server.fetch_user_id', new_callable=AsyncMock) as mock_fetch:
#         mock_fetch.return_value = None # Simulate fetch_user_id failing
#         with client.websocket_connect("/ws?device_id=test_device") as websocket:
#             # Connection should be accepted first, then error sent, then closed.
#             # FastAPI TestClient for WebSockets might behave differently or require careful handling
#             # to check messages before closure by server.
#             try:
#                 data = websocket.receive_json()
#                 assert data["type"] == "error" # Or EventType.ERROR.value
#                 assert data["content"]["message"] == "User authentication failed."
                
#                 # Check if connection is closed (this might raise an exception)
#                 # with pytest.raises(WebSocketDisconnect): # Or specific exception from your WS library
#                 #     websocket.receive_json() 
#             except Exception as e: # Replace with specific WebSocketDisconnect exception if available
#                 pass # Expected if server closes connection

# def test_websocket_auth_success():
#     client = TestClient(app)
#     with patch('ws_server.fetch_user_id', new_callable=AsyncMock) as mock_fetch_user_id:
#         mock_fetch_user_id.return_value = "mock_user_123"
#         # Further mocking might be needed for create_workspace_manager_for_connection, etc.
#         # if the test goes deeper into the connection logic.
#         with patch('ws_server.create_workspace_manager_for_connection') as mock_create_workspace, \
#              patch('ws_server.get_client') as mock_get_llm_client, \
#              patch('ws_server.create_agent_for_connection') as mock_create_agent: # Mock deeper calls
            
#             mock_create_workspace.return_value = (MagicMock(), "mock_session_uuid")
#             mock_get_llm_client.return_value = MagicMock()
#             mock_create_agent.return_value = MagicMock()

#             try:
#                 with client.websocket_connect("/ws?X-Device-ID=test_device_success") as websocket: # Pass X-Device-ID if needed
#                     # Check for CONNECTION_ESTABLISHED or other initial messages
#                     data = websocket.receive_json() 
#                     assert data["type"] == EventType.CONNECTION_ESTABLISHED.value
#                     # The connection should remain open here for further interaction if auth is successful
#                     # Send a ping or init_agent to confirm
#                     websocket.send_json({"type": "ping"})
#                     response = websocket.receive_json()
#                     assert response["type"] == EventType.PONG.value
#             except Exception as e:
#                 pytest.fail(f"WebSocket connection failed or closed unexpectedly: {e}")

# Note: The WebSocket endpoint tests are more complex due to the async nature and
# the need to mock multiple dependencies. They are placeholders and would need
# careful implementation and possibly more specific exception handling for disconnects.
# The primary focus for this subtask was fetch_user_id.
# The use of `global_args` in ws_server.py will also need to be handled for tests,
# likely by patching `global_args` or refactoring ws_server.py to make `args`
# more directly configurable or injectable for endpoints.
# For example, using FastAPI's dependency injection for settings.

# To run these tests:
# Ensure you are in the root directory of the project.
# Run `python -m pytest`
# If `ws_server.py` is not directly in the root or `PYTHONPATH` is not set up,
# tests might fail due to import errors. The sys.path manipulation is a common way to handle this for simple cases.
# A more robust solution involves proper packaging or using `pytest` with `PYTHONPATH` env var.

# Also, the logger patching:
# If `ws_logger` is `logging.getLogger("websocket_server")`, then `patch.object(ws_logger, 'error')`
# should work as intended.
# The `json` import was missing for `json.JSONDecodeError`, added.
import json
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

# Import EventType and app from ws_server
from ws_server import app, EventType, global_args as ws_server_global_args

# It's important that `global_args` in `ws_server.py` is initialized or patched
# for tests that might trigger code paths relying on it (like `create_workspace_manager_for_connection`
# if it uses `global_args.workspace` or `global_args.use_container_workspace`).
# A simple way for tests is to set it before running endpoint tests:
# ws_server.global_args = MagicMock(workspace="test_ws", use_container_workspace=False, ...)
# Or, better, refactor ws_server.py to use FastAPI's dependency injection for settings.
# For now, fetch_user_id tests don't depend on global_args.

# The `create_workspace_manager_for_connection` function (now in ws_server.py)
# is called in the `/ws` endpoint. If testing that endpoint, `global_args` needs to be set.
# For example, before TestClient(app) or within a fixture:
@pytest.fixture(autouse=True)
def setup_global_args_for_tests():
    """Set up ws_server.global_args for tests that need it."""
    class MockArgs:
        workspace = "./test_workspace_dir" # Use a dedicated test workspace
        use_container_workspace = False
        project_id = "test_project"
        region = "test_region"
        # Add other args create_workspace_manager_for_connection or other parts of /ws might need
        # For example, those used by create_agent_for_connection if not mocking that far
        logs_path = "test_agent_logs.txt"
        minimize_stdout_logs = True
        context_manager = "standard" # Or "file-based"
        docker_container_id = None
        needs_permission = False


    # Ensure the test workspace directory exists
    Path(MockArgs.workspace).mkdir(parents=True, exist_ok=True)
    
    # Patch global_args in the ws_server module
    # This is a common approach if dependency injection isn't used for settings.
    # Note: This directly modifies the module's global.
    # Consider if ws_server can be refactored to take settings via DI for better testability.
    original_global_args = ws_server_global_args
    ws_server.global_args = MockArgs()
    yield
    # Restore original global_args after test if necessary, though for a test suite,
    # it might be acceptable to leave it patched if all tests expect this mock.
    ws_server.global_args = original_global_args


# Test for WebSocket authentication failure (fetch_user_id returns None)
def test_websocket_auth_fetch_user_id_none():
    client = TestClient(app)
    with patch('ws_server.fetch_user_id', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = None # Simulate fetch_user_id failing

        with pytest.raises(WebSocketDisconnect) as excinfo:
            with client.websocket_connect("/ws") as websocket:
                # The server should send an error and close the connection.
                # TestClient might raise WebSocketDisconnect when server closes.
                # We need to see if a message is received *before* the disconnect.
                # This behavior can be tricky with TestClient.
                # A more direct way is to check the close code if available,
                # or ensure the disconnect happens.
                # Let's try to receive, expecting it to fail after server closes.
                data = websocket.receive_json() # This might fail if server closes too fast
                                                # or succeed if message sent before close
                assert data["type"] == EventType.ERROR.value
                assert data["content"]["message"] == "User authentication failed."
                # Try receiving again, expecting a disconnect or specific close message
                websocket.receive_json() # This should raise an error indicating closure

        # Check the close code if available in excinfo (depends on TestClient version and underlying library)
        # For Starlette's TestClient, the disconnect exception itself is the primary check.
        # print(f"Disconnect info: {excinfo.value.code if hasattr(excinfo.value, 'code') else 'N/A'}")
        assert mock_fetch.called # Ensure fetch_user_id was actually called


# Test for WebSocket authentication success path (fetch_user_id returns a user_id)
# but X-Device-ID header is missing.
def test_websocket_auth_success_fetch_user_id_but_missing_device_id():
    client = TestClient(app)
    with patch('ws_server.fetch_user_id', new_callable=AsyncMock) as mock_fetch_user_id:
        mock_fetch_user_id.return_value = "mock_user_123" # fetch_user_id succeeds

        # Attempt to connect without X-Device-ID header.
        # TestClient websocket_connect headers are for HTTP handshake, not subprotocol/WebSocket headers.
        # FastAPI gets WebSocket headers from the connection scope.
        # We rely on the endpoint logic to extract it. If it's missing, error should occur.
        # The current ws_server.py code extracts device_id_header from websocket.headers.
        # For TestClient, these are passed in the `headers` argument to websocket_connect.
        
        with pytest.raises(WebSocketDisconnect):
             with client.websocket_connect("/ws", headers={}) as websocket: # No X-Device-ID
                data = websocket.receive_json()
                assert data["type"] == EventType.ERROR.value
                assert data["content"]["message"] == "X-Device-ID header is required and was not found."
                websocket.receive_json() # Expect closure

        assert mock_fetch_user_id.called


# Test for successful WebSocket connection and initial message
def test_websocket_auth_fully_successful_connection():
    client = TestClient(app)
    with patch('ws_server.fetch_user_id', new_callable=AsyncMock) as mock_fetch_user_id, \
         patch('ws_server.create_workspace_manager_for_connection') as mock_create_workspace, \
         patch('ws_server.get_client', return_value=MagicMock()) as mock_get_llm_client: # Mock LLM client
        
        mock_fetch_user_id.return_value = "test_user_xyz"
        
        # Mock for create_workspace_manager_for_connection
        mock_ws_manager_instance = MagicMock(spec=Path) # Simulate a path-like object for workspace_manager.root
        mock_ws_manager_instance.root = Path("./test_workspace_dir/mock_uuid")
        mock_create_workspace.return_value = (mock_ws_manager_instance, "mock_uuid_for_dir")

        # Connect with necessary headers for success (X-Device-ID)
        # Headers in TestClient's websocket_connect are for the initial HTTP handshake.
        # FastAPI's WebSocket class then provides these headers to the endpoint.
        headers = {"X-Device-ID": "test_device_123"}
        try:
            with client.websocket_connect("/ws", headers=headers) as websocket:
                # 1. Check for CONNECTION_ESTABLISHED message
                data = websocket.receive_json()
                assert data["type"] == EventType.CONNECTION_ESTABLISHED.value
                assert "Connected to Agent WebSocket Server" in data["content"]["message"]
                assert "workspace_path" in data["content"]
                
                # Connection should remain open. We can try a ping for example.
                # To test ping, we need create_agent_for_connection to be mocked as well,
                # because init_agent is usually called before ping.
                # For now, just checking connection_established is enough for this test's scope.

        except WebSocketDisconnect:
            pytest.fail("WebSocket disconnected unexpectedly during successful auth test.")
        
        assert mock_fetch_user_id.called
        assert mock_create_workspace.called
        # LLM client should also be fetched if auth and workspace setup are fine
        # This happens before messages are processed, within the try block of websocket_endpoint
        assert mock_get_llm_client.called


# The SQLAlchemy `text` import and `Event` model import in `ws_server.py` are unused
# residues from previous versions. They don't affect these tests but could be cleaned up.
# from sqlalchemy import asc, text
# from ii_agent.db.models import Event
# These are not used by fetch_user_id or the parts of /ws being tested here.
# However, if `get_sessions_by_device_id` or `get_session_events` were called and
# still had SQLAlchemy code, that would be an issue. They were updated to use MongoDB.
# The `Event` model from `ii_agent.db.models` would be for SQLAlchemy, not MongoDB.
# The `asc` and `text` from `sqlalchemy` are also not used in the MongoDB versions.
# This is just a note on ws_server.py's current state.
