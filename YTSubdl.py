import youtube_dl
import json
import requests
import threading
import time
import re
import vtt2srt
from urllib.parse import parse_qs
import os
from languages import languages
from pathlib import Path
import argparse
import re 
import sys




yt_url_pattern = '^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$'

def playlist_extract(url):
    videos = {}
    ydl_opts = {
            'dump-json': True,
            'quiet':True,
            'extract_flat':"in_playlist",
            'flat-playlist':True,
            }
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
    except:
        return 
    
    for video in info_dict['entries']:
        videos[video['id']] = [video["title"],"https://www.youtube.com/watch?v="+video["id"]]
    return videos
    
                           
def extract_subtitles(url):
    
    ydl_opts = {
            'dump-json': True,
            'quite':True,
            'writeautomaticsub':True,
            'writesubtitles':True,
            }
            
    
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
    
   
    title = info_dict['title']
    
    automatic_captions = info_dict.get('automatic_captions',{})
    subtitles = info_dict.get('subtitles',{})
    
    return subtitles,automatic_captions
    
def print_to_screen(typ,text):
    if _print:
        print(typ+" : "+text)

       
def yturl_validator(url):
    match = re.findall(yt_url_pattern,url)
    if not match:
        return 
    if 'youtube.com' in url.lower() or 'youtu.be' in url.lower():
        if 'list=' in url or 'watch?v=' in url:
            return True
  
def get_info(url):
    yt_videos = {}
    if "list=" in url:
        print("Downloading playlist info...")
        playlist_videos = playlist_extract(url)
        print("Downloaded playlist info.")
        if playlist_videos:
            yt_videos.update(playlist_videos)
        return yt_videos
    
    print("Downloading video info...")
    ydl_opts = {
            'dump-json': True,
            'quiet':True,
            }
    
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
    
    print("Downloaded video info.")
    title = info_dict['title']
    video_id = info_dict['id']
    yt_videos[video_id] = [title,"https://www.youtube.com/watch?v="+video_id]
    return yt_videos
    
def verify_language_code(code):
    langs = languages.get("639-3")
    for lang in langs:
        if lang.get("alpha_2","not_exist") == code:
            return [lang['name'],code]
        
            
def prepare_arguments(args):
    parsed_args = {}
    
    url = args.url
    if not yturl_validator(url):
        print("Error > Invalid Youtube Url")
        sys.exit(1) 
    
    language_code = args.language.lower() if len(args.language)<3 else args.language.lower()[0:2]
    language = verify_language_code(language_code)
    if not language:
        print(f"Error > The language code '{language_code}' doesn't corresponds to any langauge.\
                                \nOmit to use default English")
        sys.exit(1)
        
    output_path = args.output
    if not os.path.exists(output_path):
        print(f"Error > The output path '{output_path}' doesn't exists.\
                                \nOmit to use default Downloads Folder")
        sys.exit(1)
    
    sub_type = args.type
    if sub_type not in ['autocc','subs']:
        print(f"Error > Wrong subtitle type, Use 'autocc' or 'subs'.\
                                \nOr omit to use default autocc")
        sys.exit(1)
    parsed_args['url'] = url
    parsed_args['language'] = language
    parsed_args['output_path'] = output_path
    parsed_args['sub_type'] = sub_type
    
    return parsed_args


def download_subtitle(video_url,video_title,lang,sub_type,output_path):
    subtitles,automatic_captions = extract_subtitles(video_url)
    
    if sub_type=='autocc':
        subtitles = automatic_captions
    
    for lang_code,formats in subtitles.items():
        if lang_code!=lang:
            continue
        
        for fmt in formats:
            if fmt['ext']!='vtt':
                continue
            r = requests.get(fmt['url'])
            filename = re.sub('[\\\\/*?:"<>|]', '', video_title)+'-'+lang+'.srt'
            save_path = os.path.join(output_path,filename)
            
            vtt2srt.convert_vtt_to_srt_v3(r.content.decode('utf8'),save_path)
            return save_path
    
    

def main():
    global _print
    _print = True
    
    arg_parser = argparse.ArgumentParser(description='Download Subtitles for YouTube Videos')
    arg_parser.add_argument('-u','--url',metavar=' ',type=str,help='Youtube Video or Playlist url,\n\
                                                                    Input ex. "{url}" with double quotes no brackets',required=True)
    arg_parser.add_argument('-l','--language',metavar=' ',type=str,help="language code e.g, 'en' for English.",default='en')
    arg_parser.add_argument('-o','--output',metavar=' ',type=str,help='Output save path.\n\
                                                                        Input ex. "{output_path}" with double quotes no brackets',default=os.path.join(Path.home(), "Downloads"))
    arg_parser.add_argument('-t','--type',metavar=' ',type=str,help='Subtitle type "autocc" or "subs".\n \
                                                                    autocc - autogenrated subtitles by YouTube.\n\
                                                                    subs - subtitles added by uploader.',default="autocc")
    
       
    args = prepare_arguments(arg_parser.parse_args())

    video_info = get_info(args['url'])
    lang = args['language']
    sub_type = args['sub_type']
    output_path = args['output_path']
    for video,info in video_info.items():
        try:
            saved_path = download_subtitle(info[1],
                                info[0],
                                lang[1],
                                sub_type,
                                output_path)
           
            
            print(f"Downloaded {info[0]} to \"{saved_path}\"")
            
        except Exception as e:
            print(e)
            print(f"Failed to download  {info[0]}")
    
    
if __name__ == '__main__':            
    main()