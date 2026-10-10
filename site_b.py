# ==========================================
# SameSite Lax+POST 2-Minute Grace Period & Cookie-Refresh Hypothesis Tester
# PoC by RivenX173
# ==========================================
from http.server import HTTPServer, BaseHTTPRequestHandler
import time
import secrets
import sys
import traceback
from urllib.parse import urlparse, parse_qs

class QuietHTTPServer(HTTPServer):
    def handle_error(self, request, client_address):
        exc_type = sys.exc_info()[0]
        if exc_type in (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            return
        traceback.print_exc()

state = {
    'first_set_at': None,
    'last_set_at': None,
    'refresh_count': 0,
    'last_value': None
}

def extract_cookie_value(cookies_header, name):
    if not cookies_header:
        return None
    for part in cookies_header.split(';'):
        part = part.strip()
        if part.startswith(name + '='):
            return part[len(name) + 1:]
    return None

class Handler(BaseHTTPRequestHandler):
    def address_string(self):
        return self.client_address[0]

    def do_GET(self):
        if self.path.startswith('/favicon.ico'):
            self.send_response(204)
            self.end_headers()
            return

        if self.path.startswith('/reset'):
            state['first_set_at'] = None
            state['last_set_at'] = None
            state['refresh_count'] = 0
            state['last_value'] = None

            if '?close=1' in self.path:
                self.send_response(200)
                self.send_header('Set-Cookie', 'test=; Path=/; Max-Age=0')
                self.end_headers()
                return

            self.send_response(302)
            self.send_header('Location', '/')
            self.send_header('Set-Cookie', 'test=; Path=/; Max-Age=0')
            self.end_headers()
            return

        now = time.time()
        parsed = urlparse(self.path)
        query_params = parse_qs(parsed.query)

        force_refresh = 'refresh' in query_params and query_params['refresh'][0] == '1'

        cookies_header = self.headers.get('Cookie')
        has_test_cookie = extract_cookie_value(cookies_header, 'test') is not None

        if not has_test_cookie and not force_refresh:
            state['first_set_at'] = None
            state['last_set_at'] = None
            state['refresh_count'] = 0
            state['last_value'] = None

        if force_refresh and not has_test_cookie:
            self.send_response(403)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Forbidden: No cookie exists to refresh.")
            return

        if state['last_set_at'] is not None and not force_refresh:
            browser_value = extract_cookie_value(cookies_header, 'test')
            cookie_value = browser_value if browser_value is not None else state['last_value']
            age_since_first = now - state['first_set_at'] if state['first_set_at'] is not None else None
            age_since_last = now - state['last_set_at']
            event = "Cookie preserved (no refresh)"
            refresh_count = state['refresh_count']
            set_cookie_header = None
            cookie_was_set = False
        else:
            new_value = secrets.token_hex(8)
            if state['first_set_at'] is None:
                state['first_set_at'] = now
                event = "FIRST ISSUE"
            else:
                state['refresh_count'] += 1
                event = f"REFRESH #{state['refresh_count']}"
            state['last_set_at'] = now
            state['last_value'] = new_value
            cookie_value = new_value
            age_since_first = now - state['first_set_at']
            age_since_last = 0.0
            refresh_count = state['refresh_count']
            set_cookie_header = f'test={new_value}; Path=/'
            cookie_was_set = True

        print("=" * 60)
        if not cookie_was_set:
            print("[KEEP] Cookie 'test' preserved")
        elif state['refresh_count'] == 0:
            print("[Initial] Cookie 'test' created")
        else:
            print("[SET] Cookie 'test' (re)issued")

        print(f"  Cookie value                 : {cookie_value}")
        if age_since_first is not None:
            print(f"  Time since FIRST ever issued : {age_since_first:.1f}s")
        if age_since_last is not None:
            print(f"  Time since LAST (re)issued   : {age_since_last:.1f}s")
        print(f"  Set-Cookie header sent?      : {'Yes' if set_cookie_header else 'No'}")
        print("=" * 60)

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        if set_cookie_header:
            self.send_header('Set-Cookie', set_cookie_header)
        self.end_headers()

        if not cookie_was_set:
            status_msg = "Cookie preserved. No new cookie was issued."
        elif state['refresh_count'] == 0:
            status_msg = "Initial cookie created (First time since Site B started)."
        else:
            status_msg = "A new cookie was just issued (Refreshed)."

        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Site B - Target</title>
            <style>
                * {{ margin:0; padding:0; box-sizing:border-box; }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: #f0f2f5; padding: 40px 20px;
                    display: flex; justify-content: center; align-items: center;
                    min-height: 100vh;
                }}
                .container {{
                    background: white; max-width: 700px; padding: 40px;
                    border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                    border: 1px solid #e0e0e0;
                }}
                h1 {{ color: #1a1a1a; font-size: 28px; margin-bottom: 10px; }}
                .badge {{
                    display: inline-block; background: #4B0082; color: white;
                    font-size: 14px; padding: 4px 14px; border-radius: 20px;
                    font-weight: 600; margin-bottom: 20px;
                }}
                .btn {{
                    color: white; font-size: 16px;
                    padding: 10px 22px; border: none; border-radius: 8px;
                    cursor: pointer; font-weight: bold; margin-top: 10px;
                    transition: background 0.2s; text-decoration: none;
                    display: inline-block;
                }}
                .refresh-btn {{
                    background-color: #4B0082;
                }}
                .refresh-btn:disabled {{ background-color: #c9c9c9; cursor: not-allowed; }}
                .refresh-btn:not(:disabled):hover {{ background-color: #6A0DAD; }}
                .reset-btn {{
                    background-color: #c62828;
                }}
                .reset-btn:hover {{ background-color: #b71c1c; }}
                .sitea-btn {{
                    background-color: #0056b3;
                }}
                .sitea-btn:hover {{ background-color: #004494; }}
                .close-btn {{
                    background-color: #424242;
                }}
                .close-btn:hover {{ background-color: #212121; }}
                .color-refresh {{ color: #4B0082; }}
                .color-reset {{ color: #c62828; }}
                .color-sitea {{ color: #0056b3; }}
                p {{ color: #333; font-size: 16px; line-height: 1.6; margin: 12px 0; }}
                .timing-box {{
                    background: #fff8e1; border: 1px solid #ffca28;
                    padding: 14px 18px; border-radius: 6px;
                    font-family: monospace; font-size: 14px; margin: 16px 0;
                }}
                .cookie-box {{
                    background: #e8f5e9; border: 1px solid #a5d6a7;
                    padding: 12px 18px; border-radius: 6px;
                    font-family: monospace; font-size: 15px; margin: 12px 0;
                }}
                .note {{
                    font-size: 14px; color: #777; margin-top: 10px;
                    line-height: 1.6;
                }}
                .note p {{
                    margin-bottom: 8px;
                }}
                .poc-credit {{
                    position: fixed; bottom: 10px; right: 10px; color: #888;
                    font-size: 12px; font-family: sans-serif;
                    background: rgba(255,255,255,0.9); padding: 5px 14px;
                    border-radius: 4px; border: 1px solid #ddd;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.08); user-select: none;
                }}
                hr {{ border: none; border-top: 1px solid #e0e0e0; margin: 20px 0; }}
                .status-msg {{
                    font-size: 18px; font-weight: bold; margin: 12px 0;
                    color: {'#2e7d32' if not cookie_was_set else '#c62828'}
                }}
                .button-group {{
                    display: flex;
                    gap: 10px;
                    flex-wrap: wrap;
                    justify-content: center;
                    margin: 10px 0;
                }}
                .button-group .btn {{
                    margin-top: 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <span class="badge">[ Target ]</span>
                <h1>Site B</h1>
                <p>This site owns the cookie that we want to test.</p>
                <hr>
                <div class="status-msg">{status_msg}</div>
                <div class="cookie-box">
                    Current cookie value (as stored in browser): <strong>test={cookie_value}</strong> (Domain: localhost)<br>
                    <span style="font-size:12px; color:#666;">Check F12 -> Application -> Cookies: the value should match this exactly.</span>
                </div>

                <div id="timers" class="timing-box" style="font-size:16px; line-height:1.9;">
                    <div>Since FIRST ever issued: <strong id="t-first">0.0s</strong> <span id="s-first" style="font-weight:bold;"></span></div>
                    <div>Since LAST (re)issued: <strong id="t-last">0.0s</strong> <span id="s-last" style="font-weight:bold;"></span></div>
                    <div style="font-size:13px; color:#777; margin-top:6px;">
                        <strong>Grace period</strong> = 120.0s (2 minutes).<br><br>
                        <strong>within 2 min (since LAST (re)issued)</strong> -> Ready for first scenario.<br>
                        - Use the <strong class="color-refresh">"Send Normal Cross-Site POST request"</strong> button on <strong class="color-sitea">Site A</strong>.<br><br>
                        <strong>past 2 min (since FIRST ever issued)</strong> -> Ready for second scenario (test if refresh resets the grace period).<br>
                        - Use the <strong class="color-refresh">"Refresh Cookie & Send Cross-Site POST request"</strong> button on <strong class="color-sitea">Site A</strong>.<br>
                        - Or: Click <strong class="color-refresh">"Refresh Cookie Now"</strong> on this site, then use <strong class="color-refresh">"Send Normal Cross-Site POST request"</strong> on <strong class="color-sitea">Site A</strong>.
                    </div>
                </div>

                <div class="button-group">
                    <button id="refresh-btn" class="btn refresh-btn" onclick="refreshCookie();">
                        Refresh Cookie Now
                    </button>
                    <a href="/reset" class="btn reset-btn">
                        Clear & Reset
                    </a>
                    <form action="http://127.0.0.1:8000/" method="GET">
                        <button type="submit" class="btn sitea-btn">
                            Go to Site A
                        </button>
                    </form>
                    <button class="btn close-btn" onclick="closeSite()">
                        Close the Site & Go to Site A
                    </button>
                </div>

                <div class="note">
                    <p>The <strong class="color-refresh">Refresh Cookie</strong> button issues a brand-new random value and resets the "LAST (re)issued" counter (but keeps tracking "FIRST ever issued" from the very beginning).</p>
                    <p>The <strong class="color-reset">Clear & Reset</strong> button erases Site B's memory of the cookie history, deletes the existing cookie, refreshes the page, and resets all time counters (both FIRST and LAST issuance timers) to zero.</p>
                    <p>The <strong style="color: #424242;">Close the Site & Go to Site A</strong> button wipes all cookie data, clears Site B memory, and moves you to a Site A. This is ideal if you want to test a cross-site POST request from Site A when absolutely no cookies exist.</p>
                </div>
            </div>
            <div class="poc-credit">PoC by RivenX173</div>

            <script>
                let elapsedFirst = {age_since_first if age_since_first is not None else 'null'};
                let elapsedLast = {age_since_last if age_since_last is not None else 'null'};
                const THRESHOLD = 120.0;
                const refreshBtn = document.getElementById('refresh-btn');

                function paint() {{
                    if (elapsedFirst !== null) {{
                        document.getElementById('t-first').textContent = elapsedFirst.toFixed(1) + 's';
                        const sFirst = document.getElementById('s-first');
                        if (elapsedFirst < THRESHOLD) {{
                            sFirst.textContent = 'FRESH';
                            sFirst.style.color = '#2e7d32';
                        }} else {{
                            sFirst.textContent = 'EXPIRED';
                            sFirst.style.color = '#c62828';
                        }}
                    }} else {{
                        document.getElementById('t-first').textContent = 'N/A';
                        document.getElementById('s-first').textContent = '';
                    }}

                    if (elapsedLast !== null) {{
                        document.getElementById('t-last').textContent = elapsedLast.toFixed(1) + 's';
                        const sLast = document.getElementById('s-last');
                        if (elapsedLast < THRESHOLD) {{
                            sLast.textContent = 'FRESH';
                            sLast.style.color = '#2e7d32';
                        }} else {{
                            sLast.textContent = 'EXPIRED';
                            sLast.style.color = '#c62828';
                        }}
                    }} else {{
                        document.getElementById('t-last').textContent = 'N/A';
                        document.getElementById('s-last').textContent = '';
                    }}
                }}

                paint();
                setInterval(() => {{
                    if (elapsedFirst !== null) elapsedFirst += 1;
                    if (elapsedLast !== null) elapsedLast += 1;
                    paint();
                }}, 1000);

                function refreshCookie() {{
                    document.getElementById('refresh-btn').disabled = true;
                    window.location.href = '/?refresh=1';
                }}

                async function closeSite() {{
                    document.cookie = "test=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                    try {{
                        await fetch('/reset?close=1');
                    }} catch (e) {{}}
                    window.location.href = 'http://127.0.0.1:8000/';
                }}
            </script>
        </body>
        </html>
        '''
        self.wfile.write(html.encode())

    def do_POST(self):
        if self.path != '/receive':
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
            return

        now = time.time()
        cookies = self.headers.get('Cookie')
        has_test_cookie = extract_cookie_value(cookies, 'test') is not None

        age_since_first = (now - state['first_set_at']) if state['first_set_at'] is not None else None
        age_since_last = (now - state['last_set_at']) if state['last_set_at'] is not None else None

        print("=" * 60)
        print("Received cross-site POST request from Site A")
        print(f"  Cookie header received       : {cookies}")
        print(f"  Does it contain 'test='?     : {'Yes' if has_test_cookie else 'No'}")
        print(f"  Age since FIRST ever issued   : {age_since_first:.1f}s" if age_since_first is not None else "  Age since FIRST ever issued   : N/A")
        print(f"  Age since LAST (re)issued     : {age_since_last:.1f}s" if age_since_last is not None else "  Age since LAST (re)issued     : N/A")
        print("=" * 60)

        if has_test_cookie:
            result_title = 'Cookie "test" was sent!'
            result_desc = 'The browser sent the "test" cookie with the cross-site POST request.'
            color = '#2e7d32'
            bg = '#e8f5e9'
            icon = '[OK]'
        else:
            result_title = 'Cookie "test" was NOT sent'
            result_desc = 'The browser did NOT send the "test" cookie with the cross-site POST request.'
            color = '#c62828'
            bg = '#ffebee'
            icon = '[X]'

        if has_test_cookie:
            if age_since_first is not None and age_since_first > 120:
                verdict = (
                    "The cookie was sent even though it's been over 2 minutes since it was "
                    "<strong>FIRST</strong> issued. "
                    "This suggests that refreshing the cookie resets the 2-minute grace period."
                )
            else:
                verdict = (
                    "The cookie is still within the first 2 minutes since it was FIRST ever issued. "
                    "Therefore, the first scenario (sending the cookie within the initial 2-minute grace period) "
                    "is expected to succeed, regardless of whether the cookie was refreshed or not. "
                    "However, the second scenario (testing whether changing the cookie value while keeping its name "
                    "resets the 120-second grace period for cross-site POST requests) cannot be properly evaluated yet. "
                    "To test this, you must wait until the FIRST ever issued timer exceeds 120 seconds, "
                    "then perform the refresh attack and check if the cookie is still sent."
                )
        else:
            if age_since_last is not None and age_since_last < 120 and age_since_first is not None and age_since_first > 120:
                verdict = (
                    "The cookie was blocked even though it's been less than 2 minutes since it was "
                    "<strong>LAST</strong> (re)issued, and it's been over 2 minutes since it was "
                    "<strong>FIRST</strong> issued. This indicates that the browser uses the original "
                    "creation time (not the refresh time) for the 2-minute Lax+POST grace period. "
                    "(Or you tampered with the cookies in the browser. Nice try, but that breaks the test.) "
                    "or the browser blocked it because Chrome finally decided to remove the 2-minute grace period."
                )
            elif age_since_first is None:
                verdict = "You forgot to visit Site B first to create the initial cookie."
            elif age_since_first is not None and age_since_first > 120:
                verdict = "The cookie was blocked, consistent with it simply being older than 2 minutes. (Or you tampered with the cookies in the browser. Nice try, but that breaks the test.)"
            else:
                verdict = (
                    "The cookie was NOT sent, even though it's still within the 2-minute grace period. "
                    "That's... odd. Either you tampered with the cookies in the browser (Nice try, but that breaks the test.) "
                    "or the browser blocked it because Chrome finally decided to remove the 2-minute grace period."
                )

        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Site B - Result</title>
            <style>
                * {{ margin:0; padding:0; box-sizing:border-box; }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: #f0f2f5; padding: 40px 20px;
                    display: flex; justify-content: center; align-items: center;
                    min-height: 100vh;
                }}
                .container {{
                    background: white; max-width: 720px; padding: 40px;
                    border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                    border: 1px solid #e0e0e0; text-align: center;
                }}
                .result-box {{
                    background: {bg}; border: 2px solid {color};
                    padding: 20px; border-radius: 10px; margin: 20px 0;
                }}
                .result-title {{ font-size: 28px; font-weight: bold; color: {color}; margin-bottom: 8px; }}
                .result-desc {{ font-size: 18px; color: #333; margin: 8px 0; }}
                .timing-box {{
                    background: #fff8e1; border: 1px solid #ffca28;
                    padding: 14px 18px; border-radius: 6px;
                    font-family: monospace; font-size: 14px; margin: 16px 0; text-align: left;
                }}
                .verdict {{
                    font-size: 16px; color: #1a1a1a; background: #f8f9fa;
                    padding: 14px; border-radius: 6px; margin: 16px 0;
                    border: 1px solid #e0e0e0; text-align: left;
                }}
                .poc-credit {{
                    position: fixed; bottom: 10px; right: 10px; color: #888;
                    font-size: 12px; font-family: sans-serif;
                    background: rgba(255,255,255,0.9); padding: 5px 14px;
                    border-radius: 4px; border: 1px solid #ddd;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.08); user-select: none;
                }}
                hr {{ border: none; border-top: 1px solid #e0e0e0; margin: 20px 0; }}
                .badge {{
                    display: inline-block; background: #4B0082; color: white;
                    font-size: 14px; padding: 4px 14px; border-radius: 20px;
                    font-weight: 600; margin-bottom: 16px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <span class="badge">[ Result ]</span>
                <div class="result-box">
                    <div class="result-title">{icon} {result_title}</div>
                    <div class="result-desc">{result_desc}</div>
                </div>
                <div class="timing-box">
                    Age since FIRST ever issued: <strong>{f"{age_since_first:.1f}s" if age_since_first is not None else "N/A"}</strong><br>
                    Age since LAST (re)issued: <strong>{f"{age_since_last:.1f}s" if age_since_last is not None else "N/A"}</strong>
                </div>
                <div class="verdict">
                    <strong>What this suggests:</strong><br>{verdict}
                </div>
                <hr>

                <div style="display: flex; gap: 10px; justify-content: center; margin-top: 20px;">
                    <form action="http://127.0.0.1:8000/" method="GET">
                        <button type="submit" style="background-color: #0056b3; color: white; font-size: 16px; padding: 10px 22px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">Back to Site A</button>
                    </form>
                    <form action="/" method="GET">
                        <button type="submit" style="background-color: #4B0082; color: white; font-size: 16px; padding: 10px 22px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">Go to Site B</button>
                    </form>
                </div>
            </div>
            <div class="poc-credit">PoC by RivenX173</div>
        </body>
        </html>
        '''

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

print("Server B (Cookie Owner) running on http://localhost:9000")
print("PoC by RivenX173")
QuietHTTPServer(('localhost', 9000), Handler).serve_forever()