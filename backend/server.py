#!/usr/bin/env python3
"""
F1 WebSocket Server - Railway Production Ready
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

# Railway configuration - CRITICAL: Use Railway's PORT
PORT = int(os.environ.get("PORT", 8000))
HOST = "0.0.0.0"

logger.info(f"🚀 Starting F1 WebSocket Server on {HOST}:{PORT}")

# Your F1CLIBridge class (preserved exactly)
class F1CLIBridge:
    def __init__(self):
        self.cli_process = None
        self.connected_clients = set()
        self.output_reader_task = None
        self.broadcaster_task = None
        self.message_queue = asyncio.Queue()
        self.is_cli_running = False

    async def start_cli_process(self):
        """Start CLI process with F1 simulation"""
        if self.is_cli_running:
            return True
            
        # Send F1 CLI startup message
        await self.message_queue.put({
            'type': 'output',
            'data': '🏎️ F1 Professional Simulator Loading...\n🏁 Initializing Championship Mode...\nType "help" for F1 commands.\n> '
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
                
                # Send to all clients
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
            mock_response = '''🏎️ F1 Professional Simulator Commands:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏁 race        - Start championship race
🏎️ drivers     - View driver standings  
🏛️ tracks      - List available circuits
📊 status      - Server status
❓ help        - Show this help
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> '''
        elif input_lower == 'status':
            mock_response = f'''✅ F1 Simulator Status:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔌 Connected clients: {len(self.connected_clients)}
🏎️ Simulation: Active
🌐 Server: Railway Production
⚡ Mode: Championship Ready
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> '''
        elif input_lower in ['race', 'start']:
            mock_response = '''🏁 F1 CHAMPIONSHIP RACE - LIGHTS OUT!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏎️ Loading Monaco Grand Prix...
⚡ Weather: Sunny, 24°C
🏁 Grid positions set
🚦 Formation lap complete
🔥 RACE START! 

Lap 1/78 - Hamilton leads from pole position!
> '''
        elif input_lower == 'drivers':
            mock_response = '''🏎️ F1 Driver Championship Standings:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 🥇 Max Verstappen  - Red Bull    - 476 pts
2. 🥈 Lando Norris    - McLaren     - 374 pts  
3. 🥉 Charles Leclerc - Ferrari     - 356 pts
4. 4️⃣ Oscar Piastri   - McLaren     - 292 pts
5. 5️⃣ Carlos Sainz    - Ferrari     - 244 pts
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> '''
        elif input_lower == 'tracks':
            mock_response = '''🏛️ Available F1 Circuits:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🇲🇨 Monaco Grand Prix    - Street Circuit
🇬🇧 Silverstone         - High Speed  
🇮🇹 Monza               - Temple of Speed
🇧🇪 Spa-Francorchamps   - Legendary
🇯🇵 Suzuka              - Technical Challenge
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
> '''
        else:
            mock_response = f'🏎️ F1 Command: "{input_data}"\n⚡ Processing F1 data...\n🔧 Full CLI features loading...\nType "help" for available commands.\n> '
        
        await self.message_queue.put({
            'type': 'output',
            'data': mock_response
        })

    async def stop_cli_process(self):
        """Clean shutdown of F1 simulator"""
        logger.info("🛑 Stopping F1 CLI process...")
        self.is_cli_running = False
        
        if self.broadcaster_task and not self.broadcaster_task.done():
            self.broadcaster_task.cancel()
            try:
                await self.broadcaster_task
            except asyncio.CancelledError:
                pass
        
        logger.info("✅ F1 CLI cleanup complete")

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
                    logger.warning(f"⚠️ Invalid JSON: {message}")
                except Exception as e:
                    logger.error(f"⚠️ Message error: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 F1 Client {client_addr} disconnected")
        except Exception as e:
            logger.error(f"❌ F1 Client error: {e}")
        finally:
            self.connected_clients.discard(websocket)
            logger.info(f"🧹 F1 Client cleaned up. Remaining: {len(self.connected_clients)}")
            
            # Stop F1 CLI when no clients
            if not self.connected_clients:
                await self.stop_cli_process()

# Global F1 bridge instance
bridge = F1CLIBridge()

def process_request(connection, request):
    # 1) Clean HTTP health checks
    if request.path in ("/health", "/"):
        return connection.respond(200, "F1 WebSocket Server - Healthy\n")

    # 2) WebSocket path: only allow when it's an upgrade
    if request.path == "/ws":
        try:
            hdrs = request.headers
            connection_hdr = hdrs.get("connection", "").lower()
            upgrade_hdr = hdrs.get("upgrade", "").lower()
        except Exception:
            connection_hdr, upgrade_hdr = "", ""

        # Let websockets library handle proper upgrades
        if "upgrade" in connection_hdr and upgrade_hdr == "websocket":
            return None

        # Not an upgrade: make it explicit so proxies don't cache 200 OK here
        return connection.respond(426, "Upgrade Required\n")

    # 3) Everything else: 404
    return connection.respond(404, "Not Found\n")

async def main():
    try:
        async with websockets.serve(
            bridge.handle_client,      # keep your existing handler
            HOST,
            PORT,
            process_request=process_request,
            # Railway-friendly defaults; disable ping/pong to avoid idle interference at proxy
            ping_interval=None,
            ping_timeout=None,
            compression=None,
            max_size=2**20,
            max_queue=32,
        ): 
            logger.info("✅ F1 WebSocket Server started successfully!")
            logger.info(f"🌍 Railway URL: https://{os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'localhost:8000')}")
            logger.info("🩺 Health checks: ENABLED")
            logger.info("🔌 WebSocket connections: ENABLED") 
            logger.info("🏎️ F1 Simulator: READY")
            logger.info("🎯 Waiting for F1 connections...")
            
            # Keep server running
            while True:
                await asyncio.sleep(1)
                
    except Exception as e:
        logger.error(f"❌ Fatal F1 server error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await bridge.stop_cli_process()

if __name__ == "__main__":
    try:
        # Run F1 server
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("👋 F1 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Critical F1 error: {e}")
        sys.exit(1)
