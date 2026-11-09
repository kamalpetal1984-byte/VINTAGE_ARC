VINTAGE — READY-TO-DEPLOY STARTER
================================

FEATURES
- Member/admin login using name + shared access code
- Shared global feed, posts, likes and comments
- 24-hour stories (text only)
- Member profiles and bios
- Account-to-account private text messages with automatic refresh
- Admin dashboard and post deletion
- Emerald + obsidian responsive design

IMPORTANT SECURITY NOTE
A shared member code is an INVITE CODE, not personal identity verification.
If everyone uses the same code and login asks only for a name, another person
could try to claim someone else's name. For a real public community, add
individual passwords or email/OTP verification before inviting people.
Never publish your admin code. Set both codes as private environment variables.
The starter stores access codes only in the hosting environment, not in source.

DEPLOY (Render + Neon; no Firebase)
1. Create a GitHub repository named vintage-social.
2. Upload all files/folders from this ZIP to that repository.
3. Create a PostgreSQL project/database at Neon.
4. Copy its pooled or direct connection string. It must start with
   postgresql:// and include sslmode=require.
5. In Render, choose New > Web Service and connect your GitHub repository.
6. Runtime: Python. Build command: pip install -r requirements.txt
   Start command: gunicorn app:app
7. In Render > Environment, add:
   SECRET_KEY = a long random string (at least 32 random characters)
   DATABASE_URL = your Neon connection string
   MEMBER_CODE = SP2413
   ADMIN_CODE = SP165
8. Deploy. Open the Render URL on phone/computer from anywhere.

FREE PLAN WARNING
Free hosting/database plans can sleep, have usage limits, and may change.
Check current provider limits before relying on it for important data.
For always-on use, a paid plan may be required.

LOCAL TEST (optional)
1. Install Python 3.11+.
2. Open terminal in this folder.
3. Run: py -m venv .venv
4. Windows: .venv\\Scripts\\activate
5. Run: pip install -r requirements.txt
6. Run: set MEMBER_CODE=SP2413
   set ADMIN_CODE=SP165
   set SECRET_KEY=some-long-random-secret
   set DATABASE_URL=sqlite:///vintage.db
7. Run: python app.py
8. Open http://127.0.0.1:5000

LIMITATIONS IN THIS FIRST VERSION
- Stories are text-only; expiry is filtered to the latest 24 hours.
- Reels/video upload, image upload, voice/video calls, push notifications,
  and end-to-end encryption are not implemented.
- Chat refreshes every 3 seconds; it is not WebSocket-based live chat.
- Shared invite codes do not provide individual account ownership.
- Add backups and moderation before inviting a large public group.
