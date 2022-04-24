import os
import json
import requests
import yt_dlp
from huepy import *

STREAM_LINK = "master.m3u8"

def read_json(filename: str) -> dict:		
	with open(filename, 'r', encoding='utf-8') as f:
		data = json.loads(f.read())
		return data

def create_dir(course_name: str, module_name: str) -> str:
	path = f"Cursos\\{course_name}\\Videos\\{module_name}"
	os.makedirs(path, exist_ok=True)
	
	return path

info = read_json('info.json')

url = info['url']
filename = info['filename']
course_name = info['course_name']
module_name = info['module_name']

path = create_dir(course_name, module_name)

path = f"{path}\\{filename}"



def down_m3u8():
	with requests.get(url, stream=True) as r:
		r.raise_for_status()
		with open(STREAM_LINK, 'wb') as f:
			for chunk in r.iter_content(chunk_size=8192): 
				f.write(chunk)


def downloader():

	#aa = requests.get(url).text
	#print(aa)

	ydl_opts = {
	    'retries': 8,
	    'fragment_retries': 6,
	    'quiet': True,
	    'outtmpl': f'{path}'
    }

	try:
		with yt_dlp.YoutubeDL(ydl_opts) as ydl:
			ydl.download(url)
	except Exception as e:
	 	print("Deu um erro com o link do Vimeo, reporte!")



def main():
	banner = f"""
 	 _   ___          _ _           _
 	| | / (_)        (_) |         | |
 	| |/ / ___      ___| |__   ___ | |_
 	|    \| \ \ /\ / / | '_ \ / _ \| __|
 	| |\  \ |\ V  V /| | |_) | (_) | |_
 	\_| \_/_| \_/\_/ |_|_.__/ \___/ \__|
 	
 	
::{bold(lightred("by Joa Roque"))} | Telegram: {under("https://t.me/joa_roque")} 

"""
	print(banner)
	downloader()
if __name__ == "__main__":
	main()
	exit()