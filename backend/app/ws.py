from fastapi import WebSocket


class ConnectionManager:
    """
    Manages all active WebSocket connections.
    """

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Accept a new WebSocket connection
        and add it to the active connections list.
        """
        await websocket.accept()

        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Remove a disconnected WebSocket.
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """
        Send a message to all connected clients.
        """

        disconnected_connections = []

        for websocket in self.active_connections:

            try:
                await websocket.send_json(message)

            except Exception:
                # Client may have disconnected unexpectedly
                disconnected_connections.append(websocket)

        # Remove disconnected clients
        for websocket in disconnected_connections:
            self.disconnect(websocket)


# Create one shared connection manager
manager = ConnectionManager()