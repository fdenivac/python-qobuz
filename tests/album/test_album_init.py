import pytest
from dotenv import dotenv_values
import qobuz
from qobuz.qopy import qobuz_api, API_URL
import responses

from tests.resources.responses import album_get_json
from tests.resources.fixtures import album

config = dotenv_values("tests/.env")


@pytest.fixture
def app():
    qobuz_api.connect_with_token(
        config["user_id"],
        config["auth_token"],
        config["app_id"],
        config["secrets"].split(","),
    )


def get_url(album_id):
    return (
        API_URL
        + "album/get"
        + "?album_id={}".format(album_id)
    )


def test_album_init(app):
    album = qobuz.Album(album_get_json)

    assert album.id == album_get_json["id"]
    assert album.title == album_get_json["title"]
    assert album.tracks_count == album_get_json["tracks_count"]
    assert album.released_at == album_get_json["released_at"]
    assert album.artist == qobuz.Artist(album_get_json["artist"])


def test_album_from_id(app, album):
    with responses.RequestsMock() as response_mock:
        response_mock.add(
            responses.GET,
            url=get_url(album.id),
            json=album_get_json,
            status=200,
            match_querystring=True,
        )

        album_from_id = qobuz.Album.from_id(album.id)

    assert album_from_id == album


def test_album_type(app, album):
    assert album.type == "album"
