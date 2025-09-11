#!/usr/bin/env python3
"""
F1 WebSocket Server - Railway Fixed Version
"""
import asyncio
import websockets
import json
import sys
import os
import logging
from pathlib import Path

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
        
        if not self.cli_available:
            # Send F1 mock startup message
            await self.message_queue.put({
                'type': 'output',
                'data': '🏎️ F1 Professional Simulator Loading...\n🏁 Championship Mode Ready\n🚧 CLI module not found - using mock mode\nType "help" for commands\n> '
            })
            self.is_cli_running = True
            self.broadcaster_task = asyncio.create_task(self._broadcast_messages())
            return True

        try:
            logger.info("🏎️ Starting F1 CLI process...")
            
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
            logger.info("✅ F1 CLI process started")
            
            # Start background tasks
            self.output_reader_task = asyncio.create_task(self._read_cli_output())
            self.broadcaster_task = asyncio.create_task(self._broadcast_messages())
            
            return True
        except Exception as e:
            logger.error(f"❌ CLI start error: {e}")
            # Fall back to mock mode
            await self.message_queue.put({
                'type': 'output', 
                'data': f'⚠️ CLI unavailable: {str(e)}\n🌐 F1 Server ready in mock mode\nType "help" for commands\n> '
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
        if hasattr(self, 'cli_process') and self.cli_process and self.cli_process.stdin and self.is_cli_running:
            try:
                self.cli_process.stdin.write(f"{input_data}\n".encode('utf-8'))
                await self.cli_process.stdin.drain()
                return
            except Exception as e:
                logger.error(f"❌ CLI input error: {e}")

        # Mock F1 responses when CLI isn't available
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

    async def stop_cli_process(self):
        """Clean shutdown of F1 simulator"""
        logger.info("🛑 Stopping F1 CLI process...")
        self.is_cli_running = False
        
        # Cancel tasks
        for task_attr in ['output_reader_task', 'broadcaster_task']:
            if hasattr(self, task_attr):
                task = getattr(self, task_attr)
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

        # Terminate CLI process
        if hasattr(self, 'cli_process') and self.cli_process:
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
                    logger.warning(f"⚠️ Invalid JSON from {client_addr}: {message}")
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
                await self.stop_cli_process()

# Global F1 bridge instance
bridge = F1CLIBridge()

# ✅ RAILWAY WEBSOCKET COMPATIBILITY FIX
async def websocket_handler(websocket, path):
    """WebSocket handler that works with Railway"""
    logger.info(f"🔌 WebSocket connection attempt to: {path}")
    await bridge.handle_client(websocket)

async def main():
    """Main F1 server function - Railway compatible"""
    try:
        logger.info(f"🚀 F1 Server starting on {HOST}:{PORT}")
        logger.info(f"🔧 Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}")
        logger.info(f"🔧 Railway PORT: {PORT}")
        
        # ✅ RAILWAY SOLUTION: Use websockets.serve without process_request
        # This avoids the "connection rejected (200 OK)" issue
        async with websockets.serve(
            websocket_handler,
            HOST,
            PORT,
            # Railway-optimized settings - no process_request to avoid conflicts
            ping_interval=None,
            ping_timeout=None,
            compression=None,
            max_size=2**20,
            max_queue=32
        ):
            logger.info("✅ F1 WebSocket Server started successfully!")
            logger.info(f"🌍 Railway URL: https://{os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'localhost:8000')}")
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
