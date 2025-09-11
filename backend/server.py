#!/usr/bin/env python3
"""
F1 WebSocket Server - Railway Production Ready with F1CLIBridge
"""
import asyncio
import websockets
import subprocess
import json
import sys
import os
import signal
import logging
from pathlib import Path
from http import HTTPStatus

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway configuration
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
        self.cli_available = self._check_cli_availability()

    def _check_cli_availability(self):
        """Check if CLI is available"""
        possible_paths = [
            "./cli/main.py",
            "../cli/main.py", 
            "/app/cli/main.py",
            str(project_root / "cli" / "main.py")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"✅ Found CLI at: {path}")
                self.cli_path = path
                return True
        
        logger.info("⚠️ No CLI found - running in WebSocket-only mode")
        return False

    async def start_cli_process(self):
        """Start CLI process if available"""
        if self.is_cli_running:
            return True
            
        if not self.cli_available:
            # Send mock CLI startup message
            await self.message_queue.put({
                'type': 'output',
                'data': '🏎️ F1 Professional Simulator Loading...\n🚧 CLI module not found - using mock mode\nType "help" for commands.\n> '
            })
            self.is_cli_running = True
            self.broadcaster_task = asyncio.create_task(self._broadcast_messages())
            return True

        try:
            logger.info("🏎️ Starting CLI process...")
            
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUNBUFFERED'] = '1'
            
            self.cli_process = await asyncio.create_subprocess_exec(
                sys.executable, "-u", self.cli_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(project_root),
                env=env
            )
            
            self.is_cli_running = True
            logger.info("✅ CLI process started")
            
            # Start background tasks
            self.output_reader_task = asyncio.create_task(self._read_cli_output())
            self.broadcaster_task = asyncio.create_task(self._broadcast_messages())
            
            return True
        except Exception as e:
            logger.error(f"❌ CLI start error: {e}")
            # Fall back to mock mode
            await self.message_queue.put({
                'type': 'output', 
                'data': f'⚠️ CLI unavailable: {str(e)}\n🌐 WebSocket server ready in mock mode\nType "help" for commands.\n> '
            })
            self.is_cli_running = True
            self.broadcaster_task = asyncio.create_task(self._broadcast_messages())
            return True

    async def _read_cli_output(self):
        """Read CLI output and queue for broadcasting"""
        try:
            while self.cli_process and self.is_cli_running:
                line_bytes = await self.cli_process.stdout.readline()
                if not line_bytes:
                    break
                    
                output = line_bytes.decode('utf-8', errors='replace')
                await self.message_queue.put({
                    'type': 'output',
                    'data': output
                })
        except Exception as e:
            logger.error(f"❌ CLI output error: {e}")
        finally:
            self.is_cli_running = False

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
        if self.cli_process and self.cli_process.stdin and self.is_cli_running:
            try:
                self.cli_process.stdin.write(f"{input_data}\n".encode('utf-8'))
                await self.cli_process.stdin.drain()
            except Exception as e:
                logger.error(f"❌ Input send error: {e}")
        else:
            # Mock responses when CLI isn't available
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
        
        # Cancel tasks
        for task in [self.output_reader_task, self.broadcaster_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Terminate CLI process
        if self.cli_process:
            try:
                if self.cli_process.stdin:
                    self.cli_process.stdin.close()
                    await self.cli_process.stdin.wait_closed()
                self.cli_process.terminate()
                await asyncio.wait_for(self.cli_process.wait(), timeout=3.0)
            except Exception:
                if self.cli_process:
                    self.cli_process.kill()
            self.cli_process = None
        
        logger.info("✅ CLI cleanup complete")

    async def handle_client(self, websocket, path):
        """Handle WebSocket client connections"""
        self.connected_clients.add(websocket)
        client_addr = websocket.remote_address
        logger.info(f"🔗 Client connected: {client_addr}. Total: {len(self.connected_clients)}")
        
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
            logger.info(f"🔌 Client {client_addr} disconnected")
        except Exception as e:
            logger.error(f"❌ Client error: {e}")
        finally:
            self.connected_clients.discard(websocket)
            logger.info(f"🧹 Client cleaned up. Remaining: {len(self.connected_clients)}")
            
            # Stop CLI when no clients
            if not self.connected_clients:
                await self.stop_cli_process()

def health_check(connection, request):
    """Handle HTTP health checks - properly detect WebSocket upgrades"""
    logger.info(f"🩺 Request to: {request.path}")
    
    # ✅ CRITICAL: Check if this is a WebSocket upgrade request
    try:
        if hasattr(request, 'headers'):
            connection_header = request.headers.get("connection", "").lower()
            upgrade_header = request.headers.get("upgrade", "").lower()
            
            # If it's a WebSocket upgrade request, DON'T handle it here
            if "upgrade" in connection_header and upgrade_header == "websocket":
                logger.info("🔄 WebSocket upgrade detected - passing to websockets library")
                return None  # Let websockets library handle the upgrade
    except Exception as e:
        logger.error(f"Header check error: {e}")
    
    # Handle regular HTTP requests (health checks)
    if request.path in ["/", "/health", "/healthz"]:
        logger.info("✅ HTTP health check - returning 200")
        return connection.respond(200, "F1 WebSocket Server - Healthy")
    else:
        logger.info("❌ HTTP 404 - unknown path")
        return connection.respond(404, "Not Found")


# Global server instance
bridge = None

async def main():
    """Main server function"""
    global bridge
    
    try:
        bridge = F1CLIBridge()
        
        logger.info("🚀 Starting WebSocket server...")
        
        # ✅ Start server with minimal configuration for Railway
        async with websockets.serve(
            bridge.handle_client,
            HOST,
            PORT,
            process_request=health_check,
            # Railway-optimized settings
            ping_interval=None,  # Disable ping
            ping_timeout=None,
            compression=None,
            max_size=2**20,  # 1MB max message
            max_queue=32
        ):
            logger.info("✅ Server started successfully!")
            logger.info(f"🌍 Listening on {HOST}:{PORT}")
            logger.info("🩺 Health endpoint: /health")
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
        if bridge:
            await bridge.stop_cli_process()

if __name__ == "__main__":
    try:
        logger.info(f"🔧 Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}")
        logger.info(f"🔧 Python: {sys.version}")
        
        # Run server
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        sys.exit(1)
