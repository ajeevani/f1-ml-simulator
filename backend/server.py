#!/usr/bin/env python3
"""
F1 WebSocket Server - Railway Health Check Fixed
"""

import asyncio
import websockets
import subprocess
import json
import sys
import os
from pathlib import Path
from http import HTTPStatus
import traceback

# Railway configuration
PORT = int(os.environ.get("PORT", 8000))
HOST = "0.0.0.0"

print(f"🚀 Starting F1 WebSocket Server on {HOST}:{PORT}")

# Add project root to path
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
        """Start the F1 CLI process"""
        if self.is_cli_running:
            return True
            
        try:
            print("🏎️ Starting F1 CLI process...")
            
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            self.cli_process = await asyncio.create_subprocess_exec(
                sys.executable, "-u", "cli/main.py",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=project_root,
                env=env
            )
            
            self.is_cli_running = True
            print("✅ F1 CLI process started")
            
            # Start background tasks
            self.output_reader_task = asyncio.create_task(self._read_cli_output())
            self.broadcaster_task = asyncio.create_task(self._broadcast_messages())
            
            return True
            
        except Exception as e:
            print(f"❌ Error starting CLI: {e}")
            self.is_cli_running = False
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
                
        except asyncio.CancelledError:
            print("📤 Output reader cancelled")
        except Exception as e:
            print(f"❌ Error reading CLI output: {e}")
        finally:
            self.is_cli_running = False

    async def _broadcast_messages(self):
        """Broadcast queued messages to all clients"""
        try:
            while self.is_cli_running:
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
                
        except asyncio.CancelledError:
            print("📡 Broadcaster cancelled")
        except Exception as e:
            print(f"❌ Error broadcasting: {e}")

    async def send_input_to_cli(self, input_data):
        """Send user input to CLI process"""
        if self.cli_process and self.cli_process.stdin and self.is_cli_running:
            try:
                self.cli_process.stdin.write(f"{input_data}\n".encode('utf-8'))
                await self.cli_process.stdin.drain()
            except Exception as e:
                print(f"❌ Error sending input: {e}")

    async def stop_cli_process(self):
        """Clean shutdown"""
        print("🛑 Stopping CLI process...")
        self.is_cli_running = False
        
        # Cancel tasks and cleanup (same as before)
        if self.output_reader_task and not self.output_reader_task.done():
            self.output_reader_task.cancel()
        if self.broadcaster_task and not self.broadcaster_task.done():
            self.broadcaster_task.cancel()
        
        if self.cli_process:
            try:
                if self.cli_process.stdin:
                    self.cli_process.stdin.close()
                self.cli_process.terminate()
                await asyncio.wait_for(self.cli_process.wait(), timeout=3.0)
            except Exception:
                pass
            self.cli_process = None

    async def handle_client(self, websocket, path):
        """Handle WebSocket client connection"""
        self.connected_clients.add(websocket)
        client_addr = websocket.remote_address
        print(f"🔗 Client connected from {client_addr}. Total: {len(self.connected_clients)}")
        
        try:
            # Start CLI for first client
            if len(self.connected_clients) == 1:
                await self.start_cli_process()
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get('type') == 'input':
                        await self.send_input_to_cli(data.get('data', ''))
                except json.JSONDecodeError:
                    print(f"⚠️ Invalid JSON: {message}")
                
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            print(f"❌ Client error: {e}")
        finally:
            self.connected_clients.discard(websocket)
            print(f"🔌 Client disconnected. Remaining: {len(self.connected_clients)}")
            
            # Stop CLI when no clients
            if not self.connected_clients:
                await self.stop_cli_process()

def health_check(connection, request):
    """Handle HTTP health check requests for Railway"""
    print(f"🩺 Health check request: {request.path}")
    
    if request.path == "/" or request.path == "/health":
        return connection.respond(
            HTTPStatus.OK,
            "F1 WebSocket Server is healthy\n"
        )
    
    return None

async def main():
    """Main server function with enhanced error handling"""
    try:
        bridge = F1CLIBridge()
        
        print(f"🚀 F1 Professional WebSocket Bridge Server")
        print(f"📡 Binding to: {HOST}:{PORT}")
        print(f"🩺 Health check: /health")
        print("="*60)
        
        # ✅ Test port binding first
        import socket
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            test_socket.bind((HOST, PORT))
            test_socket.close()
            print(f"✅ Port {PORT} is available for binding")
        except Exception as e:
            print(f"❌ Cannot bind to port {PORT}: {e}")
            sys.exit(1)
        
        # ✅ Start WebSocket server with proper error handling
        server = await websockets.serve(
            bridge.handle_client,
            HOST,
            PORT,
            process_request=health_check,
            ping_interval=20,
            ping_timeout=10
        )
        
        print("✅ WebSocket server started successfully!")
        print("🩺 HTTP health checks enabled")
        print("🔗 Waiting for connections...")
        print("🌍 Server accessible at:", f"https://{os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'localhost:' + str(PORT))}")
        
        # ✅ Keep server running with proper cleanup
        try:
            await server.wait_closed()
        except KeyboardInterrupt:
            print("\n🛑 Received interrupt signal")
        finally:
            await bridge.stop_cli_process()
            server.close()
            await server.wait_closed()
            
    except Exception as e:
        print(f"❌ CRITICAL SERVER ERROR: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        # ✅ Add platform-specific event loop handling
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        print("🔄 Starting asyncio event loop...")
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n🏁 Server stopped by user")
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        print(f"❌ Full traceback: {traceback.format_exc()}")
        sys.exit(1)