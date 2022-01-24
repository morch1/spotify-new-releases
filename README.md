# spotify-utils

## usage:
```
python spotify-utils.py config_file.hjson
```

## config.hjson file example:
```
{
    # this part of the file contains basic config such as API credentials for services etc
    
    # some tasks need to store data locally
    db_path: C:\path\to\database.db

    # spotify api info
    spotify: {
        client_id: ...
        client_secret: ...
        redirect_uri: http://localhost:8090
        region: PL
        username: ...
    }

    # lastfm api info
    lastfm: {
        # set all to null if you dont use last.fm (some tasks won't work)
        api_key: ...
        api_secret: ...
        username: ...
        password_hash: ...
        # update scrobbles stored in database before running commands?
        update_scrobbles: true
    }

    # join api info (for notifications)
    join: {
        # set both fields to null to disable notifications
        api_key: ...
        # these devices will receive notifications:
        device_ids: [
            "...",
            "...",
            "...",
        ]
    }

    # below is the list of tasks to perform when this config file is used
    # look inside commands/(name of task).py for explanation of arguments
    tasks: [
        {
            cmd: sync_playlist
            args: {
                dst_playlist_id: ...
                src_playlist_id: ...
                sync_mode: update
            }
        },
        {
            cmd: update_likes_playlist2
            args: {
                dst_playlist_id: ...
                ignore_suffix: ...
            }
        },
        {
            cmd: update_likes_playlist
            args: {
                dst_playlist_id: ...
                other_playlists: [
                    "...",
                    "...",
                    "...",
                ]
                check_albums: true
            }
        },
        {
            cmd: remove_duplicates
            args: {
                playlist_ids: [
                    "...",
                    "...",
                    "...",
                ]
            }
        },
        {
            cmd: update_top_playlist
            args: {
                playlist_id: ...
                num_days: 365
                num_tracks: 100
            }
        },
        {
            cmd: update_top_playlist
            args: {
                playlist_id: ...
                date_end: 1577836800
                num_days: 30
                num_tracks: 30
            }
        },
        {
            cmd: update_on_this_day
            args: {
                2020: ...
                2019: ...
                2018: ...
                2017: ...
                2016: ...
                2015: ...
            }
        },
        {
            cmd: update_playlist_notifications
        }
    ]
}
```
