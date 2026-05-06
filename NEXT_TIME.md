# Voice Library Resume

Start the app from the repo root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_app.ps1
```

Start it in the background:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_app.ps1 -Background
```

Stop the app:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\stop_app.ps1
```

Open:

```text
http://127.0.0.1:5000
```

Current app entrypoints:

- `app/app.py` is the main Flask app.
- `app/templates/index.html` is the main UI.
- `app.py` at the repo root is the simple launcher.
