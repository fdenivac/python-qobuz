import pytest
from dotenv import dotenv_values
import qobuz
from qobuz.qopy import qobuz_api, API_URL
import responses

from tests.resources.responses import playlist_get_user_playlists_json
from tests.resources.fixtures import user


config = dotenv_values("tests/.env")


@pytest.fixture
def app():
    qobuz_api.connect_with_token(
        config["user_id"],
        config["auth_token"],
        config["app_id"],
        config["secrets"].split(","),
    )

def get_url(user, filter="owner", limit=50, offset=0):
    return (
        API_URL
        + "playlist/getUserPlaylists"
        + "?filter={}".format(filter)
        + "&limit={}".format(limit)
        + "&offset={}".format(offset)
    )


@pytest.fixture
def response_user_playlists(user):
    with responses.RequestsMock() as response_mock:
        response_mock.add(
            responses.GET,
            url=get_url(user),
            json=playlist_get_user_playlists_json,
            status=200,
            match_querystring=True,
        )

        yield response_mock


def test_playlists_len(app, user, response_user_playlists):
    playlists = user.playlists_get()

    assert len(playlists) != 0
    assert len(playlists) == len(
        playlist_get_user_playlists_json["playlists"]["items"]
    )


def test_playlists_content(app, user, response_user_playlists):
    playlists = user.playlists_get()
    playlists_resp = playlist_get_user_playlists_json["playlists"]["items"]

    for i in range(len(playlists)):
        assert playlists[i].id == playlists_resp[i]["id"]
        assert playlists[i].name == playlists_resp[i]["name"]
        assert playlists[i].description == playlists_resp[i]["description"]
