import os
import uuid
from pathlib import Path
from typing import Optional, Any
from datetime import datetime
import pymongo
from dotenv import load_dotenv
from ii_agent.core.event import RealtimeEvent

load_dotenv()


class DatabaseManager:
    """Manager class for database operations using MongoDB."""

    def __init__(self, mongodb_uri: Optional[str] = None, db_name: str = "agent_db"):
        """Initialize the database manager.

        Args:
            mongodb_uri: MongoDB connection string. Defaults to MONGODB_URI env var.
            db_name: Name of the database to use.
        """
        if mongodb_uri is None:
            mongodb_uri = os.getenv("MONGODB_URI")
            if not mongodb_uri:
                raise ValueError(
                    "MongoDB connection string not provided and MONGODB_URI not set."
                )

        self.client = pymongo.MongoClient(mongodb_uri)
        self.db = self.client[db_name]
        self.sessions_collection = self.db["sessions"]
        self.events_collection = self.db["events"]

    def create_session(
        self,
        composite_session_id: str,
        workspace_session_uuid: uuid.UUID, # For the directory name
        workspace_path: Path,
        user_id: str,
        device_id: Optional[str] = None,
    ) -> tuple[str, Path]:
        """Create a new session document in MongoDB using a composite session ID.

        Args:
            composite_session_id: The composite ID (user_id + device_id) for the session.
            workspace_session_uuid: The UUID used for the actual workspace directory name.
            workspace_path: The full path to the workspace directory.
            user_id: The identifier for the user.
            device_id: Optional device identifier for the session.

        Returns:
            A tuple of (composite_session_id, workspace_path).
        """
        now = datetime.utcnow()

        # 1. Deactivate existing active sessions for this user_id and device_id
        self.sessions_collection.update_many(
            {"user_id": user_id, "device_id": device_id, "is_active": True},
            {"$set": {"is_active": False, "deactivated_at": now}},
        )

        # 2. Create or Reactivate Session using upsert
        # If a session with _id = composite_session_id exists, it will be updated.
        # Otherwise, a new session will be inserted.
        update_document = {
            "$set": {
                "user_id": user_id,
                "device_id": device_id,
                "workspace_session_uuid": str(workspace_session_uuid),
                "workspace_dir": str(workspace_path),
                "is_active": True,
                "last_activated_at": now,
            },
            "$setOnInsert": {
                "created_at": now, # Set created_at only if it's a new document
                "_id": composite_session_id # Set _id on insert
            }
        }
        
        self.sessions_collection.update_one(
            {"_id": composite_session_id}, # Query by composite_session_id
            update_document,
            upsert=True,
        )
        
        return composite_session_id, workspace_path

    def save_event(
        self,
        session_id: str, # This is the composite ID
        user_id: str,
        device_id: Optional[str],
        event: RealtimeEvent,
    ) -> Any: # Returns MongoDB _id
        """Save an event to the events collection in MongoDB.

        Args:
            session_id: The identifier of the session this event belongs to.
            user_id: The identifier of the user associated with this event.
            device_id: The identifier of the device associated with this event.
            event: The event to save.

        Returns:
            The MongoDB-generated _id for the event document.
        """
        event_document = {
            "session_id": session_id,
            "user_id": user_id,
            "device_id": device_id,
            "timestamp": datetime.utcnow(),
            "event_type": event.type.value,
            "event_payload": event.model_dump(),
        }
        result = self.events_collection.insert_one(event_document)
        return result.inserted_id

    def get_session_events(self, session_id: uuid.UUID) -> list[dict]:
        """Get all events for a session using session_uuid.

        Args:
            session_id: The UUID of the session (maps to 'session_uuid' in events).

        Returns:
            A list of event documents.
        """
        # Events should be linked via the composite session_id.
        # The `session_uuid` field in the event document should store the composite_session_id.
        # Or, the query here should be on `session_id` if that's what's stored in events.
        # For clarity, let's assume events store `session_id` (composite)
        return list(self.events_collection.find({"session_id": str(session_id)}))

    def get_session_by_workspace(self, workspace_dir: str) -> Optional[dict]:
        """Get a session by its workspace directory.

        Args:
            workspace_dir: The workspace directory path.

        Returns:
            The session document if found, None otherwise.
        """
        return self.sessions_collection.find_one({"workspace_dir": workspace_dir})

    def get_session_by_id(self, session_id: uuid.UUID) -> Optional[dict]:
        """Get a session by its UUID (document _id).

        Args:
            session_id: The UUID of the session.

        Returns:
            The session document if found, None otherwise.
        """
        # This method might need adjustment if session_id is composite.
        # It currently queries _id which is composite_session_id.
        # If session_id is UUID, then it's fine.
        return self.sessions_collection.find_one({"_id": str(session_id)})

    def get_sessions_by_device_id(self, device_id: str) -> list[dict]:
        """Get all sessions for a specific device ID, sorted by creation time descending.

        Args:
            device_id: The device identifier.

        Returns:
            A list of session documents.
        """
        return list(
            self.sessions_collection.find({"device_id": device_id}).sort(
                "created_at", pymongo.DESCENDING
            )
        )

    def get_events_for_session(
        self,
        session_id: str,
        limit: int = 0,
        sort_order=pymongo.ASCENDING,
        event_type_filter: Optional[str] = None,
    ) -> list[dict]:
        """Get events for a specific session_id, sorted by timestamp, with optional limit and type filter.
        This 'session_id' can be the composite ID.

        Args:
            session_id: The session identifier (can be composite).
            limit: The maximum number of events to return. 0 means no limit.
            sort_order: pymongo.ASCENDING or pymongo.DESCENDING for timestamp sorting.
            event_type_filter: Optional event type string to filter by (e.g., "user_message").

        Returns:
            A list of event documents.
        """
        find_query = {"session_id": session_id}
        if event_type_filter:
            find_query["event_type"] = event_type_filter
            
        query_cursor = self.events_collection.find(find_query).sort(
            "timestamp", sort_order
        )
        if limit > 0:
            query_cursor = query_cursor.limit(limit)
        return list(query_cursor)


# Example usage (for testing purposes, can be removed or adapted):
# if __name__ == "__main__":
#     # Ensure MONGODB_URI is set in your .env file or environment
#     db_manager = DatabaseManager()
#     print("MongoDB client initialized.")

    #     # Test create_session (assuming user_id is passed correctly)
#     test_session_uuid = uuid.uuid4()
#     test_workspace_path = Path(f"/tmp/workspace_{test_session_uuid}")
#     test_user_id = "test_user_for_retrieval"
#     test_device_id = "device_for_retrieval"
#     s_uuid, w_path = db_manager.create_session(
#         session_uuid=test_session_uuid,
#         workspace_path=test_workspace_path,
#         user_id=test_user_id, # Added user_id
#         device_id=test_device_id,
#     )
#     print(f"Session created with UUID: {s_uuid} at {w_path} for user {test_user_id}")

    #     # Test save_event
#     from ii_agent.core.event import EventType
#     test_event_1 = RealtimeEvent(
#         type=EventType.USER_MESSAGE, content={"text": "Hello 1"}
#     )
#     test_event_2 = RealtimeEvent(
#         type=EventType.SYSTEM_MESSAGE, content={"text": "Processing 1"}
#     )
    
#     # Using session_uuid for save_event's session_id for now as per current save_event
#     # This might change if save_event expects a composite ID
#     event_mongo_id_1 = db_manager.save_event(
#         session_id=str(test_session_uuid), # Using session_uuid as session_id for event
#         user_id=test_user_id,
#         device_id=test_device_id,
#         event=test_event_1
#     )
#     print(f"Event 1 saved with MongoDB _id: {event_mongo_id_1}")
#     import time; time.sleep(0.01) # Ensure distinct timestamps
#     event_mongo_id_2 = db_manager.save_event(
#         session_id=str(test_session_uuid), # Using session_uuid as session_id for event
#         user_id=test_user_id,
#         device_id=test_device_id,
#         event=test_event_2
#     )
#     print(f"Event 2 saved with MongoDB _id: {event_mongo_id_2}")

    #     # Test get_session_by_id
#     retrieved_session = db_manager.get_session_by_id(test_session_uuid)
#     print(f"Retrieved session by ID ({test_session_uuid}): {retrieved_session}")

    #     # Test get_session_by_workspace
#     retrieved_session_ws = db_manager.get_session_by_workspace(str(test_workspace_path))
#     print(f"Retrieved session by workspace ({test_workspace_path}): {retrieved_session_ws}")

    #     # Test get_sessions_by_device_id
#     retrieved_sessions_device = db_manager.get_sessions_by_device_id(test_device_id)
#     print(f"Retrieved sessions by device ID ({test_device_id}): {retrieved_sessions_device}")

    #     # Test get_session_events (using session_uuid)
#     # This method's session_id param is session_uuid.
#     # If events use composite session_id, then their 'session_uuid' field should be populated.
#     # The current save_event uses the passed session_id (which could be composite)
#     # For this test to work with get_session_events, events need a 'session_uuid' field.
#     # Let's assume save_event stores session_uuid in event_document["session_uuid"] as well.
#     # If not, this test or get_session_events needs adjustment.
#     # For now, let's assume events are saved with a 'session_id' field that is str(session_uuid)
#     # based on current save_event. If so, get_session_events needs to query on 'session_id'.
#     # Let's adjust get_session_events to query on 'session_id' for this example to work.
#     # (Original thought: "session_uuid": str(session_id) - changing this for test)
#     # If the 'session_id' in events is the composite ID, then this test is flawed for get_session_events.
#     # For now, the test for get_session_events might need careful setup or the method adjusted.
#     # Let's assume `save_event` saves `session_id` as the `session_uuid` for this test.
    
#     # Re-saving event with session_uuid in a field named 'session_uuid' if get_session_events expects that
#     # Or, adjust get_session_events to use the 'session_id' field which is str(session_uuid)
#     # Current get_session_events uses "session_uuid": str(session_id)
#     # This means events need a field named "session_uuid" that matches the session_uuid.
#     # The current save_event uses "session_id" for the event's session identifier.
#     # To make get_session_events work as written, save_event would need to also save a session_uuid field.
    
#     # Simplification: Let's assume `get_session_events` `session_id` parameter is the value to query for in the `session_id` field of events.
#     retrieved_events_for_session = db_manager.get_session_events(test_session_uuid) # Pass UUID
#     print(f"Retrieved events (get_session_events for {test_session_uuid}): {retrieved_events_for_session}")
#     # This will work if get_session_events queries {"session_id": str(session_id)}

    #     # Test get_events_for_session (using str(session_uuid) as the session_id for events)
#     retrieved_events_flexible = db_manager.get_events_for_session(str(test_session_uuid), limit=1, sort_order=pymongo.DESCENDING)
#     print(f"Retrieved events (get_events_for_session for {test_session_uuid}, limit 1 DESC): {retrieved_events_flexible}")
    
#     # Clean up (optional)
#     # db_manager.sessions_collection.delete_one({"_id": str(test_session_uuid)})
#     # db_manager.events_collection.delete_many({"session_id": str(test_session_uuid)})
#     # print("Test data cleaned up.")

# Example usage (for testing purposes, remove later):
# if __name__ == "__main__":
#     # Ensure MONGODB_URI is set in your .env file or environment
#     db_manager = DatabaseManager()
#     print("MongoDB client initialized.")

#     # Test create_session (assuming user_id is passed correctly)
#     test_session_uuid = uuid.uuid4()
#     test_workspace_path = Path(f"/tmp/workspace_{test_session_uuid}")
#     test_user_id = "test_user_for_retrieval"
#     test_device_id = "device_for_retrieval"
#     s_uuid, w_path = db_manager.create_session(
#         session_uuid=test_session_uuid,
#         workspace_path=test_workspace_path,
#         user_id=test_user_id, # Added user_id
#         device_id=test_device_id,
#     )
#     print(f"Session created with UUID: {s_uuid} at {w_path} for user {test_user_id}")

#     # Test save_event
#     from ii_agent.core.event import EventType
#     test_event_1 = RealtimeEvent(
#         type=EventType.USER_MESSAGE, content={"text": "Hello 1"}
#     )
#     test_event_2 = RealtimeEvent(
#         type=EventType.SYSTEM_MESSAGE, content={"text": "Processing 1"}
#     )
    
#     # Using session_uuid for save_event's session_id for now as per current save_event
#     # This might change if save_event expects a composite ID
#     event_mongo_id_1 = db_manager.save_event(
#         session_id=str(test_session_uuid), # Using session_uuid as session_id for event
#         user_id=test_user_id,
#         device_id=test_device_id,
#         event=test_event_1
#     )
#     print(f"Event 1 saved with MongoDB _id: {event_mongo_id_1}")
#     import time; time.sleep(0.01) # Ensure distinct timestamps
#     event_mongo_id_2 = db_manager.save_event(
#         session_id=str(test_session_uuid), # Using session_uuid as session_id for event
#         user_id=test_user_id,
#         device_id=test_device_id,
#         event=test_event_2
#     )
#     print(f"Event 2 saved with MongoDB _id: {event_mongo_id_2}")

#     # Test get_session_by_id
#     retrieved_session = db_manager.get_session_by_id(test_session_uuid)
#     print(f"Retrieved session by ID ({test_session_uuid}): {retrieved_session}")

#     # Test get_session_by_workspace
#     retrieved_session_ws = db_manager.get_session_by_workspace(str(test_workspace_path))
#     print(f"Retrieved session by workspace ({test_workspace_path}): {retrieved_session_ws}")

#     # Test get_sessions_by_device_id
#     retrieved_sessions_device = db_manager.get_sessions_by_device_id(test_device_id)
#     print(f"Retrieved sessions by device ID ({test_device_id}): {retrieved_sessions_device}")

#     # Test get_session_events (using session_uuid)
#     # This method's session_id param is session_uuid.
#     # If events use composite session_id, then their 'session_uuid' field should be populated.
#     # The current save_event uses the passed session_id (which could be composite)
#     # For this test to work with get_session_events, events need a 'session_uuid' field.
#     # Let's assume save_event stores session_uuid in event_document["session_uuid"] as well.
#     # If not, this test or get_session_events needs adjustment.
#     # For now, let's assume events are saved with a 'session_id' field that is str(session_uuid)
#     # based on current save_event. If so, get_session_events needs to query on 'session_id'.
#     # Let's adjust get_session_events to query on 'session_id' for this example to work.
#     # (Original thought: "session_uuid": str(session_id) - changing this for test)
#     # If the 'session_id' in events is the composite ID, then this test is flawed for get_session_events.
#     # For now, the test for get_session_events might need careful setup or the method adjusted.
#     # Let's assume `save_event` saves `session_id` as the `session_uuid` for this test.
    
#     # Re-saving event with session_uuid in a field named 'session_uuid' if get_session_events expects that
#     # Or, adjust get_session_events to use the 'session_id' field which is str(session_uuid)
#     # Current get_session_events uses "session_uuid": str(session_id)
#     # This means events need a field named "session_uuid" that matches the session_uuid.
#     # The current save_event uses "session_id" for the event's session identifier.
#     # To make get_session_events work as written, save_event would need to also save a session_uuid field.
    
#     # Simplification: Let's assume `get_session_events` `session_id` parameter is the value to query for in the `session_id` field of events.
#     retrieved_events_for_session = db_manager.get_session_events(test_session_uuid) # Pass UUID
#     print(f"Retrieved events (get_session_events for {test_session_uuid}): {retrieved_events_for_session}")
#     # This will work if get_session_events queries {"session_id": str(session_id)}

#     # Test get_events_for_session (using str(session_uuid) as the session_id for events)
#     retrieved_events_flexible = db_manager.get_events_for_session(str(test_session_uuid), limit=1, sort_order=pymongo.DESCENDING)
#     print(f"Retrieved events (get_events_for_session for {test_session_uuid}, limit 1 DESC): {retrieved_events_flexible}")
    
#     # Clean up (optional)
#     # db_manager.sessions_collection.delete_one({"_id": str(test_session_uuid)})
#     # db_manager.events_collection.delete_many({"session_id": str(test_session_uuid)})
#     # print("Test data cleaned up.")
