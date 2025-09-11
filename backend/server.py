#!/usr/bin/env python3
"""
F1 WebSocket Server - Railway HTTP + WebSocket Hybrid
"""
import asyncio
import websockets
import json
import sys
import os
import logging
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import socketserver
from urllib.parse import urlparse

# Railway setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PORT = int(os.environ.get("PORT", 8000))
HOST = "0.0.0.0"

# Add project root to path for CLI imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class F1CLIBridge:
    def __init__(self):
        self.connected_clients = set()
        self.is_cli_running = False
        self.message_queue = asyncio.Queue()
        self.broadcaster_task = None
        self.cli_available = self._check_cli_availability()

    def _check_cli_availability(self):
        """Check if CLI module is available"""
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
        
        logger.info("⚠️ No CLI found - running in mock mode")
        return False

    async def start_cli_process(self):
        if self.is_cli_running:
            return True
        
        # Send F1 mock startup message
        await self.message_queue.put({
            'type': 'output',
            'data': '🏎️ F1 Professional Simulator Loading...\n🏁 Championship Mode Ready\n🚧 CLI module not found - using mock mode\nType "help" for commands\n> '
        })
        self.is_cli_running = True
        self.broadcaster_task = asyncio.create_task(self._broadcast_messages())
        return True

    async def _broadcast_messages(self):
        """Broadcast F1 messages to all clients"""
        try:
            while self.is_cli_running or not self.message_queue.empty():
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
            logger.error(f"❌ Broadcast error: {e}")

    async def send_input_to_cli(self, input_data):
        """Handle F1 simulator commands"""
        input_lower = input_data.lower().strip()
        
        if input_lower == 'help':
            response = '''🏎️ F1 Professional Simulator Commands:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏁 race        - Start championship race
🏎️ drivers     - View driver standings  
🏛️ tracks      - List available circuits
📊 status      - Server status
❓ help        - Show this help
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> '''
        elif input_lower == 'status':
            response = f'''✅ F1 Simulator Status:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔌 Connected clients: {len(self.connected_clients)}
🏎️ Simulation: Active  
🌐 Server: Railway Production
⚡ Mode: Championship Ready
🚧 CLI: {'Available' if self.cli_available else 'Mock Mode'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> '''
        elif input_lower in ['race', 'start']:
            response = '''🏁 F1 CHAMPIONSHIP RACE - LIGHTS OUT!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏎️ Loading Monaco Grand Prix...
⚡ Weather: Sunny, 24°C
🏁 Grid positions set
🚦 Formation lap complete
🔥 RACE START! 

Lap 1/78 - Hamilton leads from pole position!
> '''
        elif input_lower == 'drivers':
            response = '''🏎️ F1 Driver Championship Standings:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 🥇 Max Verstappen  - Red Bull    - 476 pts
2. 🥈 Lando Norris    - McLaren     - 374 pts  
3. 🥉 Charles Leclerc - Ferrari     - 356 pts
4. 4️⃣ Oscar Piastri   - McLaren     - 292 pts
5. 5️⃣ Carlos Sainz    - Ferrari     - 244 pts
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> '''
        elif input_lower == 'tracks':
            response = '''🏛️ Available F1 Circuits:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🇲🇨 Monaco Grand Prix    - Street Circuit
🇬🇧 Silverstone         - High Speed  
🇮🇹 Monza               - Temple of Speed
🇧🇪 Spa-Francorchamps   - Legendary
🇯🇵 Suzuka              - Technical Challenge
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> '''
        else:
            response = f'🏎️ F1 Command: "{input_data}"\n⚡ Processing F1 data...\n🔧 Full CLI features {"loading" if self.cli_available else "in mock mode"}...\nType "help" for available commands.\n> '
        
        await self.message_queue.put({
            'type': 'output',
            'data': response
        })

    async def handle_client(self, websocket):
        """Handle F1 WebSocket client connections"""
        self.connected_clients.add(websocket)
        client_addr = websocket.remote_address
        logger.info(f"🔗 F1 Client connected: {client_addr}. Total: {len(self.connected_clients)}")
        
        try:
            # Start F1 CLI for first client
            if len(self.connected_clients) == 1:
                await self.start_cli_process()

            # Send F1 welcome message
            welcome = {
                'type': 'welcome',
                'data': '🏎️ F1 Professional Simulator Connected!\n🏁 Ready for Championship Mode!\n'
            }
            await websocket.send(json.dumps(welcome))

            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get('type') == 'input':
                        await self.send_input_to_cli(data.get('data', ''))
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Invalid JSON from {client_addr}")
                except Exception as e:
                    logger.error(f"⚠️ Message error from {client_addr}: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 F1 Client {client_addr} disconnected")
        except Exception as e:
            logger.error(f"❌ F1 Client error: {e}")
        finally:
            self.connected_clients.discard(websocket)
            logger.info(f"🧹 F1 Client cleaned up. Remaining: {len(self.connected_clients)}")
            
            # Stop F1 CLI when no clients
            if not self.connected_clients:
                self.is_cli_running = False
                if self.broadcaster_task:
                    self.broadcaster_task.cancel()

# Global F1 bridge instance
bridge = F1CLIBridge()

# ✅ HTTP Handler for Railway Health Checks
class RailwayHealthHandler(BaseHTTPRequestHandler):
    """Handle Railway HTTP health checks"""
    
    def do_GET(self):
        logger.info(f"🩺 HTTP health check: {self.path}")
        
        if self.path in ['/', '/health', '/healthz']:
            # Return successful health check
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Content-Length', '27')
            self.end_headers()
            self.wfile.write(b'F1 WebSocket Server - Healthy')
            logger.info("✅ Health check successful")
        else:
            # Return 404 for unknown paths
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        # Suppress default HTTP server logging
        pass

def start_http_health_server():
    """Start HTTP server for Railway health checks"""
    try:
        httpd = HTTPServer((HOST, PORT), RailwayHealthHandler)
        logger.info(f"🩺 HTTP health server started on {HOST}:{PORT}")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"❌ HTTP health server error: {e}")

async def start_websocket_server():
    """Start WebSocket server on port 8001"""
    ws_port = PORT + 1
    try:
        logger.info(f"🔌 Starting F1 WebSocket server on {HOST}:{ws_port}")
        
        async with websockets.serve(
            bridge.handle_client,
            HOST,
            ws_port,
            ping_interval=None,
            ping_timeout=None,
            compression=None
        ):
            logger.info(f"✅ F1 WebSocket server ready on {HOST}:{ws_port}")
            
            # Keep running
            while True:
                await asyncio.sleep(1)
                
    except Exception as e:
        logger.error(f"❌ WebSocket server error: {e}")
        raise

async def main():
    """Main F1 server function - Hybrid HTTP + WebSocket"""
    try:
        logger.info(f"🚀 F1 Hybrid Server starting...")
        logger.info(f"🔧 Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}")
        logger.info(f"🔧 Railway PORT: {PORT}")
        
        # Start HTTP server in background thread for health checks
        http_thread = threading.Thread(target=start_http_health_server, daemon=True)
        http_thread.start()
        logger.info("🩺 HTTP health server started")
        
        # Start WebSocket server on port 8001
        await start_websocket_server()
        
    except Exception as e:
        logger.error(f"❌ Fatal F1 server error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        # Run F1 hybrid server
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("👋 F1 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Critical F1 error: {e}")
        sys.exit(1)
