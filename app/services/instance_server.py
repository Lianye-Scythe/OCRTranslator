from PySide6.QtNetwork import QLocalServer


class InstanceServerService:
    def __init__(self, window, server_name: str, *, log_func=None):
        self.window = window
        self.server_name = server_name
        self.log = log_func or (lambda message: None)
        self.server: QLocalServer | None = None

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
            QLocalServer.removeServer(self.server_name)

    def _handle_new_connection(self):
        if not self.server:
            return
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            socket.readyRead.connect(lambda socket=socket: self._read_message(socket))
            socket.disconnected.connect(socket.deleteLater)

    def _read_message(self, socket):
        message = bytes(socket.readAll()).decode("utf-8", errors="ignore").strip()
        if message == "show":
            self.log("Received activation request from another launch")
            self.window.show_main_window()
        elif message == "capture":
            self.log("Received capture request from another launch")
            self.window.show_main_window()
            self.window.start_selection()
        socket.disconnectFromServer()
