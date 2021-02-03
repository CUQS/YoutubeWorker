import json
import os
from tqdm import tqdm
import threading
import time
from youtube_dl import YoutubeDL

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

threading_end_count = [0]


def download_process(thread_list, df, data_path, proxy_list):
    df_t = df.loc[thread_list]

    vid_list = [df_t.loc[idx]["vid"] for idx in thread_list]

    count = 0
    
    start = [time.time()]
    end = [start[0]]

    if proxy_list:
        ydl_opts = {
            'ignoreerrors': True,
            'outtmpl': f'{data_path}/'+'%(id)s.%(ext)s',
            'noplaylist': True,
            'sleep_interval': 3,
            'proxy': proxy_list[0]
        }
    else:
        ydl_opts = {
            'ignoreerrors': True,
            'outtmpl': f'{data_path}/'+'%(id)s.%(ext)s',
            'noplaylist': True,
            'sleep_interval': 3
        }
    
    url_list = ["https://www.youtube.com/watch?v="+vid for vid in vid_list]

    if len(url_list) > 25:
        url_list = chunkify(url_list, len(url_list) // 25)
        for ui in url_list:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download(ui)
            end[0] = time.time()
            if (end[0] - start[0]) // 60 > 30:
                time.sleep(300)
                start[0] = time.time()
    else:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download(url_list)

    threading_end_count[0] += 1


def chunkify(lst, n):
    return [lst[i::n] for i in range(n)]


class JsonWorker:
    def __init__(self, load_file="query.json"):
        self.json_file = load_file
        self.save_flag = True
        self.load_json()
    
    def load_json(self):
        if os.path.exists(self.json_file):
            with open(self.json_file, "r") as f:
                self.data_all = json.loads(f.read())
        else:
            self.data_all = {"data": [], "vid": []}
    
    def add_one(self, data, vid):
        self.data_all["data"].append(data)
        self.data_all["vid"].append(vid)
    
    def save(self, name=None):
        save_name = name if name else self.json_file
        if self.save_flag:
            with open(save_name, "w") as f:
                json.dump(self.data_all, f)
        else:
            print("post process is no need to save json file!!")
    
    def check_in(self, vid):
        return vid in self.data_all["vid"]
    
    def to_df(self):
        import pandas as pd
        duration_all = 0
        
        df = {"duration": [], "duration_mod": [], "query": [], "vid": [], "language": []}
        for di in self.data_all["data"]:
            df["duration"].append(di["duration"])

            dura = di["duration"]

            duration_all += di["duration"]

            dura = (dura // 60) // 5
            dura = "{}~{} min".format(dura*5, (dura+1)*5)
            df["duration_mod"].append(dura)

            query_split = di["query"].split("_")
            df["language"].append(query_split[0])

            df["query"].append(query_split[1:])

            df["vid"].append(di["vid"])
        
        print("all of the video have a duration of {:.3f} days".format(duration_all/60/60/24))
        duration_all = duration_all/60/60/24

        return [pd.DataFrame(df), duration_all]


class YoutubeWorker(JsonWorker):
    def __init__(self, download_path, json_file="query.json"):
        super(YoutubeWorker, self).__init__(json_file)
        self.data_path = download_path if download_path[-1] != "/" else download_path[:-1]
        self.file_all = []
        self.file_type = []
        self.part_file = []
        self.rest_file = []
        self.get_downloaded_part()
        self.save_flag = False
        
    def youtube_query(self, page=30, max_minu=30):
        print("---------------- query youtube... ----------------")
        for language in list(query_all):
            for query in list(query_all[language]):
                time.sleep(3)
                page_finish = os.system("python query_script.py --query '{}' --json_file {} --language {} --page {} --max_minu {}".format(query, self.json_file, language, page, max_minu))
                if page_finish != 256:
                    time.sleep(3)
                    os.system("python query_script.py --query '{}' --json_file {} --language {} --page {} --max_minu {}".format(query, self.json_file, language, page, max_minu))
        time.sleep(3)
        self.load_json()
        print("finished!!")

    def youtube_download(self, thread_num, proxy_list=None):
        threading_end_count[0] = 0

        self.remove_part()
        self.data_all_to_rest()
        df, _ = self.to_df()

        thread_id = [i for i in range(df["vid"].count())]
        thread_id = chunkify(thread_id, thread_num)

        for idx, ti in enumerate(thread_id):
            print(f"---------------- thread {idx} ----------------")
            th = threading.Thread(target=download_process, args=(ti, df, self.data_path, proxy_list,))
            th.start()
            time.sleep(5)

        while threading_end_count[0] < thread_num:
            continue

    def get_downloaded_part(self):
        print("---------------- check downloaded file... ----------------")
        self.file_type = []
        self.file_all = []
        self.part_file = []
        for root, dirs_name, files_name in os.walk(self.data_path):
            for fi in files_name:
                name_part = fi.split(".")
                if len(name_part) == 2:
                    fn, ft = name_part
                    self.file_all.append(fn)
                    if not ft in self.file_type:
                        self.file_type.append(ft)
                else:
                    self.part_file.append(os.path.join(root, fi))
        print("finished!!")

    def remove_part(self):
        print("---------------- remove incomplete file... ----------------")
        for part_i in tqdm(self.part_file):
            os.remove(part_i)
        print(f"{len(self.part_file)} part files are removed!!")
        print("finished !!")

    def data_all_to_rest(self):
        print("---------------- check rest file... ----------------")
        self.check_rest()
        if len(self.rest_file) > 0:
            print("prepare download info for rest...")
            vid_t = []
            data_all_t = []
            for di in tqdm(self.data_all["data"]):
                if di["vid"] in self.rest_file:
                    data_all_t.append(di)
                    vid_t.append(di["vid"])
            self.data_all["data"] = data_all_t
            self.data_all["vid"] = vid_t
            print("finished!!")
    
    def check_rest(self):
        print("check download filed file...")
        self.rest_file = []
        for fi in tqdm(self.data_all["vid"]):
            if not fi in self.file_all:
                self.rest_file.append(fi)
        print(f"{len(self.rest_file)} rest files")

    def generate_latest(self):
        self.load_json()
        self.get_downloaded_part()
        self.remove_part()

        print("---------------- generate latest json file... ----------------")
        data_all_t = {"data":[], "vid": []}
        for di in tqdm(self.data_all["data"]):
            if di["vid"] in self.file_all:
                data_all_t["vid"].append(di["vid"])
                di["file_name"] = di["vid"]+".{}".format(self.file_type[self.file_all.index(di["vid"])])
                data_all_t["data"].append(di)
        self.data_all = data_all_t
        self.save_flag = True
        self.save(f"latest_{self.json_file}")
        self.save_flag = False


