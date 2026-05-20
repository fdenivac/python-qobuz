import pytest
from dotenv import dotenv_values
import qobuz
from qobuz.qopy import qobuz_api, API_URL
import responses

from tests.resources.responses import artist_search_json
from tests.resources.fixtures import artist

config = dotenv_values("tests/.env")

@pytest.fixture
def app():
    qobuz_api.connect_with_token(
        config["user_id"],
        config["auth_token"],
        config["app_id"],
        config["secrets"].split(","),
    )

def get_url(artist_id):
    return (
        API_URL
        + "artist/get"
        + "?artist_id={}".format(artist_id)
    )


def test_artist_init(app):
    artist_item = artist_search_json["artists"]["items"][0]

    artist = qobuz.Artist(artist_item)

    assert artist.id == artist_item["id"]
    assert artist.name == artist_item["name"]
    assert artist.picture == artist_item["picture"]
    assert artist.slug == artist_item["slug"]
    assert artist.albums_count == artist_item["albums_count"]


def test_artist_from_id(app):
    artist_item = artist_search_json["artists"]["items"][0]

    with responses.RequestsMock() as response_mock:
        response_mock.add(
            responses.GET,
            url=get_url(artist_item["id"]),
            json=artist_item,
            status=200,
            match_querystring=True,
        )

        artist_from_id = qobuz.Artist.from_id(artist_item["id"])

    assert artist_from_id == qobuz.Artist(artist_item)


def test_artist_type(app, artist):
    assert artist.type == "artist"
