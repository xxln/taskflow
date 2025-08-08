from __future__ import annotations

import asyncio
import json
import signal
import uuid
from dataclasses import asdict
from typing import Any, Dict, List, Optional

import websockets
from websockets.server import WebSocketServerProtocol

from .manager import TaskManager, TaskManagerError, ProjectNotFoundError, TaskNotFoundError
from .models import TaskStatus


# Minimal JSON-RPC 2.0 helpers
def rpc_result(id_: Any, result: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def rpc_error(id_: Any, code: int, message: str, data: Optional[Any] = None) -> Dict[str, Any]:
    err: Dict[str, Any] = {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}
    if data is not None:
        err["error"]["data"] = data
    return err


def rpc_notify(method: str, params: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "method": method, "params": params}


class MCPServer:
    """Minimal MCP-like server over WebSocket using JSON-RPC 2.0.

    Methods provided (MVP):
      - mcp.getProjects -> [projectName]
      - mcp.setBaseDir { path }
      - mcp.listTasks { project, filters? } -> [Task]
      - mcp.createTask { project, title, description?, notes? } -> Task
      - mcp.updateTask { project, task_id, fields } -> Task
      - mcp.deleteTask { project, task_id } -> { ok: true }
      - mcp.addNote { project, task_id, note }
      - mcp.startIteration { project, task_id }
      - mcp.completeIteration { project, task_id }
      - mcp.projectStatus { project }

    Notifications:
      - mcp.taskUpdated { project, task_id }
      - mcp.projectUpdated { project }
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 8787, base_dir: str = "projects") -> None:
        self.host = host
        self.port = port
        self.manager = TaskManager(base_dir=base_dir)
        self.connections: List[WebSocketServerProtocol] = []

    async def broadcast(self, message: Dict[str, Any]) -> None:
        if not self.connections:
            return
        dead: List[WebSocketServerProtocol] = []
        for ws in self.connections:
            try:
                await ws.send(json.dumps(message))
            except Exception:
                dead.append(ws)
        for ws in dead:
            try:
                self.connections.remove(ws)
            except ValueError:
                pass

    async def handle(self, ws: WebSocketServerProtocol) -> None:
        self.connections.append(ws)
        try:
            async for raw in ws:
                try:
                    req = json.loads(raw)
                    method = req.get("method")
                    id_ = req.get("id")
                    params = req.get("params") or {}
                except Exception:
                    await ws.send(json.dumps(rpc_error(None, -32700, "Parse error")))
                    continue

                try:
                    if method == "mcp.getProjects":
                        result = self.manager.list_projects()
                        await ws.send(json.dumps(rpc_result(id_, result)))

                    elif method == "mcp.setBaseDir":
                        path = params.get("path")
                        if not path:
                            await ws.send(json.dumps(rpc_error(id_, -32602, "Missing 'path'")))
                            continue
                        # Re-initialize manager with new base dir
                        self.manager = TaskManager(base_dir=path)
                        await ws.send(json.dumps(rpc_result(id_, {"base_dir": path})))
                        await self.broadcast(rpc_notify("mcp.projectUpdated", {"project": "*"}))

                    elif method == "mcp.listTasks":
                        project = params.get("project")
                        if not project:
                            await ws.send(json.dumps(rpc_error(id_, -32602, "Missing 'project'")))
                            continue
                        filters = params.get("filters") or {}
                        ids = self.manager.list_tasks(project)
                        tasks = []
                        for tid in ids:
                            try:
                                task = self.manager.get_task(project, tid)
                                if filters:
                                    status = filters.get("status")
                                    if status and task.status.value != status:
                                        continue
                                tasks.append(task.to_dict())
                            except TaskNotFoundError:
                                continue
                        await ws.send(json.dumps(rpc_result(id_, tasks)))

                    elif method == "mcp.createTask":
                        project = params.get("project")
                        title = params.get("title")
                        if not project or not title:
                            await ws.send(json.dumps(rpc_error(id_, -32602, "Missing 'project' or 'title'")))
                            continue
                        description = params.get("description", "")
                        notes = params.get("notes", "")
                        task = self.manager.create_task(project, title, description, notes)
                        await ws.send(json.dumps(rpc_result(id_, task.to_dict())))
                        await self.broadcast(rpc_notify("mcp.taskUpdated", {"project": project, "task_id": task.id}))

                    elif method == "mcp.updateTask":
                        project = params.get("project")
                        task_id = params.get("task_id")
                        fields = params.get("fields", {})
                        if not project or not task_id:
                            await ws.send(json.dumps(rpc_error(id_, -32602, "Missing 'project' or 'task_id'")))
                            continue
                        # Status first if present
                        if "status" in fields:
                            self.manager.set_task_status(project, task_id, fields["status"])
                        task = self.manager.get_task(project, task_id)
                        changed = False
                        if "title" in fields and isinstance(fields["title"], str) and fields["title"].strip():
                            task.title = fields["title"].strip(); changed = True
                        if "description" in fields and isinstance(fields["description"], str):
                            task.description = fields["description"]; changed = True
                        if "notes" in fields and isinstance(fields["notes"], str):
                            task.notes = fields["notes"]; changed = True
                        if changed:
                            self.manager.storage.save_task(task)
                        details = self.manager.get_task_details(project, task_id)
                        await ws.send(json.dumps(rpc_result(id_, details)))
                        await self.broadcast(rpc_notify("mcp.taskUpdated", {"project": project, "task_id": task_id}))

                    elif method == "mcp.deleteTask":
                        project = params.get("project")
                        task_id = params.get("task_id")
                        if not project or not task_id:
                            await ws.send(json.dumps(rpc_error(id_, -32602, "Missing 'project' or 'task_id'")))
                            continue
                        # delete task file and iterations
                        self._delete_task(project, task_id)
                        await ws.send(json.dumps(rpc_result(id_, {"ok": True})))
                        await self.broadcast(rpc_notify("mcp.taskUpdated", {"project": project, "task_id": task_id}))

                    elif method == "mcp.addNote":
                        project = params.get("project")
                        task_id = params.get("task_id")
                        note = params.get("note")
                        if not project or not task_id or not note:
                            await ws.send(json.dumps(rpc_error(id_, -32602, "Missing 'project', 'task_id' or 'note'")))
                            continue
                        self.manager.add_iteration_note(project, task_id, note)
                        await ws.send(json.dumps(rpc_result(id_, {"ok": True})))
                        await self.broadcast(rpc_notify("mcp.taskUpdated", {"project": project, "task_id": task_id}))

                    elif method == "mcp.startIteration":
                        project = params.get("project")
                        task_id = params.get("task_id")
                        if not project or not task_id:
                            await ws.send(json.dumps(rpc_error(id_, -32602, "Missing 'project' or 'task_id'")))
                            continue
                        it = self.manager.start_task(project, task_id)
                        await ws.send(json.dumps(rpc_result(id_, it.to_dict())))
                        await self.broadcast(rpc_notify("mcp.taskUpdated", {"project": project, "task_id": task_id}))

                    elif method == "mcp.completeIteration":
                        project = params.get("project")
                        task_id = params.get("task_id")
                        if not project or not task_id:
                            await ws.send(json.dumps(rpc_error(id_, -32602, "Missing 'project' or 'task_id'")))
                            continue
                        self.manager.complete_iteration(project, task_id)
                        await ws.send(json.dumps(rpc_result(id_, {"ok": True})))
                        await self.broadcast(rpc_notify("mcp.taskUpdated", {"project": project, "task_id": task_id}))

                    elif method == "mcp.projectStatus":
                        project = params.get("project")
                        if not project:
                            await ws.send(json.dumps(rpc_error(id_, -32602, "Missing 'project'")))
                            continue
                        info = self.manager.get_project_status(project)
                        await ws.send(json.dumps(rpc_result(id_, info)))

                    else:
                        await ws.send(json.dumps(rpc_error(id_, -32601, f"Method not found: {method}")))
                except (TaskManagerError, ProjectNotFoundError, TaskNotFoundError) as exc:
                    await ws.send(json.dumps(rpc_error(id_, -32000, str(exc))))
                except Exception as exc:  # noqa: BLE001
                    await ws.send(json.dumps(rpc_error(id_, -32001, "Internal error", str(exc))))
        finally:
            try:
                self.connections.remove(ws)
            except ValueError:
                pass

    def _delete_task(self, project: str, task_id: str) -> None:
        # Remove task file and iterations via storage
        storage = self.manager.storage
        tasks_dir = storage.base_dir / project / "tasks"
        for f in tasks_dir.glob(f"{task_id}-*.yaml"):
            f.unlink(missing_ok=True)
        for f in tasks_dir.glob(f"{task_id}.iter*.yaml"):
            f.unlink(missing_ok=True)

    async def start(self) -> None:
        async with websockets.serve(self.handle, self.host, self.port):
            # Run until interrupted
            done = asyncio.Future()
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, lambda s=sig: done.set_result(True))
            await done


def main() -> None:
    server = MCPServer()
    asyncio.run(server.start())


if __name__ == "__main__":
    main()


