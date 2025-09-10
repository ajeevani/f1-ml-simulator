#!/usr/bin/env python3
"""
F1 WebSocket Server - Fixed for websockets 15.0.1
"""
import asyncio
import websockets
import subprocess
import json
import sys
import os
import http
from pathlib import Path
from http import HTTPStatus

# ✅ CRITICAL: Use Railway's assigned port
PORT = int(os.environ.get("PORT", 8765))  # Railway sets PORT environment variable
HOST = "0.0.0.0"  # Must bind to 0.0.0.0 for Railway

print(f"🚀 Server starting on {HOST}:{PORT}")
print(f"📡 WebSocket URL will be: wss://f1-ml-simulator-production.up.railway.app")

async def process_request(path, request):
    """Handle HTTP requests and CORS for WebSocket connections"""
    
    headers = request.headers
    origin = headers.get("origin", "")
    
    # ✅ Allow connections from your Vercel frontend
    allowed_origins = [
        "https://f1-ml-simulator.vercel.app",  # Replace with YOUR Vercel domain
        "http://localhost:5173",             # Local development
        "http://localhost:3000",             # Alternative local port
    ]
    
    upgrade = headers.get("upgrade", "").lower()
    connection = headers.get("connection", "").lower()
    
    # Handle WebSocket upgrade requests
    if upgrade == "websocket" and "upgrade" in connection:
        # ✅ Validate origin for security
        if origin in allowed_origins:
            print(f"✅ Allowing WebSocket connection from: {origin}")
            return None  # Allow the connection
        else:
            print(f"❌ Blocking WebSocket connection from unauthorized origin: {origin}")
            return (
                HTTPStatus.FORBIDDEN,
                [("Content-Type", "text/plain")],
                b"Origin not allowed"
            )
    
    # Handle HTTP requests (health checks, browser visits)
    if path == "/" or path == "/health":
        return (
            HTTPStatus.OK,
            [
                ("Content-Type", "text/html"),
                ("Access-Control-Allow-Origin", "*"),
                ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
                ("Access-Control-Allow-Headers", "Content-Type"),
            ],
            f"""<!DOCTYPE html>
<html>
<head><title>F1 WebSocket Server</title></head>
<body>
    <h1>🏎️ F1 Professional WebSocket Server</h1>
    <p>✅ Server is running on Railway</p>
    <p>🔌 WebSocket URL: wss://this-domain</p>
    <p>📡 Connect from your React app</p>
    <p>🩺 Health check: OK</p>
</body>
</html>""".encode('utf-8')
        )
    
    return (
        HTTPStatus.NOT_FOUND,
        [("Content-Type", "text/plain")],
        b"Not Found"
    )

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
            env['PYTHONLEGACYWINDOWSSTDIO'] = '0'
            
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
        
        # Cancel tasks
        if self.output_reader_task and not self.output_reader_task.done():
            self.output_reader_task.cancel()
            try:
                await self.output_reader_task
            except asyncio.CancelledError:
                pass

        if self.broadcaster_task and not self.broadcaster_task.done():
            self.broadcaster_task.cancel()
            try:
                await self.broadcaster_task
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
            except asyncio.TimeoutError:
                print("⚠️ Force killing CLI process")
                self.cli_process.kill()
                await self.cli_process.wait()
            except Exception as e:
                print(f"⚠️ Error during CLI termination: {e}")
            
            self.cli_process = None
        
        print("✅ CLI process stopped cleanly")

    async def handle_client(self, websocket, path=None):
        """Handle WebSocket client connection"""
        self.connected_clients.add(websocket)
        client_addr = websocket.remote_address
        print(f"🔗 Client connected from {client_addr} to {path or '/'}. Total: {len(self.connected_clients)}")
        
        try:
            # Start CLI for first client
            if len(self.connected_clients) == 1:
                await self.start_cli_process()

            # Send welcome message
            welcome = {
                'type': 'welcome',
                'data': '🏎️ Connected to F1 WebSocket Server!\n'
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
                    print(f"⚠️ Message handling error: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"🔌 Client {client_addr} disconnected normally")
        except Exception as e:
            print(f"❌ Client error: {e}")
        finally:
            self.connected_clients.discard(websocket)
            print(f"🔌 Client {client_addr} cleaned up. Remaining: {len(self.connected_clients)}")
            
            # Stop CLI when no clients
            if not self.connected_clients:
                await self.stop_cli_process()

# ✅ FIXED: Correct process_request for websockets 15.0.1
def health_check(connection, request):
    """Handle HTTP health check requests"""
    print(f"🩺 Health check: {request.path}")
    
    if request.path in ["/", "/health", "/healthz"]:
        return connection.respond(
            http.HTTPStatus.OK, 
            "🏎️ F1 WebSocket Server - OK\n"
        )
    
    # Return 404 for other paths
    return connection.respond(
        http.HTTPStatus.NOT_FOUND,
        "404 Not Found\n"
    )

async def main():
    """Main server function"""
    bridge = F1CLIBridge()
    
    print("🔧 Environment PORT:", os.environ.get('PORT', 'Not set'))
    print("🔧 Using PORT:", PORT)
    print("🔧 Using HOST:", HOST)
    print()
    print("🚀 F1 Professional WebSocket Bridge Server")
    print(f"📡 WebSocket: {HOST}:{PORT}")
    print(f"🩺 Health Check: http://{HOST}:{PORT}/health")
    print("=" * 56)
    
    try:
        # Create the websocket server with correct parameters for 15.0.1
        async with websockets.serve(
            bridge.handle_client,
            HOST,
            PORT,
            process_request=health_check,
            # Railway compatibility settings
            ping_interval=20,
            ping_timeout=10,
            close_timeout=10
        ) as server:
            print("✅ WebSocket server ready!")
            print("🩺 HTTP health checks enabled")
            print("🌐 Waiting for connections...")
            
            # Keep server running
            await server.wait_closed()
            
    except Exception as e:
        print(f"❌ Server startup error: {e}")
        raise
    finally:
        await bridge.stop_cli_process()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)
