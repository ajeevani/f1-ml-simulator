#!/usr/bin/env python3
"""
F1 WebSocket Server - Single Port Railway Compatible
"""
import asyncio
import websockets
import json
import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway configuration - SINGLE PORT ONLY
PORT = int(os.environ.get("PORT", 8000))
HOST = "0.0.0.0"

logger.info(f"🚀 Starting F1 WebSocket Server on {HOST}:{PORT}")

# Add project root to path for CLI access
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class F1CLIBridge:
    def __init__(self):
        self.cli_process = None
        self.connected_clients = set()
        self.output_reader_task = None
        self.broadcaster_task = None
        self.message_queue = asyncio.Queue()
        self.is_cli_running = False

    async def start_cli_process(self):
        """Start CLI process if available"""
        if self.is_cli_running:
            return True
            
        # Send mock CLI startup message
        await self.message_queue.put({
            'type': 'output',
            'data': '🏎️ F1 Professional Simulator Loading...\n🚧 CLI module not found - using mock mode\nType "help" for commands.\n> '
        })
        self.is_cli_running = True
        self.broadcaster_task = asyncio.create_task(self._broadcast_messages())
        return True

    async def _broadcast_messages(self):
        """Broadcast queued messages to all clients"""
        try:
            while self.is_cli_running or not self.message_queue.empty():
                try:
                    message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                if not self.connected_clients:
                    continue

                json_message = json.dumps(message, ensure_ascii=False)
                
                # Send to all clients
                disconnected = set()
                for client in self.connected_clients.copy():
                    try:
                        await client.send(json_message)
                    except Exception:
                        disconnected.add(client)
                
                # Remove disconnected clients
                self.connected_clients -= disconnected
                
        except Exception as e:
            logger.error(f"❌ Broadcast error: {e}")

    async def send_input_to_cli(self, input_data):
        """Send user input to CLI process or handle mock responses"""
        input_lower = input_data.lower().strip()
        
        if input_lower == 'help':
            mock_response = '''🏎️ F1 Simulator Commands:
- help: Show this help
- status: Server status  
- start: Start F1 simulation
- race: Begin race
- quit: Exit simulator
> '''
        elif input_lower == 'status':
            mock_response = f'✅ F1 Server Running\n📊 Connected clients: {len(self.connected_clients)}\n🚧 CLI: Mock Mode\n> '
        elif input_lower in ['start', 'race']:
            mock_response = '🏁 Starting F1 Professional Championship...\n🏎️ Loading tracks and drivers...\n⚡ Simulation ready!\n> '
        elif input_lower == 'quit':
            mock_response = '👋 Thanks for using F1 Simulator!\n> '
        else:
            mock_response = f'F1 Simulator: {input_data}\n🚧 Full CLI features loading...\nType "help" for commands.\n> '
        
        await self.message_queue.put({
            'type': 'output',
            'data': mock_response
        })

    async def stop_cli_process(self):
        """Clean shutdown"""
        logger.info("🛑 Stopping CLI process...")
        self.is_cli_running = False
        
        if self.broadcaster_task and not self.broadcaster_task.done():
            self.broadcaster_task.cancel()
            try:
                await self.broadcaster_task
            except asyncio.CancelledError:
                pass
        
        logger.info("✅ CLI cleanup complete")

    async def handle_client(self, websocket):
        """Handle WebSocket client connections"""
        self.connected_clients.add(websocket)
        client_addr = websocket.remote_address
        logger.info(f"🔗 WebSocket client connected: {client_addr}. Total: {len(self.connected_clients)}")
        
        try:
            # Start CLI for first client
            if len(self.connected_clients) == 1:
                await self.start_cli_process()

            # Send welcome message
            welcome = {
                'type': 'welcome',
                'data': '🏎️ F1 WebSocket Server Connected!\n'
            }
            await websocket.send(json.dumps(welcome))

            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get('type') == 'input':
                        await self.send_input_to_cli(data.get('data', ''))
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Invalid JSON: {message}")
                except Exception as e:
                    logger.error(f"⚠️ Message error: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 WebSocket client {client_addr} disconnected")
        except Exception as e:
            logger.error(f"❌ WebSocket client error: {e}")
        finally:
            self.connected_clients.discard(websocket)
            logger.info(f"🧹 Client cleaned up. Remaining: {len(self.connected_clients)}")
            
            # Stop CLI when no clients
            if not self.connected_clients:
                await self.stop_cli_process()

# Global bridge instance
bridge = F1CLIBridge()

# ✅ CRITICAL FIX: Proper Railway-compatible process_request
def process_request(connection, request):
    """Handle HTTP health checks while allowing WebSocket upgrades"""
    logger.info(f"🔍 Request: {request.path}")
    
    # ✅ Check if this is a WebSocket upgrade request
    try:
        if hasattr(request, 'headers'):
            connection_header = request.headers.get("connection", "").lower()
            upgrade_header = request.headers.get("upgrade", "").lower()
            
            # If it's a WebSocket upgrade, let websockets library handle it
            if "upgrade" in connection_header and upgrade_header == "websocket":
                logger.info("🔄 WebSocket upgrade - allowing")
                return None  # Critical: Return None to allow WebSocket upgrade
        
        # Handle HTTP health checks for Railway
        if request.path in ["/", "/health", "/healthz"]:
            logger.info("✅ Health check response")
            return connection.respond(200, "F1 WebSocket Server - Healthy")
        else:
            return connection.respond(404, "Not Found")
            
    except Exception as e:
        logger.error(f"❌ Process request error: {e}")
        # Fallback - allow the request to proceed
        return None

async def main():
    """Main server function - SINGLE PORT"""
    try:
        logger.info("🚀 Starting F1 WebSocket Server...")
        logger.info(f"🔧 Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}")
        logger.info(f"🔧 PORT: {PORT}")
        
        # ✅ SINGLE PORT SERVER - Railway compatible
        async with websockets.serve(
            bridge.handle_client,
            HOST,
            PORT,
            process_request=process_request,
            # Railway optimized settings
            ping_interval=None,  # Disable ping for Railway compatibility
            ping_timeout=None,
            compression=None
        ):
            logger.info("✅ F1 WebSocket Server started successfully!")
            logger.info(f"🌍 Listening on {HOST}:{PORT}")
            logger.info("🩺 Health checks enabled")
            logger.info("🔌 WebSocket connections enabled")
            logger.info("🎯 Server ready for connections")
            
            # Keep server running
            while True:
                await asyncio.sleep(1)
                
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await bridge.stop_cli_process()

if __name__ == "__main__":
    try:
        # Run server
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        sys.exit(1)
