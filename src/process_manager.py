import asyncio
import atexit
import os
import signal
import subprocess
import sys
from typing import Dict, List, Optional, Callable, Any

def kill_process_tree(pid: int) -> None:
    """
    Forcefully terminates a process and all its child / worker processes.
    On Windows, uses 'taskkill /F /T /PID <pid>' to cleanly wipe out the entire tree.
    On POSIX, uses process group signals or SIGKILL.
    """
    if not pid or pid <= 0:
        return

    if sys.platform == "win32":
        try:
            # CREATE_NO_WINDOW prevents command prompt window from popping up
            flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True,
                check=False,
                creationflags=flags
            )
        except Exception:
            pass
    else:
        try:
            pgid = os.getpgid(pid)
            os.killpg(pgid, signal.SIGKILL)
        except Exception:
            try:
                os.kill(pid, signal.SIGKILL)
            except Exception:
                pass


class ManagedProcess:
    def __init__(
        self,
        task_id: str,
        name: str,
        process: asyncio.subprocess.Process,
        on_stopped: Optional[Callable[[], Any]] = None
    ):
        self.task_id = task_id
        self.name = name
        self.process = process
        self.pid = process.pid if process else None
        self.on_stopped = on_stopped
        self.stopped_by_user = False


class ProcessManager:
    """
    Centralized process supervisor for tracking, coordinating,
    and safely terminating background tasks and their worker pools.
    """
    def __init__(self):
        self._processes: Dict[str, ManagedProcess] = {}
        self._listeners: List[Callable[[], None]] = []

    def add_listener(self, listener: Callable[[], None]) -> None:
        """Register a callback invoked whenever processes start, stop, or are unregistered."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[], None]) -> None:
        """Unregister a listener callback."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_listeners(self) -> None:
        for listener in list(self._listeners):
            try:
                listener()
            except Exception:
                pass

    def register(
        self,
        task_id: str,
        name: str,
        process: asyncio.subprocess.Process,
        on_stopped: Optional[Callable[[], Any]] = None
    ) -> ManagedProcess:
        """Register a new active background task."""
        managed = ManagedProcess(task_id, name, process, on_stopped)
        self._processes[task_id] = managed
        self._notify_listeners()
        return managed

    def unregister(self, task_id: str) -> None:
        """Remove a task from registry upon natural completion or post-stop cleanup."""
        if task_id in self._processes:
            del self._processes[task_id]
            self._notify_listeners()

    def is_running(self, task_id: str) -> bool:
        """Check if a specific task process is currently active."""
        managed = self._processes.get(task_id)
        if not managed or not managed.process:
            return False
        return managed.process.returncode is None

    def was_stopped_by_user(self, task_id: str) -> bool:
        """Check if a task was flagged as intentionally terminated by user force stop."""
        managed = self._processes.get(task_id)
        return managed.stopped_by_user if managed else False

    def get_running_count(self) -> int:
        """Return the count of active processes."""
        return sum(1 for mp in self._processes.values() if mp.process and mp.process.returncode is None)

    def get_running_names(self) -> List[str]:
        """Return list of human-readable names of currently running tasks."""
        return [mp.name for mp in self._processes.values() if mp.process and mp.process.returncode is None]

    async def kill_process(self, task_id: str) -> bool:
        """
        Forcefully terminate a single process and its entire worker tree.
        """
        managed = self._processes.get(task_id)
        if not managed:
            return False

        managed.stopped_by_user = True

        if managed.pid:
            kill_process_tree(managed.pid)

        if managed.process:
            try:
                managed.process.kill()
            except ProcessLookupError:
                pass
            except Exception:
                pass

        if managed.on_stopped:
            try:
                if asyncio.iscoroutinefunction(managed.on_stopped):
                    await managed.on_stopped()
                else:
                    managed.on_stopped()
            except Exception:
                pass

        self._notify_listeners()
        return True

    async def kill_all(self) -> int:
        """
        Forcefully terminate ALL registered running processes and their worker trees.
        Returns the number of processes killed.
        """
        active_tasks = [
            mp for mp in list(self._processes.values())
            if mp.process and mp.process.returncode is None
        ]

        if not active_tasks:
            return 0

        # Mark all as stopped by user
        for mp in active_tasks:
            mp.stopped_by_user = True

        # Kill process trees in parallel
        for mp in active_tasks:
            if mp.pid:
                kill_process_tree(mp.pid)

            if mp.process:
                try:
                    mp.process.kill()
                except ProcessLookupError:
                    pass
                except Exception:
                    pass

            if mp.on_stopped:
                try:
                    if asyncio.iscoroutinefunction(mp.on_stopped):
                        await mp.on_stopped()
                    else:
                        mp.on_stopped()
                except Exception:
                    pass

        self._notify_listeners()
        return len(active_tasks)

    def kill_all_sync(self) -> int:
        """
        Synchronous kill-all used during application shutdown or atexit cleanup.
        """
        active_tasks = [
            mp for mp in list(self._processes.values())
            if mp.process and mp.process.returncode is None
        ]

        for mp in active_tasks:
            mp.stopped_by_user = True
            if mp.pid:
                kill_process_tree(mp.pid)
            if mp.process:
                try:
                    mp.process.kill()
                except Exception:
                    pass

        return len(active_tasks)


# Global singleton instance
process_manager = ProcessManager()

# Ensure all child worker trees are killed when Python process exits
atexit.register(process_manager.kill_all_sync)
