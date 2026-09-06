import asyncio
from collections.abc import Callable, Coroutine
from typing import Any


class TaskPool:
    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task[Any]] = {}
        self._stop_events: dict[str, asyncio.Event] = {}

    @property
    def active_ids(self) -> list[str]:
        return list(self._tasks.keys())

    def start(self, task_id: str, coro_func: Callable[[asyncio.Event], Coroutine[Any, Any, None]]) -> None:
        """Démarre une tâche identifiée par task_id.
        coro_func doit accepter l'Event d'arrêt en paramètre.
        """
        if task_id in self._tasks:
            raise ValueError(f"Task {task_id} already running")

        stop_event = asyncio.Event()
        task = asyncio.create_task(coro_func(stop_event))

        self._tasks[task_id] = task
        self._stop_events[task_id] = stop_event

        # Nettoyage auto quand la tâche se termine (naturellement ou via stop)
        task.add_done_callback(lambda t, tid=task_id: self._cleanup(tid))

    def stop(self, task_id: str) -> None:
        """Signale à la tâche de s'arrêter (soft stop via Event)."""
        if task_id in self._stop_events:
            self._stop_events[task_id].set()

    def _cleanup(self, task_id: str) -> None:
        self._tasks.pop(task_id, None)
        self._stop_events.pop(task_id, None)

    async def wait(self, task_id: str) -> None:
        """Attend la fin effective de la tâche (utile pour un stop bloquant)."""
        task = self._tasks.get(task_id)
        if task:
            await task

    async def stop_and_wait(self, task_id: str) -> None:
        self.stop(task_id)
        await self.wait(task_id)

    def is_running(self, task_id: str) -> bool:
        return task_id in self._tasks

    async def shutdown(self) -> None:
        """Arrête proprement toutes les tâches restantes."""
        for event in self._stop_events.values():
            event.set()
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)