import pytest
from dotenv import dotenv_values
import qobuz
from qobuz.qopy import qobuz_api, API_URL
import responses

from tests.resources.fixtures import user, playlist
from tests.resources.responses import playlist_get_tracks_json
from tests.resources.responses import playlist_add_tracks_json

config = dotenv_values("tests/.env")

@pytest.fixture
def app():
    qobuz_api.connect_with_token(
        config["user_id"],
        config["auth_token"],
        config["app_id"],
        config["secrets"].split(","),
    )


def get_url(playlist_id):
    return (
        API_URL
        + "playlist/delete"
        + "?playlist_id={}".format(playlist_id)
    )


def test_playlist_delete(app, playlist, user):
    with responses.RequestsMock() as response_mock:
        response_mock.add(
            responses.GET,
            get_url(playlist_id=playlist.id),
            json={"status": "success"},
            status=200,
            match_querystring=True,
        )

        assert user.playlist_delete(playlist)
