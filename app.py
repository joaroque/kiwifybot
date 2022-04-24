import json
import requests

from kiwify import Kiwibot

from flask import (
	Flask,
	flash, 
	request, 
	url_for, 
	redirect,
	render_template
	)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sdfgh5ehezxs323r'

def read_json(filename: str, path=None) -> str:		
	with open(filename, 'r', encoding='utf-8') as f:
		data = json.loads(f.read())
		return data

bot = Kiwibot()
creds = read_json('login.json')
bot.login(creds['email'],creds['password'])


@app.route('/', methods=['POST', 'GET'])
def index():
	if not bot._is_logged: 
		return "<h1>Erro ao iniciar sessão</h1>"
	courses = bot.get_courses()
	return render_template('index.html.j2', courses=courses)


def write_json(data, name):
	name = f'{name}.json'
	with open(name, 'w', encoding='utf-8') as f:
		json.dump(data, f, ensure_ascii=False, indent=4)


@app.route('/course')
def course():
	course_id = request.args.get('courseId')

	course = bot.get_modules(course_id)
	return render_template('course.html.j2', course=course)


@app.route('/module')
def module():
	course_id = request.args.get('courseId')
	module_id = request.args.get('moduleId')

	course = bot.get_modules(course_id)

	return render_template('module.html.j2', 
		course=course, 
		module_id=module_id)


@app.route('/download')
def downloader():
	course_id = request.args.get('courseId')
	module_id = request.args.get('moduleId')
	lesson_id = request.args.get('lesson_id')
	file_type = request.args.get('type')
	
	# pdf or video
	bot.downloader(course_id, module_id, lesson_id, file_type)

	flash('O download iniciará em breve', category="success")
	return '<script>document.location.href = document.referrer</script>'


@app.route('/login', methods=['POST', 'GET'])
def login():
	if bot._is_logged:
		return redirect('/')

	if request.method == 'POST':
		email = request.form.get('email')
		password  = request.form.get('password')

		try:
			r = bot.login(email, password)
			return redirect('/')

		except Exception as e:
			flash('Erro ao fazer login', category='danger')
			flash(e, category='danger')

	return render_template('login.html.j2')


@app.route('/logout', methods=['GET'])
def logoutFlask():
	bot.logout()
	return redirect('/login')





if __name__ == '__main__':
	app.run(port=5000, debug=False)