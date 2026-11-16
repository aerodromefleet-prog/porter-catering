Porter Catering Reports - Proper Version
==========================================

For testing on Porter Airline catering flights.

Login
-----
Username: gagan
Password: Aisxx2026

Features
--------
- Proper login
- Create catering flight: Flight Number, Date, Time
- Guard Name + Security License Number
- Upload multiple photos (documents + seals)
- View past flights and photos
- Mobile friendly

Email Setup (Required for automatic emails)
-------------------------------------------
1. Go to the Google Account for aerodromefleet@gmail.com
2. Enable 2-Step Verification if not already on
3. Create an App Password:
   - Google Account → Security → 2-Step Verification → App passwords
   - Generate one for "Mail"
4. Open app.py and replace YOUR_GMAIL_APP_PASSWORD with the 16-character app password

Emails will be sent to: report@security-ais.com
From: aerodromefleet@gmail.com

How to Run Locally (for testing)
--------------------------------
1. Install Flask:
   pip install flask

2. Set the App Password in app.py (see above)

3. Run:
   python app.py

4. On Gagan’s phone (same Wi-Fi), open:
   http://YOUR-COMPUTER-IP:5000


Next Step
---------
Once Gagan tests a few flights and it works as intended,
we can put it on a server and connect app.aerodromesecurity.com
