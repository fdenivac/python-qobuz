import pytest
from dotenv import dotenv_values
import qobuz
from qobuz.qopy import qobuz_api, API_URL
import responses

from tests.resources.responses import playlist_create_json
from tests.resources.fixtures import playlist


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
        + "playlist/get"
        + "?playlist_id={}".format(playlist_id)
    )


def test_playlist_init(app):
    playlist = qobuz.Playlist(playlist_create_json)

    assert playlist.id == playlist_create_json["id"]
    assert playlist.name == playlist_create_json["name"]
    assert playlist.description == playlist_create_json["description"]


def test_playlist_from_id(app, playlist):
    with responses.RequestsMock() as response_mock:
        response_mock.add(
            responses.GET,
            url=get_url(playlist.id),
            json=playlist_create_json,
            status=200,
            match_querystring=True,
        )

        playlist_from_id = qobuz.Playlist.from_id(playlist.id)

    assert playlist_from_id == playlist
