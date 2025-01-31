from qobuz import api, Track


class Playlist(object):
    """This class represents a playlist from the Qobuz-API.

    Parameters
    ----------
    playlist_item: dict
        Dictionary as returned from the JSON-API to represent a playist

        Keys should include:
        'id', 'name', 'description', 'duration', 'public', 'collaborative', 'tracks_count', 'update_at',
    user: User
        Add when the playlist is your own, otherwise tracks won't be accessible
    """

    __slots__ = ["id", "name", "description", "duration", "public", "collaborative", "tracks_count", "updated_at", "_user"]

    def __init__(self, playlist_item, user=None):
        self.id = playlist_item.get("id")
        self.name = playlist_item.get("name")
        self.description = playlist_item.get("description")
        self.duration = playlist_item.get("duration")
        self.public = playlist_item.get("is_public")
        self.collaborative = playlist_item.get("is_collaborative")
        self.tracks_count = playlist_item.get("tracks_count")
        self.updated_at = playlist_item.get("updated_at")
        self._user = user

    def __eq__(self, other):
        return (
            self.id == other.id
            and self.name == other.name
            and self.description == other.description
        )

    def get_tracks(self, limit=50, offset=0, raw=False):
        """Tracks of the playlist.

        Parameters
        ---------
        limit: int
            Number of elements returned per request
        offset: int
            Offset from which to obtain limit elements
        raw: bool
            results will be returned as json if True

        Returns
        -------
        lst
            List of Tracks
        """
        token = self._user.auth_token if self._user else None

        playlist = api.request(
            "playlist/get",
            playlist_id=self.id,
            extra="tracks",
            limit=limit,
            user_auth_token=token,
            offset=offset,
        )

        if raw:
            return playlist

        return [Track(t, user=self._user) for t in playlist["tracks"]["items"]]

    def _split_into_chunks(self, iterable, chunk_size):
        """Split a iterable into smaller chunks.

        Parameters
        ----------
        iterable
            Iterable to be split
        chunk_size: int
            Max number of elements per chunk
        """
        splitted = list(zip(*[iter(iterable)] * chunk_size))

        # Include the last chunk, which length was smaller than chunk_size
        num_extra = len(iterable) % chunk_size
        if num_extra:
            splitted.append(iterable[-num_extra:])

        return splitted

    def add_tracks(self, tracks, own, max_elements_per_request=50):
        """Add tracks to the playlist.

        In order to limit the length of the resulting URL for a very large
        number of tracks, split the request into multiple.

        Parameters
        ----------
        tracks: list: Track or int (track id)
            Tracks to be added
        own: User
            Adding tracks requires a logged in User
        max_elements_per_request: int
            Split the request into multiple. Each with at most this many tracks
        """
        if isinstance(tracks[0], int):
            track_ids = tracks
        else:
            track_ids = [t.id for t in tracks]

        for c in self._split_into_chunks(track_ids, max_elements_per_request):
            api.request(
                "playlist/addTracks",
                playlist_id=self.id,
                comma_encoding=False,
                track_ids=",".join(map(str, c)),
                user_auth_token=own.auth_token,
            )

    def del_tracks(self, tracks, own, max_elements_per_request=50):
        """Delete tracks from the playlist.

        In order to limit the length of the resulting URL for a very large
        number of tracks, split the request into multiple.

        Parameters
        ----------
        tracks: list: Track or int (playlist track id)
            Tracks to be deleted. Note that the id used here, is Track.playlist_track_id, returned via Playlist.get_tracks
        own: User
            Deleting tracks requires a logged in User
        max_elements_per_request: int
            Split the request into multiple. Each with at most this many tracks
        """
        if isinstance(tracks[0], int):
            track_ids = tracks
        else:
            track_ids = [t.playlist_track_id for t in tracks]

        for c in self._split_into_chunks(track_ids, max_elements_per_request):
            api.request(
                "playlist/deleteTracks",
                playlist_id=self.id,
                comma_encoding=False,
                playlist_track_ids=",".join(map(str, c)),
                user_auth_token=own.auth_token,
            )

    @classmethod
    def from_id(cls, playlist_id, user=None):
        token = user.auth_token if user is not None else None

        playlist = api.request(
            "playlist/get", playlist_id=playlist_id, user_auth_token=token
        )

        return cls(playlist, user=user)

    @classmethod
    def search(cls, query, limit=50, offset=0, user=None):
        """Search for a playlist.

        Parameters
        ----------
        query: str
            Search query
        limit: int
            Number of elements returned per request
        offset: int
            Offset from which to obtain limit elements

        Returns
        -------
        list of Playlist
            Resulting playlists for the search query
        """
        playlists = api.request(
            "playlist/search", 
            query=query, limit=limit, offset=offset,
            user_auth_token=user.auth_token if user is not None else None,
            )

        return [cls(p, user) for p in playlists["playlists"]["items"]]
