"""
    Code adapted from https://github.com/amardikamahdi/qobuz-dl
"""
import logging
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from qobuz.bundle import Bundle
from qobuz import qopy

logger = logging.getLogger(__name__)


class QobuzOAuth:
    def __init__(self):
        self.client = None
        self.app_id = None
        self.secrets = None
        self.private_key = None
        self.oauth_user_id = None
        self.oauth_user_auth_token = None

    def initialize_client_with_oauth(self, code, app_id, secrets, private_key):
        self.client = qopy.Client()
        self.client._prepare_connect(app_id, secrets)
        usr_info = self.client.login_with_oauth_code(code, private_key)
        self.oauth_user_id = usr_info.get("user", {}).get("id")
        self.oauth_user_auth_token = usr_info.get("user_auth_token")

    def get_tokens(self):
        bundle = Bundle()
        self.app_id = bundle.get_app_id()
        self.secrets = [secret for secret in bundle.get_secrets().values() if secret]
        self.private_key = bundle.get_private_key() or ""

    def handle_oauth_login(self, code=None):
        """
        Authenticate with OAuth

        On success, the calling tool is responsible for saving the elements necessary for a future login.
        Typically :
            - self.oauth_user_auth_token
            - self.oauth_user_id
            - self.app_id
            - self.secrets
            - self.private_key
        """
        self.get_tokens()

        if not code:
            # Find available port
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", 0))
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                port = s.getsockname()[1]

            oauth_url = (
                f"https://www.qobuz.com/signin/oauth"
                f"?ext_app_id={self.app_id}"
                f"&redirect_url=http://localhost:{port}"
            )

            class OAuthHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    parsed = urlparse(self.path)
                    params = parse_qs(parsed.query)
                    auth_code = params.get(
                        "code", [params.get("code_autorisation", [""])[0]]
                    )[0]
                    if auth_code:
                        OAuthHandler.auth_code = auth_code
                        self.send_response(200)
                        self.send_header("Content-type", "text/html")
                        self.end_headers()
                        self.wfile.write(
                            b"<html><body style='font-family:system-ui;text-align:center;padding:60px'><h2>Login successful</h2><p>You can close this tab and return to your terminal.</p></body></html>"
                        )
                    else:
                        self.send_response(400)
                        self.end_headers()
                        self.wfile.write(
                            b"<html><body><h2>Login failed</h2></body></html>"
                        )

                def log_message(self, format, *args):
                    pass

            OAuthHandler.auth_code = None

            print("Open this URL in your browser to authenticate with Qobuz:")
            print(f"    {oauth_url}")
            print(
                f"A local server on port {port} will capture the OAuth code automatically."
            )

            server = HTTPServer(("127.0.0.1", port), OAuthHandler)
            thread = threading.Thread(target=server.handle_request)
            thread.start()

            input("Press Enter after completing login in your browser...")

            server.server_close()
            thread.join()

            if OAuthHandler.auth_code:
                code = OAuthHandler.auth_code
            else:
                print("FAILED: No OAuth code received. Please try again.")
                return False
        else:
            if "code" in code or "code_autorisation" in code:
                parsed = urlparse(code)
                params = parse_qs(parsed.query)
                code = params.get("code", [params.get("code_autorisation", [""])[0]])[0]

        if not code:
            print("FAILED: No OAuth code found in the provided URL")
            return False

        if not hasattr(self, "client") or self.client is None:
            print("Refreshing app_id and secrets...")
            self.get_tokens()

        self.initialize_client_with_oauth(
            code, self.app_id, self.secrets, self.private_key
        )
        print("OAuth login infos successful!")
        return True
