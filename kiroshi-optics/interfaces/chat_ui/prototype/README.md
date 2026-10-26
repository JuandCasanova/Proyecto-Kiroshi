# Kiroshi camera prototype

Standalone, dependency-free desktop UI prototype for the Kiroshi object-scanning flow. It only requests the browser's default user-facing camera; no image upload or audio capture is available.

## Run locally

From the `kiroshi-optics` directory in PowerShell:

```powershell
python -m http.server 8000 --directory interfaces\chat_ui\prototype
```

Open `http://localhost:8000` in a browser and allow camera access when prompted. Stop the server with `Ctrl+C`.

The camera preview is live, but the classification pipeline is not implemented or connected. Scan stages and result values are clearly marked as demonstrations; no video is stored or sent to a backend.
