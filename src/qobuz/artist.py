import qobuz
from qobuz.qopy import qobuz_api


class Artist(object):
    """This class represents an artist from the Qobuz-API.

    Parameters
    ----------
    artist_item: dict
        Dictionary as returned from the JSON-API to represent an artist

        Keys should include:
        'id', 'name', 'picture', 'slug', 'album_count', 'biography', 'favorited_at'
    """

    __slots__ = [
        "id",
        "name",
        "picture",
        "slug",
        "albums_count",
        "biography",
        "favorited_at",
    ]

    def __init__(self, artist_item):
        self.id = artist_item.get("id")
        self.name = artist_item.get("name")
        self.picture = artist_item.get("picture")
        self.slug = artist_item.get("slug")
        self.albums_count = artist_item.get("albums_count")
        self.biography = artist_item.get("biography", {}).get("summary")
        self.favorited_at = artist_item.get("favorited_at")

    def __eq__(self, other):
        return (
            self.id == other.id
            and self.name == other.name
            and self.picture == other.picture
            and self.slug == other.slug
            and self.albums_count == other.albums_count
        )

    @property
    def type(self):
        return "artist"

    def get_all_tracks(self, offset=0, limit=50):
        """Get tracks for this artist"""
        res = qobuz_api.api_call(
            "artist/get",
            artist_id=self.id,
            extra="tracks",
            offset=offset,
            limit=limit,
        )

        return [qobuz.Track(t) for t in res["tracks"]["items"]]

    def get_all_albums(self, offset=0, limit=50):
        """Return albums of an artist.

        Parameters
        ----------
        limit: int
            Number of elements returned per request
        offset: int
            Offset from which to obtain limit elements

        Returns
        -------
        list of Album
            Albums from the artist
        """
        albums = qobuz_api.api_call(
            "artist/get",
            artist_id=self.id,
            extra="albums",
            offset=offset,
            limit=limit,
        )

        return [qobuz.Album(a) for a in albums["albums"]["items"]]

    @classmethod
    def from_id(cls, id):
        """Build Artist from id"""
        return cls(qobuz_api.api_call("artist/get", artist_id=id))

    @classmethod
    def search(cls, artist, limit=50, offset=0, raw=False):
        """Search for an artist.

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
        list of Artist
            Resulting playlists for the search query
        """
        req = qobuz_api.api_call(
            "artist/search", query=artist, limit=limit, offset=offset
        )

        if raw:
            return req

        return [cls(a) for a in req["artists"]["items"]]
