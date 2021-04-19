import os
import sys
import logging
import base64
import json

import requests

from .threaded_aio_dlder import AioDownloader


def ensure_dir(directory):
    directory = os.path.abspath(directory)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    return directory

class Downloader:
    def __init__(self, api_key, api_secret, bearer_token=None, thread_number=2, coro_number=5):
        self.log = logging.getLogger("downloader")
        if bearer_token:
            self.bearer_token = bearer_token
        else:
            self.bearer_token = self.bearer(api_key, api_secret)
        self.log.info("Bearer token is " + self.bearer_token)
        self.d = AioDownloader()
        self.d.start(thread_number, coro_number)

    def bearer(self, key, secret):
        """Receive the bearer token and return it.

        Args:
            key: API key.
            secret: API string.
        """

        # setup
        credential = base64.b64encode(
            bytes("{}:{}".format(key, secret), "utf-8")
        ).decode()
        url = "https://api.twitter.com/oauth2/token"
        headers = {
            "Authorization": "Basic {}".format(credential),
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        }
        payload = {"grant_type": "client_credentials"}

        # post the request
        r = requests.post(url, headers=headers, params=payload)

        # check the response
        if r.status_code == 200:
            return r.json()["access_token"]
        else:
            raise RuntimeError("Bearer TokenNot Fetched")

    def download_media_of_tweet(self, tid, save_dest, size="large", include_video=False, 
            include_photo=True, is_extended=False, goto_quoted=False):
        ''' '''    
        save_dest = ensure_dir(save_dest)

        tweet = self.get_tweet(tid, is_extended)
        self.process_tweet(tweet, save_dest, size, include_video, include_photo, goto_quoted)

    def download_media_of_user(self, user, save_dest, size="large", limit=3200, rts=False, 
        include_video=False, include_photo=True, since_id=0):
        """Download and save images that user uploaded.

        Args:
            user: User ID.
            save_dest: The directory where images will be saved.
            size: Which size of images to download.
            rts: Whether to include retweets or not.
        """

        save_dest = ensure_dir(save_dest)

        alltweets = self.get_user_tweets(user, None, limit, rts, since_id)
        self.log.info(f"{user} Got {len(alltweets)} tweets")
        for tweet in alltweets:
            self.process_tweet(tweet, save_dest, include_video=include_video, include_photo=include_photo)

    def download_media_of_list(self, user, listname, save_dest, size="large", limit=3200, 
        rts=False, include_video=False, include_photo=True, since_id=0):
        """Download and save images of a list.

        Args:
            user: list owner name.
            listname: list slug
            save_dest: The directory where images will be saved.
            size: Which size of images to download.
            rts: Whether to include retweets or not.
        """

        save_dest = ensure_dir(save_dest)

        alltweets = self.get_list_tweets(user, listname, None, limit, rts, since_id)
        self.log.info(f"{user}:{listname} Got {len(alltweets)} tweets")
        for tweet in alltweets:
            self.process_tweet(tweet, save_dest, include_video=include_video, include_photo=include_photo)

    def api_fetch_tweets(self, url, payload, start, count, rts, since_id):
        # setup
        bearer_token = self.bearer_token
        headers = {"Authorization": "Bearer {}".format(bearer_token)}

        payload["count"]=  count
        payload["include_rts"] = rts
        if start:
            payload["max_id"] = start - 1  #max_id is inclusive
        if since_id:
            payload["since_id"] = since_id #since_id is exclusive

        alltweets = []
        while True:
            # get the request
            r = requests.get(url, headers=headers, params=payload)
            # check the response
            tweets = []
            if r.status_code == 200:
                tweets = r.json()
            else:
                self.log.error(f"{url} error, code: {r.status_code}")
            
            if not tweets:
                break

            alltweets.extend(tweets)
            payload["max_id"] = tweets[-1]['id'] - 1
            payload['count'] = count - len(alltweets)

            if len(alltweets) >= count:
                #self.log.info(f" the number of tweets {len(alltweets)} checked reach the limit {count}")
                break
            if len(tweets) < 200: # No more tweets left:200 is the twitter-api limit
                break
        
        #self.log.info(f"Got {len(alltweets)} tweets")
        return alltweets

    def get_user_tweets(self, user, start=None, count=200, rts=False, since_id=0):
        """Download user's tweets and return them as a list.

        Args:
            user: User ID.
            start: Tweet ID.
            rts: Whether to include retweets or not.
        """

        apiurl = "https://api.twitter.com/1.1/statuses/user_timeline.json"
        payload = {"screen_name": user}

        return self.api_fetch_tweets(apiurl, payload, start, count, rts, since_id)

    def get_list_tweets(self, username, listname, start=None, count=200, rts=False, since_id=0):
        """Download user's tweets and return them as a list.

        Args:
            user: User ID.
            start: Tweet ID.
            rts: Whether to include retweets or not.
        """
        apiurl = "https://api.twitter.com/1.1/lists/statuses.json"
        payload = {"owner_screen_name": username, "slug":listname}
        
        return self.api_fetch_tweets(apiurl, payload, start, count, rts, since_id)

    def get_tweet(self, tid, is_extended=False):
        """Download single tweet

        Args:
            tid: Tweet ID.
            is_extended: extended tweet mode
        """

        bearer_token = self.bearer_token
        url = "https://api.twitter.com/1.1/statuses/show.json"
        headers = {"Authorization": f"Bearer {bearer_token}"}
        payload = {"id": tid, "include_entities": "true"}
        if is_extended:
            self.log.info("Extended mode")
            payload["tweet_mode"] = "extended"
        # get the request
        r = requests.get(url, headers=headers, params=payload)

        # check the response
        if r.status_code == 200:
            tweet = r.json()
            self.log.info(f"Got tweet with id {tid} of user @{tweet['user']['name']}")
            return tweet
        else:
            self.log.error(f"{url} error, code was {r.status_code}")
            return None

    def process_tweet(self, tweet, save_dest, size="large", include_video=False, include_photo=True, goto_quoted=False):
        if 'retweeted_status' in tweet:
            tweet = tweet['retweeted_status']
            self.log.debug('this is a retweet, turn to orignal tweet')
        elif ("quoted_status" in tweet) and goto_quoted:
            tweet = tweet['quoted_status']
            self.log.debug('this is a quoted tweet, turn to orignal tweet')

        id_str = tweet["id_str"]
        # save the image
        images = self.extract_media_list(tweet, include_video, include_photo)
        for i, image in enumerate(images, 1):
            self.save_media(image, save_dest, f"{id_str}-{i}", size)

        return len(images)

    def extract_media_list(self, tweet, include_video, include_photo):
        """Return the url of the image embedded in tweet.

        Args:
            tweet: A dict object representing a tweet.
        """
        extended = tweet.get("extended_entities")
        if not extended:
            return []

        rv = []
        if "media" in extended:
            for x in extended["media"]:
                if x["type"] == "photo" and include_photo: 
                    url = x["media_url"]
                    rv.append(url)
                elif x["type"] in ["video", "animated_gif"] and include_video:
                    variants = x["video_info"]["variants"]
                    variants.sort(key=lambda x: x.get("bitrate", 0))
                    url = variants[-1]["url"].rsplit("?tag")[0]
                    rv.append(url)
        return rv

    def save_media(self, image, path, name, size="large"):
        """Download and save an image to path.

        Args:
            image: The url of the image.
            path: The directory where the image will be saved.
            name: It is used for naming the image.
            size: Which size of images to download.
        """
        if image:
            # image's path with a new name
            ext = os.path.splitext(image)[1]
            save_file = os.path.join(path, name + ext)
            if ext not in [".mp4"]:
                real_url = image + ":" + size
            else:
                real_url = image

            # save the image in the specified directory (or don't)
            #ensure_dir(save_file)
            if not (os.path.exists(save_file)):
                self.d.add_url(real_url, save_file)
            else:
                self.log.info(f"Skipping downloaded {image}")
