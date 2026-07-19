import flet as ft
import requests

API_URL = "http://127.0.0.1:8000"


def main(page: ft.Page):
    page.title = "EventMaster"
    page.window.width = 400
    page.window.height = 700

    def show_error(msg):
        page.snack_bar = ft.SnackBar(content=ft.Text(msg), bgcolor=ft.Colors.RED_400)
        page.snack_bar.open = True
        page.update()

    # --- Экран авторизации ---
    def show_auth():
        page.clean()
        u_in = ft.TextField(label="Email")
        p_in = ft.TextField(label="Пароль", password=True)

        # Переключатель режима
        mode = "login"

        def toggle_mode(e):
            nonlocal mode
            mode = "register" if mode == "login" else "login"
            btn_action.text = "Зарегистрироваться" if mode == "register" else "Войти"
            btn_toggle.text = "Уже есть аккаунт? Войти" if mode == "register" else "Нет аккаунта? Регистрация"
            page.update()

        def submit(e):
            if mode == "login":
                res = requests.post(f"{API_URL}/token", data={"username": u_in.value, "password": p_in.value})
                if res.status_code == 200:
                    page.client_storage.set("token", res.json()["access_token"])
                    show_events()
                else:
                    show_error("Ошибка входа: неверные данные")
            else:
                # Регистрация использует эндпоинт /users/
                res = requests.post(f"{API_URL}/users/", json={"email": u_in.value, "password": p_in.value})
                if res.status_code == 200:
                    page.snack_bar = ft.SnackBar(content=ft.Text("Регистрация успешна! Теперь войдите."))
                    page.snack_bar.open = True
                    toggle_mode(None)  # Переключаем обратно на логин
                else:
                    show_error("Ошибка регистрации: возможно, email уже занят")

        btn_action = ft.ElevatedButton("Войти", on_click=submit)
        btn_toggle = ft.TextButton("Нет аккаунта? Регистрация", on_click=toggle_mode)

        page.add(u_in, p_in, btn_action, btn_toggle)

    # --- Экран событий ---
    def show_events():
        page.clean()
        token = page.client_storage.get("token")
        headers = {"Authorization": f"Bearer {token}"}

        list_view = ft.ListView(expand=True)

        def load():
            list_view.controls.clear()
            res = requests.get(f"{API_URL}/events/", headers=headers)
            if res.status_code == 200:
                for ev in res.json():
                    # Удаление
                    def delete(e, eid=ev['id']):
                        requests.delete(f"{API_URL}/events/{eid}", headers=headers)
                        load()

                    list_view.controls.append(ft.ListTile(
                        title=ft.Text(ev['title']),
                        subtitle=ft.Text(ev['description']),
                        trailing=ft.IconButton(ft.Icons.DELETE, on_click=delete)
                    ))
            page.update()

        # Создание
        t_in = ft.TextField(label="Название")
        d_in = ft.TextField(label="Описание")
        cat_in = ft.TextField(label="Категория")
        date_in = ft.TextField(label="Дата (ГГГГ-ММ-ДД ТЧЧ:ММ:СС)")

        def create(e):
            data = {"title": t_in.value, "description": d_in.value, "category": cat_in.value,
                    "event_date": date_in.value}
            requests.post(f"{API_URL}/events/", headers=headers, json=data)
            load()

        page.add(t_in, d_in, cat_in, date_in, ft.ElevatedButton("Создать", on_click=create), list_view)
        load()

    show_auth()


ft.app(target=main)