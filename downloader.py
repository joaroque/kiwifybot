import os
import sys
import json
import requests
import yt_dlp
from huepy import *

if sys.platform == 'win32':
	try:
		sys.stdout.reconfigure(encoding='utf-8', errors='replace')
		sys.stderr.reconfigure(encoding='utf-8', errors='replace')
	except Exception:
		pass

def read_json(filename: str) -> dict:		
	with open(filename, 'r', encoding='utf-8') as f:
		data = json.loads(f.read())
		return data

def create_dir(course_name: str, module_name: str) -> str:
	path = os.path.join("Cursos", course_name, "Videos", module_name)
	os.makedirs(path, exist_ok=True)
	return path

def downloader(json_path: str = 'info.json'):
	if not os.path.exists(json_path):
		print(bad(f"Arquivo de informações '{json_path}' não encontrado!"))
		return

	info = read_json(json_path)

	url = info['url'].strip()
	filename = info['filename']
	course_name = info['course_name']
	module_name = info['module_name']

	# Corrige links relativos da Kiwify
	if url.startswith('/'):
		url = f"https://d3pjuhbfoxhm7c.cloudfront.net{url}"

	dir_path = create_dir(course_name, module_name)
	file_path = os.path.join(dir_path, filename)

	ydl_opts = {
		'retries': 10,
		'fragment_retries': 10,
		'quiet': False,
		'no_warnings': False,
		'outtmpl': file_path,
		'windowsfilenames': True,
	}

	print(run(f"Curso: {course_name}"))
	print(run(f"Módulo: {module_name}"))
	print(run(f"Arquivo: {filename}"))
	print(run("Iniciando download, aguarde...\n"))

	try:
		with yt_dlp.YoutubeDL(ydl_opts) as ydl:
			ydl.download([url])
		print("\n" + good(f"Vídeo baixado com sucesso: {file_path}"))
	except Exception as e:
		print("\n" + bad(f"Erro ao baixar o vídeo: {e}"))

def main():
	banner = r"""
 	 _   ___          _ _           _
 	| | / (_)        (_) |         | |
 	| |/ / ___      ___| |__   ___ | |_
 	|    \| \ \ /\ / / | '_ \ / _ \| __|
 	| |\  \ |\ V  V /| | |_) | (_) | |_
 	\_| \_/_| \_/\_/ |_|_.__/ \___/ \__|
""" + f"\n::{bold(lightred('by Joa Roque'))} | Telegram: {under('https://t.me/joa_roque')}\n\n"

	print(banner)
	json_file = sys.argv[1] if len(sys.argv) > 1 else 'info.json'
	downloader(json_file)

if __name__ == "__main__":
	main()
