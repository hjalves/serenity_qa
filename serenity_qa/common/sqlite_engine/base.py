from django.db.backends.sqlite3 import base


class DatabaseWrapper(base.DatabaseWrapper):
    def _start_transaction_under_autocommit(self):
        """
        Start all explicit transactions with BEGIN IMMEDIATE,
        not BEGIN DEFERRED, which is the default.

        This is a workaround to avoid "database is locked" errors,
        when doing `update_or_create` statements (and many others)
        in a concurrent environment.
        """
        self.cursor().execute("BEGIN IMMEDIATE")
