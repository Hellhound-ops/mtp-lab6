"""Проверки страниц, входа, доступа к кабинету и выхода."""

import unittest

from werkzeug.security import generate_password_hash

from main import create_app


class SiteTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app({
            "TESTING": True,
            "SECRET_KEY": "unit-test-key",
            "LAB_USER": "Учебный пользователь",
            "LAB_PASSWORD_HASH": generate_password_hash("unit-test-password"),
            "SESSION_COOKIE_SECURE": False,
        }).test_client()

    def test_public_pages(self):
        for path, marker in (
            ("/", "styles.css"),
            ("/bootstrap", "bootstrap.min.css"),
            ("/catalog", "Циклы и функции"),
            ("/static/styles.css", "color-scheme"),
        ):
            with self.subTest(path=path), self.client.get(path) as response:
                self.assertEqual(response.status_code, 200)
                self.assertIn(marker, response.get_data(as_text=True))

    def test_login_and_logout(self):
        self.assertEqual(self.client.get("/account").location, "/login")
        self.assertEqual(self.client.post("/login").status_code, 400)
        self.assertEqual(self.client.get("/login").status_code, 200)
        with self.client.session_transaction() as data:
            token = data["csrf_token"]
        form = {"csrf_token": token, "username": "Учебный пользователь", "password": "wrong"}
        self.assertEqual(self.client.post("/login", data=form).status_code, 401)
        self.assertEqual(self.client.get("/account").location, "/login")
        form["password"] = "unit-test-password"
        response = self.client.post("/login", data=form, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Вы вошли", response.get_data(as_text=True))
        self.assertEqual(self.client.post("/logout", data={"csrf_token": token}).status_code, 400)
        with self.client.session_transaction() as data:
            new_token = data["csrf_token"]
        self.assertEqual(self.client.post("/logout", data={"csrf_token": new_token}).location, "/")
        self.assertEqual(self.client.get("/account").location, "/login")
