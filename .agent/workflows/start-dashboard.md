---
description: How to start the VVUSD Recruitment Dashboard
---

## Start the Dashboard

// turbo-all

1. Start the web server:
```bash
cd ~/Desktop/Recruitment && python3 serve_dashboard.py
```

2. Open your browser to http://localhost:8000

## Refresh Data (if roster files were updated)

1. Regenerate the dashboard data from the Excel files:
```bash
cd ~/Desktop/Recruitment && python3 generate_dashboard_data.py
```

2. Then start the server:
```bash
cd ~/Desktop/Recruitment && python3 serve_dashboard.py
```

3. Open your browser to http://localhost:8000

## Stop the Server

Press `Ctrl+C` in the terminal where the server is running.
