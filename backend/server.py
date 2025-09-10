#!/usr/bin/env python3
"""
F1 WebSocket Server - Fixed Method Binding
"""

import asyncio
import websockets
import subprocess
import json
import sys
import os
from pathlib import Path
from http import HTTPStatus

# Production configuration
PORT = int(os.environ.get("PORT", 8765))
HOST = "0.0.0.0"

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
        self.connected_clients.add(websocket)
        client_addr = websocket.remote_address
        print(f"🔗 Client connected from {client_addr} to {path or 'unknown'}. Total: {len(self.connected_clients)}")
        
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
            print(f"🔌 Client {client_addr} disconnected. Remaining: {len(self.connected_clients)}")
            
            # Stop CLI when no clients
            if not self.connected_clients:
                await self.stop_cli_process()


# ✅ CORRECT: Handle Request object for websockets v15.0.1
async def process_request(path, request):
    """Handle HTTP requests from health checkers"""
    
    # Access headers through request.headers
    headers = request.headers
    
    upgrade = headers.get("upgrade", "").lower()
    connection = headers.get("connection", "").lower()
    
    # If it's a proper WebSocket upgrade request, let it through
    if upgrade == "websocket" and "upgrade" in connection:
        return None  # Let websockets library handle it
    
    # Handle HTTP requests (health checks, browser access, etc.)
    if path == "/" or path == "/health":
        return (
            HTTPStatus.OK,
            [
                ("Content-Type", "text/html"),
                ("Access-Control-Allow-Origin", "*")
            ],
            b"<html><body><h1>F1 WebSocket Bridge Server is running!</h1></body></html>"
        )
    
    # For all other paths
    return (
        HTTPStatus.NOT_FOUND,
        [("Content-Type", "text/plain")],
        b"404 Not Found"
    )

async def main():
    """Main server function"""
    bridge = F1CLIBridge()
    
    print("🚀 F1 Professional WebSocket Bridge Server")
    print(f"📡 WebSocket: {HOST}:{PORT}")
    print(f"🩺 Health Check: http://{HOST}:{PORT}/")
    print("=" * 56)
    
    # Create the websocket server with proper handler binding
    server = await websockets.serve(
        bridge.handle_client,  # This will work with the updated signature
        HOST,
        PORT,
        process_request=process_request
    )
    
    print("✅ WebSocket server ready!")
    print("🩺 HTTP health checks enabled")
    print("🌐 Waiting for connections...")
    
    try:
        await server.wait_closed()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
    finally:
        await bridge.stop_cli_process()
        server.close()
        await server.wait_closed()
        print("✅ Server shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)
