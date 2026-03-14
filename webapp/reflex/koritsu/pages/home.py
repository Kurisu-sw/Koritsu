import reflex as rx
from koritsu.state.auth_state import AuthState

# ── Palette ────────────────────────────────────────────────────────────────
BG          = "linear-gradient(135deg, #08080f 0%, #0b0f1a 50%, #07101e 100%)"
PANEL       = "rgba(255,255,255,0.05)"
HOVER       = "rgba(255,255,255,0.09)"
BORDER      = "rgba(255,255,255,0.10)"
ACCENT      = "#3b82f6"
ACCENT2     = "rgba(59,130,246,0.18)"
ACCENT_GLOW = "rgba(59,130,246,0.30)"
TEXT        = "rgba(255,255,255,0.92)"
MUTED       = "rgba(255,255,255,0.40)"
MUTED2      = "rgba(255,255,255,0.22)"
DANGER      = "#f87171"
SUCCESS     = "#34d399"
SANS        = "-apple-system,BlinkMacSystemFont,'SF Pro Display','Segoe UI',system-ui,sans-serif"

INPUT_STYLE = {
    "background": "rgba(255,255,255,0.04)",
    "border": f"1px solid {BORDER}",
    "border_radius": "12px",
    "color": TEXT,
    "font_family": SANS,
    "font_size": "14px",
    "padding": "12px 16px",
    "width": "100%",
    "outline": "none",
    "transition": "all 0.2s",
    "_focus": {
        "border_color": ACCENT,
        "box_shadow": f"0 0 0 3px {ACCENT2}",
    },
    "_placeholder": {"color": MUTED2},
}


# ── Nav bar ────────────────────────────────────────────────────────────────

def _nav_link(label: str, href: str) -> rx.Component:
    return rx.link(
        rx.box(
            rx.text(label, color=TEXT, font_size="13px",
                    font_family=SANS, font_weight="500"),
            background=PANEL,
            border=f"1px solid {BORDER}",
            padding="7px 18px",
            border_radius="10px",
            cursor="pointer",
            transition="all 0.2s",
            _hover={
                "background": HOVER,
                "border_color": "rgba(255,255,255,0.20)",
            },
        ),
        href=href,
        text_decoration="none",
    )


def _auth_nav_buttons() -> rx.Component:
    """Login/Register buttons shown when not logged in."""
    return rx.hstack(
        rx.el.button(
            "Войти",
            color=TEXT,
            font_size="13px",
            font_family=SANS,
            font_weight="500",
            background=PANEL,
            border=f"1px solid {BORDER}",
            padding="7px 18px",
            border_radius="10px",
            cursor="pointer",
            transition="all 0.2s",
            on_click=AuthState.open_login,
        ),
        rx.el.button(
            "Регистрация",
            color="white",
            font_size="13px",
            font_family=SANS,
            font_weight="600",
            background=f"linear-gradient(135deg,{ACCENT},#2563eb)",
            border="none",
            padding="7px 18px",
            border_radius="10px",
            box_shadow=f"0 2px 12px {ACCENT_GLOW}",
            cursor="pointer",
            transition="all 0.2s",
            on_click=AuthState.open_register,
        ),
        spacing="2",
    )


def _user_avatar() -> rx.Component:
    """Circular avatar with user initial."""
    return rx.box(
        rx.text(
            AuthState.user_initial,
            color="white",
            font_size="13px",
            font_weight="700",
            font_family=SANS,
        ),
        width="34px",
        height="34px",
        min_width="34px",
        background=f"linear-gradient(135deg,{ACCENT},#2563eb)",
        border_radius="50%",
        display="flex",
        align_items="center",
        justify_content="center",
        border="2px solid rgba(255,255,255,0.15)",
    )


def _user_menu() -> rx.Component:
    """User avatar + dropdown shown when logged in."""
    return rx.menu.root(
        rx.menu.trigger(
            rx.hstack(
                _user_avatar(),
                rx.text(
                    AuthState.username,
                    color=TEXT,
                    font_size="13px",
                    font_family=SANS,
                    font_weight="500",
                    display=["none", "none", "block"],
                ),
                spacing="2",
                align="center",
                cursor="pointer",
                padding="4px 8px",
                border_radius="12px",
                transition="all 0.15s",
                _hover={"background": HOVER},
            ),
        ),
        rx.menu.content(
            rx.menu.item(
                rx.hstack(
                    rx.icon("crown", size=14, color="#fbbf24"),
                    rx.text("Подписка", font_family=SANS, font_size="13px"),
                    spacing="2", align="center",
                ),
            ),
            rx.menu.item(
                rx.hstack(
                    rx.icon("settings", size=14, color=MUTED),
                    rx.text("Настройки", font_family=SANS, font_size="13px"),
                    spacing="2", align="center",
                ),
            ),
            rx.menu.separator(),
            rx.menu.item(
                rx.hstack(
                    rx.icon("log-out", size=14, color=DANGER),
                    rx.text("Выйти", font_family=SANS, font_size="13px", color=DANGER),
                    spacing="2", align="center",
                ),
                on_click=AuthState.do_logout,
            ),
            background="rgba(15,15,25,0.95)",
            border=f"1px solid {BORDER}",
            backdrop_filter="blur(20px) saturate(180%)",
            border_radius="14px",
            padding="6px",
            box_shadow="0 16px 48px rgba(0,0,0,0.5)",
        ),
    )


def _nav() -> rx.Component:
    return rx.box(
        rx.hstack(
            # Logo
            rx.hstack(
                rx.box(
                    rx.text("K", color=ACCENT, font_size="18px", font_weight="700",
                            font_family=SANS),
                    width="32px", height="32px",
                    background=f"linear-gradient(135deg,{ACCENT2},{ACCENT_GLOW})",
                    border=f"1px solid {ACCENT}",
                    border_radius="10px",
                    display="flex", align_items="center", justify_content="center",
                ),
                rx.text("Koritsu", color=TEXT, font_size="17px", font_weight="600",
                        font_family=SANS, letter_spacing="-0.3px"),
                spacing="2", align="center",
            ),
            rx.spacer(),
            # Nav links
            rx.hstack(
                _nav_link("Fragmos", "/fragmos"),
                _nav_link("Engrafo", "/engrafo"),
                spacing="2",
            ),
            rx.spacer(),
            # Right side: auth buttons or user menu
            rx.cond(
                AuthState.is_logged_in,
                _user_menu(),
                _auth_nav_buttons(),
            ),
            align="center",
            width="100%",
        ),
        position="fixed",
        top="0", left="0", right="0",
        z_index="100",
        background="rgba(8,8,15,0.75)",
        backdrop_filter="blur(20px) saturate(180%)",
        border_bottom=f"1px solid {BORDER}",
        padding_x="32px",
        height="56px",
        display="flex",
        align_items="center",
    )


# ── App card ───────────────────────────────────────────────────────────────

def _app_card(
    icon: rx.Component,
    icon_bg: str,
    title: str,
    subtitle: str,
    description: str,
    tags: list[str],
    href: str,
    tag_colors: list[str] | None = None,
) -> rx.Component:
    tag_colors = tag_colors or [ACCENT2] * len(tags)

    tag_pills = rx.hstack(
        *[
            rx.box(
                rx.text(tag, color=MUTED, font_size="11px", font_family=SANS,
                        font_weight="600", letter_spacing="0.4px"),
                background=col,
                border_radius="6px",
                padding="3px 10px",
            )
            for tag, col in zip(tags, tag_colors)
        ],
        spacing="2",
        flex_wrap="wrap",
    )

    return rx.link(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.box(
                        icon,
                        width="48px", height="48px",
                        background=icon_bg,
                        border_radius="14px",
                        border=f"1px solid rgba(255,255,255,0.10)",
                        display="flex", align_items="center", justify_content="center",
                    ),
                    rx.vstack(
                        rx.text(title, color=TEXT, font_size="18px", font_weight="700",
                                font_family=SANS, letter_spacing="-0.4px"),
                        rx.text(subtitle, color=MUTED, font_size="12px",
                                font_family=SANS, font_weight="500",
                                letter_spacing="0.6px", text_transform="uppercase"),
                        spacing="0", align="start",
                    ),
                    rx.spacer(),
                    rx.text("→", color=MUTED2, font_size="20px", transition="all 0.2s"),
                    align="center", width="100%",
                ),
                rx.box(height="1px", background=BORDER, width="100%"),
                rx.text(description, color=MUTED, font_size="14px",
                        font_family=SANS, line_height="1.7", font_weight="400"),
                tag_pills,
                spacing="4", align="start", width="100%",
            ),
            background=PANEL,
            border=f"1px solid {BORDER}",
            border_radius="20px",
            padding="28px",
            backdrop_filter="blur(20px)",
            transition="all 0.25s cubic-bezier(0.4,0,0.2,1)",
            cursor="pointer",
            _hover={
                "background": HOVER,
                "border_color": "rgba(255,255,255,0.18)",
                "transform": "translateY(-4px)",
                "box_shadow": "0 20px 60px rgba(0,0,0,0.4)",
            },
        ),
        href=href,
        text_decoration="none",
        display="block",
    )


# ── Auth strip (not logged in) ────────────────────────────────────────────

def _auth_strip_guest() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text("Начните прямо сейчас", color=TEXT, font_size="20px",
                        font_weight="700", font_family=SANS, letter_spacing="-0.4px"),
                rx.text("Создайте аккаунт или войдите в систему",
                        color=MUTED, font_size="14px", font_family=SANS),
                spacing="1", align="start",
            ),
            rx.spacer(),
            rx.hstack(
                rx.el.button(
                    "Войти",
                    color=TEXT,
                    font_size="14px",
                    font_family=SANS,
                    font_weight="500",
                    background=PANEL,
                    border=f"1px solid {BORDER}",
                    padding="10px 24px",
                    border_radius="12px",
                    cursor="pointer",
                    transition="all 0.2s",
                    on_click=AuthState.open_login,
                ),
                rx.el.button(
                    "Регистрация",
                    color="white",
                    font_size="14px",
                    font_family=SANS,
                    font_weight="600",
                    background=f"linear-gradient(135deg,{ACCENT},#2563eb)",
                    border="none",
                    padding="10px 24px",
                    border_radius="12px",
                    box_shadow=f"0 4px 20px {ACCENT_GLOW}",
                    cursor="pointer",
                    transition="all 0.2s",
                    on_click=AuthState.open_register,
                ),
                spacing="3",
            ),
            align="center", width="100%",
            flex_wrap="wrap",
            gap="16px",
        ),
        background=PANEL,
        border=f"1px solid {BORDER}",
        border_radius="20px",
        padding="28px 32px",
        backdrop_filter="blur(20px)",
        width="100%",
        max_width="860px",
        margin_x="auto",
    )


# ── Welcome strip (logged in) ─────────────────────────────────────────────

def _sub_badge() -> rx.Component:
    return rx.box(
        rx.text(
            AuthState.sub_label,
            color=ACCENT,
            font_size="11px",
            font_family=SANS,
            font_weight="700",
            letter_spacing="0.5px",
        ),
        background=ACCENT2,
        border=f"1px solid {ACCENT}",
        border_radius="8px",
        padding="3px 10px",
    )


def _stat_item(label: str, value) -> rx.Component:
    return rx.vstack(
        rx.text(label, color=MUTED, font_size="11px", font_family=SANS,
                font_weight="600", letter_spacing="0.5px", text_transform="uppercase"),
        rx.text(value, color=TEXT, font_size="15px", font_family=SANS,
                font_weight="600"),
        spacing="1",
        align="start",
    )


def _welcome_strip() -> rx.Component:
    return rx.box(
        rx.vstack(
            # Welcome row
            rx.hstack(
                _user_avatar(),
                rx.vstack(
                    rx.hstack(
                        rx.text(
                            "Добро пожаловать в Koritsu, ",
                            rx.text(AuthState.username, as_="span", font_weight="700"),
                            "!",
                            color=TEXT,
                            font_size="20px",
                            font_weight="500",
                            font_family=SANS,
                            letter_spacing="-0.4px",
                        ),
                        _sub_badge(),
                        spacing="3",
                        align="center",
                        flex_wrap="wrap",
                    ),
                    spacing="1",
                    align="start",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            # Divider
            rx.box(height="1px", background=BORDER, width="100%"),
            # Stats row
            rx.hstack(
                _stat_item("Подписка", AuthState.sub_label),
                rx.box(width="1px", height="36px", background=BORDER),
                _stat_item("Действует до", AuthState.sub_expire_display),
                rx.box(width="1px", height="36px", background=BORDER),
                _stat_item("Токены", AuthState.tokens_left),
                spacing="5",
                align="center",
                flex_wrap="wrap",
            ),
            spacing="4",
            align="start",
            width="100%",
        ),
        background=PANEL,
        border=f"1px solid {BORDER}",
        border_radius="20px",
        padding="28px 32px",
        backdrop_filter="blur(20px)",
        width="100%",
        max_width="860px",
        margin_x="auto",
    )


# ── Auth modal ─────────────────────────────────────────────────────────────

def _modal_input(placeholder: str, value, on_change, input_type: str = "text") -> rx.Component:
    return rx.el.input(
        placeholder=placeholder,
        value=value,
        on_change=on_change,
        type=input_type,
        **INPUT_STYLE,
    )


def _modal_tab(label: str, is_active, on_click) -> rx.Component:
    return rx.box(
        rx.text(label, font_size="14px", font_family=SANS, font_weight="600"),
        padding="10px 0",
        cursor="pointer",
        color=rx.cond(is_active, TEXT, MUTED2),
        border_bottom=rx.cond(is_active, f"2px solid {ACCENT}", "2px solid transparent"),
        transition="all 0.2s",
        flex="1",
        text_align="center",
        on_click=on_click,
    )


def _submit_btn(label: str, on_click) -> rx.Component:
    return rx.el.button(
        label,
        color="white",
        font_size="14px",
        font_family=SANS,
        font_weight="600",
        background=f"linear-gradient(135deg,{ACCENT},#2563eb)",
        border="none",
        padding="12px 0",
        border_radius="12px",
        box_shadow=f"0 4px 20px {ACCENT_GLOW}",
        cursor="pointer",
        transition="all 0.2s",
        text_align="center",
        width="100%",
        on_click=on_click,
    )


def _login_form() -> rx.Component:
    return rx.vstack(
        _modal_input(
            "Имя пользователя",
            AuthState.login_username,
            AuthState.set_login_username,
        ),
        _modal_input(
            "Пароль",
            AuthState.login_password,
            AuthState.set_login_password,
            input_type="password",
        ),
        _submit_btn("Войти", AuthState.do_login),
        spacing="3",
        width="100%",
    )


def _register_form() -> rx.Component:
    return rx.vstack(
        _modal_input(
            "Имя пользователя",
            AuthState.register_username,
            AuthState.set_register_username,
        ),
        _modal_input(
            "Пароль (мин. 12, заглавная + спецсимвол)",
            AuthState.register_password,
            AuthState.set_register_password,
            input_type="password",
        ),
        _modal_input(
            "Подтвердите пароль",
            AuthState.register_password_confirm,
            AuthState.set_register_password_confirm,
            input_type="password",
        ),
        _submit_btn("Создать аккаунт", AuthState.do_register),
        spacing="3",
        width="100%",
    )


def _auth_modal() -> rx.Component:
    return rx.cond(
        AuthState.show_auth_modal,
        rx.box(
            # Backdrop
            rx.box(
                position="fixed",
                inset="0",
                background="rgba(0,0,0,0.60)",
                backdrop_filter="blur(8px)",
                z_index="200",
                on_click=AuthState.close_auth_modal,
            ),
            # Modal card
            rx.box(
                rx.vstack(
                    # Tabs
                    rx.hstack(
                        _modal_tab(
                            "Вход",
                            AuthState.auth_tab == "login",
                            AuthState.switch_to_login,
                        ),
                        _modal_tab(
                            "Регистрация",
                            AuthState.auth_tab == "register",
                            AuthState.switch_to_register,
                        ),
                        width="100%",
                        border_bottom=f"1px solid {BORDER}",
                        margin_bottom="8px",
                    ),
                    # Error message
                    rx.cond(
                        AuthState.auth_error != "",
                        rx.box(
                            rx.hstack(
                                rx.icon("alert-circle", size=14, color=DANGER),
                                rx.text(
                                    AuthState.auth_error,
                                    color=DANGER,
                                    font_size="13px",
                                    font_family=SANS,
                                ),
                                spacing="2",
                                align="center",
                            ),
                            background="rgba(248,113,113,0.08)",
                            border=f"1px solid rgba(248,113,113,0.20)",
                            border_radius="10px",
                            padding="10px 14px",
                            width="100%",
                        ),
                    ),
                    # Success message
                    rx.cond(
                        AuthState.auth_success != "",
                        rx.box(
                            rx.hstack(
                                rx.icon("check-circle", size=14, color=SUCCESS),
                                rx.text(
                                    AuthState.auth_success,
                                    color=SUCCESS,
                                    font_size="13px",
                                    font_family=SANS,
                                ),
                                spacing="2",
                                align="center",
                            ),
                            background="rgba(52,211,153,0.08)",
                            border=f"1px solid rgba(52,211,153,0.20)",
                            border_radius="10px",
                            padding="10px 14px",
                            width="100%",
                        ),
                    ),
                    # Form
                    rx.cond(
                        AuthState.auth_tab == "login",
                        _login_form(),
                        _register_form(),
                    ),
                    spacing="3",
                    width="100%",
                ),
                position="fixed",
                top="50%",
                left="50%",
                transform="translate(-50%, -50%)",
                z_index="201",
                background="rgba(12,12,20,0.92)",
                border=f"1px solid {BORDER}",
                border_radius="22px",
                padding="28px",
                backdrop_filter="blur(40px) saturate(180%)",
                box_shadow="0 32px 80px rgba(0,0,0,0.6), 0 0 1px rgba(255,255,255,0.1)",
                width="min(400px, 90vw)",
            ),
        ),
    )


# ── Footer ─────────────────────────────────────────────────────────────────

def _footer() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.spacer(),
            rx.hstack(
                rx.link(rx.text("Fragmos", color=MUTED2, font_size="13px",
                                font_family=SANS, _hover={"color": MUTED}),
                        href="/fragmos", text_decoration="none"),
                rx.link(rx.text("Engrafo", color=MUTED2, font_size="13px",
                                font_family=SANS, _hover={"color": MUTED}),
                        href="/engrafo", text_decoration="none"),
                spacing="5",
            ),
            align="center", width="100%",
        ),
        border_top=f"1px solid {BORDER}",
        padding_x="32px",
        padding_y="24px",
        background="rgba(8,8,15,0.60)",
        backdrop_filter="blur(12px)",
    )


# ── Page ───────────────────────────────────────────────────────────────────

def home_page() -> rx.Component:
    return rx.box(
        _nav(),
        _auth_modal(),

        # Main content
        rx.box(
            # Glow blob
            rx.box(
                width="700px", height="400px",
                background=f"radial-gradient(ellipse,{ACCENT_GLOW} 0%,transparent 70%)",
                position="absolute",
                top="0", left="50%",
                transform="translateX(-50%)",
                pointer_events="none",
                z_index="0",
            ),
            rx.vstack(
                rx.grid(
                    _app_card(
                        icon=rx.icon("workflow", size=22, color=ACCENT),
                        icon_bg=f"linear-gradient(135deg,{ACCENT2},{ACCENT_GLOW})",
                        title="Fragmos",
                        subtitle="Генератор блок схем с AI",
                        description=(
                            "Генерируйте блок схемы для редактора DarawIO по коду с помощью AI"
                        ),
                        tags=[""],
                        href="/fragmos",
                    ),
                    _app_card(
                        icon=rx.icon("file-text", size=22, color="rgba(167,139,250,0.9)"),
                        icon_bg="linear-gradient(135deg,rgba(167,139,250,0.18),rgba(167,139,250,0.30))",
                        title="Engrafo",
                        subtitle="Генератор отчетов с AI ассистентом",
                        description=(
                            "Автоматическая генрерация отчета и обьясненние содержания с помощью агента"
                        ),
                        tags=[""],
                        href="/engrafo",
                    ),
                    columns="2",
                    spacing="5",
                    width="100%",
                    auto_rows="1fr",
                ),
                # Auth strip or welcome strip
                rx.cond(
                    AuthState.is_logged_in,
                    _welcome_strip(),
                    _auth_strip_guest(),
                ),
                spacing="6",
                align="center",
                width="100%",
                max_width="860px",
                margin_x="auto",
                padding_x="24px",
                position="relative",
                z_index="1",
            ),
            position="relative",
            padding_top="calc(56px + 48px)",
            padding_bottom="32px",
            overflow="hidden",
            flex="1",
        ),

        _footer(),

        background=BG,
        min_height="100vh",
        display="flex",
        flex_direction="column",
        font_family=SANS,
    )
