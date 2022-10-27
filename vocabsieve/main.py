import sys
from PyQt5.QtWidgets import *
from app_window import *
from settings import *
from threading import Thread

def main():
    app = QApplication(sys.argv)
    app_window = AppWindow()

    def handle_server_excep(server_name: str, e: Exception):
        print(e)
        app_window.widgets.status(f"{server_name} failed")

    def invoke_in_thread(f):
        t = Thread(target=f, daemon=True)
        t.start()
        return t

    def start_api_server():
        invoke_in_thread(
            pass_exceptions(
                lambda: APIServer(
                    settings.get("api_host"), 
                    settings.get("api_port")), 
                lambda e: handle_server_excep("API server", e)))

    def start_reader_server():
        invoke_in_thread(
            pass_exceptions(
                lambda: ReaderServer(
                    settings.get("reader_host"), 
                    settings.get("reader_port")), 
                lambda e: handle_server_excep("Reader server", e)))

    app_window.show()

    # Servers
    if settings.get("api_enabled"):
        start_api_server()
    if settings.get("reader_enabled"):
        start_reader_server()

    sys.exit(app.exec())

main()
