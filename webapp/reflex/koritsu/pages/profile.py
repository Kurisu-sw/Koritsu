import reflex as rx
from koritsu.state.profile_state import ProfileState

# ── Цветовая схема ────────────────────────────────────────────────────────────
BG_COLOR = "#0a0a0a"
TEXT_PRIMARY = "rgba(255, 255, 255, 0.9)"
TEXT_SECONDARY = "rgba(255, 255, 255, 0.6)"
TEXT_TERTIARY = "rgba(255, 255, 255, 0.4)"
ACCENT_BLUE = "#3b82f6"
ACCENT_PURPLE = "#a855f7"
SUCCESS_GREEN = "#22c55e"
DANGER_RED = "#ef4444"

# ── Стили ─────────────────────────────────────────────────────────────────────

GLASS_CARD_STYLE = {
    "background": "rgba(255, 255, 255, 0.04)",
    "backdrop_filter": "blur(40px) saturate(180%)",
    "border": "1px solid rgba(255, 255, 255, 0.08)",
    "border_radius": "20px",
    "box_shadow": "0 8px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.07)",
}

GLASS_CARD_HOVER_STYLE = {
    **GLASS_CARD_STYLE,
    "_hover": {
        "background": "rgba(255, 255, 255, 0.07)",
        "border": "1px solid rgba(255, 255, 255, 0.14)",
        "box_shadow": "0 16px 56px rgba(59, 130, 246, 0.2), 0 4px 16px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.1)",
        "transform": "translateY(-2px)",
    },
    "transition": "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
}

INPUT_STYLE = {
    "background": "rgba(255, 255, 255, 0.06)",
    "border": "1px solid rgba(255, 255, 255, 0.1)",
    "border_radius": "12px",
    "padding": "14px 16px",
    "color": "rgba(255, 255, 255, 0.9)",
    "font_size": "15px",
    "width": "100%",
    "outline": "none",
    "backdrop_filter": "blur(20px)",
    "transition": "all 0.2s ease",
    "_placeholder": {"color": "rgba(255, 255, 255, 0.25)"},
    "_focus": {
        "background": "rgba(255, 255, 255, 0.09)",
        "border": "1px solid rgba(59, 130, 246, 0.6)",
        "box_shadow": "0 0 0 3px rgba(59, 130, 246, 0.12)",
    },
}

GRADIENT_BUTTON_STYLE = {
    "background": f"linear-gradient(135deg, {ACCENT_BLUE}, {ACCENT_PURPLE})",
    "color": "white",
    "border_radius": "12px",
    "border": "none",
    "padding": "12px 24px",
    "cursor": "pointer",
    "font_weight": "500",
    "font_size": "14px",
    "transition": "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
    "_hover": {
        "box_shadow": "0 6px 24px rgba(59, 130, 246, 0.5)",
        "transform": "translateY(-1px)",
    },
}

SIDEBAR_STYLE = {
    "width": "240px",
    "min_width": "240px",
    "padding": "28px 20px",
    "flex_shrink": "0",
    "border_right": "1px solid rgba(255, 255, 255, 0.07)",
    "background": "rgba(0, 0, 0, 0.15)",
}

MAIN_CONTENT_STYLE = {
    "flex_grow": "1",
    "padding": "36px 40px",
    "overflow_y": "auto",
    "min_height": "600px",
}

LAYOUT_STYLE = {
    "background": BG_COLOR,
    "position": "relative",
    "overflow": "hidden",
    "min_height": "100vh",
}

CONTAINER_STYLE = {
    "width": "1080px",
    "max_width": "100%",
    "background": "rgba(18, 18, 26, 0.75)",
    "backdrop_filter": "blur(60px) saturate(200%)",
    "border": "1px solid rgba(255, 255, 255, 0.08)",
    "border_radius": "28px",
    "box_shadow": "0 32px 80px rgba(0, 0, 0, 0.6), 0 4px 16px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.06)",
    "overflow": "hidden",
    "display": "flex",
    "position": "relative",
    "z_index": "1",
}

# ── Градиентный фон ───────────────────────────────────────────────────────────


def gradient_background() -> rx.Component:
    """Анимированный градиентный фон с двумя пятнами."""
    return rx.box(
        # Верхнее-левое синее пятно
        rx.box(
            width="600px",
            height="600px",
            background=f"radial-gradient(ellipse, rgba(59, 130, 246, 0.3) 0%, transparent 70%)",
            position="absolute",
            top="-100px",
            left="-100px",
            filter="blur(48px)",
            animation="pulse 4s ease-in-out infinite, float 8s ease-in-out infinite",
        ),
        # Нижнее-правое фиолетовое пятно
        rx.box(
            width="500px",
            height="500px",
            background=f"radial-gradient(ellipse, rgba(168, 85, 247, 0.2) 0%, transparent 70%)",
            position="absolute",
            bottom="-100px",
            right="-100px",
            filter="blur(48px)",
            animation="pulse 4s ease-in-out infinite 2s, float 10s ease-in-out infinite reverse",
        ),
        position="fixed",
        inset="0",
        pointer_events="none",
        z_index="0",
    )


# ── Сайдбар ───────────────────────────────────────────────────────────────────


def sidebar_item(
    icon: rx.Component,
    label: str,
    href: str,
    is_active: bool = False,
) -> rx.Component:
    """Элемент меню сайдбара."""
    return rx.link(
        rx.hstack(
            rx.box(
                icon,
                width="32px",
                height="32px",
                display="flex",
                align_items="center",
                justify_content="center",
                border_radius="9px",
                background=rx.cond(is_active, "rgba(59,130,246,0.2)", "rgba(255,255,255,0.04)"),
                border=rx.cond(is_active, "1px solid rgba(59,130,246,0.3)", "1px solid rgba(255,255,255,0.06)"),
                flex_shrink="0",
            ),
            rx.text(
                label,
                color=rx.cond(is_active, "rgba(255,255,255,0.95)", "rgba(255,255,255,0.45)"),
                font_size="13.5px",
                font_weight=rx.cond(is_active, "500", "400"),
            ),
            gap="10px",
            align="center",
            width="100%",
        ),
        href=href,
        display="block",
        padding="8px 10px",
        border_radius="12px",
        cursor="pointer",
        transition="all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
        text_decoration="none",
        background=rx.cond(is_active, "rgba(255,255,255,0.07)", "transparent"),
        border=rx.cond(is_active, "1px solid rgba(255,255,255,0.1)", "1px solid transparent"),
        _hover={
            "background": "rgba(255,255,255,0.05)",
            "border": "1px solid rgba(255,255,255,0.08)",
        },
    )


def sidebar() -> rx.Component:
    """Левая панель навигации."""
    return rx.box(
        rx.vstack(
            rx.box(
                rx.text(
                    "Настройки",
                    color=TEXT_PRIMARY,
                    font_size="17px",
                    font_weight="600",
                    letter_spacing="-0.01em",
                ),
                rx.text(
                    "Управление аккаунтом",
                    color=TEXT_TERTIARY,
                    font_size="12px",
                    margin_top="2px",
                ),
                padding_bottom="20px",
                border_bottom="1px solid rgba(255,255,255,0.06)",
                width="100%",
                margin_bottom="12px",
            ),
            sidebar_item(
                rx.icon("user", size=15, color=rx.cond(ProfileState.is_account_active, ACCENT_BLUE, "rgba(255,255,255,0.45)")),
                "Аккаунт",
                "/profile",
                is_active=ProfileState.is_account_active,
            ),
            sidebar_item(
                rx.icon("folder-open", size=15, color=rx.cond(ProfileState.is_files_active, ACCENT_BLUE, "rgba(255,255,255,0.45)")),
                "Файлы",
                "/profile/files",
                is_active=ProfileState.is_files_active,
            ),
            sidebar_item(
                rx.icon("users", size=15, color=rx.cond(ProfileState.is_referral_active, ACCENT_BLUE, "rgba(255,255,255,0.45)")),
                "Реферальная программа",
                "/profile/referral",
                is_active=ProfileState.is_referral_active,
            ),
            spacing="1",
            align="start",
            width="100%",
        ),
        **SIDEBAR_STYLE,
        height="100%",
        display="flex",
        flex_direction="column",
    )


# ── Страница Аккаунт ──────────────────────────────────────────────────────────


def avatar_component() -> rx.Component:
    """Аватар пользователя — круглый."""
    return rx.box(
        rx.cond(
            ProfileState.avatar_url != "",
            rx.el.img(
                src=ProfileState.avatar_url,
                alt="Avatar",
                width="96px",
                height="96px",
                object_fit="cover",
                border_radius="50%",
            ),
            rx.box(
                rx.text(
                    ProfileState.user_initial,
                    color="white",
                    font_size="32px",
                    font_weight="700",
                ),
                width="96px",
                height="96px",
                background=f"linear-gradient(135deg, {ACCENT_BLUE}, {ACCENT_PURPLE})",
                border_radius="50%",
                display="flex",
                align_items="center",
                justify_content="center",
                box_shadow="0 4px 20px rgba(59, 130, 246, 0.3)",
            ),
        ),
        # Индикатор онлайн
        rx.box(
            width="18px",
            height="18px",
            background=SUCCESS_GREEN,
            border_radius="50%",
            position="absolute",
            bottom="4px",
            right="4px",
            border="3px solid rgba(18,18,26,0.9)",
            box_shadow="0 0 0 1px rgba(34,197,94,0.4)",
        ),
        # Оверлей камеры при наведении
        rx.box(
            rx.icon("camera", size=20, color="white"),
            width="100%",
            height="100%",
            background="rgba(0, 0, 0, 0.55)",
            border_radius="50%",
            display="flex",
            align_items="center",
            justify_content="center",
            opacity="0",
            cursor="pointer",
            transition="opacity 0.25s ease",
            _hover={"opacity": "1"},
            position="absolute",
            top="0",
            left="0",
        ),
        position="relative",
        flex_shrink="0",
        cursor="pointer",
        on_click=ProfileState.open_avatar_upload,
    )


def user_info() -> rx.Component:
    """Информация о пользователе."""
    return rx.vstack(
        rx.text(
            ProfileState.display_name,
            color=TEXT_PRIMARY,
            font_size="24px",
            font_weight="600",
            margin_bottom="8px",
        ),
        rx.text(
            "@" + ProfileState.username,
            color=TEXT_SECONDARY,
            font_size="18px",
        ),
        spacing="0",
        align="start",
    )


def profile_card() -> rx.Component:
    """Карточка профиля пользователя."""
    return rx.box(
        rx.hstack(
            avatar_component(),
            user_info(),
            width="100%",
            align="center",
            gap="24px",
        ),
        padding="28px 32px",
        margin_bottom="20px",
        **GLASS_CARD_STYLE,
    )


def settings_header() -> rx.Component:
    """Заголовок секции настроек."""
    return rx.text(
        "УЧЁТНЫЕ ДАННЫЕ",
        color="rgba(255,255,255,0.25)",
        font_size="11px",
        font_weight="600",
        letter_spacing="0.1em",
        text_transform="uppercase",
        margin_bottom="10px",
        padding_x="4px",
    )


def _pw_req_row(check: bool, label: str) -> rx.Component:
    return rx.hstack(
        rx.cond(
            check,
            rx.icon("circle-check", size=13, color=SUCCESS_GREEN),
            rx.icon("circle-dot", size=13, color="rgba(255,255,255,0.25)"),
        ),
        rx.text(
            label,
            font_size="12px",
            color=rx.cond(check, SUCCESS_GREEN, "rgba(255,255,255,0.4)"),
        ),
        gap="6px",
        align="center",
        transition="color 0.2s ease",
    )


def password_requirements() -> rx.Component:
    """Подсказка с требованиями к паролю."""
    return rx.box(
        rx.vstack(
            _pw_req_row(ProfileState.pw_check_length, "Не менее 12 символов"),
            _pw_req_row(ProfileState.pw_check_upper, "Хотя бы одна заглавная буква (A–Z или А–Я)"),
            _pw_req_row(ProfileState.pw_check_special, "Хотя бы один спецсимвол (!@#$%^&* ...)"),
            spacing="1",
            align="start",
        ),
        padding="10px 14px",
        border_radius="10px",
        background="rgba(255,255,255,0.03)",
        border="1px solid rgba(255,255,255,0.07)",
        margin_top="8px",
        width="100%",
    )


def edit_field_row(
    label: str,
    value: str,
    input_value: str,
    is_editing: bool,
    start_edit_fn,
    save_fn,
    cancel_fn,
    set_input_fn,
    is_password: bool = False,
    old_password_value: str = "",
    set_old_password_fn=None,
) -> rx.Component:
    """Строка редактируемого поля."""
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(
                    label,
                    color=TEXT_TERTIARY,
                    font_size="11px",
                    font_weight="500",
                    letter_spacing="0.06em",
                    text_transform="uppercase",
                ),
                rx.cond(
                    is_editing,
                    rx.box(),
                    rx.text(
                        value,
                        color=TEXT_PRIMARY,
                        font_size="15px",
                        margin_top="2px",
                    ),
                ),
                spacing="0",
                align="start",
                flex_grow="1",
            ),
            rx.cond(
                is_editing,
                rx.hstack(
                    rx.box(
                        rx.icon("check", size=16, color=SUCCESS_GREEN),
                        padding="8px",
                        cursor="pointer",
                        on_click=save_fn,
                        border_radius="8px",
                        background="rgba(34,197,94,0.1)",
                        border="1px solid rgba(34,197,94,0.2)",
                        transition="all 0.2s",
                        _hover={"background": "rgba(34,197,94,0.2)", "transform": "scale(1.05)"},
                    ),
                    rx.box(
                        rx.icon("x", size=16, color="rgba(255,255,255,0.5)"),
                        padding="8px",
                        cursor="pointer",
                        on_click=cancel_fn,
                        border_radius="8px",
                        background="rgba(255,255,255,0.05)",
                        border="1px solid rgba(255,255,255,0.08)",
                        transition="all 0.2s",
                        _hover={"background": "rgba(255,255,255,0.1)", "transform": "scale(1.05)"},
                    ),
                    gap="8px",
                    align="center",
                ),
                rx.box(
                    rx.icon("pencil", size=14, color="rgba(255,255,255,0.35)"),
                    padding="8px",
                    cursor="pointer",
                    on_click=start_edit_fn,
                    border_radius="8px",
                    background="rgba(255,255,255,0.0)",
                    border="1px solid rgba(255,255,255,0.0)",
                    transition="all 0.2s",
                    _hover={
                        "background": "rgba(255,255,255,0.07)",
                        "border": "1px solid rgba(255,255,255,0.1)",
                        "color": "white",
                    },
                ),
            ),
            width="100%",
            align="center",
            justify="between",
        ),
        rx.cond(
            is_editing,
            rx.vstack(
                rx.cond(
                    is_password,
                    rx.el.input(
                        value=old_password_value,
                        on_change=set_old_password_fn,
                        type="password",
                        placeholder="Текущий пароль",
                        **INPUT_STYLE,
                        margin_top="14px",
                    ),
                    rx.box(),
                ),
                rx.el.input(
                    value=input_value,
                    on_change=set_input_fn,
                    type="password" if is_password else "text",
                    placeholder="Новый пароль" if is_password else "Новое значение",
                    **INPUT_STYLE,
                    margin_top="8px",
                ),
                rx.cond(
                    is_password,
                    password_requirements(),
                    rx.box(),
                ),
                spacing="0",
                width="100%",
            ),
            rx.box(),
        ),
        padding="20px 24px",
        border_bottom="1px solid rgba(255, 255, 255, 0.06)",
        transition="background 0.2s ease",
        _hover={"background": "rgba(255,255,255,0.02)"},
    )


def profile_message_banner() -> rx.Component:
    """Баннер с сообщением об успехе или ошибке."""
    return rx.cond(
        ProfileState.profile_message != "",
        rx.box(
            rx.text(
                ProfileState.profile_message,
                font_size="14px",
                color=rx.cond(ProfileState.profile_message_is_error, DANGER_RED, SUCCESS_GREEN),
            ),
            padding="12px 20px",
            border_radius="10px",
            background=rx.cond(
                ProfileState.profile_message_is_error,
                "rgba(239, 68, 68, 0.1)",
                "rgba(34, 197, 94, 0.1)",
            ),
            border=rx.cond(
                ProfileState.profile_message_is_error,
                "1px solid rgba(239, 68, 68, 0.3)",
                "1px solid rgba(34, 197, 94, 0.3)",
            ),
            margin_bottom="16px",
            width="100%",
        ),
    )


def password_section() -> rx.Component:
    """Секция смены пароля."""
    return rx.box(
        rx.text(
            "ПАРОЛЬ",
            color="rgba(255,255,255,0.25)",
            font_size="11px",
            font_weight="600",
            letter_spacing="0.1em",
            text_transform="uppercase",
            margin_bottom="16px",
        ),
        rx.vstack(
            rx.el.input(
                value=ProfileState.old_password_input,
                on_change=ProfileState.set_old_password_input,
                type="password",
                placeholder="Текущий пароль",
                **INPUT_STYLE,
            ),
            rx.el.input(
                value=ProfileState.password_input,
                on_change=ProfileState.set_password_input,
                type="password",
                placeholder="Новый пароль",
                **INPUT_STYLE,
            ),
            password_requirements(),
            rx.cond(
                ProfileState.profile_message != "",
                rx.box(
                    rx.text(
                        ProfileState.profile_message,
                        font_size="13px",
                        color=rx.cond(ProfileState.profile_message_is_error, DANGER_RED, SUCCESS_GREEN),
                    ),
                    padding="10px 14px",
                    border_radius="10px",
                    background=rx.cond(
                        ProfileState.profile_message_is_error,
                        "rgba(239,68,68,0.08)",
                        "rgba(34,197,94,0.08)",
                    ),
                    border=rx.cond(
                        ProfileState.profile_message_is_error,
                        "1px solid rgba(239,68,68,0.25)",
                        "1px solid rgba(34,197,94,0.25)",
                    ),
                    width="100%",
                ),
            ),
            rx.el.button(
                "Сохранить пароль",
                on_click=ProfileState.save_password,
                background="rgba(255,255,255,0.08)",
                color="rgba(255,255,255,0.85)",
                border="1px solid rgba(255,255,255,0.12)",
                border_radius="12px",
                padding="13px 24px",
                cursor="pointer",
                font_weight="500",
                font_size="14px",
                width="100%",
                transition="all 0.2s ease",
                _hover={
                    "background": "rgba(255,255,255,0.13)",
                    "border": "1px solid rgba(255,255,255,0.2)",
                    "color": "white",
                },
            ),
            spacing="3",
            width="100%",
        ),
        padding="28px 32px",
        border_bottom="1px solid rgba(255,255,255,0.06)",
    )


def settings_card() -> rx.Component:
    """Карточка настроек."""
    return rx.box(
        password_section(),
        edit_field_row(
            "Отображаемое имя",
            ProfileState.display_name,
            ProfileState.display_name_input,
            ProfileState.editing_display_name,
            ProfileState.start_edit_display_name,
            ProfileState.save_display_name,
            ProfileState.cancel_edit_display_name,
            ProfileState.set_display_name_input,
        ),
        overflow="hidden",
        **GLASS_CARD_STYLE,
    )


def account_page() -> rx.Component:
    """Страница аккаунта."""
    return rx.vstack(
        rx.text(
            "Аккаунт",
            color=TEXT_PRIMARY,
            font_size="30px",
            font_weight="600",
            margin_bottom="24px",
        ),
        profile_card(),
        settings_header(),
        settings_card(),
        spacing="0",
        align="start",
        width="100%",
    )


# ── Страница Файлы ────────────────────────────────────────────────────────────


def search_bar() -> rx.Component:
    """Поисковая строка."""
    return rx.box(
        rx.hstack(
            rx.icon("search", size=20, color=TEXT_TERTIARY),
            rx.el.input(
                placeholder="Поиск по файлам...",
                value=ProfileState.search_query,
                on_change=ProfileState.set_search_query,
                flex_grow="1",
                background="transparent",
                border="none",
                padding_left="48px",
                color="white",
                font_size="14px",
                outline="none",
                _placeholder={"color": TEXT_TERTIARY},
            ),
            width="100%",
            align="center",
        ),
        padding="16px",
        margin_bottom="24px",
        **GLASS_CARD_STYLE,
    )


def file_icon(file_type: str) -> rx.Component:
    """Иконка файла в зависимости от типа."""
    icon_map = {
        "document": ("file-text", "#60a5fa"),
        "image": ("image", "#c084fc"),
        "audio": ("music", "#4ade80"),
        "video": ("video", "#f87171"),
    }
    icon_name, color = icon_map.get(file_type, ("file", "#60a5fa"))
    
    return rx.box(
        rx.icon(icon_name, size=24, color=color),
        width="48px",
        height="48px",
        background="rgba(255, 255, 255, 0.05)",
        border_radius="12px",
        padding="12px",
        display="flex",
        align_items="center",
        justify_content="center",
        flex_shrink="0",
    )


def file_card(file_data) -> rx.Component:
    """Карточка файла."""
    return rx.box(
        rx.hstack(
            file_icon(file_data.file_type),
            rx.vstack(
                rx.text(
                    file_data.name,
                    color=TEXT_PRIMARY,
                    font_size="14px",
                    margin_bottom="4px",
                ),
                rx.text(
                    f"{file_data.size} • {file_data.date}",
                    color=TEXT_TERTIARY,
                    font_size="13px",
                ),
                spacing="0",
                align="start",
            ),
            rx.spacer(),
            rx.el.button(
                "Открыть",
                padding="8px 16px",
                border_radius="8px",
                background="rgba(255, 255, 255, 0.05)",
                border="1px solid rgba(255, 255, 255, 0.1)",
                color="rgba(255, 255, 255, 0.8)",
                font_size="13px",
                cursor="pointer",
                transition="all 0.3s ease",
                _hover={
                    "background": "rgba(255, 255, 255, 0.1)",
                    "color": "white",
                },
            ),
            width="100%",
            align="center",
        ),
        padding="16px",
        **GLASS_CARD_HOVER_STYLE,
    )


def files_page() -> rx.Component:
    """Страница файлов."""
    return rx.vstack(
        rx.text(
            "Файлы",
            color=TEXT_PRIMARY,
            font_size="30px",
            font_weight="600",
            margin_bottom="24px",
        ),
        rx.box(
            rx.vstack(
                rx.icon("folder-open", size=40, color=TEXT_TERTIARY),
                rx.text(
                    "Раздел в разработке",
                    color=TEXT_TERTIARY,
                    font_size="16px",
                    text_align="center",
                    margin_top="16px",
                ),
                align="center",
                width="100%",
            ),
            padding="48px",
            width="100%",
            **GLASS_CARD_STYLE,
        ),
        spacing="0",
        align="start",
        width="100%",
    )


# ── Страница Реферальная программа ────────────────────────────────────────────


def stat_card(icon: rx.Component, icon_bg: str, label: str, value: str) -> rx.Component:
    """Карточка статистики."""
    return rx.box(
        rx.hstack(
            rx.box(
                icon,
                width="40px",
                height="40px",
                background=icon_bg,
                border_radius="12px",
                padding="12px",
                display="flex",
                align_items="center",
                justify_content="center",
            ),
            rx.vstack(
                rx.text(
                    label,
                    color="rgba(255, 255, 255, 0.5)",
                    font_size="14px",
                ),
                rx.text(
                    value,
                    color="white",
                    font_size="24px",
                    font_weight="600",
                ),
                spacing="0",
                align="start",
            ),
            width="100%",
            align="center",
        ),
        padding="16px",
        **GLASS_CARD_HOVER_STYLE,
    )


def stats_row() -> rx.Component:
    """Строка статистики."""
    return rx.grid(
        stat_card(
            rx.icon("users", size=20, color="#60a5fa"),
            "rgba(59, 130, 246, 0.2)",
            "Рефералы",
            ProfileState.total_referrals_count,
        ),
        columns="1",
        spacing="4",
        margin_bottom="24px",
        width="100%",
    )


def referral_link_card() -> rx.Component:
    """Карточка реферальной ссылки."""
    return rx.box(
        rx.text(
            "Ваша реферальная ссылка",
            color=TEXT_PRIMARY,
            font_size="14px",
            margin_bottom="16px",
        ),
        rx.hstack(
            rx.el.input(
                value=ProfileState.referral_link,
                read_only=True,
                flex_grow="1",
                **INPUT_STYLE,
            ),
            rx.el.button(
                rx.cond(
                    ProfileState.copied,
                    rx.hstack(
                        rx.icon("check", size=20),
                        rx.text("Скопировано"),
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.icon("copy", size=20),
                        rx.text("Копировать"),
                        spacing="2",
                    ),
                ),
                on_click=ProfileState.copy_referral_link,
                **GRADIENT_BUTTON_STYLE,
            ),
            width="100%",
            align="center",
        ),
        padding="24px",
        margin_bottom="24px",
        **GLASS_CARD_STYLE,
    )


def referral_header() -> rx.Component:
    """Заголовок списка рефералов."""
    return rx.text(
        "СТАТИСТИКА ПО РЕФЕРАЛАМ",
        color=TEXT_SECONDARY,
        font_size="14px",
        font_weight="600",
        letter_spacing="0.1em",
        text_transform="uppercase",
        margin_bottom="16px",
    )


def referral_avatar(name) -> rx.Component:
    """Аватар реферала."""
    # Получаем первые буквы имени и фамилии
    first_initial = name[0].upper()
    
    return rx.box(
        rx.text(
            first_initial,
            color="white",
            font_size="14px",
            font_weight="600",
        ),
        width="48px",
        height="48px",
        background=f"linear-gradient(135deg, {ACCENT_BLUE}, {ACCENT_PURPLE})",
        border_radius="50%",
        display="flex",
        align_items="center",
        justify_content="center",
        flex_shrink="0",
    )


def referral_status_badge(status) -> rx.Component:
    """Бадж статуса реферала."""
    return rx.box(
        rx.text(
            rx.cond(status == "active", "Активен", "Ожидание"),
            color=rx.cond(status == "active", "#4ade80", "#facc15"),
            font_size="13px",
        ),
        padding="4px 12px",
        background=rx.cond(status == "active", "rgba(34, 197, 94, 0.2)", "rgba(234, 179, 8, 0.2)"),
        border_radius="9999px",
    )


def referral_card(ref_data) -> rx.Component:
    """Карточка реферала."""
    return rx.box(
        rx.hstack(
            referral_avatar(ref_data.name),
            rx.vstack(
                rx.text(
                    ref_data.name,
                    color=TEXT_PRIMARY,
                    font_size="14px",
                    margin_bottom="4px",
                ),
                rx.text(
                    ref_data.date,
                    color=TEXT_TERTIARY,
                    font_size="13px",
                ),
                spacing="0",
                align="start",
            ),
            rx.spacer(),
            rx.hstack(
                rx.vstack(
                    rx.text(
                        "Заработано",
                        color="rgba(255, 255, 255, 0.5)",
                        font_size="12px",
                        margin_bottom="4px",
                    ),
                    rx.text(
                        ref_data.earnings,
                        color=SUCCESS_GREEN,
                        font_size="14px",
                        font_weight="600",
                    ),
                    spacing="0",
                    align="start",
                ),
                rx.vstack(
                    rx.text(
                        "Дата",
                        color="rgba(255, 255, 255, 0.5)",
                        font_size="12px",
                        margin_bottom="4px",
                    ),
                    rx.text(
                        ref_data.date,
                        color="rgba(255, 255, 255, 0.8)",
                        font_size="13px",
                    ),
                    spacing="0",
                    align="start",
                ),
                referral_status_badge(ref_data.status),
                spacing="6",
                align="center",
            ),
            width="100%",
            align="center",
        ),
        padding="16px",
        **GLASS_CARD_HOVER_STYLE,
    )


def referral_connect_screen() -> rx.Component:
    """Экран подключения к реферальной программе."""
    return rx.box(
        rx.box(
            rx.icon("users", size=40, color="white"),
            width="80px",
            height="80px",
            background=f"linear-gradient(135deg, {ACCENT_BLUE}, {ACCENT_PURPLE})",
            border_radius="50%",
            display="flex",
            align_items="center",
            justify_content="center",
            margin="auto",
            margin_bottom="24px",
        ),
        rx.text(
            "Подключитесь к реферальной программе",
            color=TEXT_PRIMARY,
            font_size="24px",
            font_weight="600",
            margin_bottom="16px",
            text_align="center",
        ),
        rx.text(
            "Приглашайте друзей и зарабатывайте бонусы за каждого активного пользователя",
            color=TEXT_SECONDARY,
            font_size="16px",
            margin_bottom="32px",
            text_align="center",
            max_width="448px",
            margin_left="auto",
            margin_right="auto",
        ),
        rx.el.button(
            "Подключить программу",
            on_click=ProfileState.connect_referral_program,
            **GRADIENT_BUTTON_STYLE,
        ),
        padding="48px",
        text_align="center",
        **GLASS_CARD_STYLE,
    )


def referral_list() -> rx.Component:
    """Список рефералов."""
    return rx.cond(
        ProfileState.referrals.length() > 0,
        rx.vstack(
            rx.foreach(
                ProfileState.referrals,
                lambda ref: referral_card(ref),
            ),
            spacing="3",
            width="100%",
        ),
        rx.box(
            rx.text(
                "Рефералы отсутствуют",
                color=TEXT_TERTIARY,
                font_size="16px",
                text_align="center",
                padding="32px",
            ),
            width="100%",
            **GLASS_CARD_STYLE,
        ),
    )


def referral_page() -> rx.Component:
    """Страница реферальной программы."""
    return rx.vstack(
        rx.text(
            "Реферальная программа",
            color=TEXT_PRIMARY,
            font_size="30px",
            font_weight="600",
            margin_bottom="24px",
        ),
        rx.cond(
            ProfileState.is_connected,
            rx.vstack(
                stats_row(),
                referral_link_card(),
                referral_header(),
                referral_list(),
                spacing="0",
                align="start",
                width="100%",
            ),
            referral_connect_screen(),
        ),
        spacing="0",
        align="start",
        width="100%",
    )


# ── Главная страница профиля ─────────────────────────────────────────────────


def profile_layout(page_content: rx.Component) -> rx.Component:
    """Общий layout для всех страниц профиля."""
    return rx.box(
        gradient_background(),
        # CSS для анимаций
        rx.el.style(
            """
            @keyframes pulse {
                0%, 100% { opacity: 0.6; transform: scale(1); }
                50% { opacity: 1; transform: scale(1.1); }
            }
            @keyframes float {
                0%, 100% { transform: translate(0, 0); }
                25% { transform: translate(30px, -30px); }
                50% { transform: translate(0, -60px); }
                75% { transform: translate(-30px, -30px); }
            }
            """
        ),
        # Avatar upload modal
        _avatar_upload_modal(),
        # Центрированный контейнер
        rx.box(
            rx.box(
                sidebar(),
                rx.box(
                    page_content,
                    **MAIN_CONTENT_STYLE,
                ),
                **CONTAINER_STYLE,
            ),
            width="100%",
            display="flex",
            justify_content="center",
            align_items="center",
            padding="64px",
            box_sizing="border-box",
        ),
        **LAYOUT_STYLE,
    )


def _avatar_upload_modal() -> rx.Component:
    """Модальное окно загрузки аватарки."""
    return rx.cond(
        ProfileState.show_avatar_upload,
        rx.box(
            # Backdrop
            rx.box(
                position="fixed",
                inset="0",
                background="rgba(0,0,0,0.60)",
                backdrop_filter="blur(8px)",
                z_index="300",
                on_click=ProfileState.close_avatar_upload,
            ),
            # Modal card
            rx.box(
                rx.vstack(
                    # Header
                    rx.hstack(
                        rx.box(
                            rx.icon("image", size=18, color=ACCENT_BLUE),
                            width="36px",
                            height="36px",
                            background="rgba(59,130,246,0.12)",
                            border="1px solid rgba(59,130,246,0.25)",
                            border_radius="10px",
                            display="flex",
                            align_items="center",
                            justify_content="center",
                        ),
                        rx.vstack(
                            rx.text(
                                "Загрузить аватарку",
                                color=TEXT_PRIMARY,
                                font_size="17px",
                                font_weight="600",
                            ),
                            rx.text(
                                "Только формат PNG",
                                color=ACCENT_BLUE,
                                font_size="12px",
                                font_weight="500",
                            ),
                            spacing="0",
                            align="start",
                        ),
                        gap="12px",
                        align="center",
                        width="100%",
                    ),
                    # Preview area
                    rx.cond(
                        ProfileState.avatar_preview_url != "",
                        # Показываем превью
                        rx.vstack(
                            rx.text(
                                "Предпросмотр",
                                color=TEXT_TERTIARY,
                                font_size="11px",
                                font_weight="600",
                                letter_spacing="0.08em",
                                text_transform="uppercase",
                            ),
                            rx.hstack(
                                # Круглый кроп-превью
                                rx.vstack(
                                    rx.box(
                                        rx.el.img(
                                            src=ProfileState.avatar_preview_url,
                                            alt="Preview",
                                            width="100%",
                                            height="100%",
                                            object_fit="cover",
                                        ),
                                        width="96px",
                                        height="96px",
                                        border_radius="50%",
                                        overflow="hidden",
                                        border="3px solid rgba(59,130,246,0.5)",
                                        box_shadow="0 0 0 4px rgba(59,130,246,0.15), 0 8px 24px rgba(0,0,0,0.4)",
                                        flex_shrink="0",
                                    ),
                                    rx.text(
                                        "96×96",
                                        color=TEXT_TERTIARY,
                                        font_size="11px",
                                        margin_top="6px",
                                    ),
                                    align="center",
                                    spacing="0",
                                ),
                                # Квадратный превью
                                rx.vstack(
                                    rx.box(
                                        rx.el.img(
                                            src=ProfileState.avatar_preview_url,
                                            alt="Preview",
                                            width="100%",
                                            height="100%",
                                            object_fit="cover",
                                        ),
                                        width="64px",
                                        height="64px",
                                        border_radius="14px",
                                        overflow="hidden",
                                        border="2px solid rgba(255,255,255,0.1)",
                                        box_shadow="0 4px 12px rgba(0,0,0,0.3)",
                                        flex_shrink="0",
                                    ),
                                    rx.text(
                                        "64×64",
                                        color=TEXT_TERTIARY,
                                        font_size="11px",
                                        margin_top="6px",
                                    ),
                                    align="center",
                                    spacing="0",
                                ),
                                # Маленький превью
                                rx.vstack(
                                    rx.box(
                                        rx.el.img(
                                            src=ProfileState.avatar_preview_url,
                                            alt="Preview",
                                            width="100%",
                                            height="100%",
                                            object_fit="cover",
                                        ),
                                        width="36px",
                                        height="36px",
                                        border_radius="50%",
                                        overflow="hidden",
                                        border="2px solid rgba(255,255,255,0.08)",
                                        flex_shrink="0",
                                    ),
                                    rx.text(
                                        "36×36",
                                        color=TEXT_TERTIARY,
                                        font_size="11px",
                                        margin_top="6px",
                                    ),
                                    align="center",
                                    spacing="0",
                                ),
                                gap="28px",
                                align="end",
                                justify_content="center",
                                padding="20px",
                                background="rgba(255,255,255,0.02)",
                                border="1px solid rgba(255,255,255,0.07)",
                                border_radius="14px",
                                width="100%",
                            ),
                            spacing="2",
                            width="100%",
                        ),
                        rx.box(),
                    ),
                    # Upload zone
                    rx.upload(
                        rx.vstack(
                            rx.cond(
                                ProfileState.avatar_preview_url != "",
                                rx.icon("refresh-cw", size=24, color=ACCENT_BLUE),
                                rx.icon("upload", size=28, color=TEXT_TERTIARY),
                            ),
                            rx.vstack(
                                rx.text(
                                    rx.cond(
                                        ProfileState.avatar_preview_url != "",
                                        "Выбрать другой файл",
                                        "Перетащите PNG или JPEG сюда или кликните",
                                    ),
                                    color=TEXT_SECONDARY,
                                    font_size="13px",
                                    font_weight="500",
                                    text_align="center",
                                ),
                                rx.hstack(
                                    rx.box(
                                        rx.text(
                                            "PNG / JPEG",
                                            color=ACCENT_BLUE,
                                            font_size="11px",
                                            font_weight="700",
                                        ),
                                        padding="3px 8px",
                                        background="rgba(59,130,246,0.12)",
                                        border="1px solid rgba(59,130,246,0.25)",
                                        border_radius="6px",
                                    ),
                                    rx.text(
                                        "Макс. размер: 5 МБ",
                                        color=TEXT_TERTIARY,
                                        font_size="11px",
                                    ),
                                    gap="8px",
                                    align="center",
                                    justify_content="center",
                                ),
                                spacing="2",
                                align="center",
                            ),
                            spacing="2",
                            align="center",
                        ),
                        id="avatar-upload",
                        accept={"image/png": [".png"], "image/jpeg": [".jpg", ".jpeg"]},
                        max_files=1,
                        on_drop=ProfileState.handle_avatar_select,
                        border=rx.cond(
                            ProfileState.avatar_preview_url != "",
                            f"2px dashed {ACCENT_BLUE}44",
                            "2px dashed rgba(255, 255, 255, 0.1)",
                        ),
                        border_radius="14px",
                        padding="20px 28px",
                        width="100%",
                        background=rx.cond(
                            ProfileState.avatar_preview_url != "",
                            "rgba(59,130,246,0.03)",
                            "rgba(255,255,255,0.02)",
                        ),
                        cursor="pointer",
                        _hover={"border_color": ACCENT_BLUE, "background": "rgba(59,130,246,0.05)"},
                        transition="all 0.2s ease",
                    ),
                    # Error message
                    rx.cond(
                        ProfileState.avatar_upload_error != "",
                        rx.hstack(
                            rx.icon("alert-circle", size=14, color=DANGER_RED),
                            rx.text(
                                ProfileState.avatar_upload_error,
                                color=DANGER_RED,
                                font_size="13px",
                            ),
                            gap="6px",
                            align="center",
                            padding="10px 14px",
                            background="rgba(239,68,68,0.08)",
                            border="1px solid rgba(239,68,68,0.2)",
                            border_radius="10px",
                            width="100%",
                        ),
                        rx.box(),
                    ),
                    # Action buttons
                    rx.hstack(
                        rx.el.button(
                            "Отмена",
                            color=TEXT_PRIMARY,
                            font_size="14px",
                            background="rgba(255, 255, 255, 0.05)",
                            border="1px solid rgba(255, 255, 255, 0.1)",
                            padding="10px 20px",
                            border_radius="10px",
                            cursor="pointer",
                            transition="all 0.2s ease",
                            _hover={"background": "rgba(255,255,255,0.09)"},
                            on_click=ProfileState.close_avatar_upload,
                        ),
                        rx.el.button(
                            rx.hstack(
                                rx.icon("check", size=15),
                                rx.text("Сохранить"),
                                gap="6px",
                                align="center",
                            ),
                            color="white",
                            font_size="14px",
                            font_weight="600",
                            background=rx.cond(
                                ProfileState.avatar_preview_url != "",
                                "rgba(34,197,94,0.2)",
                                "rgba(255,255,255,0.08)",
                            ),
                            border=rx.cond(
                                ProfileState.avatar_preview_url != "",
                                "1px solid rgba(34,197,94,0.5)",
                                "1px solid rgba(255,255,255,0.08)",
                            ),
                            padding="10px 20px",
                            border_radius="10px",
                            cursor=rx.cond(ProfileState.avatar_preview_url != "", "pointer", "default"),
                            opacity=rx.cond(ProfileState.avatar_preview_url != "", "1", "0.4"),
                            transition="all 0.2s ease",
                            box_shadow=rx.cond(
                                ProfileState.avatar_preview_url != "",
                                "0 0 12px rgba(34,197,94,0.3)",
                                "none",
                            ),
                            _hover=rx.cond(
                                ProfileState.avatar_preview_url != "",
                                {"box_shadow": "0 0 20px rgba(34,197,94,0.5)", "transform": "translateY(-1px)"},
                                {},
                            ),
                            on_click=ProfileState.upload_avatar,
                        ),
                        spacing="3",
                        width="100%",
                        justify_content="end",
                    ),
                    spacing="4",
                    width="100%",
                ),
                position="fixed",
                top="50%",
                left="50%",
                transform="translate(-50%, -50%)",
                z_index="301",
                background="rgba(12,12,20,0.96)",
                border="1px solid rgba(255, 255, 255, 0.1)",
                border_radius="22px",
                padding="28px",
                backdrop_filter="blur(40px) saturate(180%)",
                box_shadow="0 32px 80px rgba(0,0,0,0.6)",
                width="min(480px, 92vw)",
            ),
        ),
    )


def profile_page() -> rx.Component:
    """Главная страница профиля (Аккаунт)."""
    return profile_layout(account_page())


def profile_files_page() -> rx.Component:
    """Страница файлов."""
    return profile_layout(files_page())


def profile_referral_page() -> rx.Component:
    """Страница реферальной программы."""
    return profile_layout(referral_page())
