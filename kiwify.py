import os
import sys
import json
import requests
from requests import Session
import pickle
import shutil
from huepy import *

from pathvalidate import sanitize_filename

if sys.platform == 'win32':
	try:
		sys.stdout.reconfigure(encoding='utf-8', errors='replace')
		sys.stderr.reconfigure(encoding='utf-8', errors='replace')
	except Exception:
		pass



class Kiwibot:
	
	LOGIN_URL = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key=AIzaSyDmOO1YAGt0X35zykOMTlolvsoBkefLKFU"
	COURSES_URL = "https://api.kiwify.com.br/v1/viewer/courses?&page=1"
	
	def __init__(self) -> None:
		self._s = Session()
		self._is_logged = False
		self._s.headers['user-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36'

	def sanatize(self, string: str) -> str:
		string = sanitize_filename(string)
		return string

	def login(self, email: str, pwd: str) -> bool:
		data = {
    		'email': f'{email}', 
    		'password': f'{pwd}', 
    		'returnSecureToken': True
		}
		
		auth_dict = self._s.post(self.LOGIN_URL, data=data).json()
		self._s.headers['authorization'] = f"Bearer {auth_dict['idToken']}"
			
		self._is_logged = True
		
		return True

	def logout(self) -> None:
		self._s = Session()
		self._s.headers['user-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36'
		self._is_logged = False

	def get_courses(self) -> list:
		res = self._s.get(self.COURSES_URL).json()
		total_courses = res.get('count', 0)
		courses_list = res.get('courses', [])
		courses_fetched = len(courses_list)
		page_count = 2

		while courses_fetched < total_courses:
			account_courses = self._s.get(f"https://api.kiwify.com.br/v1/viewer/courses?&page={page_count}").json()
			new_courses = account_courses.get('courses', [])
			if not new_courses:
				break
			courses_list.extend(new_courses)
			courses_fetched += len(new_courses)
			page_count += 1

		return courses_list

	def get_modules(self, module_id: str) -> dict:
		modules = self._s.get(f"https://api.kiwify.com.br/v1/viewer/courses/{module_id}").json()
		return modules

	def get_lessons(self, module_id: str) -> dict:
		lessons = self._s.get(f"https://api.kiwify.com.br/v1/viewer/courses/{module_id}").json()
		return lessons

	def downloader(self, 
		course_id: str, 
		module_id: str, 
		lesson_id: str, 
		file_type: str) -> None:
		info = self.extract_info(course_id, 
								module_id, 
								lesson_id, 
								file_type)
		if not info:
			print(bad("Aula ou arquivo não encontrado!"))
			return

		course_name = self.sanatize(info[0])
		module_name = self.sanatize(info[1])
		filename = info[2]
		file_url = info[3]

		if not file_url:
			print(bad("Link de download não disponível para esta aula!"))
			return

		self.download(file_url,
					filename, 
					file_type,
					course_name, 
					module_name)

	def write_json(self, data: dict, name: str) -> None:
		with open(f'{name}.json', 'w', encoding='utf-8') as file:
			json.dump(data, file, ensure_ascii=False, indent=4)

	# Baixar
	def download(self, 
		url: str, 
		filename: str, 
		file_type: str, 
		course_name: str, 
		module_name: str) -> None:

		url = url.strip()
		
		if file_type == 'pdf':
			print(run(f"Baixando PDF: {filename}"))
			print(run("Aguarde..."))

			dest_dir = self.create_dir(course_name, module_name, 'pdf')
			dest_file = os.path.join(dest_dir, filename)

			try:
				r = self._s.get(url, stream=True)
				r.raise_for_status()

				# Caso a API retorne um JSON com a URL de download redirecionada
				if 'application/json' in r.headers.get('Content-Type', ''):
					data = r.json()
					download_url = data.get('url') or data.get('download_url')
					if download_url:
						r = requests.get(download_url, stream=True)
						r.raise_for_status()

				with open(dest_file, 'wb') as f:
					for chunk in r.iter_content(chunk_size=8192):
						if chunk:
							f.write(chunk)

				print(good(f"PDF baixado com sucesso: {dest_file}"))
				return dest_file
			except Exception as e:
				print(bad(f"Erro ao baixar PDF: {e}"))
				return None

		else:
			data = {
				"url": url,
				"filename": filename,
				"course_name": course_name,
				"module_name": module_name
			}

			self.write_json(data, "info")
			python_exe = sys.executable
			os.system(f'start "Kiwify Downloader" cmd /K ""{python_exe}" downloader.py"')

	def create_dir(self, course_name: str, module_name: str, file_type: str) -> str:
		if file_type == 'pdf':
			path = os.path.join("Cursos", course_name, "Videos", module_name, "PDFs")
		else:
			path = os.path.join("Cursos", course_name, "Videos", module_name)
		os.makedirs(path, exist_ok=True)
		return path

	def move(self, file: str, dest: str) -> None:
		path = os.path.join(dest, file)
		if not os.path.exists(path):
			shutil.move(file, dest)
		else:
			print(bad("O arquivo já existe"))

	def extract_info(self, 
		course_id: str, 
		module_id: str, 
		lesson_id: str, 
		file_type: str):
		modules = self.get_modules(course_id)
		course_data = modules.get('course', {})
		course_name = course_data.get('name', 'Curso')

		for module in course_data.get('modules', []):
			if module.get('id') == module_id:
				module_name = module.get('name', 'Modulo')

				for lesson in module.get('lessons', []):
					if lesson.get('id') == lesson_id:
						lesson_title = (lesson.get('title') or '').strip()

						if file_type == 'video' and lesson.get('video'):
							video = lesson['video']
							video_url = (
								video.get('stream_link_full_url')
								or video.get('download_link_full_url')
								or video.get('stream_link')
								or video.get('download_link')
								or video.get('url')
							)

							if video_url and video_url.startswith('/'):
								video_url = f"https://d3pjuhbfoxhm7c.cloudfront.net{video_url}"

							name = lesson_title or video.get('name') or 'video'
							name = self.sanatize(name).strip()
							if not name.lower().endswith(('.mp4', '.mkv', '.mov', '.webm', '.avi')):
								name = f"{name}.mp4"

							return [course_name, module_name, name, video_url]

						elif file_type == 'pdf' and lesson.get('files'):
							file_obj = lesson['files'][0]
							file_name = file_obj.get('name', 'anexo.pdf')
							filename = self.sanatize(file_name).strip()
							file_url = file_obj.get('url') or f"https://api.kiwify.com.br/v1/viewer/courses/{course_id}/files/{file_obj['id']}?forceDownload=true"
							return [course_name, module_name, filename, file_url]

		return None




# bot = Kiwibot()
# bot.login("thiagoplrmkt@gmail.com","Cursos1234")
# bot.get_courses()
# bot.downloader("0805c38a-9841-4c4a-afe7-7944e2ad89d8", 
# 			"889addb8-e305-48eb-a8f1-5b124944201c", 
# 			"22c1362d-ce29-4dd0-92bb-5c14c09d6f85",
# 			"video")
