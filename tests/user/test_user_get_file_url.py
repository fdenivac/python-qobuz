import pytest
from dotenv import dotenv_values
import qobuz
from qobuz.qopy import qobuz_api, API_URL
import responses
import time

from tests.resources.fixtures import user, track
from tests.resources.responses import get_file_url_json

config = dotenv_values("tests/.env")

@pytest.fixture
def app():
    qobuz_api.connect_with_token(
        config["user_id"],
        config["auth_token"],
        config["app_id"],
        config["secrets"].split(","),
    )



def get_url(track_id, format_id, user_auth_token, request_ts, intent="stream"):
    params = {
        "track_id": track_id,
        "format_id": format_id,
        "user_auth_token": user_auth_token,
        "intent": intent,
        # "app_id": qobuz.api.APP_ID,
    }

    # request_sig = qobuz.api._get_request_sig(
    #     timestamp=request_ts,
    #     url=qobuz.api.API_URL + "track/getFileUrl",
    #     **params
    # )

    return (
        API_URL
        + "track/getFileUrl"
        + "?track_id={}".format(track_id)
        + "&intent={}".format(intent)
        # + "&request_ts={}".format(request_ts)
        # + "&request_sig={}".format(request_sig)
        + "&format_id={}".format(format_id)
        # + "&user_auth_token={}".format(user_auth_token)
        # + "&app_id={}".format(qobuz.api.APP_ID)
    )


def test_user_get_file_url(app, user, track, monkeypatch):
    # The validation schema contains the current timestamp.
    # For testing, we set that constant
    current_time = time.time()

    def mytime():
        return current_time

    monkeypatch.setattr(time, "time", mytime)

    resp = get_file_url_json
    url = get_url(
        track_id=track.id,
        format_id=resp["format_id"],
        user_auth_token=user.auth_token,
        request_ts=int(current_time),
    )

    with responses.RequestsMock() as response_mock:
        response_mock.add(
            responses.GET,
            url=url,
            json=resp,
            status=200,
            match_querystring=True,
        )

        track_url = user.get_file_url(
            track.id, format_id=resp["format_id"], intent="stream"
        )
