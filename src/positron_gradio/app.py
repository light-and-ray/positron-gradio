import threading, time, asyncio
from pathlib import Path

import toga
import gradio as gr
import gradio.utils
# Workaround to fix Thread 'Thread-1 (launch)' already has a main context
gradio.utils.safe_get_lock = lambda: asyncio.Lock()
gradio.utils.safe_get_stop_event = lambda: asyncio.Event()


class MyGradioApp():
    def __init__(self, resourcesPath: Path):
        self._resourcesPath = resourcesPath
        self._serverThread = None
        self._app_ready_condition = threading.Condition()
        self._initApp()

    def _initApp(self):
        theme = gradio.themes.Origin()
        with gr.Blocks(analytics_enabled=False, theme=theme) as self._app:
            with gr.Row():
                with gr.Column():
                    with gr.Row():
                        gr.Image(scale=0, interactive=False, value=self._resourcesPath / 'toga.png')
                        gr.Markdown("# Gradio inside Toga Positron")
                    gr.Markdown(f"Resources path is `{self._resourcesPath}`")
                    gr.ColorPicker(label="Color Picker", value="#da9a9a")
                with gr.Column():
                    name = gr.Textbox(label="Enter your name")
                    @gr.render(inputs=[name])
                    def renderHelloName(name: str):
                        if name.strip():
                            gr.Markdown(f"Hello, {name}! 👋")
                    button = gr.Button("Click me", variant="primary")
                    button.click(fn=lambda: gr.Info("Clicked"))

    def launch(self):
        self._app.launch(allowed_paths=[self._resourcesPath])

    def launchInThread(self):
        self._serverThread = threading.Thread(target=self.launch)
        self._serverThread.daemon = True
        self._serverThread.start()

    def stop(self, *args, **kwargs):
        self._app.close()
        return True

    def getsockname(self):
        return self._app.server_name, self._app.server_port

    def waitUntilRunning(self, timeout=30, interval=0.5):
        start_time = time.time()

        while not self._app.is_running:
            if time.time() - start_time >= timeout:
                raise TimeoutError("Application did not start within the specified timeout.")
            time.sleep(interval)


class PositronGradio(toga.App):
    def startup(self):
        self.web_view = toga.WebView()

        self._gradioApp = MyGradioApp(self.paths.app / "resources")
        self._gradioApp.launchInThread()

        self.on_exit = self._gradioApp.stop

        self._gradioApp.waitUntilRunning()
        host, port = self._gradioApp.getsockname()
        self.web_view.url = f"http://{host}:{port}/"

        self.main_window = toga.MainWindow()
        self.main_window.content = self.web_view
        self.main_window.show()


def main():
    return PositronGradio()
