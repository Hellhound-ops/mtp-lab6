"""ЛР №6, вариант 3: Flask, шаблоны и вход в личный кабинет."""

import os
import secrets

import click
from flask import Flask, abort, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


BOOKS = (
    {"title": "Структурное программирование", "topic": "Циклы и функции"},
    {"title": "Объектно-ориентированное программирование", "topic": "Классы и наследование"},
    {"title": "Веб-программирование", "topic": "Маршруты и шаблоны"},
)


def create_app(config=None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        LAB_USER=os.getenv("LAB_USER"),
        LAB_PASSWORD_HASH=os.getenv("LAB_PASSWORD_HASH"),
        SESSION_COOKIE_SECURE=bool(os.getenv("DYNO")),
        SESSION_COOKIE_SAMESITE="Lax",
        MAX_CONTENT_LENGTH=8192,
    )
    if config:
        app.config.update(config)

    def check_form_token() -> None:
        token = session.get("csrf_token")
        submitted = request.form.get("csrf_token", "")
        if not token or not secrets.compare_digest(token.encode(), submitted.encode()):
            abort(400, description="Некорректный токен формы")

    @app.get("/")
    def home():
        return app.send_static_file("index.html")

    @app.get("/bootstrap")
    def bootstrap_page():
        return render_template("bootstrap.html")

    @app.get("/catalog")
    def catalog():
        return render_template("catalog.html", books=BOOKS)

    @app.route("/login", methods=("GET", "POST"))
    def login():
        expected = app.config["LAB_USER"]
        password_hash = app.config["LAB_PASSWORD_HASH"]
        if not (app.secret_key and expected and password_hash):
            return render_template("login.html", configured=False), 503
        if request.method == "POST":
            check_form_token()
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            valid_password = check_password_hash(password_hash, password)
            if not valid_password or not secrets.compare_digest(expected.encode(), username.encode()):
                return render_template("login.html", configured=True, invalid=True), 401
            session.clear()
            session.update(username=expected, csrf_token=secrets.token_urlsafe(32))
            return redirect(url_for("account"))
        session.setdefault("csrf_token", secrets.token_urlsafe(32))
        return render_template("login.html", configured=True)

    @app.get("/account")
    def account():
        if not session.get("username") or session["username"] != app.config["LAB_USER"]:
            return redirect(url_for("login"))
        return render_template("account.html")

    @app.post("/logout")
    def logout():
        check_form_token()
        session.clear()
        return redirect(url_for("home"))

    @app.cli.command("make-credentials")
    def make_credentials():
        """Создать хеш пароля и случайный ключ для конфигурации."""
        password = click.prompt("Пароль", hide_input=True, confirmation_prompt=True)
        click.echo(f"LAB_PASSWORD_HASH={generate_password_hash(password)}")
        click.echo(f"SECRET_KEY={secrets.token_hex(32)}")

    return app


app = create_app()


if __name__ == "__main__":
    app.run()
