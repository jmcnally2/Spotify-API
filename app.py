"""
    This code was based on these repositories,
    so special thanks to:
        https://github.com/datademofun/spotify-flask
        https://github.com/drshrey/spotify-flask-auth-example

"""

from flask import Flask, request, redirect, g, render_template, session
from spotify_requests import spotify
from random import randrange

app = Flask(__name__)
app.secret_key = "some key for session"

# ----------------------- AUTH API PROCEDURE -------------------------


@app.route("/auth")
def auth():
    return redirect(spotify.AUTH_URL)


@app.route("/callback/")
def callback():
    auth_token = request.args["code"]
    auth_header = spotify.authorize(auth_token)
    session["auth_header"] = auth_header

    return profile()


def valid_token(resp):
    return resp is not None and not "error" in resp


# -------------------------- API REQUESTS ----------------------------


@app.route("/")
def index():
    return render_template("profile.html")


@app.route("/artist/<id>")
def artist(id):
    artist = spotify.get_artist(id)

    if artist["images"]:
        image_url = artist["images"][0]["url"]
    else:
        image_url = "http://bit.ly/2nXRRfX"

    tracksdata = spotify.get_artist_top_tracks(id)
    tracks = tracksdata["tracks"]

    related = spotify.get_related_artists(id)
    related = related["artists"]

    return render_template(
        "artist.html",
        artist=artist,
        related_artists=related,
        image_url=image_url,
        tracks=tracks,
    )


@app.route("/profile")
def profile():
    if "auth_header" in session:
        auth_header = session["auth_header"]
        # get profile data
        profile_data = spotify.get_users_profile(auth_header)

        # get user playlist data
        playlist_data = spotify.get_users_playlists(auth_header)

        # get user recently played tracks
        recently_played = spotify.get_users_recently_played(auth_header)

        if valid_token(recently_played):
            return render_template(
                "profile.html",
                user=profile_data,
                playlists=playlist_data["items"],
                recently_played=recently_played["items"],
            )

    return render_template("profile.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/featured_playlists")
def featured_playlists():
    if "auth_header" in session:
        auth_header = session["auth_header"]
        hot = spotify.get_featured_playlists(auth_header)
        if valid_token(hot):
            return render_template("featured_playlists.html", hot=hot)

    return render_template("profile.html")


@app.route("/recommended")
def recommended():
    if "auth_header" in session:
        auth_header = session["auth_header"]

        tracks = spotify.get_users_top(auth_header, "tracks")
        top_tracks = [0] * 2
        for i in range(2):
            top_tracks[i] = tracks["items"][i]["id"]

        artists = spotify.get_users_top(auth_header, "artists")
        top_artists = [0] * 2
        for i in range(2):
            top_artists[i] = artists["items"][i]["id"]

        genre_seed = artists["items"][0]["genres"][
            randrange(len(artists["items"][0]["genres"]))
        ]

        recommendations = spotify.get_recommended_tracks(
            auth_header, top_artists, top_tracks, genre_seed
        )

        return render_template(
            "recommended.html", recom_songs=recommendations, auth_header=auth_header
        )

    return render_template("profile")


@app.route("/save_track/<track_id>/<track_name>")
def save_track(track_id, track_name):
    if "auth_header" in session:
        auth_header = session["auth_header"]

        spotify.put_new_saved_track(auth_header, track_id)

        return render_template(
            "track_saved.html", track_id=track_id, track_name=track_name
        )

    return render_template("profile")


if __name__ == "__main__":
    app.run(debug=True, port=spotify.PORT)

