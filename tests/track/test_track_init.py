import pytest
from dotenv import dotenv_values
import qobuz
from qobuz.qopy import qobuz_api, API_URL
import responses

from tests.resources.responses import track_search_json, artist_get_albums_json
from tests.resources.fixtures import artist, track

config = dotenv_values("tests/.env")


@pytest.fixture
def app():
    qobuz_api.connect_with_token(
        config["user_id"],
        config["auth_token"],
        config["app_id"],
        config["secrets"].split(","),
    )


def test_track_init(app):
    track_item = track_search_json["tracks"]["items"][0]

    track = qobuz.Track(track_item)

    assert track.id == track_item["id"]
    assert track.title == track_item["title"]
    assert track.album == qobuz.Album(track_item["album"])
    assert track.duration == track_item["duration"]
    assert track.media_number == track_item["media_number"]
    assert track.track_number == track_item["track_number"]


def test_track_type(app, track):
    assert track.type == "track"


def test_track_artist_lookup(app, track, artist):
    with responses.RequestsMock() as response_mock:
        response_mock.add(
            responses.GET,
            url=API_URL + "artist/get",
            json=artist_get_albums_json,
            status=200,
            match_querystring=False,
        )

        assert track.artist == qobuz.Artist(artist_get_albums_json)
