# Youtube Search & Download

## requirements

- youtube-dl
- youtubesearchpython

## useage

- **before running**

  check and modify your "*query_all*" in [tools.py](tools.py)

```python
query_all = {
    "fr": {
        "jouer tennis": "fr_playing tennis"
    },
    "en":{
        "playing tennis": "en_playing tennis"
    },
    "ja":{
        "テニスをやる": "ja_playing tennis"
    },
    "de":{
        "tennis spielen": "de_playing tennis"
    },
    "zh": {
        "打网球": "zh_playing tennis"
    }
}
```

### query

```python
from tools import YoutubeWorker
youtube_worker = YoutubeWorker(download_path="./", json_file="query.json")
youtube_worker.youtube_query(page=30, max_minu=30)
```

- *youtube_query* only need to run once before download
- after *youtube_query* , generated json file "*query.json*" like this

```python
{
    "data": [
        {"duration": 135, "vid": "60w7mf1Z6tg", "query": "fr_playing tennis"}, 
        {"duration": 165, "vid": "-Ymf3BMDfcY", "query": "fr_playing tennis"}
    ]
    "vid": [
        "60w7mf1Z6tg", "-Ymf3BMDfcY"
    ]
}
```

### download

```python
youtube_worker = YoutubeWorker(download_path="./", json_file="query.json")
youtube_worker.youtube_download(thread_num=4)
# if you have a list of proxy
# youtube_worker.youtube_download(thread_num=4, proxy_list=["proxy1", "proxy2"])
```

- *youtube_download* will check "*query.json*" and files in *donwload_path* and remove incomplete files, then download the rest of the file.
- you could run *youtube_download* several times to download all of the files (Please Limit the duration of download)

### generate latest json file

```python
youtube_worker = YoutubeWorker(download_path="./", json_file="query.json")
youtube_worker.generate_latest()
```

- "*generate_latest*" will remove incomplete files and generate all the avaliable file' json file "*latest_query_json*"

```python
{
    "data": [
        {"duration": 135, "vid": "60w7mf1Z6tg", "query": "fr_playing tennis", "file_name": "60w7mf1Z6tg.mp4"}, 
        {"duration": 165, "vid": "-Ymf3BMDfcY", "query": "fr_playing tennis", "file_name": "-Ymf3BMDfcY.mp4"}
    ]
    "vid": [
        "60w7mf1Z6tg", "-Ymf3BMDfcY"
    ]
}
```
