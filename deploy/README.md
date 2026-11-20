# AgriGuard Demo — Deploy Guide

**OS detected: Windows.** All scripts are PowerShell (`.ps1`).

---

## What the scripts do

| File | Purpose |
|---|---|
| `start-demo.ps1` | Installs deps → starts backend + AI + proxy → health-checks → opens tunnel → prints public link |
| `stop-demo.ps1` | Cleanly kills every process started above |
| `rebuild-and-start.ps1` | Same as start, but rebuilds the Expo web bundle first (use after frontend code changes) |
| `proxy.js` | Node.js reverse-proxy: serves `frontend/dist/`, routes `/api/v1/*` and `/api/ai/*` |

---

## First-time setup (do this once, before demo day)

### 1. Allow PowerShell scripts to run
Open PowerShell **as Administrator** and run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Say **Y** when prompted.

### 2. Install Node.js (if not already installed)
Download from https://nodejs.org (LTS version).  
Verify: `node --version` should print v18 or higher.

### 3. Install Python (if not already installed)
Download from https://python.org (3.10 or higher).  
**Tick "Add Python to PATH"** during install.  
Verify: `python --version`

### 4. cloudflared (tunnel — no account needed)
The start script **auto-downloads** `cloudflared.exe` on first run.  
If it fails (no internet during first run), download manually:

```
https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
```
Save it as `AGRIGUARD\deploy\cloudflared.exe`.

### 5. Test everything locally before demo day
```powershell
cd "C:\Users\PC\Pictures\Screenshots\AGRIGUARD"
.\deploy\start-demo.ps1
```
You should see a `https://xxxx.trycloudflare.com` link printed at the end.  
Open it in a browser and confirm the app loads.

---

## Everyday start command

Open PowerShell, navigate to the project root, run:

```powershell
cd "C:\Users\PC\Pictures\Screenshots\AGRIGUARD"
.\deploy\start-demo.ps1
```

That is the only command you need.  
The public link is printed at the end. Share it with your audience.

## Stop command

```powershell
.\deploy\stop-demo.ps1
```

---

## Getting a new public link

The Cloudflare Quick Tunnel link changes every time you restart.

```powershell
.\deploy\stop-demo.ps1
.\deploy\start-demo.ps1
```

A fresh `https://xxxx.trycloudflare.com` link is printed at the end.

---

## Ports used

| Service | Port | What it does |
|---|---|---|
| Backend FastAPI | 8000 | Farmer data, auth, reports, alerts |
| AI FastAPI | 5000 | Pest detection, ask assistant |
| Node proxy | 3000 | Serves frontend + routes API calls |
| Cloudflare tunnel | — | Maps a public https:// URL → port 3000 |

---

## Service start commands (manual / debugging)

If you need to start services one by one:

**Backend:**
```powershell
cd "C:\Users\PC\Pictures\Screenshots\AGRIGUARD\backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive docs: http://localhost:8000/docs

**AI service:**
```powershell
cd "C:\Users\PC\Pictures\Screenshots\AGRIGUARD"
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000
```
Interactive docs: http://localhost:5000/docs

**Proxy:**
```powershell
cd "C:\Users\PC\Pictures\Screenshots\AGRIGUARD\deploy"
node proxy.js
```

**Tunnel only (after services are up):**
```powershell
.\deploy\cloudflared.exe tunnel --url http://localhost:3000 --no-autoupdate
```

---

## Creating demo data (real data through the app)

The database starts empty. Here is how to create real demo records before your presentation:

### Create a farmer account
1. Open the app (public link or `http://localhost:3000`).
2. Tap **Register**.
3. Enter:
   - **Full name:** any name (e.g. `Demo Farmer`)
   - **Phone number:** any Rwandan format (e.g. `+250788000001`)
   - **Password:** at least 6 characters
   - **District:** `Musanze` (or any real Rwanda district)
   - **Sector:** `Muhoza`
4. Tap **Register** — you are now logged in.

### Submit a crop report (to test AI)
1. From the Home screen, tap **Report a Problem**.
2. Step 1 — pick **Maize**.
3. Step 2 — select symptoms: `yellowing_leaves`, `holes_in_leaves`. Add description: `I see small worms eating my maize leaves`.
4. Step 3 — skip the photo (tap Next) or upload any plant photo from your gallery.
5. Step 4 — confirm location (Musanze / Muhoza pre-filled) and tap **Submit**.
6. The AI result card appears with the detected pest, severity, and recommendations.

### Try the Ask AgriGuard chat
1. Tap the **Ask** tab.
2. Type: `How do I treat Fall Armyworm on maize?`
3. The AI assistant responds in English. Switch language to Kinyarwanda and ask again.

### View the demo without a real account
The welcome screen has an **Explore Interactive Demo** button — this loads sample data without any network calls. Use this if the backend is not running.

---

## Demo Day Checklist ✅

### The night before

- [ ] Run `.\deploy\start-demo.ps1` and confirm the public link works in a browser.
- [ ] Create the demo farmer account and submit one report (steps above) so the app is not empty.
- [ ] Confirm the AI result card appears with a pest name and recommendations.
- [ ] Stop everything with `.\deploy\stop-demo.ps1`.

### Demo day — before you present

- [ ] **Plug in your laptop charger.** The tunnel dies if the laptop sleeps.
- [ ] Open **Power Options → Sleep → Never** (while plugged in):
  - Win+S → "Power & sleep settings" → "Screen" = 15 min, **"Sleep" = Never**.
- [ ] Disable Windows Update forced restarts:
  - Win+S → "Windows Update" → pause updates for 7 days.
- [ ] Run `.\deploy\start-demo.ps1`.
- [ ] Copy the printed `https://xxxx.trycloudflare.com` link.
- [ ] Open it on your laptop AND on your phone to confirm it works on both.
- [ ] Keep the PowerShell windows open in the background — do not close them.

### During the demo

- Open the public link on your phone and hand it to judges.
- Share the link on the presentation slide or in the chat.
- The **Explore Interactive Demo** button on the welcome screen works fully offline (no backend needed) — use it as a fallback if the connection drops.

### If the link dies mid-demo

The Cloudflare tunnel occasionally disconnects on slow or switching Wi-Fi.

```powershell
# Stop everything
.\deploy\stop-demo.ps1

# Restart — a new link is printed in ~30 seconds
.\deploy\start-demo.ps1
```

Share the new link with your audience. The database (SQLite file `backend/agriguard.db`) is preserved — all previously created accounts and reports are still there.

### If a port is already in use

The stop script kills processes by port. If it misses one:
```powershell
# Find and kill manually:
netstat -ano | findstr :8000
Stop-Process -Id <PID shown above> -Force
```
Then run `start-demo.ps1` again.

---

## Known limitations

- **The public link changes on every restart.** This is a free Quick Tunnel — no static domain. For a permanent URL, use a paid Cloudflare tunnel plan or deploy to Render/Railway.
- **SQLite database** is local. All data disappears if you delete `backend/agriguard.db`. Back it up before demo day.
- **AI runs in mock mode** by default (`AI_MODE=mock`). Results are deterministic and labelled "Diagnosis Pending" in the UI. To use real OpenAI vision, add `OPENAI_API_KEY=sk-...` and `AI_MODE=openai` to the root `.env`.
- **Neo4j is optional.** The backend uses an in-memory fallback automatically when Neo4j is not running. This is fine for the demo.
- **Image uploads** save to `backend/app/static/uploads/` on disk. They are served through the proxy at `/uploads/*`.
- **USSD / IVR** screens are interactive simulators — they do not connect to real telecoms infrastructure.
- **No refresh-token support.** JWTs expire after 24 hours (set by `ACCESS_TOKEN_EXPIRE_MINUTES=1440`). If a session expires during the demo, log out and log back in.

---

## File layout of this deploy/ folder

```
deploy/
├── proxy.js              — Node reverse-proxy (no npm install needed — pure stdlib)
├── start-demo.ps1        — Start everything + print public link
├── stop-demo.ps1         — Clean shutdown
├── rebuild-and-start.ps1 — Rebuild Expo web bundle then start
├── README.md             — This file
├── cloudflared.exe       — Downloaded automatically on first run
├── tunnel.log            — Cloudflare tunnel output (auto-created)
├── .tunnel.pid           — PID of tunnel process (auto-created)
└── .last-url.txt         — Last printed public URL (auto-created)
```
