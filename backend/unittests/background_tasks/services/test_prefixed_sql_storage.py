from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from huey.api import Huey
from peewee import SqliteDatabase

from application.background_tasks.services.prefixed_sql_storage import (
    PrefixedSqlHuey,
    PrefixedSqlStorage,
)

EXPECTED_TABLE_NAMES = {"huey_kv", "huey_schedule", "huey_task", "huey_counter"}


class TestPrefixedSqlStorage(TestCase):
    def setUp(self) -> None:
        # A file based database is needed, because peewee closes the connection
        # after creating the tables, which would discard an in-memory database.
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        self.database = SqliteDatabase(str(Path(temporary_directory.name) / "huey.db"))
        self.addCleanup(self.database.close)

    def _sqlite_master(self, object_type: str) -> dict[str, tuple[str, str]]:
        with self.database:
            rows = self.database.execute_sql(
                "SELECT name, tbl_name, sql FROM sqlite_master WHERE type = ?", (object_type,)
            ).fetchall()
        return {name: (tbl_name, sql) for name, tbl_name, sql in rows}

    # ---------------------------------------------------------------
    # create_models
    # ---------------------------------------------------------------

    def test_create_models_renames_tables(self):
        storage = PrefixedSqlStorage(name="test", database=self.database)

        self.assertEqual("huey_kv", getattr(storage.KV, "_meta").table_name)
        self.assertEqual("huey_schedule", getattr(storage.Schedule, "_meta").table_name)
        self.assertEqual("huey_task", getattr(storage.Task, "_meta").table_name)
        self.assertEqual("huey_counter", getattr(storage.Counter, "_meta").table_name)

    def test_create_models_invalidates_cached_table(self):
        storage = PrefixedSqlStorage(name="test", database=self.database)

        for model, table_name in (
            (storage.KV, "huey_kv"),
            (storage.Schedule, "huey_schedule"),
            (storage.Task, "huey_task"),
            (storage.Counter, "huey_counter"),
        ):
            sql, _ = model.select().sql()
            self.assertIn(f'FROM "{table_name}"', sql)

    def test_create_models_has_exactly_one_task_index(self):
        storage = PrefixedSqlStorage(name="test", database=self.database)

        self.assertEqual(1, len(getattr(storage.Task, "_meta").indexes))

    # ---------------------------------------------------------------
    # create_tables
    # ---------------------------------------------------------------

    def test_create_tables_creates_only_prefixed_tables(self):
        PrefixedSqlStorage(name="test", database=self.database)

        self.assertEqual(EXPECTED_TABLE_NAMES, set(self._sqlite_master("table")))

    def test_create_tables_creates_task_index_on_prefixed_table(self):
        PrefixedSqlStorage(name="test", database=self.database)

        indexes = self._sqlite_master("index")
        self.assertIn("task_priority_id", indexes)
        table_name, sql = indexes["task_priority_id"]
        self.assertEqual("huey_task", table_name)
        self.assertEqual('CREATE INDEX "task_priority_id" ON "huey_task" ("priority" DESC, "id")', sql)

    def test_create_tables_creates_schedule_index_on_prefixed_table(self):
        PrefixedSqlStorage(name="test", database=self.database)

        indexes = self._sqlite_master("index")
        self.assertIn("schedule_queue_timestamp", indexes)
        table_name, sql = indexes["schedule_queue_timestamp"]
        self.assertEqual("huey_schedule", table_name)
        self.assertEqual('CREATE INDEX "schedule_queue_timestamp" ON "huey_schedule" ("queue", "timestamp")', sql)

    def test_drop_tables_drops_prefixed_tables(self):
        storage = PrefixedSqlStorage(name="test", database=self.database)

        storage.drop_tables()

        self.assertEqual(set(), set(self._sqlite_master("table")))

    # ---------------------------------------------------------------
    # storage operations on the renamed tables
    # ---------------------------------------------------------------

    def test_enqueue_and_dequeue(self):
        storage = PrefixedSqlStorage(name="test", database=self.database)

        storage.enqueue(b"task_1", priority=1)
        storage.enqueue(b"task_2", priority=2)

        self.assertEqual(2, storage.queue_size())
        # Higher priority first, which is the code path using the recreated index
        self.assertEqual(b"task_2", storage.dequeue())
        self.assertEqual(b"task_1", storage.dequeue())
        self.assertEqual(0, storage.queue_size())
        self.assertIsNone(storage.dequeue())

    def test_put_and_pop_data(self):
        storage = PrefixedSqlStorage(name="test", database=self.database)

        storage.put_data("key", b"value")

        self.assertTrue(storage.has_data_for_key("key"))
        self.assertEqual(b"value", storage.peek_data("key"))
        self.assertEqual(b"value", storage.pop_data("key"))
        self.assertFalse(storage.has_data_for_key("key"))

    def test_add_to_schedule_and_read_schedule(self):
        storage = PrefixedSqlStorage(name="test", database=self.database)

        storage.add_to_schedule(b"scheduled_task", 1_000)

        self.assertEqual(1, storage.schedule_size())
        self.assertEqual([], storage.read_schedule(999))
        self.assertEqual([b"scheduled_task"], storage.read_schedule(1_000))
        self.assertEqual(0, storage.schedule_size())

    def test_incr_counter(self):
        storage = PrefixedSqlStorage(name="test", database=self.database)

        self.assertEqual(1, storage.incr("counter"))
        self.assertEqual(3, storage.incr("counter", 2))

        storage.delete_counter("counter")

        self.assertEqual(1, storage.incr("counter"))

    # ---------------------------------------------------------------
    # PrefixedSqlHuey
    # ---------------------------------------------------------------

    def test_prefixed_sql_huey(self):
        huey = PrefixedSqlHuey(name="test", database=self.database)

        self.assertIsInstance(huey, Huey)
        self.assertIsInstance(huey.storage, PrefixedSqlStorage)
        self.assertEqual("test", huey.storage.name)
        self.assertEqual(EXPECTED_TABLE_NAMES, set(self._sqlite_master("table")))
