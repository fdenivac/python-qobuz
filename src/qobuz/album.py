import qobuz
from qobuz.qopy import qobuz_api


class Album(object):
    """This class represents a Album from the Qobuz-API.

    Parameters
    ----------
    album_item: dict
        Dictionary as returned from the JSON-API to represent a album

        Keys should include:
        'id', 'title', 'tracks_count', 'media_count', 'released_at', 'artist', 'images', 'genre', 'favorited_at'
    """

    __slots__ = [
        "id",
        "title",
        "version",
        "images",
        "tracks_count",
        "media_count",
        "released_at",
        "artist",
        "genre",
        "favorited_at",
        "_tracks",
    ]

    def __init__(self, album_item):
        self.id = album_item.get("id")
        self.title = album_item.get("title")
        self.version = album_item.get("version")
        self.images = album_item.get("image")  # dict of urls on images
        self.tracks_count = album_item.get("tracks_count")
        self.media_count = album_item.get("media_count")
        self.released_at = album_item.get("released_at")
        self.artist = qobuz.Artist(album_item["artist"])
        self.genre = album_item.get("genre")["name"]
        self.favorited_at = album_item.get("favorited_at")
        self._tracks = None

    @property
    def type(self):
        return "album"

    @property
    def tracks(self):
        """get tracks for this album"""
        if self._tracks is None:
            self._update_tracks()

        return self._tracks

    def _update_tracks(self):
        resp = qobuz_api.api_call("album/get", album_id=self.id)

        self._tracks = [qobuz.Track(t, album=self) for t in resp["tracks"]["items"]]

    def __eq__(self, other):
        return (
            self.id == other.id
            and self.title == other.title
            and self.tracks_count == other.tracks_count
            and self.released_at == other.released_at
            and self.artist == other.artist
        )

    @classmethod
    def from_id(cls, id, raw=False):
        datas = qobuz_api.api_call(
            "album/get",
            album_id=id,
        )
        if raw:
            return datas
        else:
            return cls(datas)

    @classmethod
    def get_featured(cls, type="new-releases", limit=50, offset=0):
        """Get featured albums.

        Parameters
        ----------
        type: str
            Accepted values are:
            most-streamed, best-sellers, new-releases, press-awards,
            editor-picks, most-featured, new-releases-full, recent-releases,
            ideal-discography, qobuzissims, album-of-the-week,
            re-release-of-the-week
        """
        albums = qobuz_api.api_call(
            "album/getFeatured",
            type=type,
            offset=offset,
            limit=limit,
        )

        return [cls(a) for a in albums["albums"]["items"]]

    @classmethod
    def search(cls, query, limit=50, offset=0, raw=False):
        """Search for a album.

        Parameters
        ----------
        query: str
            Search query
        limit: int
            Number of elements returned per request
        offset: int
            Offset from which to obtain limit elements
        raw: bool
            results will be returned as json if True

        Returns
        -------
        list of Album
            Resulting albums for the search query
        """
        albums = qobuz_api.api_call(
            "album/search",
            query=query,
            offset=offset,
            limit=limit,
        )

        if raw:
            return albums

        return [cls(a) for a in albums["albums"]["items"]]
