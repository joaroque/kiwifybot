import os
import json
from requests import Session
import pickle
import shutil
from huepy import *

from pathvalidate import sanitize_filename



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

	def get_courses(self) -> dict:
		courses = self._s.get(self.COURSES_URL).json()
		total_courses = courses['count']
		courses_fetched = 10
		courses_list = courses['courses']
		page_count = 1

		while courses_fetched < total_courses:
		    account_courses = self._s.get(f"https://api.kiwify.com.br/v1/viewer/courses?&page={page_count}").json()
		    page_count += 1
		    courses_fetched += 10
		    courses_list.append(account_courses['courses'])

		with open('aa.json', 'w', encoding='utf-8') as f:
			json.dump(courses_list, f, ensure_ascii=False, indent=4)
		return courses_list
		
		#c = courses_list[0]
		#infos = self._s.get(f"https://api.kiwify.com.br/v1/viewer/courses/{c['id']}").json()


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
		course_name = self.sanatize(info[0])
		module_name = self.sanatize(info[1])
		filename = info[2]
		file_url = info[3]


		path = self.create_dir(course_name, module_name, file_type)
		file = self.download(file_url, filename, file_type)
		self.move(file, path)

	# Baixar
	def download(self, url: str, filename: str, file_type) -> None:
		url = url.strip()
		
		print(run(f"Baixando:"))
		print(run("Aguarde..."))
		
		if file_type == 'pdf':
			url = self._s.get(url).json()
			url = url['url']

		s = Session()

		with s.get(url, stream=True) as r:
			r.raise_for_status()
			with open(filename, 'wb') as f:
				for chunk in r.iter_content(chunk_size=8192): 
					f.write(chunk)
		print(good("Baixado com sucesso"))
		return filename

	def create_dir(self, course_name: str, module_name: str, file_type: str) -> str:
		if file_type == 'pdf':
			path = f"Cursos\\{course_name}\\Videos\\{module_name}\\PDFs"
			os.makedirs(path, exist_ok=True)
		
		if file_type == 'video':
			path = f"Cursos\\{course_name}\\Videos\\{module_name}"
			os.makedirs(path, exist_ok=True)
		
		return path


	def move(self, file: str, dest: str) -> None:
		path = f"{dest}\\{file}"
		
		if not os.path.exists(path):
			shutil.move(file, dest)
		else:
			print(bad("O arquivo já existe"))


	def extract_info(self, 
		course_id: str, 
		module_id: str, 
		lesson_id: str, 
		file_type: str) -> None:
		courses = self.get_courses()
		for course in courses:
			if course_id == course['id']:
				course_name = course['name']
				
				modules = self.get_modules(course_id)
				for module in modules['course']['modules']:
					if module_id == module['id']:
						module_name = module['name']

						for lesson in module['lessons']:
							if lesson_id == lesson['id']:
								if lesson['files']:
									file_id = lesson['files'][0]['id']
									filename = lesson['files'][0]['name']
									file_url = "https://api.kiwify.com.br/v1/viewer/courses/"
									file_url += f"{course_id}/files/{file_id}?forceDownload=true"
									
									#file_url = lesson['files'][0]['url']

								if lesson['video']:
									videoname = lesson['video']['name']
									video_url = lesson['video']['download_link']

		if file_type == 'video':
			return [course_name, module_name, videoname, video_url]
		else:
			return [course_name, module_name, filename, file_url]



# bot = Kiwibot()
# bot.login("thiagoplrmkt@gmail.com","Cursos1234")
# bot.get_courses()
# bot.downloader("0805c38a-9841-4c4a-afe7-7944e2ad89d8", 
# 			"889addb8-e305-48eb-a8f1-5b124944201c", 
# 			"22c1362d-ce29-4dd0-92bb-5c14c09d6f85",
# 			"video")
