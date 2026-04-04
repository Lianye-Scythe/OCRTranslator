from PySide6.QtCore import QTimer
from PySide6.QtNetwork import QLocalServer


class InstanceServerService:
    def __init__(self, window, server_name: str, *, log_func=None):
        self.window = window
        self.server_name = server_name
        self.log = log_func or (lambda message: None)
        self.server: QLocalServer | None = None
        self._socket_buffers: dict[int, bytearray] = {}

    def setup(self):
        try:
            QLocalServer.removeServer(self.server_name)
        except Exception:  # noqa: BLE001
            pass
        self.server = QLocalServer(self.window)
        self.server.newConnection.connect(self._handle_new_connection)
        if not self.server.listen(self.server_name):
            self.log(f"Instance server listen failed: {self.server.errorString()}")
        self.window.instance_server = self.server
        return self.server

    def close(self):
        if self.server and self.server.isListening():
            self.server.close()
            self._socket_buffers.clear()
            QLocalServer.removeServer(self.server_name)

    def _handle_new_connection(self):
        if not self.server:
            return
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            socket.readyRead.connect(lambda socket=socket: self._read_message(socket))
            socket.disconnected.connect(lambda socket=socket: self._cleanup_socket(socket))

    def _cleanup_socket(self, socket):
        self._socket_buffers.pop(id(socket), None)
        socket.deleteLater()

    def _read_message(self, socket):
        socket_id = id(socket)
        buffer = self._socket_buffers.setdefault(socket_id, bytearray())
        buffer.extend(bytes(socket.readAll()))
        if b"\n" not in buffer:
            return
        message_bytes, _, _ = buffer.partition(b"\n")
        self._socket_buffers.pop(socket_id, None)
        message = message_bytes.decode("utf-8", errors="ignore").strip().lower()
        reply = "unknown"
        if message == "show":
            self.log("Received activation request from another launch")
            self.window.show_main_window()
            reply = "ok"
        elif message == "capture":
            self.log("Received capture request from another launch")
            self.window.show_main_window()
            QTimer.singleShot(0, self.window.start_selection)
            reply = "ok"
        try:
            socket.write(f"{reply}\n".encode("utf-8"))
            socket.flush()
        except Exception:  # noqa: BLE001
            pass
        socket.disconnectFromServer()
