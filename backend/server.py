#!/usr/bin/env python3
"""
F1 WebSocket Server - Render/Aiohttp/CLI Bridge - FIXED
"""
import asyncio
import json
import sys
import os
import logging
from pathlib import Path
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PORT = int(os.environ.get("PORT", 8000))
HOST = "0.0.0.0"

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

CLI_PATHS = [
    "./cli/main.py",
    "../cli/main.py",
    "/app/cli/main.py",
    str(project_root / "cli" / "main.py")
]

@web.middleware
async def cors_middleware(request, handler):
    resp = await handler(request)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,POST'
    return resp

async def healthcheck(request):
    return web.Response(text="F1 Simulator OK\n", content_type="text/plain")

async def notfound(request):
    return web.Response(text="Not Found\n", status=404, content_type="text/plain")

async def websocket_handler(request):
    logger.info(f"WebSocket upgrade requested from {request.remote}. Headers: {dict(request.headers)}")
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    logger.info(f"WebSocket connection established with {request.remote}")

    # Find CLI file
    cli_path = None
    for path in CLI_PATHS:
        if os.path.exists(path):
            cli_path = path
            logger.info(f"✅ Found CLI at: {path}")
            break

    if cli_path is None:
        # Mock mode if CLI not found
        await ws.send_json({
            'type': 'output',
            'data': '🏎️ F1 Professional Simulator Loading...\n🏁 Championship Mode Ready\n🚧 CLI module not found - using mock mode\nType "help" for commands\n> '
        })
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                input_data = msg.data.strip().lower()
                if input_data == "help":
                    await ws.send_json({'type': 'output', 'data': '🏎️ F1 Professional Simulator Commands:\n- race\n- drivers\n- tracks\n- status\n- help\n> '})
                elif input_data == "drivers":
                    await ws.send_json({'type': 'output', 'data': '🏎️ F1 Driver Standings:\n1. Verstappen 2. Norris 3. Leclerc 4. Piastri 5. Sainz\n> '})
                elif input_data == "tracks":
                    await ws.send_json({'type': 'output', 'data': '🏛️ Available F1 Circuits:\nMonaco, Silverstone, Monza, Spa, Suzuka\n> '})
                elif input_data == "race":
                    await ws.send_json({'type': 'output', 'data': '🏁 Starting F1 Championship Race!\nLap 1: Hamilton leads...\n> '})
                elif input_data == "status":
                    await ws.send_json({'type': 'output', 'data': '✅ F1 Simulator Status: Championship Ready\n> '})
                else:
                    await ws.send_json({'type': 'output', 'data': f'🏎️ Command "{input_data}" not recognized.\nType "help" for commands.\n> '})
        await ws.close()
        return ws

    # Start CLI process (true bridge mode)
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUNBUFFERED'] = '1'

    cli_proc = await asyncio.create_subprocess_exec(
        sys.executable, "-u", cli_path,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=str(project_root),
        env=env
    )

    # Read CLI output and send to frontend in real-time
    async def read_cli_output():
        try:
            while True:
                line = await cli_proc.stdout.readline()
                if not line:
                    break
                output = line.decode('utf-8', errors='replace')
                if output.strip():
                    await ws.send_json({'type': 'output', 'data': output})
        except Exception as e:
            logger.error(f"❌ CLI output error: {e}")

    # Listen for frontend input and send to CLI stdin
    async def read_ws_input():
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = msg.data
                    # Accept both raw string and JSON
                    try:
                        parsed = json.loads(data)
                        input_data = parsed.get("data", "")
                    except Exception:
                        input_data = data
                    if cli_proc.stdin:
                        cli_proc.stdin.write(f"{input_data}\n".encode('utf-8'))
                        await cli_proc.stdin.drain()
                except Exception as e:
                    logger.error(f"❌ Error sending input to CLI: {e}")

    # Run both tasks concurrently
    tasks = [
        asyncio.create_task(read_cli_output()),
        asyncio.create_task(read_ws_input())
    ]

    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    # Clean up: close CLI process and WebSocket
    for task in pending:
        task.cancel()
    try:
        if cli_proc.stdin:
            cli_proc.stdin.close()
            await cli_proc.stdin.wait_closed()
        cli_proc.terminate()
        await asyncio.wait_for(cli_proc.wait(), timeout=3)
    except Exception:
        try:
            cli_proc.kill()
            await asyncio.wait_for(cli_proc.wait(), timeout=3)
        except Exception:
            pass
    await ws.close()
    logger.info("✅ F1 CLI bridge cleaned up and WebSocket closed")
    return ws

def create_app():
    app = web.Application(middlewares=[cors_middleware])
    app.router.add_get('/ws', websocket_handler)
    app.router.add_post('/ws', notfound)
    app.router.add_get('/health', healthcheck)
    app.router.add_get('/', healthcheck)
    app.router.add_route('*', '/{tail:.*}', notfound)
    return app

if __name__ == "__main__":
    try:
        app = create_app()
        web.run_app(app, host=HOST, port=PORT)
    except KeyboardInterrupt:
        logger.info("👋 F1 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Critical F1 error: {e}")
        sys.exit(1)