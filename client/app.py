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

    def get_headers():
        token = page.client_storage.get("token")
        return {"Authorization": f"Bearer {token}"}

    # Объявляем функции заранее, чтобы они видели друг друга
    def show_events():
        page.clean()
        page.appbar = ft.AppBar(title=ft.Text("События"),
                                actions=[ft.IconButton(ft.Icons.PERSON, on_click=lambda _: show_profile())])

        list_view = ft.ListView(expand=True)

        def load():
            list_view.controls.clear()
            res = requests.get(f"{API_URL}/events/", headers=get_headers())
            if res.status_code == 200:
                for ev in res.json():
                    def delete(e, eid=ev['id']):
                        requests.delete(f"{API_URL}/events/{eid}", headers=get_headers())
                        load()

                    list_view.controls.append(ft.ListTile(
                        title=ft.Text(ev['title']),
                        subtitle=ft.Text(ev['description']),
                        trailing=ft.IconButton(ft.Icons.DELETE, on_click=delete)
                    ))
            page.update()

        t_in = ft.TextField(label="Название")
        d_in = ft.TextField(label="Описание")
        cat_in = ft.Dropdown(label="Категория", options=[
            ft.dropdown.Option("IT"), ft.dropdown.Option("Спорт"),
            ft.dropdown.Option("Игры"), ft.dropdown.Option("Другое")
        ])
        date_in = ft.TextField(label="Дата (ГГГГ-ММ-ДД ЧЧ:ММ:СС)")

        def create(e):
            payload = {
                "title": t_in.value,
                "description": d_in.value,
                "category": cat_in.value,
                "event_date": date_in.value.replace(" ", "T") if date_in.value else None
            }
            res = requests.post(f"{API_URL}/events/", headers=get_headers(), json=payload)
            if res.status_code == 200:
                t_in.value = d_in.value = date_in.value = ""
                cat_in.value = None
                load()
            else:
                show_error("Ошибка создания")

        page.add(t_in, d_in, cat_in, date_in, ft.ElevatedButton("Создать событие", icon=ft.Icons.ADD, on_click=create),
                 list_view)
        load()

    def show_profile(e=None):
        page.clean()
        page.appbar = ft.AppBar(title=ft.Text("Мой профиль"),
                                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: show_events()))

        def delete_from_profile(e, eid):
            requests.delete(f"{API_URL}/events/{eid}", headers=get_headers())
            show_profile()

        res = requests.get(f"{API_URL}/users/me/events/", headers=get_headers())
        if res.status_code == 200:
            data = res.json()
            created_list = ft.ListView(expand=True)
            for ev in data['created']:
                created_list.controls.append(ft.ListTile(
                    title=ft.Text(ev['title']),
                    subtitle=ft.Text(ev['category']),
                    trailing=ft.IconButton(ft.Icons.DELETE,
                                           on_click=lambda e, eid=ev['id']: delete_from_profile(e, eid))
                ))

            joined_list = ft.ListView(expand=True)
            for ev in data['participated']:
                joined_list.controls.append(ft.ListTile(title=ft.Text(ev['title'])))

            page.add(ft.Text("Созданные:", weight="bold"), created_list, ft.Divider(),
                     ft.Text("Участие:", weight="bold"), joined_list)
        page.update()

    def show_auth():
        page.appbar = None
        page.clean()
        u_in = ft.TextField(label="Email")
        p_in = ft.TextField(label="Пароль", password=True)
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
                    show_error("Ошибка входа")
            else:
                res = requests.post(f"{API_URL}/users/", json={"email": u_in.value, "password": p_in.value})
                if res.status_code == 200:
                    toggle_mode(None)
                else:
                    show_error("Ошибка регистрации")

        btn_action = ft.ElevatedButton("Войти", on_click=submit)
        btn_toggle = ft.TextButton("Нет аккаунта? Регистрация", on_click=toggle_mode)
        page.add(u_in, p_in, btn_action, btn_toggle)

    show_auth()


ft.app(target=main)