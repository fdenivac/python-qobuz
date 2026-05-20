"""
    Code adapted from https://github.com/amardikamahdi/qobuz-dl

    Wrapper for Qo-DL Reborn. This is a sligthly modified version
    of qopy, originally written by Sorrow446. All credits to the
    original author.
"""

import base64
import hashlib
import logging
import time

import requests
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

RESET = "Reset your credentials with 'myqobuz.py authenticate'"

API_URL = "https://www.qobuz.com/api.json/0.2/"

log = logging.getLogger(__name__)


class AuthenticationError(Exception):
    pass


class IneligibleError(Exception):
    pass


class InvalidAppIdError(Exception):
    pass


class InvalidAppSecretError(Exception):
    pass


class InvalidQuality(Exception):
    pass


def _extract_error_payload(response):
    try:
        payload = response.json()
        if isinstance(payload, dict):
            return payload
    except ValueError:
        pass
    return {}


def _categorize_api_failure(epoint, status_code, api_message):
    msg = (api_message or "").lower()
    catalog_endpoints = {
        "album/get",
        "track/get",
        "playlist/get",
        "artist/get",
        "label/get",
    }

    if status_code == 404 and epoint in catalog_endpoints:
        return (
            "RESOURCE_NOT_FOUND",
            "Requested item ID is not available in Qobuz catalog for this account/region.",
        )
    if status_code == 401:
        return (
            "AUTH_REQUIRED",
            "Session/auth token is invalid or expired; re-authentication is required.",
        )
    if status_code == 403:
        return (
            "ACCESS_DENIED",
            "Access denied for this endpoint with current account permissions.",
        )
    if status_code == 429:
        return (
            "RATE_LIMITED",
            "Too many API requests; retry after a short cooldown.",
        )
    if status_code == 400 and "app_id" in msg:
        return (
            "INVALID_APP_ID",
            "Invalid or missing app_id provided to Qobuz API.",
        )
    if status_code == 400:
        return (
            "INVALID_REQUEST",
            "Request parameters/signature are invalid for this endpoint.",
        )
    if status_code >= 500:
        return (
            "QOBUZ_SERVER_ERROR",
            "Qobuz service returned a server error; retry may succeed.",
        )

    return (
        "API_ERROR",
        "Unexpected API error response.",
    )


class QobuzApiError(requests.exceptions.HTTPError):
    """Rich HTTP/API error with categorized reason details."""

    def __init__(
        self,
        endpoint,
        status_code,
        category,
        description,
        api_message=None,
        api_code=None,
        response=None,
    ):
        self.endpoint = endpoint
        self.status_code = status_code
        self.category = category
        self.description = description
        self.api_message = api_message
        self.api_code = api_code
        self.response = response
        message = self.format_message()
        super().__init__(message, response=response)

    def format_message(self):
        bits = [
            f"HTTP {self.status_code}",
            self.category,
            self.description,
            f"endpoint={self.endpoint}",
        ]
        if self.api_code is not None:
            bits.append(f"api_code={self.api_code}")
        if self.api_message:
            bits.append(f"api_message={self.api_message}")
        return " | ".join(bits)


def _build_qobuz_api_error(epoint, response):
    payload = _extract_error_payload(response)
    api_message = payload.get("message")
    api_code = payload.get("code")
    category, description = _categorize_api_failure(
        epoint,
        response.status_code,
        api_message,
    )
    return QobuzApiError(
        endpoint=epoint,
        status_code=response.status_code,
        category=category,
        description=description,
        api_message=api_message,
        api_code=api_code,
        response=response,
    )


class Client:

    def __init__(self):
        self.secrets = None
        self.id = None
        self.session = None
        self.base = API_URL
        self.sec = None
        self.session_id = None
        self.session_infos = None
        self.session_key = None
        self._auth_method = None  # 'password' | 'token' — used by reauth()
        self._auth_creds = {}

    def connect_with_token(self, user_id, user_auth_token, app_id, secrets):
        """
        init and authentication OAuth token
        """
        self._prepare_connect(app_id, secrets)
        self.auth_with_token(user_id, user_auth_token)

    def _prepare_connect(self, app_id, secrets):
        self.secrets = secrets
        self.id = str(app_id)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0",
                "X-App-Id": self.id,
                "Content-Type": "application/json;charset=UTF-8",
            }
        )
        self.base = API_URL
        self.sec = None
        self.session_id = None
        self.session_infos = None
        self.session_key = None
        self._auth_method = None  # 'password' | 'token' — used by reauth()
        self._auth_creds = {}

    def api_call(self, epoint, **kwargs):
        if epoint == "track/getFileUrl":
            unix = time.time()
            track_id = kwargs["id"]
            fmt_id = kwargs["fmt_id"]
            if int(fmt_id) not in (5, 6, 7, 27):
                raise InvalidQuality("Invalid quality id: choose between 5, 6, 7 or 27")
            r_sig = "trackgetFileUrlformat_id{}intentstreamtrack_id{}{}{}".format(
                fmt_id, track_id, unix, kwargs.get("sec", self.sec)
            )
            r_sig_hashed = hashlib.md5(r_sig.encode("utf-8")).hexdigest()
            params = {
                "request_ts": unix,
                "request_sig": r_sig_hashed,
                "track_id": track_id,
                "format_id": fmt_id,
                "intent": "stream",
            }
        elif epoint == "session/start":
            params = {"profile": "qbz-1"}
            params["request_ts"] = int(time.time())
            params["request_sig"] = self._modern_sig(
                epoint, params, kwargs.get("sec", self.sec)
            )
        elif epoint == "file/url":
            track_id = kwargs["id"]
            fmt_id = kwargs["fmt_id"]
            if int(fmt_id) not in (6, 7, 27):
                raise InvalidQuality("Invalid quality id: choose between 6, 7 or 27")
            params = {
                "track_id": track_id,
                "format_id": fmt_id,
                "intent": "import",
            }
            params["request_ts"] = int(time.time())
            params["request_sig"] = self._modern_sig(
                epoint, params, kwargs.get("sec", self.sec)
            )
        else:
            params = kwargs
        if epoint == "session/start":
            r = self.session.post(
                self.base + epoint,
                data=params,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        else:
            r = self.session.get(self.base + epoint, params=params)

        log.debug("API %s → HTTP %s", epoint, r.status_code)
        if epoint == "user/login":
            if r.status_code == 401:
                raise AuthenticationError("Invalid credentials.\n" + RESET)
            elif r.status_code == 400:
                raise InvalidAppIdError("Invalid app id.\n" + RESET)
            else:
                log.info("Logged: OK")
        elif (
            epoint in ["track/getFileUrl", "favorite/getUserFavorites", "file/url"]
            and r.status_code == 400
        ):
            raise InvalidAppSecretError(f"Invalid app secret: {r.json()}.\n" + RESET)
        elif (
            r.status_code == 401
            and epoint != "user/login"
            and not kwargs.get("_retried")
        ):
            result = self._call_retry_auth(epoint, **kwargs)
            if result is not None:
                return result

        if not r.ok:
            raise _build_qobuz_api_error(epoint, r)
        return r.json()

    def _call_retry_auth(self, epoint, **kwargs):
        """Re-authenticate and retry *epoint* once on a 401 response."""
        if not self._auth_method:
            return None
        log.info("Session expired. Attempting re-authentication...")
        try:
            self.reauth()
            # mark as retry so we don't loop infinitely
            kwargs["_retried"] = True
            return self.api_call(epoint, **kwargs)
        except Exception as e:
            raise AuthenticationError(
                f"Re-authentication failed: {e}. Run 'qobuz-dl oauth' to log in again."
            ) from e

    def auth_with_token(self, user_id, user_auth_token):
        params = {
            "user_id": str(user_id),
            "user_auth_token": user_auth_token,
            "app_id": self.id,
        }
        r = self.session.get(self.base + "user/login", params=params)
        if r.status_code == 401:
            raise AuthenticationError("Invalid credentials.\n" + RESET)
        if r.status_code == 400:
            raise InvalidAppIdError("Invalid app id.\n" + RESET)
        r.raise_for_status()
        usr_info = r.json()
        if not usr_info["user"]["credential"]["parameters"]:
            raise IneligibleError("Free accounts are not eligible to download tracks.")
        self.uat = user_auth_token
        self.session.headers.update({"X-User-Auth-Token": self.uat})
        self.label = usr_info["user"]["credential"]["parameters"]["short_label"]
        log.info("Membership: %s", self.label)
        self.cfg_setup()
        # store for potential reauth
        self._auth_method = "token"
        self._auth_creds = {"user_id": user_id, "user_auth_token": user_auth_token}

    def reauth(self):
        """Re-authenticate using stored credentials.

        Called automatically by api_call when a 401 is received.
        Reset session state so a fresh session/start cycle can run.
        """
        self.session_id = None
        self.session_key = None
        self.session_infos = None
        if self._auth_method == "token":
            self.auth_with_token(**self._auth_creds)
        else:
            raise AuthenticationError("No credentials stored for re-authentication.")

    def multi_meta(self, epoint, key, id, type):
        total = 1
        offset = 0
        while total > 0:
            if type in ["tracks", "albums"]:
                j = self.api_call(epoint, id=id, offset=offset, type=type)[type]
            else:
                j = self.api_call(epoint, id=id, offset=offset, type=type)
            if offset == 0:
                yield j
                total = j[key] - 500
            else:
                yield j
                total -= 500
            offset += 500

    def get_album_meta(self, id):
        return self.api_call("album/get", id=id)

    def get_track_meta(self, id):
        return self.api_call("track/get", id=id)

    def _modern_sig(self, epoint, params, sec):
        object_, method = epoint.split("/")
        r_sig = [object_, method]
        for key in sorted(params):
            value = params[key]
            if key not in ("request_ts", "request_sig") and isinstance(
                value, (str, int, float)
            ):
                r_sig.extend((key, str(value)))
        r_sig.extend((str(params["request_ts"]), sec))
        return hashlib.md5("".join(r_sig).encode("utf-8")).hexdigest()

    @staticmethod
    def _b64url_decode(value):
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

    def _derive_session_key(self):
        salt, info = self.session_infos.split(".")
        return HKDF(
            algorithm=hashes.SHA256(),
            length=16,
            salt=self._b64url_decode(salt),
            info=self._b64url_decode(info),
        ).derive(bytes.fromhex(self.sec))

    def _unwrap_track_key(self, key_token):
        _, wrapped, iv = key_token.split(".")
        decryptor = Cipher(
            algorithms.AES(self.session_key),
            modes.CBC(self._b64url_decode(iv)),
        ).decryptor()
        padded = decryptor.update(self._b64url_decode(wrapped)) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        return unpadder.update(padded) + unpadder.finalize()

    def get_artist_meta(self, id):
        return self.multi_meta("artist/get", "albums_count", id, None)

    def get_plist_meta(self, id):
        return self.multi_meta("playlist/get", "tracks_count", id, None)

    def get_label_meta(self, id):
        return self.multi_meta("label/get", "albums_count", id, None)

    def search_albums(self, query, limit):
        return self.api_call("album/search", query=query, limit=limit)

    def search_artists(self, query, limit):
        return self.api_call("artist/search", query=query, limit=limit)

    def search_playlists(self, query, limit):
        return self.api_call("playlist/search", query=query, limit=limit)

    def search_tracks(self, query, limit):
        return self.api_call("track/search", query=query, limit=limit)

    def get_favorite_albums(self, offset, limit):
        return self.api_call(
            "favorite/getUserFavorites", type="albums", offset=offset, limit=limit
        )

    def get_favorite_tracks(self, offset, limit):
        return self.api_call(
            "favorite/getUserFavorites", type="tracks", offset=offset, limit=limit
        )

    def get_favorite_artists(self, offset, limit):
        return self.api_call(
            "favorite/getUserFavorites", type="artists", offset=offset, limit=limit
        )

    def get_user_playlists(self, limit):
        return self.api_call("playlist/getUserPlaylists", limit=limit)

    def test_secret(self, sec):
        try:
            self.api_call("track/getFileUrl", id=5966783, fmt_id=5, sec=sec)
            return True
        except InvalidAppSecretError:
            return False

    def login_with_oauth_code(self, code, private_key):
        # Step 1: Exchange code for token via /oauth/callback
        callback_url = self.base + "oauth/callback"
        params = {
            "code": code,
            "private_key": private_key,
            "app_id": self.id,
        }
        r = self.session.get(callback_url, params=params)
        r.raise_for_status()
        json_resp = r.json()
        token = json_resp.get("token")
        if not token:
            raise AuthenticationError("No token in OAuth callback response")

        # Step 2: GET /user/login with X-User-Auth-Token to fetch full profile
        self.uat = token
        self.session.headers.update({"X-User-Auth-Token": self.uat})
        login_url = self.base + "user/login"
        r = self.session.post(
            login_url,
            headers={"Content-Type": "text/plain;charset=UTF-8"},
            data="extra=partner",
        )
        if r.status_code == 401:
            raise AuthenticationError("OAuth token rejected")
        r.raise_for_status()
        usr_info = r.json()
        if not usr_info["user"]["credential"]["parameters"]:
            raise IneligibleError("Free accounts are not eligible to download tracks.")
        self.label = usr_info["user"]["credential"]["parameters"]["short_label"]
        log.info("Membership: %s", self.label)
        self.cfg_setup()
        return usr_info

    def cfg_setup(self):
        for secret in self.secrets:
            # Falsy secrets
            if not secret:
                continue

            if self.test_secret(secret):
                self.sec = secret
                break

        if self.sec is None:
            raise InvalidAppSecretError("Can't find any valid app secret.\n" + RESET)


#
# create qobuz_api instance
#
qobuz_api = Client()
