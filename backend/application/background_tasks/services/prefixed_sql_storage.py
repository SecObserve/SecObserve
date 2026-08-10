from functools import partial
from typing import Any

from huey.api import Huey
from huey.contrib.sql_huey import SqlStorage


class PrefixedSqlStorage(SqlStorage):
    def create_models(self) -> tuple[Any, Any, Any, Any]:
        KV, Schedule, Task, Counter = super().create_models()

        # Task is special: super().create_models() already called
        # add_index() on it, which cached a reference to the OLD table
        # object inside the index itself. We have to drop that index,
        # rename, invalidate the table cache, then re-add the index.
        task_meta = getattr(Task, "_meta")
        task_meta.indexes = []

        for model, suffix in ((KV, "kv"), (Schedule, "schedule"), (Task, "task"), (Counter, "counter")):
            meta = getattr(model, "_meta")
            meta.table_name = f"huey_{suffix}"
            del meta.table  # invalidate peewee's cached Table object

        task_id_field = getattr(Task, "id")
        Task.add_index(Task.priority.desc(), task_id_field)
        return KV, Schedule, Task, Counter


PrefixedSqlHuey = partial(Huey, storage_class=PrefixedSqlStorage)
