# ONLYJOBS

Small resume-parsing and job-matching demo (Flask backend + static frontend).

## Requirements
- Python 3.8+
- Git (optional)

## Setup (recommended)
Run these from the project root.

Windows (PowerShell):

```powershell
python -m venv .venv
# If Activation is blocked, allow for current user once:
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Windows (one-off without activating):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe backend\app.py
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run the server
Activate the venv (or use the venv Python) and start the backend:

```powershell
cd backend
python app.py
```

Open your browser at http://127.0.0.1:5000

## Frontend
The frontend is static files in the `frontend` folder and served by the Flask app. You can also open `frontend/index.html` directly for quick view, but use the Flask server for API integration.

## Common troubleshooting
- If you see `ModuleNotFoundError`, ensure you're running Python from the project venv (use `.\.venv\Scripts\python.exe` or activate the venv before `python`).
- PowerShell activation blocked: run the `Set-ExecutionPolicy` command shown above.
- If using `spacy`, you may need to install a language model manually, for example:

```bash
python -m spacy download en_core_web_sm
```

## Notes
- Uploads are saved to the `uploads` folder (created automatically by the app).
- The app listens on port `5000` by default.

## License
This Project belongs to me 
