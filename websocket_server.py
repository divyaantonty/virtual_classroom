import asyncio
import websockets
import json

# Store active sessions and their data
sessions = {}
clients = {}
whiteboard_states = {}  # Store the current state of each whiteboard

async def handle_websocket(websocket, path):
    try:
        async for message in websocket:
            data = json.loads(message)
            session_id = data.get('session')

            if data['type'] == 'join':
                # Add client to session
                if session_id not in sessions:
                    sessions[session_id] = set()
                    whiteboard_states[session_id] = []  # Initialize empty whiteboard state
                
                sessions[session_id].add(websocket)
                clients[websocket] = session_id

                # Send current whiteboard state to new user
                await websocket.send(json.dumps({
                    'type': 'init',
                    'state': whiteboard_states[session_id]
                }))

                # Broadcast user count
                await broadcast_to_session(session_id, {
                    'type': 'users',
                    'count': len(sessions[session_id])
                })

            elif data['type'] == 'draw':
                # Store drawing action in whiteboard state
                if session_id in whiteboard_states:
                    whiteboard_states[session_id].append({
                        'type': 'draw',
                        'x': data['x'],
                        'y': data['y'],
                        'color': data['color'],
                        'width': data['width'],
                        'tool': data.get('tool', 'pen')
                    })
                await broadcast_to_session(session_id, data, exclude=websocket)

            elif data['type'] == 'clear':
                # Clear whiteboard state
                if session_id in whiteboard_states:
                    whiteboard_states[session_id] = []
                await broadcast_to_session(session_id, data)

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # Cleanup when client disconnects
        if websocket in clients:
            session_id = clients[websocket]
            if session_id in sessions:
                sessions[session_id].remove(websocket)
                if len(sessions[session_id]) == 0:
                    del sessions[session_id]
                    del whiteboard_states[session_id]
                else:
                    await broadcast_to_session(session_id, {
                        'type': 'users',
                        'count': len(sessions[session_id])
                    })
            del clients[websocket]

async def broadcast_to_session(session_id, message, exclude=None):
    if session_id in sessions:
        for client in sessions[session_id]:
            if client != exclude:
                await client.send(json.dumps(message))

start_server = websockets.serve(handle_websocket, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()