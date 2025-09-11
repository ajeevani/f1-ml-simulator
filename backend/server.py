#!/usr/bin/env python3
"""
F1 WebSocket Server - Railway Production Ready
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Railway configuration
PORT = int(os.environ.get("PORT", 8000))
HOST = "0.0.0.0"

print(f"🚀 F1 WebSocket Server Starting...")
print(f"🔧 PORT: {PORT}")
print(f"🔧 HOST: {HOST}")
print(f"🔧 Python: {sys.version}")
print(f"🔧 CWD: {os.getcwd()}")
print(f"🔧 Railway ENV: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}")

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
        """Check if CLI is available and log the file structure"""
        print("🔍 Checking CLI availability...")
        
        # List current directory contents
        try:
            files = os.listdir('.')
            print(f"📁 Current directory files: {files}")
        except Exception as e:
            print(f"❌ Cannot list current directory: {e}")
        
        # Check for CLI in various locations
        possible_paths = [
            "./cli/main.py",
            "../cli/main.py", 
            "./main.py",
            "/app/cli/main.py"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"✅ Found CLI at: {path}")
                self.cli_path = path
                return True
        
        print("⚠️ No CLI found - running in WebSocket-only mode")
        return False

    async def start_cli_process(self):
        """Start CLI process if available"""
        if self.is_cli_running:
            return True
            
        if not self.cli_available:
            print("⚠️ CLI not available - sending mock response")
            await self.message_queue.put({
                'type': 'output',
                'data': '🏎️ F1 WebSocket Server Connected!\n🚧 CLI module loading...\n> '
            })
            return True

        try:
            print("🏎️ Starting CLI process...")
            
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUNBUFFERED'] = '1'
            
            self.cli_process = await asyncio.create_subprocess_exec(
                sys.executable, "-u", self.cli_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env
            )
            
            self.is_cli_running = True
            print("✅ CLI process started")
            
            # Start background tasks
            self.output_reader_task = asyncio.create_task(self._read_cli_output())
            self.broadcaster_task = asyncio.create_task(self._broadcast_messages())
            
            return True
        except Exception as e:
            print(f"❌ CLI start error: {e}")
            # Fall back to mock mode
            await self.message_queue.put({
                'type': 'output', 
                'data': f'⚠️ CLI unavailable: {str(e)}\n🌐 WebSocket server ready\n> '
            })
            return False

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
            print(f"❌ CLI output error: {e}")
        finally:
            self.is_cli_running = False

    async def _broadcast_messages(self):
        """Broadcast queued messages to all clients"""
        try:
            while True:
                try:
                    message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    if not self.is_cli_running and not self.connected_clients:
                        break
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
            print(f"❌ Broadcast error: {e}")

    async def send_input_to_cli(self, input_data):
        """Send user input to CLI process or handle mock responses"""
        if self.cli_process and self.cli_process.stdin and self.is_cli_running:
            try:
                self.cli_process.stdin.write(f"{input_data}\n".encode('utf-8'))
                await self.cli_process.stdin.drain()
            except Exception as e:
                print(f"❌ Input send error: {e}")
        else:
            # Mock response when CLI isn't available
            mock_response = f"Echo: {input_data}\n🚧 Full CLI features loading...\n> "
            await self.message_queue.put({
                'type': 'output',
                'data': mock_response
            })

    async def stop_cli_process(self):
        """Clean shutdown"""
        print("🛑 Stopping CLI process...")
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
        
        print("✅ Cleanup complete")

    async def handle_client(self, websocket, path=None):
        """Handle WebSocket client connections"""
        self.connected_clients.add(websocket)
        client_addr = websocket.remote_address
        print(f"🔗 Client connected: {client_addr}. Total: {len(self.connected_clients)}")
        
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
                    print(f"⚠️ Invalid JSON: {message}")
                except Exception as e:
                    print(f"⚠️ Message error: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"🔌 Client {client_addr} disconnected")
        except Exception as e:
            print(f"❌ Client error: {e}")
        finally:
            self.connected_clients.discard(websocket)
            print(f"🔌 Client cleaned up. Remaining: {len(self.connected_clients)}")
            
            # Stop CLI when no clients
            if not self.connected_clients:
                await self.stop_cli_process()

def health_check(connection, request):
    """Handle HTTP health checks"""
    print(f"🩺 Health check: {request.path}")
    
    if request.path in ["/", "/health", "/healthz"]:
        return connection.respond(
            HTTPStatus.OK,
            "F1 WebSocket Server - Healthy ✅\n"
        )
    
    return None

class F1Server:
    def __init__(self):
        self.connected_clients = set()
        self.server = None
        self.running = True

    async def handle_websocket(self, websocket, path):
        """Handle WebSocket connections with error recovery"""
        client_addr = websocket.remote_address
        self.connected_clients.add(websocket)
        logger.info(f"🔗 WebSocket connected: {client_addr}. Total: {len(self.connected_clients)}")
        
        try:
            # Send welcome message
            await websocket.send(json.dumps({
                'type': 'output',
                'data': '🏎️ F1 WebSocket Server Connected!\nType "help" for commands.\n> '
            }))

            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get('type') == 'input':
                        user_input = data.get('data', '').strip()
                        
                        # Simple command handling
                        if user_input.lower() == 'help':
                            response = 'Available commands:\n- help: Show this help\n- status: Server status\n- echo <text>: Echo back text\n> '
                        elif user_input.lower() == 'status':
                            response = f'✅ Server running\n📊 Connected clients: {len(self.connected_clients)}\n> '
                        elif user_input.lower().startswith('echo '):
                            echo_text = user_input[5:]
                            response = f'Echo: {echo_text}\n> '
                        else:
                            response = f'You entered: {user_input}\nType "help" for commands.\n> '
                        
                        await websocket.send(json.dumps({
                            'type': 'output',
                            'data': response
                        }))
                        
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'type': 'output',
                        'data': 'Invalid JSON format\n> '
                    }))
                except Exception as e:
                    logger.error(f"Message handling error: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 WebSocket disconnected: {client_addr}")
        except Exception as e:
            logger.error(f"❌ WebSocket error: {e}")
        finally:
            self.connected_clients.discard(websocket)
            logger.info(f"🧹 Cleaned up client. Remaining: {len(self.connected_clients)}")

    def health_check(self, connection, request):
        """Handle HTTP health checks - simplified and robust"""
        logger.info(f"🩺 Health check: {request.path}")
        
        try:
            if request.path in ["/", "/health", "/healthz"]:
                # Return simple text response
                return connection.respond(
                    200,
                    "F1 WebSocket Server - Healthy\n"
                )
            else:
                return connection.respond(
                    404,
                    "Not Found\n"
                )
        except Exception as e:
            logger.error(f"Health check error: {e}")
            # Fallback response
            return connection.respond(200, "OK\n")

    async def start_server(self):
        """Start the WebSocket server with proper error handling"""
        try:
            logger.info("🚀 Starting WebSocket server...")
            
            # Start server with basic configuration
            self.server = await websockets.serve(
                self.handle_websocket,
                HOST,
                PORT,
                process_request=self.health_check,
                ping_interval=None,  # Disable ping for Railway compatibility
                ping_timeout=None,
                compression=None
            )
            
            logger.info("✅ Server started successfully!")
            logger.info(f"🌍 Listening on {HOST}:{PORT}")
            logger.info("🩺 Health endpoint: /health")
            
            return self.server
            
        except Exception as e:
            logger.error(f"❌ Server startup failed: {e}")
            raise

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down server...")
        self.running = False
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        logger.info("✅ Server stopped")

# Global server instance
server_instance = None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"📡 Received signal {signum}")
    if server_instance:
        asyncio.create_task(server_instance.shutdown())

async def main():
    """Main server function with comprehensive error handling"""
    global server_instance
    
    try:
        # Setup signal handlers
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Create and start server
        server_instance = F1Server()
        server = await server_instance.start_server()
        
        logger.info("🎯 Server ready for connections")
        
        # Keep server running
        try:
            while server_instance.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("📡 Server loop cancelled")
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if server_instance:
            await server_instance.shutdown()

if __name__ == "__main__":
    try:
        # Ensure clean event loop
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Run server
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        sys.exit(1)