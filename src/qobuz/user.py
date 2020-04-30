import hashlib
import uuid

from qobuz import api, Artist, Album, Track, Playlist


class User(object):
    """Own user to be logged in.

    Some operations require an authenticated user.

    Parameters
    ----------
    username: str
        Username or e-mail of the user
    password: str
        Password for the username
    """

    def __init__(self, username, password, device_manufacturer_id=None):
        self.username = username
        if device_manufacturer_id is None:
            device_manufacturer_id = uuid.uuid4()

        login_resp = api.request(
            "user/login",
            username=username,
            password=self._hash_password(password),
            device_manufacturer_id=device_manufacturer_id,
        )

        self.auth_token = login_resp["user_auth_token"]
        self.id = login_resp["user"]["id"]
        self.credential_id = login_resp["user"]["credential"]["id"]
        self.device_id = login_resp["user"]["device"]["id"]

    @staticmethod
    def _hash_password(password):
        """Hash the password with MD5.

        Parameters
        ----------
        password: str
            Plain password

        Returns
        -------
        str
            Hashed password to be used for logging in
        """
        return hashlib.md5(password.encode()).hexdigest()

    @staticmethod
    def reset_password(username):
        """Request the resetting of the current password.

        Parameters
        ----------
        username: str
            Username to be sent a email with instructions.

        Returns
        -------
        bool
            Successfully requested
        """
        resp = api.request("user/resetPassword", username=username)

        return resp.get("status") == "success"


    def _get_params_splitted(self, kwargs, chunk_size=50):
        """Get all ids from kwarg, split params into chunk
        """
        def get_ids(args, name):
            value = args.get(name)
            if not value: 
                return []
            if not isinstance(value, list):
                value = [value]
            if len(value) == 0:
                return []
            if isinstance(value[0], int) or isinstance(value[0], str):
                return value
            return [v.id for v in value]

        artist_ids = get_ids(kwargs, 'artists')
        album_ids = get_ids(kwargs, 'albums')
        track_ids = get_ids(kwargs, 'tracks')

        params_split = list()
        while True:
            params = {}
            params["user_auth_token"] = self.auth_token
            cur_size = 0

            ids, artist_ids = artist_ids[:chunk_size], artist_ids[chunk_size:]
            if len(ids):
                params["artist_ids"] = ids
                cur_size += len(ids) 
                if cur_size == chunk_size:
                    params_split.append(params)
                    continue

            ids, album_ids = album_ids[:chunk_size - cur_size], album_ids[chunk_size - cur_size:]
            if len(ids):
                params["album_ids"] = ids
                cur_size += len(ids) 
                if cur_size == chunk_size:
                    params_split.append(params)
                    continue

            ids, track_ids = track_ids[:chunk_size - cur_size], track_ids[chunk_size - cur_size:]
            if len(ids):
                params["track_ids"] = ids
                cur_size += len(ids)
                if cur_size == chunk_size:
                    params_split.append(params)
                    continue

            if cur_size > 0:
                params_split.append(params)
            break

        return params_split


    def favorites_add(self, **kwargs):
        """Add artists/albums/tracks to user's favorites.

        kwargs
        ----------
        artists : Artist, int, str or list of these
        albums : Album, int or str or list of these
        tracks : Track, int, str or list of these

        Returns
        -------
        bool
            Successfully added to favorites
        """

        for params in  self._get_params_splitted(kwargs):
            status = api.request(
                "favorite/create",
                **params
            )
            if status.get("status") != "success":
                return False
        return True

    def favorites_del(self, **kwargs):
        """Delete artists/albums/tracks from favorites.

        Parameters
        ----------
        artists : Artist, int, str or list of these
        albums : Album, int or str or list of these
        tracks : Track, int, str or list of these

        Returns
        -------
        bool
            Successfully deleted from favorites
        """

        for params in  self._get_params_splitted(kwargs):
            status = api.request(
                "favorite/delete",
                **params,
            )
            if status.get("status") != "success":
                return False
        return True

    def favorites_status(self, obj):
        """Get status whether obj is in the favorites.

        Parameters
        ----------
        obj: Artist/Album/Track
            Object to be added to the favorites

        Returns
        -------
        bool
            Successfully deleted from favorites
        """
        status = api.request(
            "favorite/status",
            item=obj.id,
            type=obj.type,
            user_auth_token=self.auth_token,
        )

        return status.get("status") == "true"

    def favorites_get(self, fav_type=None, limit=50, offset=0, raw=False):
        """Get all favorites for the user.

        Parameters
        ----------
        fav_type: str
            Favorite type: 'artists', 'albums' or 'tracks'
        limit: int
            Number of elements returned per request
        offset: int
            Offset from which to obtain limit elements
        raw: bool
            results will be returned as json if True

        Returns
        -------
        list
            List containing Artist/Album/Track objects
        """
        favorites = api.request(
            "favorite/getUserFavorites",
            type=fav_type,
            limit=limit,
            offset=offset,
            user_auth_token=self.auth_token,
        )

        if raw:
            return favorites

        if fav_type == "artists":
            return [Artist(f) for f in favorites["artists"]["items"]]
        if fav_type == "albums":
            return [Album(f) for f in favorites["albums"]["items"]]
        if fav_type == "tracks":
            return [Track(f) for f in favorites["tracks"]["items"]]
        else:
            all_favorites = [Artist(f) for f in favorites["artists"]["items"]]
            all_favorites.append(
                Album(f) for f in favorites["albums"]["items"]
            )
            all_favorites.append(
                Track(f) for f in favorites["tracks"]["items"]
            )
            return all_favorites

    def playlists_get(self, filter="owner", limit=50, offset=0, raw=False):
        result = api.request(
            "playlist/getUserPlaylists",
            filter=filter,
            limit=limit,
            offset=offset,
            user_auth_token=self.auth_token,
        )

        if raw:
            return result
        return [Playlist(p, user=self) for p in result["playlists"]["items"]]

    def playlist_create(
        self, name, description=None, is_public=0, is_collaborative=0
    ):
        """Create a new playlist.

        Parameters
        ----------
        name: str
            Name for the new playlist
        description: str
            Description for the playlist
        is_public: bool
            Flag to make the playlist public.
        is_collaborative: bool
            Flag to make the playlist collaborative.
        """
        playlist = api.request(
            "playlist/create",
            name=name,
            description=description,
            is_public=is_public,
            is_collaborative=is_collaborative,
            user_auth_token=self.auth_token,
        )

        return Playlist(playlist)

    def playlist_delete(self, playlist):
        """Delete a playlist.

        Parameters
        ----------
        playlist: Playlist or int (playlist id)
            Playlist to be deleted

        Returns
        -------
        bool
            Successfully deleted playlist
        """
        if isinstance(playlist, int):
            id = playlist
        else:
            id = playlist.id
        status = api.request(
            "playlist/delete",
            playlist_id=id,
            user_auth_token=self.auth_token,
        )

        return status.get("status") == "success"

    def get_file_url(self, track_id, format_id=None, intent=None):
        """Get the file url for a track.

        Parameters
        ----------
        track_id: int
            Track-ID to get the url for
        format_id: int
            Format ID following qobuz specifications:
             5: MP3 320
             6: FLAC Lossless
             7: FLAC Hi-Res 24 bit =< 96kHz,
            27: FLAC Hi-Res 24 bit >96 kHz & =< 192 kHz
        intent: str
            How the application will use the file URL
            Either 'stream', 'import', or 'download'.

        Returns
        -------
        str
            URL to the appropriate file
        """
        resp = api.request(
            "track/getFileUrl",
            signed=True,
            track_id=track_id,
            format_id=format_id,
            intent=intent,
            user_auth_token=self.auth_token,
        )

        return resp.get("url")
