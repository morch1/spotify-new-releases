# spotify-utils

tools for automatic management of spotify library

## how to run

1. create `config.hjson` according to provided example

1. run the command below to authenticate with spotify (the token is then cached so you only need to do this once)
    ```
    docker-compose run --rm spotify_utils python auth.py
    ```

1. start the tool
    ```
    docker-compose up -d
    ```
