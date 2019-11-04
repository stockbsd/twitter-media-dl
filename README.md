# Download twitter resources

Download tweet images and videos. Run threads which has a event loop to download resources asynchronously.

```
pip3 install twitter-dl
```

```
usage: twitter-dl [-h] [-c CONFIDENTIAL]
                                  [-s {large,medium,small,thumb,orig}]
                                  [--video] [--nophoto]
                                  [-l LIMIT] [--rts]
                                  [--thread-number THREAD_NUMBER]
                                  [--coro-number CORO_NUMBER]
                                  [--since SID]
                                  [--tweet] [--list] [--file]
                                  resource_id dest

Download all images and/or videos uploaded by a twitter user you specify

positional arguments:
  resource_id           An ID of a twitter user. Also accept user id files, list or
                        tweet id.
  dest                  Specify where to put images/videos

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIDENTIAL, --confidential CONFIDENTIAL
                        a json file containing (a key and a secret) or bearer_token
  -s {large,medium,small,thumb,orig}, --size {large,medium,small,thumb,orig}
                        specify the size of images
  --tweet               indicate resource_id is a numbered tweet id
  --list                indicate resource_id is a list (user:slug) 
  --file                indicate resource_id is a username file(each in a line)
  --video               include video
  --nophoto             exclude photo
  -l LIMIT, --limit LIMIT
                        the maximum number of tweets to check (most recent first)
  --rts                 save images contained in retweets
  --thread-number       THREAD_NUMBER
  --coro-number         CORO_NUMBER
  --since               SID
```

```
Examples:
    twitter-dl --tweet 1191067520033337345 pv
    twitter-dl --rts -l 10 --video ladygaga pv
    twitter-dl --rts -l 10 --video --nophoto --list YouTube:hey-fam pv
    twitter-dl --rts -l 10 --video --file idfiles.txt pv
```