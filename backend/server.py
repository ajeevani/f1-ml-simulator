#!/usr/bin/env python3
"""
F1 WebSocket Server - Railway Compatible with /ws path
"""
import asyncio
import websockets
import json
import sys
import os
import logging

# Railway setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PORT = int(os.environ.get("PORT", 8000))
HOST = "0.0.0.0"

class F1CLIBridge:
    def __init__(self):
        self.connected_clients = set()
        self.is_cli_running = False
        self.message_queue = asyncio.Queue()
        self.broadcaster_task = None

    async def start_cli_process(self):
        if self.is_cli_running:
            return True
        
        await self.message_queue.put({
            'type': 'output',
            'data': '🏎️ F1 Professional Simulator\n🏁 Championship Mode Ready\nType "help" for commands\n> '
        })
        self.is_cli_running = True
        self.broadcaster_task = asyncio.create_task(self._broadcast_messages())
        return True

    async def _broadcast_messages(self):
        try:
            while self.is_cli_running:
                try:
                    message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                if not self.connected_clients:
                    continue

                json_message = json.dumps(message, ensure_ascii=False)
                disconnected = set()
                for client in self.connected_clients.copy():
                    try:
                        await client.send(json_message)
                    except Exception:
                        disconnected.add(client)
                self.connected_clients -= disconnected
        except Exception as e:
            logger.error(f"Broadcast error: {e}")

    async def send_input_to_cli(self, input_data):
        input_lower = input_data.lower().strip()
        
        responses = {
            'help': '🏎️ F1 Commands:\n- race: Start race\n- status: Show status\n- help: This help\n> ',
            'status': f'✅ F1 Server Status:\n🔌 Clients: {len(self.connected_clients)}\n🏎️ Mode: Championship\n> ',
            'race': '🏁 F1 RACE START!\n🏎️ Lights out and away we go!\n⚡ Hamilton takes the lead!\n> '
        }
        
        response = responses.get(input_lower, f'F1: {input_data}\nType "help" for commands\n> ')
        
        await self.message_queue.put({
            'type': 'output',
            'data': response
        })

    async def handle_client(self, websocket):
        self.connected_clients.add(websocket)
        logger.info(f"F1 Client connected. Total: {len(self.connected_clients)}")
        
        try:
            if len(self.connected_clients) == 1:
                await self.start_cli_process()

            await websocket.send(json.dumps({
                'type': 'welcome',
                'data': '🏎️ F1 WebSocket Server Connected!\n'
            }))

            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get('type') == 'input':
                        await self.send_input_to_cli(data.get('data', ''))
                except Exception as e:
                    logger.error(f"Message error: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("F1 Client disconnected")
        except Exception as e:
            logger.error(f"F1 Client error: {e}")
        finally:
            self.connected_clients.discard(websocket)
            logger.info(f"F1 Client cleaned up. Remaining: {len(self.connected_clients)}")
            
            if not self.connected_clients:
                self.is_cli_running = False
                if self.broadcaster_task:
                    self.broadcaster_task.cancel()

bridge = F1CLIBridge()

# ✅ CRITICAL FIX: Handle /ws path specifically
def process_request(connection, request):
    logger.info(f"Request to: {request.path}")
    
    # ✅ Handle WebSocket upgrade on /ws path
    if request.path == "/ws":
        # Check if it's a proper WebSocket upgrade request
        try:
            connection_header = request.headers.get("connection", "").lower()
            upgrade_header = request.headers.get("upgrade", "").lower()
            
            if "upgrade" in connection_header and upgrade_header == "websocket":
                logger.info("✅ WebSocket upgrade allowed on /ws")
                return None  # Allow WebSocket upgrade
            else:
                # Not a WebSocket upgrade - return 426 Upgrade Required
                logger.info("❌ Non-WebSocket request to /ws - returning 426")
                return connection.respond(426, "Upgrade Required")
        except Exception as e:
            logger.error(f"Header parsing error: {e}")
            return connection.respond(426, "Upgrade Required")
    
    # ✅ Handle regular HTTP health checks
    elif request.path in ["/", "/health"]:
        logger.info("✅ HTTP health check")
        return connection.respond(200, "F1 WebSocket Server - Healthy")
    
    # ✅ All other paths get 404
    else:
        return connection.respond(404, "Not Found")

async def main():
    logger.info(f"🚀 F1 Server starting on {HOST}:{PORT}")
    
    try:
        async with websockets.serve(
            bridge.handle_client,
            HOST,
            PORT,
            process_request=process_request,
            ping_interval=None,
            ping_timeout=None
        ):
            logger.info("✅ F1 Server ready!")
            logger.info("🔌 WebSocket endpoint: /ws")
            logger.info("🩺 Health endpoint: /health")
            while True:
                await asyncio.sleep(1)
                
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
