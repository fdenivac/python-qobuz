import qobuz


class Album(object):
    """This class represents a Album from the Qobuz-API.

    Parameters
    ----------
    album_item: dict
        Dictionary as returned from the JSON-API to represent a album

        Keys should include:
        'id', 'title', 'tracks_count', 'media_count', 'released_at', 'artist', 'images', 'genre'
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
        "_tracks",
        "_user",
    ]

    def __init__(self, album_item, user=None):
        self.id = album_item.get("id")
        self.title = album_item.get("title")
        self.version = album_item.get("version")
        self.images = album_item.get("image")       # dict of urls on images
        self.tracks_count = album_item.get("tracks_count")
        self.media_count = album_item.get("media_count")
        self.released_at = album_item.get("released_at")
        self.artist = qobuz.Artist(album_item["artist"])
        self.genre = album_item.get("genre")['name']
        self._tracks = None
        self._user = user


    @property
    def type(self):
        return "album"

    @property
    def tracks(self):
        if self._tracks is None:
            self._update_tracks()

        return self._tracks

    def _update_tracks(self):
        resp = qobuz.api.request("album/get", album_id=self.id, user_auth_token=self._user.auth_token if self._user is not None else None)

        self._tracks = [
            qobuz.Track(t, album=self) for t in resp["tracks"]["items"]
        ]

    def __eq__(self, other):
        return (
            self.id == other.id
            and self.title == other.title
            and self.tracks_count == other.tracks_count
            and self.released_at == other.released_at
            and self.artist == other.artist
        )

    @classmethod
    def from_id(cls, id, user=None):
        return cls(qobuz.api.request("album/get", album_id=id, user_auth_token=user.auth_token if user is not None else None), user)

    @classmethod
    def get_featured(cls, type="new-releases", limit=50, offset=0, user=None):
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
        albums = qobuz.api.request(
            "album/getFeatured", type=type, offset=offset, limit=limit, user_auth_token=user.auth_token if user is not None else None
        )

        return [cls(a, user) for a in albums["albums"]["items"]]

    @classmethod
    def search(cls, query, limit=50, offset=0, raw=False, user=None):
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
        token = user.auth_token if user is not None else None
        albums = qobuz.api.request(
            "album/search", query=query, offset=offset, limit=limit, user_auth_token=token
        )

        if raw:
            return albums

        return [cls(a, user) for a in albums["albums"]["items"]]
