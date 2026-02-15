import flet as ft
import requests
import asyncio
import json
import base64
import websockets

# Configuration
API_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws"

class IoneClient:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Ione Messenger"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.padding = 20
        self.user_id = None
        self.username = None
        self.display_name = None
        self.ws = None
        
        self.file_picker = ft.FilePicker(on_result=self.on_file_result)
        self.page.overlay.append(self.file_picker)
        self.init_views()

    def init_views(self):
        # Login View Components
        self.login_username = ft.TextField(label="Username", width=300)
        self.login_password = ft.TextField(label="Password", password=True, can_reveal_password=True, width=300)
        
        # Registration View Components
        self.reg_username = ft.TextField(label="Username", width=300)
        self.reg_display_name = ft.TextField(label="Display Name", width=300)
        self.reg_password = ft.TextField(label="Password", password=True, can_reveal_password=True, width=300)

        # Chat View Components
        self.chat_messages = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True)
        self.new_message = ft.TextField(hint_text="Type a message...", expand=True, on_submit=self.send_message_click)
        
        self.show_login()

    def show_login(self, e=None):
        self.page.clean()
        self.page.add(
            ft.Column([
                ft.Text("Ione Messenger", size=30, weight=ft.FontWeight.BOLD),
                self.login_username,
                self.login_password,
                ft.ElevatedButton("Login", on_click=self.login_click),
                ft.TextButton("Don't have an account? Register", on_click=self.show_register)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def show_register(self, e=None):
        self.page.clean()
        self.page.add(
            ft.Column([
                ft.Text("Create Account", size=30, weight=ft.FontWeight.BOLD),
                self.reg_username,
                self.reg_display_name,
                self.reg_password,
                ft.ElevatedButton("Register", on_click=self.register_click),
                ft.TextButton("Back to Login", on_click=self.show_login)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def show_chat(self):
        self.page.clean()
        self.page.add(
            ft.AppBar(
                title=ft.Text(f"Ione - {self.display_name} (ID: {self.user_id})"),
                bgcolor=ft.Colors.SURFACE_VARIANT,
                actions=[ft.IconButton(ft.Icons.LOGOUT, on_click=self.show_login)]
            ),
            ft.Container(
                content=self.chat_messages,
                expand=True,
                padding=10,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=10,
            ),
            ft.Row([
                ft.IconButton(ft.Icons.IMAGE, on_click=lambda _: self.file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)),
                ft.IconButton(ft.Icons.MIC, on_click=lambda _: print("Voice recorded")), # Placeholder
                self.new_message,
                ft.IconButton(ft.Icons.SEND, on_click=self.send_message_click)
            ])
        )
        asyncio.create_task(self.listen_ws())

    async def login_click(self, e):
        try:
            response = requests.post(f"{API_URL}/login", json={
                "username": self.login_username.value,
                "password": self.login_password.value
            })
            if response.status_code == 200:
                data = response.json()
                self.user_id = data["id"]
                self.username = data["username"]
                self.display_name = data["display_name"]
                self.show_chat()
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("Login failed! Check credentials."))
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as ex:
            print(f"Login error: {ex}")

    async def register_click(self, e):
        try:
            response = requests.post(f"{API_URL}/register", json={
                "username": self.reg_username.value,
                "display_name": self.reg_display_name.value,
                "password": self.reg_password.value
            })
            if response.status_code == 200:
                self.page.snack_bar = ft.SnackBar(ft.Text("Registered successfully! Please login."))
                self.page.snack_bar.open = True
                self.show_login()
            else:
                self.page.snack_bar = ft.SnackBar(ft.Text("Registration failed!"))
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as ex:
            print(f"Register error: {ex}")

    async def listen_ws(self):
        try:
            async with websockets.connect(f"{WS_URL}/{self.user_id}") as websocket:
                self.ws = websocket
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    self.add_message_to_ui(data)
        except Exception as e:
            print(f"WebSocket error: {e}")

    def add_message_to_ui(self, data):
        is_me = data["sender_id"] == self.user_id
        alignment = ft.MainAxisAlignment.END if is_me else ft.MainAxisAlignment.START
        color = ft.Colors.BLUE_700 if is_me else ft.Colors.GREY_800
        
        msg_content = ft.Text(data["content"], color=ft.Colors.WHITE)
        
        if data["type"] == "image":
            # Image display from URL or Base64
            img_src = data["content"]
            if img_src.startswith("/uploads/"):
                img_src = f"{API_URL}{img_src}"
            
            try:
                msg_content = ft.Image(src=img_src, width=250, border_radius=10, fit=ft.ImageFit.CONTAIN)
            except:
                msg_content = ft.Text("[Error loading image]")

        self.chat_messages.controls.append(
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text(data["sender_name"], size=10, color=ft.Colors.WHITE70),
                        msg_content
                    ]),
                    padding=10,
                    bgcolor=color,
                    border_radius=10,
                    width=250 if data["type"] == "text" else None
                )
            ], alignment=alignment)
        )
        self.page.update()

    async def send_message_click(self, e):
        if self.new_message.value and self.ws:
            msg = {"content": self.new_message.value, "type": "text"}
            await self.ws.send(json.dumps(msg))
            self.new_message.value = ""
            self.page.update()

    def on_file_result(self, e: ft.FilePickerResultEvent):
        if e.files:
            file = e.files[0]
            try:
                with open(file.path, "rb") as f:
                    encoded_string = base64.b64encode(f.read()).decode("utf-8")
                    asyncio.create_task(self.ws.send(json.dumps({
                        "content": encoded_string,
                        "type": "image"
                    })))
            except Exception as ex:
                print(f"File upload error: {ex}")

def main(page: ft.Page):
    IoneClient(page)

if __name__ == "__main__":
    ft.app(target=main)
