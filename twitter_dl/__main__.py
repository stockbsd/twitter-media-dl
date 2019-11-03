import os
import argparse
import json
import logging

from . import Downloader


def main():
    DEBUG = os.getenv("DEBUG")
    logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO,
        format='%(levelname)-7s %(name)11s: %(message)s')

    parser = argparse.ArgumentParser(
        description="Download all images uploaded by a twitter user you specify"
    )
    parser.add_argument(
        "resource_id",
        help="An ID of a twitter user. Also accept tweet url or tweet id.",
    )
    parser.add_argument("dest", help="Specify where to put images")
    parser.add_argument(
        "-c",
        "--confidential",
        help="a json file containing a key and a secret",
        default=os.getenv("TWITTER_AUTH", os.path.expanduser("~/.twitter.json")),
    )
    parser.add_argument(
        "-s",
        "--size",
        help="specify the size of images",
        default="orig",
        choices=["large", "medium", "small", "thumb", "orig"],
    )
    parser.add_argument(
        "--tweet",
        help="indicate you gived a tweet id",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--list",
        help="indicate you gived a list by user:slug",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--file",
        help="indicate you gived a username file",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--video", help="include video", default=False, action="store_true"
    )
    parser.add_argument(
        "--nophoto", dest="photo", help="exclude photo", action="store_false"
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        help="the maximum number of tweets to check (most recent first)",
        default=3200,
    )
    parser.add_argument(
        "--since",
        type=int,
        help="the min id of tweets to check (most recent first)",
        default=0,
    )
    parser.add_argument(
        "--rts", help="save images contained in retweets", action="store_true"
    )
    parser.add_argument("--thread-number", type=int, default=2)
    parser.add_argument("--coro-number", type=int, default=5)
    args = parser.parse_args()

    if args.confidential:
        with open(args.confidential) as f:
            confidential = json.loads(f.read())
        
        bearer_token = confidential.get("bearer_token")
        api_key = confidential.get("consumer_key")
        api_secret = confidential.get("consumer_secret")
        if not (bearer_token or (api_key and api_secret)):
            raise RuntimeError("Confidentials Not Supplied")
    else:
        raise RuntimeError("Confidentials Not Supplied")

    downloader = Downloader(api_key, api_secret, bearer_token, args.thread_number, args.coro_number)

    if args.tweet:
        downloader.download_media_of_tweet(args.resource_id, args.dest, args.size, args.video, 
            args.photo)
        downloader.d.join()
    elif args.list:
        username, listname = args.resource_id.split(':')
        downloader.download_media_of_list(username, listname, args.dest, args.size, 
            args.limit, args.rts, args.video, args.photo, args.since)
        downloader.d.join()      
    elif args.file:
        with open(args.resource_id) as f:
            for line in f:
                id = line.strip()
                if id and not id.startswith('#'):
                    try:
                        downloader.download_media_of_user(id, args.dest, args.size, 
                            args.limit, args.rts, args.video, args.photo, args.since)
                    except Exception as e:
                        pass
            downloader.d.join()
    else:
        downloader.download_media_of_user(args.resource_id, args.dest, args.size, 
            args.limit, args.rts, args.video, args.photo, args.since)
        downloader.d.join()
    #print('finished!')


if __name__ == "__main__":
    main()
