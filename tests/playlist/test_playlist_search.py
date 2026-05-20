import pytest
from dotenv import dotenv_values
import qobuz
from qobuz.qopy import qobuz_api, API_URL
import responses

from tests.resources.responses import playlist_search_json

config = dotenv_values("tests/.env")

@pytest.fixture
def app():
    qobuz_api.connect_with_token(
        config["user_id"],
        config["auth_token"],
        config["app_id"],
        config["secrets"].split(","),
    )


def get_url(query, limit=50, offset=0):
    return (
        API_URL
        + "playlist/search"
        + "?query={0}".format(query)
        + "&limit={}".format(limit)
        + "&offset={}".format(offset)
    )


@pytest.fixture
def response_search():
    with responses.RequestsMock() as response_mock:
        response_mock.add(
            responses.GET,
            url=get_url(playlist_search_json["query"]),
            json=playlist_search_json,
            status=200,
            match_querystring=True,
        )

        yield response_mock


def test_search_len(app, response_search):
    playlists = qobuz.Playlist.search(playlist_search_json["query"])

    assert len(playlists) != 0
    assert len(playlists) == len(playlist_search_json["playlists"]["items"])


def test_search_content(app, response_search):
    playlists = qobuz.Playlist.search(playlist_search_json["query"])
    playlists_resp = playlist_search_json["playlists"]["items"]

    assert playlists[0].id == playlists_resp[0]["id"]
    assert playlists[0].name == playlists_resp[0]["name"]
    assert playlists[0].description == playlists_resp[0]["description"]
