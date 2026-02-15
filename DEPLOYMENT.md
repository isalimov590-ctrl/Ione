# Ione Messenger: Deployment and Testing Instructions

This document provides instructions for deploying and testing the Ione messenger application, consisting of a FastAPI backend and a Flet frontend, on a mobile device using Pydroid 3 and Termux.

## 1. Prerequisites

Before you begin, ensure you have the following applications installed on your Android device:

*   **Pydroid 3:** A Python IDE for Android that allows you to run Python scripts.
*   **Termux:** A terminal emulator for Android that provides a Linux environment, useful for running the FastAPI server in the background.

### Python Package Installation

Both Pydroid 3 and Termux will need the following Python packages. It is recommended to install them in both environments to avoid conflicts.

**In Pydroid 3:**

Open Pydroid 3, go to `Pip` -> `Install` and search for and install the following packages:

*   `flet`
*   `fastapi`
*   `uvicorn`
*   `websockets`
*   `requests`

Alternatively, you can open the Pydroid 3 terminal and run:

```bash
pip install flet fastapi uvicorn websockets requests
```

**In Termux:**

Open Termux and run the following commands to install Python and the necessary packages:

```bash
pkg update && pkg upgrade
pkg install python
pip install flet fastapi uvicorn websockets requests
```

## 2. Project Setup

1.  **Transfer Files:** Transfer the `server.py` and `client.py` files to a directory on your phone that is accessible by both Pydroid 3 and Termux. A common location is `/sdcard/Ione/` or a similar path within your internal storage.

    *For example, let's assume you place them in `/sdcard/Ione/`.*

## 3. Running the Backend Server (FastAPI)

1.  **Open Termux:** Launch the Termux application.
2.  **Navigate to Project Directory:** Change to the directory where you saved your files:

    ```bash
    cd /sdcard/Ione/
    ```

3.  **Run the Server:** Execute the `server.py` file. The server will listen on `0.0.0.0:8000`.

    ```bash
    python server.py
    ```

    You should see output indicating that Uvicorn is running, similar to:
    ```
    INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
    INFO:     Started reloader process [xxxxx] using statreload
    INFO:     Started server process [xxxxx]
    INFO:     Waiting for application startup.
    INFO:     Application startup complete.
    ```

    *Keep this Termux session running in the background. You can swipe from the left edge of the screen to open the Termux menu and create a new session for the client.*

## 4. Running the Frontend Client (Flet)

1.  **Open Pydroid 3:** Launch the Pydroid 3 application.
2.  **Open `client.py`:** Navigate to and open the `client.py` file within Pydroid 3.
3.  **Modify API/WS URLs (if necessary):** If your Termux server is not accessible via `127.0.0.1` (localhost) from Pydroid 3, you might need to find your device's local IP address and update `API_URL` and `WS_URL` in `client.py` accordingly. For local testing on the same device, `127.0.0.1` should generally work.

    *Example if you need to change it (replace `YOUR_DEVICE_IP` with your actual IP, e.g., `192.168.1.100`):*
    ```python
    API_URL = "http://YOUR_DEVICE_IP:8000"
    WS_URL = "ws://YOUR_DEVICE_IP:8000/ws"
    ```

4.  **Run the Client:** Tap the yellow 
play button in Pydroid 3 to run `client.py`.

    Flet will launch the application. It might open in your default browser or as a standalone Flet application, depending on your Pydroid 3 and Flet setup.

## 5. Testing the Application

1.  **Registration:** On the client, click "Don't have an account? Register" and create a new user.
2.  **Login:** Use the newly created credentials to log in.
3.  **Messaging:** Send text messages. You should see them appear in the chat interface.
4.  **Image Sending:** Click the image icon. This will trigger the file picker. Select an image from your gallery. The image should be encoded and sent to the server, then displayed in the chat.

## Important Notes for Mobile Development

*   **File Paths:** Be mindful of file paths on Android. `/sdcard/` typically refers to your device's internal storage.
*   **Permissions:** For media and voice messages, your Python environment (Pydroid 3/Termux) might require storage and microphone permissions. Ensure these are granted in your Android settings.
*   **Network:** Both client and server need to be able to communicate. If you're using `127.0.0.1` and they are in different environments (e.g., Termux and Pydroid 3's internal browser), ensure they can resolve localhost correctly. If not, use your device's local IP address.
*   **Voice Messages:** The current `client.py` has a placeholder for voice messages. Implementing actual audio recording and streaming on Android with pure Python can be complex due to OS-level permissions and hardware access. For a robust solution, you might need to explore platform-specific Flet integrations or external libraries that handle audio recording.

This setup allows for rapid prototyping and testing of your Ione messenger directly on your Android device.
