#!/usr/bin/python
import os
import sys
import time
import json
import urllib
import requests
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


class MovieEventHandler(PatternMatchingEventHandler):
    """
    En docstring
    """
    patterns = ["*.avi", "*.mkv"]

    def format_subtitle(self, metadata):
        return metadata["overview"]

    def format_title(self, metadata):
        return metadata["title"]

    def get_metadata(self, movie_name):
        api_key = os.environ["THEMOVIEDB_API_KEY"]
        query = {'api_key': api_key, 'language': 'en-US',
                 'query': movie_name, 'page': '1', 'include_adult': 'false'}
        url_encoded_query = urllib.urlencode(query)
        response = requests.get(
            "https://api.themoviedb.org/3/search/movie?" + url_encoded_query)
        if response.status_code != 200:
            raise ValueError(
                'Request to themoviedb returned an error %s, the response is:\n%s'
                % (response.status_code, response.text)
            )
        else:
            j = json.loads(response.content)
            results = j["results"]
            print results
            if len(results) > 0:
                return results[0]
            else:
                print "Could not find movie"

    def format_poster(self, metadata):
        return "https://image.tmdb.org/t/p/w500" + metadata["poster_path"]

    def on_created(self, event):
        server_name = os.environ["PLEX_SERVER_NAME"]
        webhook_url = os.environ["PLEX_WEBHOOK"]
        movie_name = os.path.basename(event.src_path)
        movie_name = movie_name.split('.')[0]
        metadata = self.get_metadata(movie_name)
        slack_data = {"channel": "#general",
                      "username": "Nya filmer",
                      "attachments": [{
                          "fallback:": "hnnn",
                          "text": self.format_subtitle(metadata),
                          "icon_emoji": ":vhs:",
                          "color": "#a67a2d",
                          "title": self.format_title(metadata),
                          "thumb_url": self.format_poster(metadata),
                          "footer":  server_name + " la just till '" + movie_name + "' :beers:",
                      }]
                      }

        response = requests.post(
            webhook_url, data=json.dumps(slack_data),
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code != 200:
            raise ValueError(
                'Request to slack returned an error %s, the response is:\n%s'
                % (response.status_code, response.text)
            )


def check_environ():
    missing = False
    if os.environ["PLEX_SERVER_NAME"] == None:
        print "Please set 'PLEX_SERVER_NAME'"
        missing = True
    if os.environ["PLEX_WEBHOOK"] == None:
        print "Please set 'PLEX_WEBHOOK'"
        missing = True
    if os.environ["THEMOVIEDB_API_KEY"] == None:
        print "Please set 'THEMOVIEDB_API_KEY'"
        missing = True

    if missing:
        sys.exit(-1)


if __name__ == "__main__":
    check_environ()

    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    observer = Observer()
    observer.schedule(MovieEventHandler(), path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
