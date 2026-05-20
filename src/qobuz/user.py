from qobuz import Artist, Album, Track, Playlist
from qobuz.qopy import qobuz_api


class User(object):
    """Own user to be logged in.

    Parameters
    ----------
    username: str
        Username or e-mail of the user
    password: str
        Password for the username
    """

    def _get_params_splitted(self, kwargs, chunk_size=50):
        """Get all ids from kwarg, split params into chunk"""

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

        artist_ids = get_ids(kwargs, "artists")
        album_ids = get_ids(kwargs, "albums")
        track_ids = get_ids(kwargs, "tracks")

        params_split = []
        while True:
            params = {}
            cur_size = 0

            ids, artist_ids = artist_ids[:chunk_size], artist_ids[chunk_size:]
            if ids:
                params["artist_ids"] = ids
                cur_size += len(ids)
                if cur_size == chunk_size:
                    params_split.append(params)
                    continue

            ids, album_ids = (
                album_ids[: chunk_size - cur_size],
                album_ids[chunk_size - cur_size :],
            )
            if ids:
                params["album_ids"] = ids
                cur_size += len(ids)
                if cur_size == chunk_size:
                    params_split.append(params)
                    continue

            ids, track_ids = (
                track_ids[: chunk_size - cur_size],
                track_ids[chunk_size - cur_size :],
            )
            if ids:
                params["track_ids"] = ids
                cur_size += len(ids)
                if cur_size == chunk_size:
                    params_split.append(params)
                    continue

            if cur_size > 0:
                params_split.append(params)
            break

        # reformat (api syntax changed)
        #   old way : [{'album_ids': '0075596094863','lqp0ziq8w7n83'}]
        #   new way : [{'album_ids': '0075596094863,lqp0ziq8w7n83}]
        for dtype in params_split:
            for key in dtype:
                dtype[key] = ','.join(dtype[key])
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
            True if all items were successfully added, False if any failed
        """
        all_success = True
        for params in self._get_params_splitted(kwargs):
            status = qobuz_api.api_call("favorite/create", **params)
            if status.get("status") != "success":
                all_success = False
        return all_success

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
            True if all items were successfully deleted, False if any failed
        """
        all_success = True
        for params in self._get_params_splitted(kwargs):
            status = qobuz_api.api_call(
                "favorite/delete",
                **params,
            )
            if status.get("status") != "success":
                all_success = False
        return all_success

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
        status = qobuz_api.api_call(
            "favorite/status",
            item=obj.id,
            type=obj.type,
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
        favorites = qobuz_api.api_call(
            "favorite/getUserFavorites",
            type=fav_type,
            limit=limit,
            offset=offset,
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
            all_favorites.append(Album(f) for f in favorites["albums"]["items"])
            all_favorites.append(
                Track(
                    f,
                )
                for f in favorites["tracks"]["items"]
            )
            return all_favorites

    def playlists_get(self, filter="owner", limit=50, offset=0, raw=False):
        result = qobuz_api.api_call(
            "playlist/getUserPlaylists",
            filter=filter,
            limit=limit,
            offset=offset,
        )
        if raw:
            return result
        return [Playlist(p) for p in result["playlists"]["items"]]

    def playlist_create(self, name, description=None, is_public=0, is_collaborative=0):
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
        playlist = qobuz_api.api_call(
            "playlist/create",
            name=name,
            description=description,
            is_public=is_public,
            is_collaborative=is_collaborative,
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
        status = qobuz_api.api_call(
            "playlist/delete",
            playlist_id=id,
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
        resp = qobuz_api.api_call(
            "track/getFileUrl",
            signed=True,
            track_id=track_id,
            format_id=format_id,
            intent=intent,
        )

        return resp.get("url")
