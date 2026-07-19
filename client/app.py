import flet as ft
import requests
from datetime import datetime, timezone

# TODO: вынести в переменную окружения / конфиг перед деплоем
API_URL = "http://127.0.0.1:8000"

CATEGORIES = ["IT", "Спорт", "Игры", "Музыка", "Образование", "Другое"]

CATEGORY_COLORS = {
    "IT": ft.Colors.BLUE,
    "Спорт": ft.Colors.GREEN,
    "Игры": ft.Colors.PURPLE,
    "Музыка": ft.Colors.PINK,
    "Образование": ft.Colors.ORANGE,
    "Другое": ft.Colors.BLUE_GREY,
}


def main(page: ft.Page):
    page.title = "EventMaster"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.INDIGO)
    page.padding = 0
    page.window.width = 460
    page.window.height = 920
    page.bgcolor = ft.Colors.GREY_50
    page.window.center()

    def show_success(message: str):
        page.snack_bar = ft.SnackBar(content=ft.Text(message, color=ft.Colors.WHITE), bgcolor=ft.Colors.GREEN_600)
        page.snack_bar.open = True
        page.update()

    def show_error(message: str):
        page.snack_bar = ft.SnackBar(content=ft.Text(message, color=ft.Colors.WHITE), bgcolor=ft.Colors.RED_400)
        page.snack_bar.open = True
        page.update()

    def perform_action(method, url, callback):
        token = page.client_storage.get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        try:
            if method == "delete":
                res = requests.delete(url, headers=headers)
            else:
                res = requests.post(url, headers=headers)
            if res.status_code == 200:
                callback()
            else:
                show_error(f"Ошибка {res.status_code}")
        except requests.exceptions.RequestException as e:
            show_error("Нет соединения с сервером")
            print(f"Error: {e}")

    def confirm_dialog(message: str, on_confirm):
        """Диалог подтверждения перед необратимым действием (например, удалением события)."""
        confirm_dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Подтверждение"),
            content=ft.Text(message),
            shape=ft.RoundedRectangleBorder(radius=14),
        )

        def close(e):
            confirm_dlg.open = False
            page.update()

        def proceed(e):
            confirm_dlg.open = False
            page.update()
            on_confirm()

        confirm_dlg.actions = [
            ft.TextButton("Отмена", on_click=close),
            ft.TextButton("Удалить", style=ft.ButtonStyle(color=ft.Colors.RED_600), on_click=proceed),
        ]
        page.overlay.append(confirm_dlg)
        confirm_dlg.open = True
        page.update()

    # ==================== ЭКРАН ВХОДА / РЕГИСТРАЦИИ ====================
    def show_auth_screen(mode="login"):
        page.appbar = None
        page.clean()
        is_login = mode == "login"

        u_in = ft.TextField(label="Имя пользователя", prefix_icon=ft.Icons.PERSON_OUTLINE, width=320)
        p_in = ft.TextField(label="Пароль", password=True, can_reveal_password=True,
                            prefix_icon=ft.Icons.LOCK_OUTLINE, width=320)

        def do_login(e):
            if not u_in.value or not p_in.value:
                show_error("Заполните все поля")
                return
            try:
                res = requests.post(f"{API_URL}/login", json={"username": u_in.value, "password": p_in.value})
                if res.status_code == 200:
                    data = res.json()
                    page.client_storage.set("access_token", data["access_token"])
                    page.client_storage.set("current_user", data["username"])
                    page.client_storage.set("current_user_id", data["user_id"])
                    show_events_screen()
                else:
                    show_error("Неверный логин или пароль")
            except requests.exceptions.RequestException as ex:
                show_error("Нет соединения с сервером")
                print(f"Error: {ex}")

        def do_register(e):
            if not u_in.value or not p_in.value:
                show_error("Заполните все поля")
                return
            try:
                res = requests.post(f"{API_URL}/register", json={"username": u_in.value, "password": p_in.value})
                if res.status_code == 200:
                    show_auth_screen("login")
                    show_success("Регистрация успешна! Теперь войдите в аккаунт")
                else:
                    detail = res.json().get("detail", "Ошибка регистрации")
                    show_error(detail)
            except requests.exceptions.RequestException as ex:
                show_error("Нет соединения с сервером")
                print(f"Error: {ex}")

        action_button = ft.ElevatedButton(
            "Войти" if is_login else "Зарегистрироваться",
            on_click=do_login if is_login else do_register,
            width=320, height=45,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
        )

        switch_button = ft.TextButton(
            "Нет аккаунта? Зарегистрироваться" if is_login else "Уже есть аккаунт? Войти",
            on_click=lambda e: show_auth_screen("register" if is_login else "login")
        )

        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.EVENT_AVAILABLE, size=56, color=ft.Colors.INDIGO),
                        ft.Text("EventMaster", size=28, weight=ft.FontWeight.BOLD),
                        ft.Text("Вход в аккаунт" if is_login else "Создание аккаунта",
                               size=15, color=ft.Colors.GREY_600),
                        ft.Container(height=10),
                        u_in, p_in,
                        ft.Container(height=5),
                        action_button,
                        switch_button,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                ),
                alignment=ft.alignment.center,
                expand=True,
                padding=20,
            )
        )
        page.update()

    # ==================== ЭКРАН ПРОФИЛЯ ====================
    def show_profile_screen(e=None):
        page.clean()
        page.appbar = ft.AppBar(
            title=ft.Text("Мои события"),
            bgcolor=ft.Colors.INDIGO,
            color=ft.Colors.WHITE,
            leading=ft.IconButton(ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE,
                                  on_click=lambda e: show_events_screen())
        )
        token = page.client_storage.get("access_token")
        try:
            res = requests.get(f"{API_URL}/users/me/events/", headers={"Authorization": f"Bearer {token}"})
            if res.status_code != 200:
                show_error(f"Ошибка загрузки профиля: {res.status_code}")
                page.add(ft.Text("Не удалось загрузить профиль", size=16))
                page.update()
                return

            data = res.json()
            created_list = ft.ListView(expand=True)
            participated_list = ft.ListView(expand=True)

            for ev in data.get('created', []):
                eid = ev['id']
                etitle = ev['title']
                created_list.controls.append(ft.ListTile(
                    leading=ft.Icon(ft.Icons.EVENT, color=ft.Colors.INDIGO),
                    title=ft.Text(ev['title']),
                    trailing=ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_400,
                                           on_click=lambda _, i=eid, t=etitle: confirm_dialog(
                                               f"Удалить событие «{t}»? Это действие необратимо.",
                                               lambda: perform_action("delete", f"{API_URL}/events/{i}", show_profile_screen)))
                ))
            if not created_list.controls:
                created_list.controls.append(ft.Text("Пока нет созданных событий", color=ft.Colors.GREY_500))

            for ev in data.get('participated', []):
                eid = ev['id']
                participated_list.controls.append(ft.ListTile(
                    leading=ft.Icon(ft.Icons.EVENT_NOTE, color=ft.Colors.INDIGO),
                    title=ft.Text(ev['title']),
                    trailing=ft.IconButton(ft.Icons.EXIT_TO_APP, icon_color=ft.Colors.ORANGE,
                                           on_click=lambda _, i=eid: perform_action("delete", f"{API_URL}/events/{i}/leave", show_profile_screen))
                ))
            if not participated_list.controls:
                participated_list.controls.append(ft.Text("Пока нет событий, к которым вы присоединились", color=ft.Colors.GREY_500))

            page.add(
                ft.Container(
                    content=ft.Column([
                        ft.Text("Созданные события", size=16, weight=ft.FontWeight.W_600),
                        created_list,
                        ft.Divider(),
                        ft.Text("Участие", size=16, weight=ft.FontWeight.W_600),
                        participated_list,
                    ]),
                    padding=15,
                    expand=True,
                )
            )
        except requests.exceptions.RequestException as ex:
            show_error("Нет соединения с сервером")
            print(f"Ошибка загрузки профиля: {ex}")
            page.add(ft.Text("Не удалось загрузить профиль"))
        page.update()

    # ==================== ЭКРАН СПИСКА СОБЫТИЙ ====================
    def show_events_screen():
        page.clean()
        uid = page.client_storage.get("current_user_id")
        events_list = ft.ListView(expand=True, spacing=10)
        reminders_banner = ft.Container(visible=False)
        search_in = ft.TextField(label="Поиск по названию", prefix_icon=ft.Icons.SEARCH,
                                 border_radius=10,
                                 on_change=lambda e: load_events())

        def get_participating_ids(token):
            """ID событий, к которым пользователь уже присоединился —
            используем отдельный эндпоинт вместо угадывания структуры participants."""
            try:
                res = requests.get(f"{API_URL}/users/me/participating/",
                                   headers={"Authorization": f"Bearer {token}"})
                if res.status_code == 200:
                    return {ev["id"] for ev in res.json()}
            except requests.exceptions.RequestException:
                pass
            return set()

        def check_reminders(token):
            try:
                res = requests.get(f"{API_URL}/events/reminders/",
                                   headers={"Authorization": f"Bearer {token}"})
                if res.status_code == 200:
                    reminders = res.json()
                    if reminders:
                        titles = ", ".join(ev["title"] for ev in reminders)
                        reminders_banner.content = ft.Row([
                            ft.Icon(ft.Icons.NOTIFICATIONS_ACTIVE, color=ft.Colors.ORANGE_800, size=18),
                            ft.Text(f"Скоро начнётся: {titles}", size=13, color=ft.Colors.ORANGE_900,
                                   expand=True),
                        ])
                        reminders_banner.bgcolor = ft.Colors.ORANGE_50
                        reminders_banner.border = ft.border.all(1, ft.Colors.ORANGE_200)
                        reminders_banner.border_radius = 10
                        reminders_banner.padding = 10
                        reminders_banner.visible = True
                    else:
                        reminders_banner.visible = False
            except requests.exceptions.RequestException:
                reminders_banner.visible = False

        sort_dd = ft.Dropdown(
            label="Сортировка", width=170, value="date",
            options=[ft.dropdown.Option("date", "По дате"), ft.dropdown.Option("name", "По имени")],
            on_change=lambda e: load_events()
        )
        category_filter_dd = ft.Dropdown(
            label="Категория", width=170, value="all",
            options=[ft.dropdown.Option("all", "Все категории")] + [ft.dropdown.Option(c, c) for c in CATEGORIES],
            on_change=lambda e: load_events()
        )

        selected_date = [None]
        selected_time = [None]
        date_pick = ft.DatePicker(on_change=lambda e: selected_date.__setitem__(0, e.control.value))
        time_pick = ft.TimePicker(on_change=lambda e: selected_time.__setitem__(0, e.control.value))
        page.overlay.extend([date_pick, time_pick])

        t_in = ft.TextField(label="Название")
        d_in = ft.TextField(label="Описание", multiline=True, min_lines=2, max_lines=3)
        category_create_dd = ft.Dropdown(
            label="Категория", value="Другое",
            options=[ft.dropdown.Option(c, c) for c in CATEGORIES],
        )

        def category_badge(category: str):
            color = CATEGORY_COLORS.get(category, ft.Colors.GREY)
            return ft.Container(
                content=ft.Text(category, size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500),
                bgcolor=color, border_radius=12, padding=ft.padding.symmetric(horizontal=10, vertical=4)
            )

        def load_events(e=None):
            events_list.controls.clear()
            token = page.client_storage.get("access_token")
            category_param = "" if category_filter_dd.value in (None, "all") else category_filter_dd.value
            joined_ids = get_participating_ids(token)
            check_reminders(token)
            try:
                res = requests.get(f"{API_URL}/events/search/",
                                   headers={"Authorization": f"Bearer {token}"},
                                   params={"q": search_in.value, "sort_by": sort_dd.value,
                                          "category": category_param})

                if res.status_code == 200:
                    events = res.json()
                    if not events:
                        events_list.controls.append(
                            ft.Container(content=ft.Text("Ничего не найдено", color=ft.Colors.GREY_500),
                                        alignment=ft.alignment.center, padding=30)
                        )
                    for ev in events:
                        eid = ev['id']
                        is_owner = ev['creator_id'] == uid
                        is_joined = eid in joined_ids
                        actions = []
                        if not is_owner:
                            if is_joined:
                                actions.append(ft.ElevatedButton(
                                    "Записан", icon=ft.Icons.EVENT_AVAILABLE,
                                    bgcolor=ft.Colors.GREEN_100, color=ft.Colors.GREEN_900,
                                    on_click=lambda _, i=eid: perform_action(
                                        "delete", f"{API_URL}/events/{i}/leave", load_events)))
                            else:
                                actions.append(ft.ElevatedButton(
                                    "Пойти", icon=ft.Icons.CHECK,
                                    on_click=lambda _, i=eid: perform_action(
                                        "post", f"{API_URL}/events/{i}/join", load_events)))
                        else:
                            actions.append(ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_400,
                                                         on_click=lambda _, i=eid, t=ev['title']: confirm_dialog(
                                                             f"Удалить событие «{t}»? Это действие необратимо.",
                                                             lambda: perform_action("delete", f"{API_URL}/events/{i}", load_events))))

                        event_date = ev.get('event_date', '')[:16].replace('T', ' ')
                        participants_data = ev.get('participants', [])
                        p_count = len(participants_data) if isinstance(participants_data, list) else 0

                        details_column = ft.Column([
                            ft.Row([ft.Icon(ft.Icons.CALENDAR_TODAY, size=15, color=ft.Colors.GREY_600),
                                   ft.Text(event_date, size=13)]),
                            ft.Text(ev.get('description', ''), size=14),
                        ])
                        if p_count > 0:
                            details_column.controls.append(
                                ft.Row([ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=15, color=ft.Colors.GREY_600),
                                       ft.Text(f"{p_count} участник(ов)", size=13, color=ft.Colors.GREY_600)])
                            )
                        details_column.controls.extend([
                            ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                            ft.Row(controls=actions, spacing=10)
                        ])

                        events_list.controls.append(
                            ft.Card(
                                elevation=2,
                                shape=ft.RoundedRectangleBorder(radius=12),
                                content=ft.ExpansionTile(
                                    title=ft.Text(ev['title'], weight=ft.FontWeight.W_600),
                                    subtitle=category_badge(ev.get('category', '')),
                                    controls=[ft.Container(content=details_column, padding=15)]
                                )
                            )
                        )
                else:
                    show_error(f"Ошибка поиска: {res.status_code}")
            except requests.exceptions.RequestException as ex:
                show_error("Нет соединения с сервером")
                print(f"[ERROR] Ошибка внутри load_events: {ex}")
            page.update()

        def create(e):
            if not t_in.value:
                show_error("Введите название события!")
                return
            if not selected_date[0] or not selected_time[0]:
                show_error("Выберите дату и время!")
                return
            dt = datetime.combine(selected_date[0], selected_time[0]).replace(tzinfo=timezone.utc)
            token = page.client_storage.get("access_token")
            try:
                res = requests.post(f"{API_URL}/events/",
                                    headers={"Authorization": f"Bearer {token}"},
                                    json={"title": t_in.value, "description": d_in.value,
                                          "category": category_create_dd.value, "event_date": dt.isoformat()})
                if res.status_code != 200:
                    show_error(f"Не удалось создать событие: {res.status_code}")
                    return
            except requests.exceptions.RequestException as ex:
                show_error("Нет соединения с сервером")
                print(f"Error: {ex}")
                return

            dlg.open = False
            t_in.value = ""
            d_in.value = ""
            show_success("Событие создано!")
            load_events()

        dlg = ft.AlertDialog(
            shape=ft.RoundedRectangleBorder(radius=14),
            title=ft.Text("Новое событие", weight=ft.FontWeight.BOLD),
            content=ft.Column([
                t_in, d_in, category_create_dd,
                ft.Row([
                    ft.ElevatedButton("Дата", icon=ft.Icons.CALENDAR_MONTH,
                                      on_click=lambda e: (setattr(date_pick, "open", True), date_pick.update())),
                    ft.ElevatedButton("Время", icon=ft.Icons.ACCESS_TIME,
                                      on_click=lambda e: (setattr(time_pick, "open", True), time_pick.update()))
                ], spacing=10)
            ], scroll=True, height=560, tight=True, spacing=14),
            actions=[ft.ElevatedButton("Создать", icon=ft.Icons.ADD, on_click=create)]
        )

        def logout(e):
            page.client_storage.remove("access_token")
            page.client_storage.remove("current_user")
            page.client_storage.remove("current_user_id")
            show_auth_screen()

        page.overlay.append(dlg)
        page.appbar = ft.AppBar(
            title=ft.Text("EventMaster"),
            bgcolor=ft.Colors.INDIGO,
            color=ft.Colors.WHITE,
            actions=[
                ft.IconButton(ft.Icons.PERSON_OUTLINE, icon_color=ft.Colors.WHITE, on_click=show_profile_screen),
                ft.IconButton(ft.Icons.LOGOUT, icon_color=ft.Colors.WHITE, on_click=logout),
            ]
        )
        page.floating_action_button = ft.FloatingActionButton(icon=ft.Icons.ADD,
                                                               on_click=lambda e: (setattr(dlg, "open", True), page.update()))
        page.add(
            ft.Container(
                content=ft.Column([
                    reminders_banner,
                    search_in,
                    ft.Row([sort_dd, category_filter_dd], spacing=10),
                    events_list,
                ], expand=True, spacing=10),
                padding=15,
                expand=True,
            )
        )
        load_events()

    if page.client_storage.get("current_user"):
        show_events_screen()
    else:
        show_auth_screen()


ft.app(target=main)