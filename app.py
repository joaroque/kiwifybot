import os
import secrets
import threading

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from kiwify import KIWIBOT_ERRORS, Kiwibot

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
bot = Kiwibot()
bot_lock = threading.Lock()


def csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


app.jinja_env.globals["csrf_token"] = csrf_token


@app.context_processor
def template_state():
    return {"bot_logged": bot.is_logged}


def require_csrf():
    provided = request.form.get("csrf_token")
    expected = session.get("csrf_token")
    if not provided or not expected or not secrets.compare_digest(provided, expected):
        abort(400)


def require_login():
    return None if bot.is_logged else redirect(url_for("login"))


email = os.environ.get("KIWIFY_EMAIL")
password = os.environ.get("KIWIFY_PASSWORD")
if email and password:
    try:
        bot.login(email, password)
    except KIWIBOT_ERRORS:
        print("Aviso: não foi possível realizar o login automático.")


@app.route("/")
def index():
    redirect_response = require_login()
    if redirect_response:
        return redirect_response
    try:
        return render_template("index.html.j2", courses=bot.get_courses())
    except KIWIBOT_ERRORS:
        flash("Não foi possível consultar os cursos.", "danger")
        return render_template("index.html.j2", courses=[]), 502


@app.route("/course")
def course():
    redirect_response = require_login()
    if redirect_response:
        return redirect_response
    return render_template(
        "course.html.j2", course=bot.get_modules(request.args.get("courseId", ""))
    )


@app.route("/module")
def module():
    redirect_response = require_login()
    if redirect_response:
        return redirect_response
    course_id = request.args.get("courseId", "")
    return render_template(
        "module.html.j2",
        course=bot.get_modules(course_id),
        module_id=request.args.get("moduleId", ""),
    )


@app.post("/download")
def downloader():
    require_csrf()
    redirect_response = require_login()
    if redirect_response:
        return redirect_response
    try:
        with bot_lock:
            result = bot.downloader(
                request.form.get("courseId", ""),
                request.form.get("moduleId", ""),
                request.form.get("lessonId", ""),
                request.form.get("type", ""),
                request.form.get("fileId") or None,
            )
        if result:
            status, destination = result
            message = (
                "Arquivo já existente" if status == "skipped" else "Download concluído"
            )
            flash(f"{message}: {destination}", "success")
        else:
            flash("Aula ou arquivo não encontrado.", "danger")
    except KIWIBOT_ERRORS as error:
        print(f"Erro de download: {error}")
        flash("O download falhou. Consulte o terminal para mais detalhes.", "danger")
    return redirect(request.referrer or url_for("index"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if bot.is_logged:
        return redirect(url_for("index"))
    if request.method == "POST":
        require_csrf()
        try:
            bot.login(request.form.get("email", ""), request.form.get("password", ""))
            return redirect(url_for("index"))
        except KIWIBOT_ERRORS:
            flash("E-mail ou senha inválidos.", "danger")
    return render_template("login.html.j2")


@app.post("/logout")
def logout():
    require_csrf()
    bot.logout()
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
