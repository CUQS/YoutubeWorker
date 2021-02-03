import time
import argparse
from tools import JsonWorker, query_all
from tqdm import tqdm
from youtubesearchpython import VideosSearch


def parse_args():
    parser = argparse.ArgumentParser(description='query youtube and generate json file')
    parser.add_argument('--query', help='query sentence',
                        default='sushi', type=str)
    parser.add_argument('--json_file',
                        default='en', type=str)
    parser.add_argument('--language', help='language',
                        default='en', type=str)
    parser.add_argument('--page', help='max page',
                        default=30, type=int)
    parser.add_argument('--max_minu', help='max minute',
                        default=30, type=int)
    args = parser.parse_args()
    return args


def search_results_select(search_results, max_duration, min_duration=[0, 0, 0]):
    """
    This is for youtubesearchpython.VideosSearch
    --------------
    data format
    --------------
        {
            "result": [
                {
                    "type": "video",
                    "id": "K4DyBUG242c",
                    "title": "Cartoon - On & On (feat. Daniel Levi) [NCS Release]",
                    "publishedTime": "5 years ago",
                    "duration": "3:28",
                    "viewCount": {
                        "text": "389,673,774 views",
                        "short": "389M views"
                    },
                    "thumbnails": [
                        {
                            "url": "https://i.ytimg.com/vi/K4DyBUG242c/hqdefault.jpg?sqp=-oaymwEjCOADEI4CSFryq4qpAxUIARUAAAAAGAElAADIQj0AgKJDeAE=&rs=AOn4CLBkTusCwcZQlmVAaRQ5rH-mvBuA1g",
                            "width": 480,
                            "height": 270
                        }
                    ],
                    "descriptionSnippet": [
                        {
                            "text": "NCS: Music Without Limitations NCS Spotify: http://spoti.fi/NCS Free Download / Stream: http://ncs.io/onandon \u25bd Connect with\u00a0..."
                        }
                    ],
                    "channel": {
                        "name": "NoCopyrightSounds",
                        "id": "UC_aEa8K-EOJ3D6gOs7HcyNg",
                        "thumbnails": [
                            {
                                "url": "https://yt3.ggpht.com/a-/AOh14GhS0G5FwV8rMhVCUWSDp36vWEvnNs5Vl97Zww=s68-c-k-c0x00ffffff-no-rj-mo",
                                "width": 68,
                                "height": 68
                            }
                        ],
                        "link": "https://www.youtube.com/channel/UC_aEa8K-EOJ3D6gOs7HcyNg"
                    },
                    "accessibility": {
                        "title": "Cartoon - On & On (feat. Daniel Levi) [NCS Release] by NoCopyrightSounds 5 years ago 3 minutes, 28 seconds 389,673,774 views",
                        "duration": "3 minutes, 28 seconds"
                    },
                    "link": "https://www.youtube.com/watch?v=K4DyBUG242c",
                    "shelfTitle": null
                },
            ]
        }
    --------------
    parameter
    --------------
        min_duration: 
            default: 
        max_duration: [hours, minutes, seconds]
    --------------
    return
    --------------
        video_meta: []
    """
    video_meta = []
    for ri in search_results["result"]:
        if ri["type"] != "video":
            continue
        if ri["duration"] == None:
            continue
        dur = [int(i) for i in ri["duration"].split(":")]
        dur.reverse()
        dura, min_dura, max_dura = 0, 0, 0
        for i in range(len(dur)):
            dura += dur[i]*60**i
        for i in range(3):
            min_dura += min_duration[i]*60**i
            max_dura += max_duration[i]*60**i
        if min_dura < dura < max_dura:
            video_meta.append({"duration": dura, "vid": ri["id"]})
    return video_meta


def youtube_query(query, json_file, language='en', page=30, max_minu=30):
    json_worker = JsonWorker(json_file)
    page_finish = False
    video_list = []
    videosSearch = VideosSearch(query, language=language)
    print("---------------- {} ----------------".format(query))
    for page_i in tqdm(range(page)):
        error_flag = False
        video_meta = search_results_select(
            videosSearch.result(), max_duration=[0, max_minu, 0])
        if len(video_meta) > 1:
            video_list.extend(video_meta)
        try:
            videosSearch.next()
        except:
            error_flag = True
        if error_flag:
            break
        time.sleep(2)
        if page_i == page-1:
            page_finish = True
    if len(video_list) >= 1:
        count = 0
        for vi in video_list:
            if json_worker.check_in(vi["vid"]):
                continue
            count += 1
            vi["query"] = query_all[language][query]
            json_worker.add_one(vi, vi["vid"])
        if count >= 1:
            print("{}: {}".format(query, count))
            json_worker.save()
        else:
            print("{}: {}".format(query, 0))
    else:
        print("{}: {}".format(query, 0))

    return page_finish


if __name__ == "__main__":
    args = parse_args()
    page_finish = youtube_query(args.query, args.json_file, args.language, args.page, args.max_minu)
    exit(page_finish)
