import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.services.instance_server import InstanceServerService


class _FakeSocket:
    def __init__(self, chunks):
        self._chunks = list(chunks)
        self.written = []
        self.disconnected = False
        self.deleted = False

    def readAll(self):
        if self._chunks:
            return self._chunks.pop(0)
        return b""

    def write(self, payload):
        self.written.append(payload)

    def flush(self):
        return True

    def disconnectFromServer(self):
        self.disconnected = True

    def deleteLater(self):
        self.deleted = True


class InstanceServerServiceTests(unittest.TestCase):
    def test_read_message_acknowledges_show_action(self):
        window = SimpleNamespace(show_main_window=Mock(), start_selection=Mock())
        service = InstanceServerService(window, "demo-server")
        socket = _FakeSocket([b"show\n"])

        service._read_message(socket)

        window.show_main_window.assert_called_once_with()
        window.start_selection.assert_not_called()
        self.assertEqual(socket.written, [b"ok\n"])
        self.assertTrue(socket.disconnected)

    @patch("app.services.instance_server.QTimer.singleShot", side_effect=lambda _delay, callback: callback())
    def test_read_message_buffers_partial_capture_command(self, _mock_single_shot):
        window = SimpleNamespace(show_main_window=Mock(), start_selection=Mock())
        service = InstanceServerService(window, "demo-server")
        socket = _FakeSocket([b"capt", b"ure\n"])

        service._read_message(socket)
        window.show_main_window.assert_not_called()
        self.assertEqual(socket.written, [])
        self.assertFalse(socket.disconnected)

        service._read_message(socket)

        window.show_main_window.assert_called_once_with()
        window.start_selection.assert_called_once_with()
        self.assertEqual(socket.written, [b"ok\n"])
        self.assertTrue(socket.disconnected)


if __name__ == "__main__":
    unittest.main()
