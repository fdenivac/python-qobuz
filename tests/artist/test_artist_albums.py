# -*- coding: utf-8 -*-
import pytest
from dotenv import dotenv_values
import qobuz
from qobuz.qopy import qobuz_api, API_URL
import responses

from tests.resources.responses import artist_get_albums_json

config = dotenv_values("tests/.env")


@pytest.fixture
def app():
    qobuz_api.connect_with_token(
        config["user_id"],
        config["auth_token"],
        config["app_id"],
        config["secrets"].split(","),
    )

def get_url(artist_id, offset=0, limit=50):
    return (
        API_URL
        + "artist/get"
        + "?artist_id={}".format(artist_id)
        + "&extra={}".format("albums")
        + "&limit={}".format(limit)
        + "&offset={}".format(offset)
    )


@pytest.fixture
def response_all_albums():
    with responses.RequestsMock() as response_mock:
        response_mock.add(
            responses.GET,
            url=get_url(artist_get_albums_json["id"]),
            json=artist_get_albums_json,
            status=200,
            match_querystring=True,
        )
        yield response_mock


def test_artist_albums_len(app, response_all_albums):
    artist = qobuz.Artist(artist_get_albums_json)

    assert len(artist.get_all_albums()) == 25


def test_artist_albums_type(app, response_all_albums):
    artist = qobuz.Artist(artist_get_albums_json)

    for a in artist.get_all_albums():
        assert isinstance(a, qobuz.Album)


def test_artist_album_content(app, response_all_albums):
    artist = qobuz.Artist(artist_get_albums_json)

    albums = artist.get_all_albums()

    assert albums[0].id == "0886443927087"
    assert albums[0].title == "Random Access Memories (Édition Studio Masters)"
    assert albums[0].tracks_count == 13
    assert albums[0].released_at == 1368741600


def test_artist_album_artist(app, response_all_albums):
    artist = qobuz.Artist(artist_get_albums_json)

    albums = artist.get_all_albums()

    for a in albums:
        assert isinstance(a.artist, qobuz.Artist)

    assert albums[0].artist.name == "Daft Punk"
    assert albums[0].artist.id == 36819
    assert albums[0].artist.picture is None
    assert albums[0].artist.slug == "daft-punk"
    assert albums[0].artist.albums_count == 52
