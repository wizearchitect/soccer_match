# Multi-PC Setup Guide

Run a soccer match across three machines on the same local network (LAN):

| Machine        | Role                          | Code folder needed |
|----------------|-------------------------------|--------------------|
| **PC 01-Pitch**   | Game server (PyGame + API)    | `pitch/`           |
| **PC 02-Blue01**  | Blue agent                    | `player/`          |
| **PC 03-Red01**   | Red agent                     | `player/`          |

> All three machines must be on the **same network** and able to reach
> **PC 01-Pitch** on TCP port **8000**.

---

## Prerequisites (every machine)

- Python 3.11 or higher
- The relevant code folder copied to that machine (see table above)
- For the player machines: an NVIDIA NIM API key (https://build.nvidia.com/)

You do **not** copy the whole project to every PC — only the folder that
machine needs. Each machine builds its own virtual environment; venvs cannot
be shared across machines.

> **Note on `.env.example` files:** Both `player/` and `team/` ship a
> `.env.example` template. Your real `.env` is **gitignored** and never copied
> with the code, so on each new machine you create it from the template:
>
> ```powershell
> copy .env.example .env      # Windows
> # cp .env.example .env      # macOS/Linux
> ```
>
> Then edit `.env` and fill in your values. What each file expects:
>
> | File              | Keys you set                                         |
> |-------------------|------------------------------------------------------|
> | `player/.env`     | `NVIDIA_API_KEY` only (server IP is set in the sidebar) |
> | `team/.env`       | `NVIDIA_API_KEY`, `PITCH_HOST`, `TEAM_COLOR`         |
>
> The `pitch/` server needs no API key; an `.env` there is optional (only for
> overriding `HOST`/`PORT`).

---

## PC 01-Pitch — The Game Server

1. Copy the `pitch/` folder to this machine.

2. Open a terminal in the `pitch/` folder and set up the environment:

   ```powershell
   python -m venv soccer_a
   soccer_a\Scripts\activate
   pip install -r requirements.txt
   ```

3. Start the server:

   ```powershell
   python -m pitch.main
   ```

   The PyGame window opens. The server binds to `0.0.0.0:8000`, so it
   accepts connections from other machines on the LAN.

4. **Find this PC's LAN IP address** — the player machines need it:

   ```powershell
   ipconfig
   ```

   Look for the "IPv4 Address" on your active adapter, e.g. `192.168.1.50`.
   Write it down; you'll enter it on PC 02 and PC 03.

5. **Allow inbound traffic on port 8000.** Windows Firewall will usually
   prompt the first time — click "Allow access" on Private networks. If it
   doesn't prompt, add a rule manually:

   ```powershell
   netsh advfirewall firewall add rule name="Pitch 8000" dir=in action=allow protocol=TCP localport=8000
   ```

6. Leave this running. Press **Spacebar** in the PyGame window to start the
   match once both players have connected.

---

## PC 02-Blue01 — Blue Player

1. Copy the `player/` folder to this machine.

2. Open a terminal in the `player/` folder and set up the environment:

   ```powershell
   python -m venv soccer_a
   soccer_a\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create your `.env` from the template and add your API key:

   ```powershell
   copy .env.example .env
   ```

   Edit `.env` and set:

   ```
   NVIDIA_API_KEY=your-actual-api-key-here
   ```

4. Launch the dashboard:

   ```powershell
   streamlit run app.py
   ```

5. In the browser sidebar:
   - **Server IP** → the LAN IP of PC 01-Pitch (e.g., `192.168.1.50`)
   - **Team** → `Blue`
   - **Position** → e.g., `Striker`
   - **Agent Name** → e.g., `Blue01`
   - Click **Start Auto-Play**

   The Blue agent appears on the pitch immediately.

---

## PC 03-Red01 — Red Player

Identical to PC 02, except choose the Red team.

1. Copy the `player/` folder to this machine.

2. Set up the environment in the `player/` folder:

   ```powershell
   python -m venv soccer_a
   soccer_a\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create `.env` and add your API key:

   ```powershell
   copy .env.example .env
   ```

   ```
   NVIDIA_API_KEY=your-actual-api-key-here
   ```

4. Launch the dashboard:

   ```powershell
   streamlit run app.py
   ```

5. In the browser sidebar:
   - **Server IP** → the LAN IP of PC 01-Pitch (e.g., `192.168.1.50`)
   - **Team** → `Red`
   - **Position** → e.g., `Striker`
   - **Agent Name** → e.g., `Red01`
   - Click **Start Auto-Play**

---

## Start the Match

Once both Blue01 and Red01 show up on the pitch, go to **PC 01-Pitch** and
press **Spacebar** in the PyGame window. Kicks are disabled until the match
starts; players can move around during the warm-up "Waiting" state.

## Scoreboard

From any machine on the network, open a browser to:

```
http://<PC 01-Pitch IP>:8000/scoreboard
```

For example: `http://192.168.1.50:8000/scoreboard`

---

## Using Full Teams Instead of Single Players

To run a full 5-agent team (1 Coach + 4 Players) on PC 02 / PC 03 instead of
a single player, copy the `team/` folder to that machine and:

```powershell
cd team
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Then edit `team/.env` and set:

```
NVIDIA_API_KEY=your-actual-api-key-here
PITCH_HOST=192.168.1.50        # the LAN IP of PC 01-Pitch
TEAM_COLOR=Blue                # or Red on the other machine
```

Run it:

```powershell
python main.py
```

> Difference from single player: the **team** reads `PITCH_HOST` from `.env`,
> while the **single player** sets the server IP in the Streamlit sidebar.

---

## Troubleshooting

- **Player can't connect / connection errors** — Confirm the Server IP in the
  sidebar matches PC 01-Pitch's current LAN IP (it can change after a reboot
  if using DHCP). Verify port 8000 is allowed through PC 01's firewall.
- **Works on localhost but not across PCs** — Almost always a firewall rule on
  PC 01-Pitch. Re-check step 5 under PC 01.
- **"NVIDIA_API_KEY is not configured"** — The player/team `.env` on that
  machine is missing or has an empty key.
- **Different subnets / Wi-Fi isolation** — Guest networks and some corporate
  Wi-Fi block PC-to-PC traffic. Put all three machines on the same router /
  VLAN.
