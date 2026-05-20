# -*- coding: utf-8 -*-
import pytest
from dotenv import dotenv_values
import qobuz
from qobuz.qopy import qobuz_api, API_URL
import responses

from tests.resources.fixtures import user, album
from tests.resources.responses import user_fav_get_albums_json

config = dotenv_values("tests/.env")


@pytest.fixture
def app():
    qobuz_api.connect_with_token(
        config["user_id"],
        config["auth_token"],
        config["app_id"],
        config["secrets"].split(","),
    )


def get_favorite_albums_url(fav_type="albums",
                            limit=50, offset=0):
    return (
        API_URL
        + "favorite/getUserFavorites"
        + "?type={}".format(fav_type)
        + "&limit={}".format(limit)
        + "&offset={}".format(offset)
    )


def get_favorite_add_albums_url(album_ids):
    return (
        API_URL
        + "favorite/create"
        + "?album_ids={}".format(album_ids)
    )


def get_favorite_del_albums_url(album_ids):
    return (
        API_URL
        + "favorite/delete"
        + "?album_ids={}".format(album_ids)
    )


@pytest.fixture
def response_fav_get_albums(user):
    with responses.RequestsMock() as response_mock:
        response_mock.add(
            responses.GET,
            url=get_favorite_albums_url(),
            json=user_fav_get_albums_json,
            status=200,
            match_querystring=False,
        )

        yield response_mock


def test_user_favorite_get_albums_type(app, user, response_fav_get_albums):
    albums = user.favorites_get(fav_type="albums")

    for a in albums:
        assert isinstance(a, qobuz.Album)


def test_user_favorite_get_albums_len(app, user, response_fav_get_albums):
    albums = user.favorites_get(fav_type="albums")

    assert len(albums) == user_fav_get_albums_json["albums"]["limit"]


def test_user_favorite_get_albums_content(app, user, response_fav_get_albums):
    albums = user.favorites_get(fav_type="albums")

    for i in range(len(albums)):
        assert albums[i] == qobuz.Album(
            user_fav_get_albums_json["albums"]["items"][i]
        )


def test_user_favorite_add_albums(app, user, album):
    fav_add_album_url = get_favorite_add_albums_url(album.id)

    with responses.RequestsMock() as response_mock:
        response_mock.add(
            responses.GET,
            url=fav_add_album_url,
            json={"status": "success"},
            status=200,
            match_querystring=True,
        )

        assert user.favorites_add(albums=album.id) is True


def test_user_favorite_del_albums(app, user, album):
    fav_del_album_url = get_favorite_del_albums_url(album.id)

    with responses.RequestsMock() as response_mock:
        response_mock.add(
            responses.GET,
            url=fav_del_album_url,
            json={"status": "success"},
            status=200,
            match_querystring=True,
        )

        assert user.favorites_del(albums=album.id) is True
