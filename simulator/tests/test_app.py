import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


simulator_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(simulator_dir))
with patch.dict(os.environ, {"DB_PASSWORD": "unit-test-only"}):
    with patch("psycopg2.connect", return_value=MagicMock()):
        import app as simulator_app
sys.path.remove(str(simulator_dir))


class InitDbTests(unittest.TestCase):
    def test_requires_database_password(self):
        with patch.object(simulator_app, "DB_PASSWORD", None):
            with self.assertRaisesRegex(RuntimeError, "DB_PASSWORD"):
                simulator_app.get_db_connection()

    def test_retries_when_database_is_not_ready(self):
        connection = MagicMock()
        with (
            patch.object(
                simulator_app,
                "get_db_connection",
                side_effect=[None, connection],
            ) as get_db_connection,
            patch.object(simulator_app.time, "sleep") as sleep,
        ):
            simulator_app.init_db()

        self.assertEqual(get_db_connection.call_count, 2)
        sleep.assert_called_once_with(2)
        created_table = connection.cursor.return_value.__enter__.return_value
        created_table.execute.assert_called_once()
        connection.commit.assert_called_once()
        connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
