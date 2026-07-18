
import os
import json
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Callable, Optional, List
from enum import Enum
from datetime import datetime

class TaskStatus(str, Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'

class Task:
    def __init__(self, task_id, func, *args, **kwargs):
        self.id = task_id
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.progress = 0
        self.message = ''
        self.created_at = datetime.now()
        self.started_at = None
        self.finished_at = None
        self.storage_path = None
        self._cancel_event = threading.Event()

    def set_storage(self, path):
        self.storage_path = path
        self._save()

    def _save(self):
        if not self.storage_path:
            return
        data = {
            'id': self.id,
            'status': self.status,
            'result': self.result,
            'error': self.error,
            'progress': self.progress,
            'message': self.message,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'args': [str(a) for a in self.args],
            'kwargs': {k: str(v) for k, v in self.kwargs.items()}
        }
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def execute(self):
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()
        self._save()
        try:
            if self._cancel_event.is_set():
                self.status = TaskStatus.CANCELLED
                self._save()
                return
            self.result = self.func(*self.args, **self.kwargs)
            self.status = TaskStatus.COMPLETED
        except Exception as e:
            self.error = str(e)
            self.status = TaskStatus.FAILED
        finally:
            self.finished_at = datetime.now()
            self._save()

    def cancel(self):
        self._cancel_event.set()
        if self.status == TaskStatus.RUNNING:
            self.status = TaskStatus.CANCELLED
            self._save()

    def update_progress(self, progress, message=''):
        self.progress = progress
        self.message = message
        self._save()

class TaskManager:
    _instance = None
    _lock = threading.Lock()
    _tasks_lock = threading.Lock()

    def __new__(cls, max_workers=4, storage_dir='storage/tasks'):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TaskManager, cls).__new__(cls)
                cls._instance.executor = ThreadPoolExecutor(max_workers=max_workers)
                cls._instance.tasks = {}
                cls._instance.storage_dir = storage_dir
                cls._instance._load_tasks()
            return cls._instance

    def _load_tasks(self):
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)
            return
        for filename in os.listdir(self.storage_dir):
            if filename.startswith('task_') and filename.endswith('.json'):
                path = os.path.join(self.storage_dir, filename)
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                        task_id = data['id']
                        task = Task(task_id, lambda: None)
                        task.status = data['status']
                        task.result = data.get('result')
                        task.error = data.get('error')
                        task.progress = data.get('progress', 0)
                        task.message = data.get('message', '')
                        task.created_at = datetime.fromisoformat(data['created_at'])
                        if data.get('started_at'):
                            task.started_at = datetime.fromisoformat(data['started_at'])
                        if data.get('finished_at'):
                            task.finished_at = datetime.fromisoformat(data['finished_at'])
                        task.storage_path = path
                        self.tasks[task_id] = task
                except Exception as e:
                    print(f'Failed to load task from {path}: {e}')

    def submit(self, func, *args, **kwargs):
        with self._tasks_lock:
            task_id = str(uuid.uuid4())
            task = Task(task_id, func, *args, **kwargs)
            task.set_storage(os.path.join(self.storage_dir, f'task_{task_id}.json'))
            self.tasks[task_id] = task
            self.executor.submit(task.execute)
            return task_id

    def get_task(self, task_id):
        with self._tasks_lock:
            task = self.tasks.get(task_id)
            if not task:
                return None
            return {
                'id': task.id,
                'status': task.status,
                'result': task.result,
                'error': task.error,
                'progress': task.progress,
                'message': task.message,
                'created_at': task.created_at.isoformat(),
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'finished_at': task.finished_at.isoformat() if task.finished_at else None,
            }

    def list_tasks(self):
        with self._tasks_lock:
            return [self.get_task(tid) for tid in self.tasks.keys()]

    def cancel_task(self, task_id):
        with self._tasks_lock:
            task = self.tasks.get(task_id)
            if not task:
                return False
            task.cancel()
            return True

    def get_user_active_tasks(self, user_id):
        with self._tasks_lock:
            return [tid for tid, task in self.tasks.items() 
                    if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING] 
                    and user_id in str(task.args)]

    def can_submit_task(self, user_id, max_tasks=2):
        return len(self.get_user_active_tasks(user_id)) < max_tasks
