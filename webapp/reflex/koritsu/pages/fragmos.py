import reflex as rx
from koritsu.state.fragmos_state import FragmosState
from koritsu.state.auth_state import AuthState

# ── Palette ───────────────────────────────────────────────────────────────────
BG          = "linear-gradient(135deg, #08080f 0%, #0b0f1a 50%, #07101e 100%)"
PANEL       = "rgba(255,255,255,0.05)"
PANEL_HVR   = "rgba(255,255,255,0.08)"
BORDER      = "rgba(255,255,255,0.10)"
BORDER_BLUE = "rgba(59,130,246,0.35)"
ACCENT      = "#3b82f6"
ACCENT_HVR  = "#2563eb"
ACCENT2     = "#818cf8"
ACCENT_GLOW = "rgba(59,130,246,0.20)"
ACTIVE_BG   = "rgba(59,130,246,0.15)"
ACTIVE_TXT  = "#60a5fa"
TEXT        = "rgba(255,255,255,0.92)"
MUTED       = "rgba(255,255,255,0.42)"
MUTED2      = "rgba(255,255,255,0.22)"
HEADER_BG   = "rgba(8,8,15,0.88)"
CODE_BG     = "rgba(255,255,255,0.04)"
DANGER      = "#f87171"
DANGER_BG   = "rgba(248,113,113,0.12)"
SUCCESS     = "#34d399"

MONO = "'SF Mono','Fira Code','Cascadia Code',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'SF Pro Display','Segoe UI',system-ui,sans-serif"

SCROLLBAR_CSS = {
    "&::-webkit-scrollbar":       {"width": "4px"},
    "&::-webkit-scrollbar-track": {"background": "transparent"},
    "&::-webkit-scrollbar-thumb": {"background": BORDER, "border_radius": "2px"},
}

# ── Nav bar (from home page) ────────────────────────────────────────────────

PANEL_H       = "rgba(255,255,255,0.05)"
HOVER_H       = "rgba(255,255,255,0.09)"
ACCENT2_H     = "rgba(59,130,246,0.18)"
ACCENT_GLOW_H = "rgba(59,130,246,0.30)"

def _nav_link(label: str, href: str) -> rx.Component:
    return rx.link(
        rx.box(
            rx.text(label, color=TEXT, font_size="13px",
                    font_family=SANS, font_weight="500"),
            background=PANEL_H,
            border=f"1px solid {BORDER}",
            padding="7px 18px",
            border_radius="10px",
            cursor="pointer",
            transition="all 0.2s",
            _hover={
                "background": HOVER_H,
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
            background=PANEL_H,
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
            box_shadow=f"0 2px 12px {ACCENT_GLOW_H}",
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
                _hover={"background": PANEL_HVR},
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
            rx.link(
                rx.hstack(
                    rx.box(
                        rx.text("K", color=ACCENT, font_size="18px", font_weight="700",
                                font_family=SANS),
                        width="32px", height="32px",
                        background=f"linear-gradient(135deg,{ACCENT2_H},{ACCENT_GLOW_H})",
                        border=f"1px solid {ACCENT}",
                        border_radius="10px",
                        display="flex", align_items="center", justify_content="center",
                    ),
                    rx.text("Koritsu", color=TEXT, font_size="17px", font_weight="600",
                            font_family=SANS, letter_spacing="-0.3px"),
                    spacing="2", align="center",
                ),
                href="/",
                text_decoration="none",
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


# ─────────────────────────────────────────────────────────────────────────────
# Shared tiny helpers
# ─────────────────────────────────────────────────────────────────────────────

def _icon_box(tag: str, size: int = 18, color: str = ACCENT,
              bg: str | None = None, radius: str = "12px",
              box_size: str = "36px") -> rx.Component:
    bg = bg or f"linear-gradient(135deg,{ACCENT_GLOW},rgba(129,140,248,0.15))"
    return rx.box(
        rx.icon(tag, size=size, color=color),
        width=box_size, height=box_size,
        background=bg, border_radius=radius,
        display="flex", align_items="center", justify_content="center",
        flex_shrink="0",
    )


def _btn(label: str | None = None, icon: str | None = None,
         on_click=None, variant: str = "ghost",
         size: str = "sm", extra: dict | None = None) -> rx.Component:
    """Ghost / filled / danger button."""
    bg    = PANEL       if variant == "ghost"  else (ACCENT if variant == "blue" else DANGER_BG)
    hover = PANEL_HVR   if variant == "ghost"  else (ACCENT_HVR if variant == "blue" else "rgba(248,113,113,0.20)")
    col   = TEXT        if variant == "ghost"  else ("white" if variant == "blue" else DANGER)
    pad   = "6px 12px"  if size == "sm"        else "10px 20px"
    fsize = "12px"      if size == "sm"        else "14px"
    children = []
    if icon:
        children.append(rx.icon(icon, size=14 if size == "sm" else 16, color=col))
    if label:
        children.append(rx.text(label, font_size=fsize, font_weight="500", color=col))
    props = dict(
        display="flex", align_items="center", gap="6px",
        padding=pad, border_radius="10px", border=f"1px solid {BORDER}",
        background=bg, cursor="pointer",
        transition="all 0.15s ease",
        _hover={"background": hover},
        _active={"transform": "scale(0.97)"},
        **(extra or {}),
    )
    if on_click:
        props["on_click"] = on_click
    return rx.button(*children, **props)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

def _chat_item(chat: dict) -> rx.Component:
    is_active = FragmosState.selected_chat_id == chat["id"]
    return rx.box(
        # Left icon
        rx.icon("layout-template", size=14,
                color=rx.cond(is_active, ACTIVE_TXT, MUTED)),
        # Text
        rx.box(
            rx.text(chat["name"], font_size="13px", font_weight="600",
                    color=rx.cond(is_active, ACTIVE_TXT, TEXT),
                    overflow="hidden", text_overflow="ellipsis",
                    white_space="nowrap"),
            rx.text(chat["timestamp"], font_size="11px", margin_top="1px",
                    color=rx.cond(is_active, "rgba(96,165,250,0.65)", MUTED)),
            flex="1", min_width="0",
        ),
        # Delete button (always visible on hover via group)
        rx.button(
            rx.icon("trash-2", size=12, color=DANGER),
            width="24px", height="24px",
            background="transparent", border="none",
            border_radius="6px", cursor="pointer", flex_shrink="0",
            display="flex", align_items="center", justify_content="center",
            opacity="0",
            css={"transition": "opacity 0.15s, background 0.15s",
                 ".group:hover &": {"opacity": "1"},
                 "&:hover": {"background": DANGER_BG}},
            on_click=FragmosState.on_request_delete(chat["id"]),
        ),
        class_name="group",
        display="flex", align_items="center", gap="8px",
        padding="10px 12px",
        border_radius="12px",
        cursor="pointer",
        background=rx.cond(is_active, ACTIVE_BG, "transparent"),
        border=rx.cond(is_active, f"1px solid {BORDER_BLUE}", "1px solid transparent"),
        box_shadow=rx.cond(is_active, "0 2px 8px rgba(59,130,246,0.12)", "none"),
        transition="all 0.15s ease",
        _hover={"background": rx.cond(is_active, ACTIVE_BG, PANEL_HVR)},
        on_click=FragmosState.on_select_chat(chat["id"]),
    )


def auth_required() -> rx.Component:
    """Экран с сообщением о необходимости авторизации"""
    return rx.box(
        # Hero icon
        rx.box(
            rx.icon("log-in", size=46, color="white"),
            width="92px", height="92px",
            background=f"linear-gradient(135deg,{ACCENT},{ACCENT2})",
            border_radius="26px",
            display="flex", align_items="center", justify_content="center",
            box_shadow=f"0 20px 60px {ACCENT_GLOW},0 8px 28px rgba(59,130,246,0.22)",
            margin_bottom="22px",
        ),
        rx.text("Требуется авторизация",
                font_size="30px", font_weight="700", color=TEXT,
                letter_spacing="-0.5px", margin_bottom="10px"),
        rx.text(
            "Войдите в систему, чтобы получить доступ к генератору блок-схем",
            font_size="15px", color=MUTED, text_align="center",
            line_height="1.6", margin_bottom="36px",
        ),
        # Login button
        rx.button(
            rx.icon("log-in", size=17, color="white"),
            rx.text("Войти", font_size="15px", font_weight="600", color="white"),
            display="flex", align_items="center", justify_content="center", gap="9px",
            width="100%", max_width="280px", padding="14px 20px",
            background=ACCENT, border_radius="14px", border="none",
            cursor="pointer",
            box_shadow="0 4px 18px rgba(59,130,246,0.32)",
            transition="all 0.15s",
            _hover={"background": ACCENT_HVR},
            _active={"transform": "scale(0.98)"},
            on_click=AuthState.open_login,
        ),
        display="flex", flex_direction="column", align_items="center",
        justify_content="center",
        flex="1", width="100%", height="100vh",
        background=BG,
    )


def sidebar() -> rx.Component:
    return rx.box(
        # ── Top bar ───────────────────────────────────────────────────────────
        rx.box(
            rx.text("История", font_size="13px", font_weight="600", color=TEXT),
            display="flex", align_items="center",
            padding="16px 12px 12px",
        ),
        # ── New button ────────────────────────────────────────────────────────
        rx.box(
            rx.button(
                rx.icon("plus", size=15, color="white"),
                rx.text("Новая блок-схема", font_size="13px",
                        font_weight="600", color="white"),
                display="flex", align_items="center",
                justify_content="center", gap="7px",
                width="100%", padding="10px 14px",
                background=ACCENT, border_radius="12px", border="none",
                cursor="pointer",
                box_shadow="0 2px 10px rgba(59,130,246,0.28)",
                transition="all 0.15s",
                _hover={"background": ACCENT_HVR,
                        "box_shadow": "0 4px 16px rgba(59,130,246,0.38)"},
                _active={"transform": "scale(0.98)"},
                on_click=FragmosState.on_new_chat_click,
            ),
            padding="0 12px 10px",
        ),
        # ── Chat list ─────────────────────────────────────────────────────────
        rx.box(
            rx.cond(
                FragmosState.chats.length() > 0,
                rx.box(
                    rx.foreach(FragmosState.chats, _chat_item),
                    display="flex", flex_direction="column", gap="2px",
                    padding="0 6px",
                ),
                # Empty schemes
                rx.box(
                    rx.icon("layout-template", size=28, color=MUTED2),
                    rx.text("У вас пока нет схем",
                            font_size="13px", color=MUTED,
                            text_align="center", margin_top="10px"),
                    rx.text("Создайте первую блок-схему",
                            font_size="11px", color=MUTED2,
                            text_align="center", margin_top="4px"),
                    display="flex", flex_direction="column",
                    align_items="center", justify_content="center",
                    padding="32px 16px", flex="1",
                ),
            ),
            flex="1", overflow_y="auto", css=SCROLLBAR_CSS,
        ),
        # Panel shell
        width="244px", flex_shrink="0",
        height="calc(100vh - 56px)",
        margin_top="56px",
        display="flex", flex_direction="column",
        background=HEADER_BG, backdrop_filter="blur(20px)",
        border_right=f"1px solid {BORDER}",
        position="sticky", top="56px",
    )


# ─────────────────────────────────────────────────────────────────────────────
# LOADING SPINNER  (used by both empty_state and diagram_viewer)
# ─────────────────────────────────────────────────────────────────────────────

def _loading_spinner() -> rx.Component:
    """Apple-style multi-step loading animation."""

    def _dot(delay: str) -> rx.Component:
        return rx.box(
            width="8px", height="8px", border_radius="50%",
            background=ACCENT,
            style={"animation": f"fpulse 1.2s ease-in-out {delay} infinite"},
        )

    def _step(icon_tag: str, label: str, delay: str) -> rx.Component:
        return rx.box(
            rx.box(
                rx.icon(icon_tag, size=13, color=ACCENT),
                width="26px", height="26px",
                background=ACCENT_GLOW,
                border_radius="8px",
                display="flex", align_items="center", justify_content="center",
                flex_shrink="0",
            ),
            rx.text(label, font_size="12px", color=MUTED, font_weight="500"),
            display="flex", align_items="center", gap="8px",
            style={"animation": f"ffade 0.4s ease {delay} both"},
        )

    return rx.box(
        # Dual concentric spinning rings
        rx.box(
            rx.box(
                width="64px", height="64px", border_radius="50%",
                border="3px solid rgba(59,130,246,0.10)",
                border_top=f"3px solid {ACCENT}",
                position="absolute", top="0", left="0",
                style={"animation": "fspin 0.9s linear infinite"},
            ),
            rx.box(
                width="44px", height="44px", border_radius="50%",
                border="2px solid rgba(129,140,248,0.12)",
                border_bottom=f"2px solid {ACCENT2}",
                position="absolute", top="10px", left="10px",
                style={"animation": "fspinr 1.4s linear infinite"},
            ),
            rx.box(
                rx.icon("network", size=18, color=ACCENT),
                position="absolute", top="50%", left="50%",
                transform="translate(-50%,-50%)",
            ),
            position="relative", width="64px", height="64px",
            margin_bottom="22px",
        ),
        rx.text("Генерация блок-схемы", font_size="16px",
                font_weight="600", color=TEXT, margin_bottom="6px",
                letter_spacing="-0.2px"),
        # Pulsing dots
        rx.box(
            _dot("0s"), _dot("0.2s"), _dot("0.4s"),
            display="flex", gap="5px", align_items="center",
            margin_bottom="28px",
        ),
        # Steps
        rx.box(
            _step("upload", "Отправляем код в нейросеть", "0.1s"),
            _step("cpu", "Анализируем структуру алгоритма", "0.5s"),
            _step("git-branch", "Строим блок-схему", "0.9s"),
            display="flex", flex_direction="column", gap="10px",
            background=PANEL,
            border=f"1px solid {BORDER}",
            border_radius="14px",
            padding="14px 18px",
        ),
        display="flex", flex_direction="column",
        align_items="center", justify_content="center",
        height="100%", min_height="360px",
    )


# ─────────────────────────────────────────────────────────────────────────────
# EMPTY STATE
# ─────────────────────────────────────────────────────────────────────────────

def empty_state() -> rx.Component:
    return rx.box(
        # Header
        rx.box(
            rx.text("Генератор блок-схем", font_size="15px",
                    font_weight="600", color=TEXT),
            height="52px", padding="0 24px",
            display="flex", align_items="center",
            background=HEADER_BG, backdrop_filter="blur(20px)",
            border_bottom=f"1px solid {BORDER}",
        ),
        # Scrollable content
        rx.box(
            rx.cond(
                FragmosState.is_generating,
                _loading_spinner(),
                rx.box(
                # Hero icon
                rx.box(
                    rx.icon("network", size=46, color="white"),
                    width="92px", height="92px",
                    background=f"linear-gradient(135deg,{ACCENT},{ACCENT2})",
                    border_radius="26px",
                    display="flex", align_items="center", justify_content="center",
                    box_shadow=f"0 20px 60px {ACCENT_GLOW},0 8px 28px rgba(59,130,246,0.22)",
                    margin_bottom="22px",
                ),
                rx.text("Создайте блок-схему",
                        font_size="30px", font_weight="700", color=TEXT,
                        letter_spacing="-0.5px", margin_bottom="10px"),
                rx.text(
                    "Вставьте код вашей функции или алгоритма, и мы автоматически\n"
                    "создадим для вас блок-схему. Поддерживает Python, C#, C++, Java и многие другие языки",
                    font_size="15px", color=MUTED, text_align="center",
                    line_height="1.6", white_space="pre-line", margin_bottom="36px",
                ),
                # ── Error banner ──────────────────────────────────────────────
                rx.cond(
                    FragmosState.generation_error != "",
                    rx.box(
                        rx.box(
                            rx.icon("circle-x", size=15, color=DANGER),
                            rx.text("Ошибка генерации", font_size="13px",
                                    font_weight="600", color=DANGER),
                            display="flex", align_items="center", gap="7px",
                        ),
                        rx.text(
                            FragmosState.generation_error,
                            font_size="12px", color="rgba(248,113,113,0.85)",
                            line_height="1.5", margin_top="6px",
                            font_family=MONO,
                            word_break="break-all",
                        ),
                        width="100%", max_width="600px",
                        padding="12px 16px", margin_bottom="14px",
                        background=DANGER_BG,
                        border=f"1px solid rgba(248,113,113,0.30)",
                        border_radius="14px",
                    ),
                    rx.box(),
                ),
                # ── Input card ────────────────────────────────────────────────
                rx.box(
                    # Card header
                    rx.box(
                        _icon_box("code-2"),
                        rx.box(
                            rx.text("Вставьте ваш код", font_size="14px",
                                    font_weight="600", color=TEXT),
                            rx.text("Поддерживаются все популярные языки",
                                    font_size="11px", color=MUTED, margin_top="1px"),
                        ),
                        display="flex", align_items="center", gap="11px",
                        padding="16px 20px",
                        border_bottom=f"1px solid {BORDER}",
                        background="linear-gradient(180deg,rgba(255,255,255,0.03),transparent)",
                        border_radius="20px 20px 0 0",
                    ),
                    # Textarea
                    rx.text_area(
                        value=FragmosState.code_input,
                        on_change=FragmosState.set_code_input,
                        placeholder=(
                            "function example() {\n"
                            "  // Ваш код здесь\n"
                            "  if (condition) {\n"
                            "    return true;\n"
                            "  }\n"
                            "  return false;\n"
                            "}"
                        ),
                        min_height="240px", padding="18px 20px",
                        background="transparent", border="none", outline="none",
                        font_family=MONO, font_size="13px", color=TEXT,
                        resize="none", width="100%", line_height="1.65",
                        box_shadow="none",
                        css={"::placeholder": {"color": MUTED2},
                             "&:focus": {"outline": "none", "box_shadow": "none"}},
                    ),
                    # Submit button
                    rx.box(
                        rx.button(
                            rx.icon("sparkles", size=17, color="white"),
                            rx.text("Создать блок-схему", font_size="15px",
                                    font_weight="600", color="white"),
                            display="flex", align_items="center",
                            justify_content="center", gap="9px",
                            width="100%", padding="14px 20px",
                            background=rx.cond(FragmosState.can_submit,
                                               ACCENT, "rgba(255,255,255,0.07)"),
                            border_radius="14px", border="none",
                            cursor=rx.cond(FragmosState.can_submit,
                                           "pointer", "not-allowed"),
                            box_shadow=rx.cond(FragmosState.can_submit,
                                               "0 4px 18px rgba(59,130,246,0.32)", "none"),
                            transition="all 0.15s",
                            _hover={"background": rx.cond(
                                FragmosState.can_submit, ACCENT_HVR,
                                "rgba(255,255,255,0.07)")},
                            _active={"transform": "scale(0.98)"},
                            on_click=FragmosState.on_submit_code,
                        ),
                        padding="14px 18px",
                        border_top=f"1px solid {BORDER}",
                        background="linear-gradient(0deg,rgba(255,255,255,0.02),transparent)",
                        border_radius="0 0 20px 20px",
                    ),
                    background=PANEL,
                    border_radius="20px",
                    border=f"1px solid {BORDER}",
                    box_shadow="0 8px 40px rgba(0,0,0,0.38)",
                    overflow="hidden",
                    width="100%", max_width="600px",
                    transition="all 0.2s",
                    _hover={"border": f"1px solid {BORDER_BLUE}",
                            "box_shadow": "0 12px 48px rgba(59,130,246,0.10)"},
                ),
                # ── Model + Settings row ──────────────────────────────────────
                rx.box(
                    rx.box(
                        rx.icon("cpu", size=13, color=MUTED),
                        rx.el.select(
                            rx.foreach(
                                FragmosState.model_list,
                                lambda m: rx.el.option(m, value=m),
                            ),
                            value=FragmosState.selected_model,
                            on_change=FragmosState.set_model,
                            style={
                                "background": "transparent",
                                "color": TEXT,
                                "border": "none",
                                "font_size": "12px",
                                "font_weight": "500",
                                "outline": "none",
                                "cursor": "pointer",
                                "font_family": SANS,
                            },
                        ),
                        display="flex", align_items="center", gap="6px",
                        padding="7px 12px",
                        background=PANEL,
                        border=f"1px solid {BORDER}",
                        border_radius="10px",
                        flex="1",
                        transition="all 0.15s",
                        _hover={"border_color": BORDER_BLUE},
                    ),
                    rx.button(
                        rx.icon("settings-2", size=14, color=MUTED),
                        rx.text("Настройки", font_size="12px",
                                font_weight="500", color=MUTED),
                        display="flex", align_items="center", gap="6px",
                        padding="7px 14px",
                        background=PANEL, border=f"1px solid {BORDER}",
                        border_radius="10px", cursor="pointer",
                        transition="all 0.15s",
                        _hover={"background": PANEL_HVR,
                                "border_color": BORDER_BLUE},
                        _active={"transform": "scale(0.97)"},
                        on_click=FragmosState.on_open_settings,
                    ),
                    display="flex", align_items="center", gap="8px",
                    width="100%", max_width="600px", margin_top="10px",
                ),
                display="flex", flex_direction="column", align_items="center",
                padding="44px 24px 32px", max_width="680px", width="100%",
            ),
            ),  # rx.cond
            flex="1", display="flex", align_items="flex-start",
            justify_content="center", overflow_y="auto",
        ),
        # Footer tip
        rx.box(
            rx.text(
                "💡 Для лучших результатов используйте структурированный код с понятными именами переменных",
                font_size="11px", color=MUTED, text_align="center",
            ),
            padding="13px 24px",
            background=HEADER_BG, backdrop_filter="blur(20px)",
            border_top=f"1px solid {BORDER}",
        ),
        flex="1", display="flex", flex_direction="column",
        height="100vh", overflow="hidden",
        padding_top="56px",
    )


# ─────────────────────────────────────────────────────────────────────────────
# DIAGRAM VIEWER
# ─────────────────────────────────────────────────────────────────────────────

def _drawio_embed() -> rx.Component:
    return rx.cond(
        FragmosState.is_generating,
        _loading_spinner(),
        rx.el.iframe(
            src=FragmosState.diagram_src,
            width="100%", height="100%",
            style={"border": "none", "background": "#141820"},
            allow="fullscreen",
        ),
    )


def _hdr_btn(icon_tag: str, label: str, handler) -> rx.Component:
    """Ghost header button with icon + label."""
    return rx.button(
        rx.icon(icon_tag, size=13, color=TEXT),
        rx.text(label, font_size="12px", font_weight="500", color=TEXT),
        display="flex", align_items="center", gap="5px",
        padding="7px 13px",
        background=PANEL,
        border=f"1px solid {BORDER}",
        border_radius="10px",
        cursor="pointer",
        transition="all 0.15s",
        _hover={"background": PANEL_HVR, "border_color": BORDER_BLUE},
        _active={"transform": "scale(0.97)"},
        on_click=handler,
    )


def diagram_viewer() -> rx.Component:
    chat = FragmosState.selected_chat
    return rx.box(
        # Header
        rx.box(
            rx.text(chat["name"], font_size="15px",
                    font_weight="600", color=TEXT),
            rx.box(flex="1"),
            # Ghost buttons
            _hdr_btn("code",        "Код",            FragmosState.on_toggle_code_modal),
            _hdr_btn("download",    "Скачать",        FragmosState.on_download),
            _hdr_btn("refresh-cw",  "Регенерировать", FragmosState.on_regenerate),
            # Bug report
            rx.button(
                rx.icon("flag", size=13, color=DANGER),
                rx.text("Баг", font_size="12px", font_weight="500", color=DANGER),
                display="flex", align_items="center", gap="5px",
                padding="7px 13px",
                background=DANGER_BG,
                border=f"1px solid rgba(248,113,113,0.25)",
                border_radius="10px", cursor="pointer",
                transition="all 0.15s",
                _hover={"background": "rgba(248,113,113,0.20)"},
                _active={"transform": "scale(0.97)"},
                on_click=FragmosState.on_open_bug,
            ),
            # Share (blue)
            rx.button(
                rx.icon("share-2", size=13, color="white"),
                rx.text("Поделиться", font_size="12px",
                        font_weight="600", color="white"),
                display="flex", align_items="center", gap="5px",
                padding="7px 13px",
                background=ACCENT, border="none",
                border_radius="10px", cursor="pointer",
                box_shadow="0 2px 8px rgba(59,130,246,0.28)",
                transition="all 0.15s",
                _hover={"background": ACCENT_HVR},
                _active={"transform": "scale(0.97)"},
                on_click=FragmosState.on_share,
            ),
            # Delete (danger)
            rx.button(
                rx.icon("trash-2", size=14, color=DANGER),
                width="34px", height="34px",
                display="flex", align_items="center", justify_content="center",
                background=DANGER_BG,
                border=f"1px solid rgba(248,113,113,0.25)",
                border_radius="10px", cursor="pointer",
                transition="all 0.15s",
                _hover={"background": "rgba(248,113,113,0.22)"},
                _active={"transform": "scale(0.97)"},
                on_click=FragmosState.on_request_delete(chat["id"]),
            ),
            display="flex", align_items="center", gap="6px",
            height="52px", padding="0 16px",
            background=HEADER_BG, backdrop_filter="blur(20px)",
            border_bottom=f"1px solid {BORDER}",
        ),
        # Sub-header breadcrumb
        rx.box(
            rx.icon("network", size=12, color=MUTED),
            rx.text("БЛОК-СХЕМА", font_size="10px", font_weight="700",
                    color=MUTED, letter_spacing="0.1em"),
            rx.box(flex="1"),
            # Баланс пользователя
            rx.box(
                rx.icon("coins", size=11, color=ACCENT),
                rx.text(f"Баланс: {AuthState.tokens_left} токенов", font_size="11px",
                        font_weight="600", color=ACCENT),
                display="flex", align_items="center", gap="4px",
                padding="3px 9px",
                background="rgba(59,130,246,0.10)",
                border=f"1px solid rgba(59,130,246,0.22)",
                border_radius="8px",
            ),
            # Потраченные токены за генерацию
            rx.cond(
                FragmosState.tokens_label != "",
                rx.box(
                    rx.icon("coins", size=11, color=SUCCESS),
                    rx.text(FragmosState.tokens_label, font_size="11px",
                            font_weight="600", color=SUCCESS),
                    display="flex", align_items="center", gap="4px",
                    padding="3px 9px",
                    background="rgba(52,211,153,0.10)",
                    border=f"1px solid rgba(52,211,153,0.22)",
                    border_radius="8px",
                    margin_left="6px",
                ),
                rx.box(),
            ),
            display="flex", align_items="center", gap="6px",
            height="36px", padding="0 20px",
            background="rgba(255,255,255,0.02)",
            border_bottom=f"1px solid {BORDER}",
        ),
        # Draw.io area
        rx.box(
            rx.box(
                _drawio_embed(),
                background=PANEL,
                border_radius="16px",
                border=f"1px solid {BORDER}",
                box_shadow="0 8px 40px rgba(0,0,0,0.32)",
                width="100%", height="100%", overflow="hidden",
            ),
            flex="1", padding="20px",
            display="flex", flex_direction="column",
            overflow="hidden",
        ),
        flex="1", display="flex", flex_direction="column",
        height="100vh", overflow="hidden",
        padding_top="56px",
    )


# ─────────────────────────────────────────────────────────────────────────────
# CODE MODAL
# ─────────────────────────────────────────────────────────────────────────────

def code_modal() -> rx.Component:
    return rx.cond(
        FragmosState.show_code,
        rx.box(
            rx.box(
                rx.box(
                    # Header
                    rx.box(
                        _icon_box("code"),
                        rx.text("Исходный код", font_size="16px",
                                font_weight="600", color=TEXT),
                        rx.box(flex="1"),
                        rx.button(
                            rx.icon("x", size=16, color=MUTED),
                            width="32px", height="32px",
                            background="transparent", border="none",
                            border_radius="50%", cursor="pointer",
                            display="flex", align_items="center",
                            justify_content="center",
                            _hover={"background": PANEL_HVR},
                            on_click=FragmosState.on_close_modal,
                        ),
                        display="flex", align_items="center", gap="11px",
                        padding="18px 20px",
                        border_bottom=f"1px solid {BORDER}",
                        background="linear-gradient(180deg,rgba(255,255,255,0.03),transparent)",
                        border_radius="22px 22px 0 0",
                    ),
                    # Body
                    rx.box(
                        rx.box(
                            rx.el.pre(
                                FragmosState.last_submitted_code,
                                font_family=MONO, font_size="12px",
                                color=TEXT, white_space="pre-wrap",
                                word_break="break-all", margin="0",
                            ),
                            background=CODE_BG, border=f"1px solid {BORDER}",
                            border_radius="14px", padding="18px",
                        ),
                        padding="20px",
                        overflow_y="auto", max_height="52vh",
                        css=SCROLLBAR_CSS,
                    ),
                    # Footer
                    rx.box(
                        rx.button(
                            "Закрыть", font_size="13px", font_weight="500",
                            color=ACTIVE_TXT, background="transparent",
                            border="none", padding="7px 14px",
                            border_radius="10px", cursor="pointer",
                            _hover={"background": PANEL_HVR},
                            on_click=FragmosState.on_close_modal,
                        ),
                        padding="10px 18px",
                        border_top=f"1px solid {BORDER}",
                        background="rgba(255,255,255,0.02)",
                        border_radius="0 0 22px 22px",
                        display="flex", justify_content="flex-end",
                    ),
                    background="rgba(14,16,26,0.97)",
                    border_radius="22px", border=f"1px solid {BORDER}",
                    box_shadow="0 24px 80px rgba(0,0,0,0.65)",
                    width="100%", max_width="680px",
                    display="flex", flex_direction="column",
                    on_click=rx.stop_propagation,
                ),
                display="flex", align_items="center",
                justify_content="center", width="100%", height="100%",
                padding="24px",
            ),
            position="fixed", top="0", left="0",
            width="100vw", height="100vh", z_index="50",
            background="rgba(0,0,0,0.55)", backdrop_filter="blur(6px)",
            on_click=FragmosState.on_close_modal,
        ),
        rx.box(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# BUG REPORT MODAL
# ─────────────────────────────────────────────────────────────────────────────

def bug_modal() -> rx.Component:
    return rx.cond(
        FragmosState.bug_open,
        rx.box(
            rx.box(
                rx.box(
                    # Header
                    rx.box(
                        _icon_box("bug", color=DANGER,
                                  bg=DANGER_BG),
                        rx.box(
                            rx.text("Сообщить об ошибке", font_size="16px",
                                    font_weight="600", color=TEXT),
                            rx.text("Опишите что пошло не так",
                                    font_size="12px", color=MUTED, margin_top="2px"),
                        ),
                        rx.box(flex="1"),
                        rx.button(
                            rx.icon("x", size=16, color=MUTED),
                            width="32px", height="32px",
                            background="transparent", border="none",
                            border_radius="50%", cursor="pointer",
                            display="flex", align_items="center",
                            justify_content="center",
                            _hover={"background": PANEL_HVR},
                            on_click=FragmosState.on_close_bug,
                        ),
                        display="flex", align_items="center", gap="11px",
                        padding="18px 20px",
                        border_bottom=f"1px solid {BORDER}",
                        background="linear-gradient(180deg,rgba(255,255,255,0.03),transparent)",
                        border_radius="22px 22px 0 0",
                    ),
                    # Body
                    rx.cond(
                        FragmosState.bug_saved,
                        rx.box(
                            rx.icon("check-circle-2", size=36, color=SUCCESS),
                            rx.text("Отчёт отправлен", font_size="16px",
                                    font_weight="600", color=TEXT,
                                    margin_top="12px"),
                            display="flex", flex_direction="column",
                            align_items="center", justify_content="center",
                            padding="36px 24px",
                        ),
                        rx.box(
                            rx.text("Что пошло не так?", font_size="13px",
                                    font_weight="500", color=MUTED,
                                    margin_bottom="8px"),
                            rx.text_area(
                                value=FragmosState.bug_text,
                                on_change=FragmosState.set_bug_text,
                                placeholder="Опишите проблему подробно...",
                                min_height="140px",
                                padding="14px 16px",
                                background=PANEL,
                                border=f"1px solid {BORDER}",
                                border_radius="12px",
                                color=TEXT, font_size="13px",
                                line_height="1.6",
                                font_family=SANS, resize="none",
                                width="100%",
                                css={
                                    "::placeholder": {"color": MUTED2},
                                    "&:focus": {
                                        "outline": "none",
                                        "border_color": BORDER_BLUE,
                                    },
                                },
                            ),
                            padding="20px",
                        ),
                    ),
                    # Footer
                    rx.cond(
                        FragmosState.bug_saved,
                        rx.box(
                            rx.button(
                                "Закрыть", font_size="13px", font_weight="500",
                                color=ACTIVE_TXT, background="transparent",
                                border="none", padding="7px 14px",
                                border_radius="10px", cursor="pointer",
                                _hover={"background": PANEL_HVR},
                                on_click=FragmosState.on_close_bug,
                            ),
                            padding="10px 18px",
                            border_top=f"1px solid {BORDER}",
                            background="rgba(255,255,255,0.02)",
                            border_radius="0 0 22px 22px",
                            display="flex", justify_content="flex-end",
                        ),
                        rx.box(
                            rx.button(
                                "Отмена", font_size="13px", font_weight="500",
                                color=MUTED, background="transparent",
                                border=f"1px solid {BORDER}",
                                padding="8px 16px", border_radius="10px",
                                cursor="pointer",
                                _hover={"background": PANEL_HVR},
                                on_click=FragmosState.on_close_bug,
                            ),
                            rx.button(
                                rx.icon("send", size=13, color="white"),
                                rx.text("Отправить", font_size="13px",
                                        font_weight="600", color="white"),
                                display="flex", align_items="center", gap="6px",
                                padding="8px 16px",
                                background=DANGER, border="none",
                                border_radius="10px", cursor="pointer",
                                box_shadow=f"0 2px 10px {DANGER_BG}",
                                transition="all 0.15s",
                                _hover={"background": "#ef4444"},
                                _active={"transform": "scale(0.97)"},
                                on_click=FragmosState.on_save_bug,
                            ),
                            display="flex", align_items="center",
                            justify_content="flex-end", gap="8px",
                            padding="12px 20px",
                            border_top=f"1px solid {BORDER}",
                            background="rgba(255,255,255,0.02)",
                            border_radius="0 0 22px 22px",
                        ),
                    ),
                    background="rgba(14,16,26,0.97)",
                    border_radius="22px", border=f"1px solid {BORDER}",
                    box_shadow="0 24px 80px rgba(0,0,0,0.65)",
                    width="100%", max_width="500px",
                    display="flex", flex_direction="column",
                    on_click=rx.stop_propagation,
                ),
                display="flex", align_items="center",
                justify_content="center", width="100%", height="100%",
                padding="24px",
            ),
            position="fixed", top="0", left="0",
            width="100vw", height="100vh", z_index="60",
            background="rgba(0,0,0,0.55)", backdrop_filter="blur(6px)",
            on_click=FragmosState.on_close_bug,
        ),
        rx.box(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# SETTINGS MODAL
# ─────────────────────────────────────────────────────────────────────────────

def _row_shell(label: str, sub: str, icon_tag: str, control: rx.Component) -> rx.Component:
    return rx.box(
        rx.box(
            rx.box(
                rx.icon(icon_tag, size=13, color=ACCENT),
                width="28px", height="28px",
                background=ACCENT_GLOW, border_radius="8px",
                display="flex", align_items="center",
                justify_content="center", flex_shrink="0",
            ),
            rx.box(
                rx.text(label, font_size="13px", font_weight="500", color=TEXT),
                rx.text(sub, font_size="11px", color=MUTED, margin_top="1px"),
            ),
            display="flex", align_items="center", gap="9px", flex="1",
        ),
        control,
        display="flex", align_items="center", justify_content="space_between",
        padding="10px 14px", border_radius="12px",
        border=f"1px solid {BORDER}", background=PANEL,
        transition="all 0.15s",
        _hover={"border_color": BORDER_BLUE, "background": PANEL_HVR},
    )


def _cfg_bool(label: str, sub: str, icon_tag: str, value, on_change) -> rx.Component:
    return _row_shell(label, sub, icon_tag,
                      rx.switch(checked=value, on_change=on_change,
                                color_scheme="blue"))


def _cfg_int(label: str, sub: str, icon_tag: str, value, on_change,
             min_val: int = 0, max_val: int = 200) -> rx.Component:
    return _row_shell(label, sub, icon_tag,
                      rx.el.input(
                          type="number", value=value,
                          on_change=on_change,
                          min=min_val, max=max_val,
                          style={
                              "width": "72px", "padding": "5px 8px",
                              "background": CODE_BG, "color": TEXT,
                              "border": f"1px solid {BORDER}",
                              "border_radius": "8px", "font_size": "13px",
                              "font_family": MONO, "text_align": "center",
                              "outline": "none",
                          },
                      ))


def _section_label(text: str) -> rx.Component:
    return rx.text(
        text.upper(),
        font_size="10px", font_weight="700",
        color=MUTED2, letter_spacing="0.08em",
        padding="14px 2px 6px",
    )


def settings_modal() -> rx.Component:
    return rx.cond(
        FragmosState.settings_open,
        rx.box(
            rx.box(
                rx.box(
                    # Header
                    rx.box(
                        _icon_box("settings-2"),
                        rx.box(
                            rx.text("Настройки генерации", font_size="16px",
                                    font_weight="600", color=TEXT),
                            rx.text("Параметры блок-схемы",
                                    font_size="12px", color=MUTED, margin_top="2px"),
                        ),
                        rx.box(flex="1"),
                        rx.button(
                            rx.icon("x", size=16, color=MUTED),
                            width="32px", height="32px",
                            background="transparent", border="none",
                            border_radius="50%", cursor="pointer",
                            display="flex", align_items="center",
                            justify_content="center",
                            _hover={"background": PANEL_HVR},
                            on_click=FragmosState.on_close_settings,
                        ),
                        display="flex", align_items="center", gap="11px",
                        padding="18px 20px",
                        border_bottom=f"1px solid {BORDER}",
                        background="linear-gradient(180deg,rgba(255,255,255,0.03),transparent)",
                        border_radius="22px 22px 0 0",
                    ),
                    # Body
                    rx.box(
                        # ── ГЛАВНЫЕ ───────────────────────────────────────────
                        _section_label("Главные"),
                        _cfg_bool("Bounding boxes", "Подсветка областей IF/WHILE/FOR",
                                  "square-dashed",
                                  FragmosState.cfg_show_bbox,
                                  FragmosState.set_cfg_show_bbox),
                        _cfg_int("Вертикальный зазор", "Расстояние между блоками",
                                 "move-vertical",
                                 FragmosState.cfg_gap_y,
                                 FragmosState.set_cfg_gap_y),
                        _cfg_int("Зазор ветвей IF", "Расстояние от края ромба до ветки",
                                 "git-branch",
                                 FragmosState.cfg_if_branch_gap,
                                 FragmosState.set_cfg_if_branch_gap),
                        _cfg_int("Коридор WHILE", "Ширина коридора возврата",
                                 "repeat-2",
                                 FragmosState.cfg_while_corridor_base,
                                 FragmosState.set_cfg_while_corridor_base),

                        # ── IF ────────────────────────────────────────────────
                        _section_label("IF / Ветвление"),
                        _cfg_int("Верт. зазор IF", "Низ ромба → верх первого блока",
                                 "arrow-down-from-line",
                                 FragmosState.cfg_if_branch_vgap,
                                 FragmosState.set_cfg_if_branch_vgap),
                        _cfg_int("Мин. зазор bbox", "Минимум между bbox-ами веток",
                                 "between-horizontal-start",
                                 FragmosState.cfg_if_branch_min_gap,
                                 FragmosState.set_cfg_if_branch_min_gap),

                        # ── WHILE / FOR ───────────────────────────────────────
                        _section_label("WHILE / FOR"),
                        _cfg_int("Шаг коридора", "Уменьшение на каждый уровень",
                                 "layers",
                                 FragmosState.cfg_while_corridor_step,
                                 FragmosState.set_cfg_while_corridor_step),
                        _cfg_int("Мин. коридор", "Минимальная ширина",
                                 "minimize-2",
                                 FragmosState.cfg_while_corridor_min,
                                 FragmosState.set_cfg_while_corridor_min),
                        _cfg_int("Зазор поворота", "Низ блока → перемычка возврата",
                                 "corner-down-left",
                                 FragmosState.cfg_while_back_turn_gap,
                                 FragmosState.set_cfg_while_back_turn_gap),
                        _cfg_int("Верх. зазор возврата", "Линия коридора → верх ромба",
                                 "arrow-up-to-line",
                                 FragmosState.cfg_while_back_top_gap,
                                 FragmosState.set_cfg_while_back_top_gap),

                        display="flex", flex_direction="column", gap="6px",
                        padding="6px 20px 20px",
                        overflow_y="auto", max_height="60vh",
                        css=SCROLLBAR_CSS,
                    ),
                    # Footer
                    rx.box(
                        rx.button(
                            "Готово", font_size="13px", font_weight="600",
                            color="white", background=ACCENT, border="none",
                            padding="8px 22px", border_radius="10px",
                            cursor="pointer", transition="all 0.15s",
                            box_shadow="0 2px 8px rgba(59,130,246,0.28)",
                            _hover={"background": ACCENT_HVR},
                            _active={"transform": "scale(0.97)"},
                            on_click=FragmosState.on_close_settings,
                        ),
                        padding="12px 20px",
                        border_top=f"1px solid {BORDER}",
                        background="rgba(255,255,255,0.02)",
                        border_radius="0 0 22px 22px",
                        display="flex", justify_content="flex-end",
                    ),
                    background="rgba(14,16,26,0.97)",
                    border_radius="22px", border=f"1px solid {BORDER}",
                    box_shadow="0 24px 80px rgba(0,0,0,0.65)",
                    width="100%", max_width="500px",
                    display="flex", flex_direction="column",
                    on_click=rx.stop_propagation,
                ),
                display="flex", align_items="center",
                justify_content="center", width="100%", height="100%",
                padding="24px",
            ),
            position="fixed", top="0", left="0",
            width="100vw", height="100vh", z_index="60",
            background="rgba(0,0,0,0.55)", backdrop_filter="blur(6px)",
            on_click=FragmosState.on_close_settings,
        ),
        rx.box(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# DELETE CONFIRMATION  (Apple Action Sheet style)
# ─────────────────────────────────────────────────────────────────────────────

def delete_confirm() -> rx.Component:
    return rx.cond(
        FragmosState.delete_confirm_open,
        rx.box(
            # Sheet container (bottom-ish centered)
            rx.box(
                rx.box(
                    # Icon + message
                    rx.box(
                        rx.box(
                            rx.icon("triangle-alert", size=22, color=DANGER),
                            width="48px", height="48px",
                            background=DANGER_BG,
                            border_radius="50%",
                            display="flex", align_items="center",
                            justify_content="center",
                            margin_bottom="12px",
                        ),
                        rx.text("Удалить блок-схему?",
                                font_size="17px", font_weight="700", color=TEXT,
                                text_align="center"),
                        rx.text(
                            "Это действие необратимо. XML-файл схемы\nбудет удалён с диска.",
                            font_size="13px", color=MUTED,
                            text_align="center", line_height="1.55",
                            white_space="pre-line", margin_top="6px",
                        ),
                        display="flex", flex_direction="column",
                        align_items="center",
                        padding="24px 24px 20px",
                    ),
                    # Divider
                    rx.box(height="1px", background=BORDER, margin="0 16px"),
                    # Buttons
                    rx.box(
                        rx.button(
                            rx.icon("trash-2", size=15, color="white"),
                            rx.text("Удалить", font_size="15px",
                                    font_weight="600", color="white"),
                            display="flex", align_items="center",
                            justify_content="center", gap="8px",
                            width="100%", padding="13px",
                            background=DANGER, border="none",
                            border_radius="14px", cursor="pointer",
                            box_shadow=f"0 4px 16px {DANGER_BG}",
                            transition="all 0.15s",
                            _hover={"background": "#ef4444"},
                            _active={"transform": "scale(0.98)"},
                            on_click=FragmosState.on_confirm_delete,
                        ),
                        rx.button(
                            "Отмена", font_size="15px", font_weight="500",
                            color=TEXT,
                            width="100%", padding="13px",
                            background=PANEL, border=f"1px solid {BORDER}",
                            border_radius="14px", cursor="pointer",
                            transition="all 0.15s",
                            _hover={"background": PANEL_HVR},
                            _active={"transform": "scale(0.98)"},
                            on_click=FragmosState.on_cancel_delete,
                        ),
                        display="flex", flex_direction="column", gap="8px",
                        padding="16px 20px 20px",
                    ),
                    background="rgba(16,18,28,0.98)",
                    border_radius="22px",
                    border=f"1px solid {BORDER}",
                    box_shadow=(
                        "0 32px 80px rgba(0,0,0,0.70),"
                        "0 0 0 1px rgba(255,255,255,0.04)"
                    ),
                    width="100%", max_width="320px",
                    overflow="hidden",
                    on_click=rx.stop_propagation,
                ),
                display="flex", align_items="center",
                justify_content="center",
                width="100%", height="100%", padding="24px",
            ),
            position="fixed", top="0", left="0",
            width="100vw", height="100vh", z_index="70",
            background="rgba(0,0,0,0.60)",
            backdrop_filter="blur(8px)",
            on_click=FragmosState.on_cancel_delete,
        ),
        rx.box(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE
# ─────────────────────────────────────────────────────────────────────────────

def fragmos_page() -> rx.Component:
    return rx.box(
        # Inject animation keyframes globally
        rx.html(
            "<style>"
            "@keyframes fpulse{"
            "0%,80%,100%{transform:scale(0.5);opacity:0.25}"
            "40%{transform:scale(1);opacity:1}"
            "}"
            "@keyframes fspin{"
            "to{transform:rotate(360deg)}"
            "}"
            "@keyframes fspinr{"
            "to{transform:rotate(-360deg)}"
            "}"
            "@keyframes ffade{"
            "from{opacity:0;transform:translateY(4px)}"
            "to{opacity:1;transform:translateY(0)}"
            "}"
            "</style>"
        ),
        # Global nav bar
        _nav(),
        rx.cond(
            FragmosState.is_authenticated,
            rx.box(
                sidebar(),
                rx.cond(FragmosState.has_selected, diagram_viewer(), empty_state()),
                # Modals (portals)
                code_modal(),
                bug_modal(),
                settings_modal(),
                delete_confirm(),
                display="flex",
                flex="1",
                min_height="100vh",
            ),
            auth_required(),
        ),
        display="flex",
        min_height="100vh",
        min_width="1024px",
        background=BG,
        font_family=SANS,
        color=TEXT,
    )
