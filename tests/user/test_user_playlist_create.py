import pytest
from dotenv import dotenv_values
import qobuz
from qobuz.qopy import qobuz_api, API_URL
import responses

from tests.resources.fixtures import user
from tests.resources.responses import playlist_create_json

config = dotenv_values("tests/.env")


@pytest.fixture
def app():
    qobuz_api.connect_with_token(
        config["user_id"],
        config["auth_token"],
        config["app_id"],
        config["secrets"].split(","),
    )


def get_playlist_create_url(
    name, description=None, is_public=False, is_collaborative=False
):
    return (
        API_URL
        + "playlist/create"
        + "?name={}".format(name)
        + "&is_public={}".format(is_public)
        + "&is_collaborative={}".format(is_collaborative)
    )


@pytest.fixture
def response_playlist_create():
    resp = playlist_create_json
    url = get_playlist_create_url(
        name=resp["name"],
        description=resp["description"],
        is_public=resp["is_public"],
        is_collaborative=resp["is_collaborative"],
    )

    with responses.RequestsMock() as response_mock:
        response_mock.add(
            responses.GET,
            url=url,
            json=resp,
            status=200,
            match_querystring=False,
        )

        yield response_mock


def test_user_playlist_create(app, user, response_playlist_create):
    resp = playlist_create_json
    playlist = user.playlist_create(
        name=resp["name"],
        description=resp["description"],
        is_public=resp["is_public"],
        is_collaborative=resp["is_collaborative"],
    )

    assert isinstance(playlist, qobuz.Playlist)
    assert playlist.id == resp["id"]
    assert playlist.name == resp["name"]
