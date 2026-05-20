import pytest
from dotenv import dotenv_values
import qobuz
from qobuz.qopy import qobuz_api, API_URL
import responses

from tests.resources.responses import artist_search_json

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
        + "artist/search"
        + "?query={0}".format(query)
        + "&limit={}".format(limit)
        + "&offset={}".format(offset)
    )


@pytest.fixture
def response_search_empty():
    with responses.RequestsMock() as response_mock:
        url = get_url("")
        resp = {
            "query": "",
            "artists": {"limit": 50, "offset": 0, "total": 0, "items": []},
        }

        response_mock.add(
            responses.GET, url, json=resp, status=200, match_querystring=True
        )

        yield response_mock


@pytest.fixture
def response_search():
    with responses.RequestsMock() as response_mock:
        response_mock.add(
            responses.GET,
            url=get_url(artist_search_json["query"]),
            json=artist_search_json,
            status=200,
            match_querystring=True,
        )

        yield response_mock


def test_search_len(app, response_search):
    artists = qobuz.Artist.search(artist_search_json["query"])

    assert len(artists) != 0
    assert len(artists) == len(artist_search_json)


def test_search_found(app, response_search):
    artists = qobuz.Artist.search(artist_search_json["query"])

    assert artists[0].name == "MGMT"
    assert artists[0].picture is None
    assert artists[0].id == 118680
    assert artists[0].albums_count == 29
    assert artists[0].slug == "mgmt"


def test_search_empty(app, response_search_empty):
    artists = qobuz.Artist.search("")

    assert len(artists) == 0
