from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

import websockets


async def rpc(ws, method: str, params: Dict[str, Any] | None = None, id_: int = 1) -> Dict[str, Any]:
    req = {"jsonrpc": "2.0", "id": id_, "method": method}
    if params:
        req["params"] = params
    await ws.send(json.dumps(req))
    resp = json.loads(await ws.recv())
    return resp


async def main() -> None:
    async with websockets.connect("ws://127.0.0.1:8787") as ws:
        print("Connected")
        print(await rpc(ws, "mcp.getProjects"))
        print(await rpc(ws, "mcp.setBaseDir", {"path": "projects"}, 2))
        print(await rpc(ws, "mcp.createTask", {"project": "demo", "title": "Try MCP"}, 3))
        print(await rpc(ws, "mcp.listTasks", {"project": "demo"}, 4))


if __name__ == "__main__":
    asyncio.run(main())


