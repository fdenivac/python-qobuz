import pytest
from dotenv import dotenv_values
import qobuz
from qobuz.qopy import qobuz_api, API_URL
import responses

from tests.resources.fixtures import playlist
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

def get_url(playlist_id, track_ids=""):
    return (
        API_URL
        + "playlist/addTracks"
        + "?playlist_id={}".format(playlist_id)
        + "&track_ids={}".format(track_ids)
    )


def test_playlist_add_tracks(app, playlist):
    track_ids = ",".join(
        [str(t["id"]) for t in playlist_get_tracks_json["tracks"]["items"]]
    )

    with responses.RequestsMock() as response_mock:
        response_mock.add(
            responses.GET,
            get_url(
                playlist_id=playlist_add_tracks_json["id"],
                track_ids=track_ids,
            ),
            json=playlist_add_tracks_json,
            status=200,
            match_querystring=True,
        )

        tracks = [
            qobuz.Track(t) for t in playlist_get_tracks_json["tracks"]["items"]
        ]

        # Match playlist-ids to add to the correct id
        playlist.id = playlist_add_tracks_json["id"]

        playlist.add_tracks(tracks)
