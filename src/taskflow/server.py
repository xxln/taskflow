from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .manager import (
    TaskManager,
    TaskManagerError,
    ProjectNotFoundError,
    TaskNotFoundError,
    IterationNotFoundError,
)
from .models import TaskStatus  # noqa: F401 - reserved for future use


class AppState:
    def __init__(self, base_dir: str = "projects") -> None:
        self.base_dir: Path = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def manager(self) -> TaskManager:
        return TaskManager(base_dir=str(self.base_dir))


state = AppState()

app = FastAPI(
    title="Taskflow API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/ui/")


@app.get("/config/base-dir")
def get_base_dir() -> Dict[str, str]:
    return {
        "base_dir": str(state.base_dir.resolve())
    }


@app.post("/config/base-dir")
def set_base_dir(payload: Dict[str, str]) -> Dict[str, str]:
    path = payload.get("path")
    if not path:
        raise HTTPException(status_code=400, detail="Missing 'path'")
    new_dir = Path(path).expanduser().resolve()
    new_dir.mkdir(parents=True, exist_ok=True)
    state.base_dir = new_dir
    # Initialize structure lazily via manager when used
    return {"base_dir": str(state.base_dir)}


# Project endpoints
@app.get("/projects")
def list_projects() -> List[str]:
    return state.manager().list_projects()


@app.post("/projects")
def create_project(payload: Dict[str, Any]) -> Dict[str, Any]:
    name = payload.get("name")
    description = payload.get("description", "")
    if not name:
        raise HTTPException(status_code=400, detail="Missing 'name'")
    try:
        project = state.manager().create_project(name, description)
        return project.to_dict()
    except TaskManagerError as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/projects/{project}/status")
def project_status(project: str) -> Dict[str, Any]:
    info = state.manager().get_project_status(project)
    if not info.get("exists"):
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project}' not found",
        )
    return info


# Task endpoints
@app.get("/projects/{project}/tasks")
def list_tasks(project: str) -> List[Dict[str, Any]]:
    try:
        manager = state.manager()
        ids = manager.list_tasks(project)
        tasks: List[Dict[str, Any]] = []
        for task_id in ids:
            try:
                task = manager.get_task(project, task_id)
                tasks.append(task.to_dict())
            except TaskNotFoundError:
                continue
        return tasks
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/projects/{project}/tasks")
def create_task(project: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    title = payload.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="Missing 'title'")
    description = payload.get("description", "")
    notes = payload.get("notes", "")
    try:
        task = state.manager().create_task(project, title, description, notes)
        return task.to_dict()
    except TaskManagerError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/projects/{project}/tasks/{task_id}")
def get_task(project: str, task_id: str) -> Dict[str, Any]:
    try:
        return state.manager().get_task_details(project, task_id)
    except (ProjectNotFoundError, TaskNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.patch("/projects/{project}/tasks/{task_id}")
def update_task(
    project: str,
    task_id: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    manager = state.manager()
    try:
        # Status update
        status = payload.get("status")
        if status is not None:
            try:
                manager.set_task_status(project, task_id, status)
            except TaskManagerError as exc:
                raise HTTPException(status_code=400, detail=str(exc))

        # Optional metadata edits (title/description/notes)
        task = manager.get_task(project, task_id)
        changed = False
        if (
            "title" in payload
            and isinstance(payload["title"], str)
            and payload["title"].strip()
        ):
            task.title = payload["title"].strip()
            changed = True
        if (
            "description" in payload
            and isinstance(payload["description"], str)
        ):
            task.description = payload["description"]
            changed = True
        if "notes" in payload and isinstance(payload["notes"], str):
            task.notes = payload["notes"]
            changed = True
        if changed:
            manager.storage.save_task(task)

        return manager.get_task_details(project, task_id)
    except (ProjectNotFoundError, TaskNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# Iteration endpoints
@app.post("/projects/{project}/tasks/{task_id}/iterations/start")
def start_iteration(project: str, task_id: str) -> Dict[str, Any]:
    try:
        iteration = state.manager().start_task(project, task_id)
        return iteration.to_dict()
    except TaskManagerError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/projects/{project}/tasks/{task_id}/iterations/note")
def add_note(
    project: str,
    task_id: str,
    payload: Dict[str, str],
) -> Dict[str, str]:
    note = payload.get("note")
    if not note:
        raise HTTPException(status_code=400, detail="Missing 'note'")
    try:
        state.manager().add_iteration_note(project, task_id, note)
        return {"ok": "true"}
    except (IterationNotFoundError, TaskManagerError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/projects/{project}/tasks/{task_id}/iterations/summary")
def set_summary(
    project: str,
    task_id: str,
    payload: Dict[str, str],
) -> Dict[str, str]:
    summary = payload.get("summary")
    if summary is None:
        raise HTTPException(status_code=400, detail="Missing 'summary'")
    try:
        state.manager().set_iteration_summary(project, task_id, summary)
        return {"ok": "true"}
    except (IterationNotFoundError, TaskManagerError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/projects/{project}/tasks/{task_id}/iterations/complete")
def complete_iteration(project: str, task_id: str) -> Dict[str, str]:
    try:
        state.manager().complete_iteration(project, task_id)
        return {"ok": "true"}
    except (IterationNotFoundError, TaskManagerError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


def main() -> None:
    import uvicorn

    web_root = Path(__file__).resolve().parents[2] / "web"
    if web_root.exists():
        # Mount static files at /ui to avoid intercepting API routes
        app.mount(
            "/ui",
            StaticFiles(directory=str(web_root), html=True),
            name="web",
        )

    uvicorn.run(
        "taskflow.server:app",
        host="127.0.0.1",
        port=8765,
        reload=False,
    )


