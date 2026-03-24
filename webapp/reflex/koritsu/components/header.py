"""
Shared header/navbar component used across all pages.
"""

import reflex as rx
from koritsu.state.auth_state import AuthState

# ── Palette (same as theme.py) ───────────────────────────────────────────────
BG_HEADER = "rgba(8,8,15,0.75)"
PANEL = "rgba(255,255,255,0.05)"
HOVER = "rgba(255,255,255,0.09)"
BORDER = "rgba(255,255,255,0.10)"
ACCENT = "#3b82f6"
ACCENT2 = "rgba(59,130,246,0.18)"
ACCENT_GLOW = "rgba(59,130,246,0.30)"
TEXT = "rgba(255,255,255,0.92)"
MUTED = "rgba(255,255,255,0.40)"
DANGER = "#f87171"
SANS = "-apple-system,BlinkMacSystemFont,'SF Pro Display','Segoe UI',system-ui,sans-serif"


# ── Building blocks ─────────────────────────────────────────────────────────

def nav_link(label: str, href: str) -> rx.Component:
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


def auth_nav_buttons() -> rx.Component:
    return rx.hstack(
        rx.link(
            rx.box(
                rx.text("Войти", color=TEXT, font_size="13px",
                        font_family=SANS, font_weight="500"),
                background=PANEL,
                border=f"1px solid {BORDER}",
                padding="7px 18px",
                border_radius="10px",
                cursor="pointer",
                transition="all 0.2s",
                _hover={"background": HOVER, "border_color": "rgba(255,255,255,0.20)"},
            ),
            href="/?auth=login",
            text_decoration="none",
        ),
        rx.link(
            rx.box(
                rx.text("Регистрация", color="white", font_size="13px",
                        font_family=SANS, font_weight="600"),
                background=f"linear-gradient(135deg,{ACCENT},#2563eb)",
                border="none",
                padding="7px 18px",
                border_radius="10px",
                box_shadow=f"0 2px 12px {ACCENT_GLOW}",
                cursor="pointer",
                transition="all 0.2s",
                _hover={"opacity": "0.9"},
            ),
            href="/?auth=register",
            text_decoration="none",
        ),
        spacing="2",
    )


def user_avatar(size: str = "34px", font_size: str = "13px") -> rx.Component:
    return rx.box(
        rx.cond(
            AuthState.user_icon != "",
            rx.el.img(
                src=AuthState.user_icon,
                alt="Avatar",
                width="100%",
                height="100%",
                object_fit="cover",
                border_radius="50%",
            ),
            rx.text(
                AuthState.user_initial,
                color="white",
                font_size=font_size,
                font_weight="700",
                font_family=SANS,
            ),
        ),
        width=size,
        height=size,
        min_width=size,
        background=rx.cond(
            AuthState.user_icon != "",
            "transparent",
            f"linear-gradient(135deg,{ACCENT},#2563eb)",
        ),
        border_radius="50%",
        overflow="hidden",
        display="flex",
        align_items="center",
        justify_content="center",
        border="2px solid rgba(255,255,255,0.15)",
        flex_shrink="0",
    )


def user_menu() -> rx.Component:
    return rx.menu.root(
        rx.menu.trigger(
            rx.hstack(
                user_avatar(),
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
                rx.link(
                    rx.hstack(
                        rx.icon("settings", size=14, color=MUTED),
                        rx.text("Настройки", font_family=SANS, font_size="13px"),
                        spacing="2", align="center",
                    ),
                    href="/profile",
                    text_decoration="none",
                    color="inherit",
                    display="flex",
                    width="100%",
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


# ── Main header component ───────────────────────────────────────────────────

def header(show_nav_links: bool = True) -> rx.Component:
    """
    Shared header for all pages.
    show_nav_links: whether to show Fragmos/Engrafo links in the center.
    """
    center_links = (
        rx.hstack(
            nav_link("Fragmos", "/fragmos"),
            nav_link("Engrafo", "/engrafo"),
            spacing="2",
        )
        if show_nav_links
        else rx.fragment()
    )

    return rx.box(
        rx.hstack(
            # Logo
            rx.link(
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
                href="/",
                text_decoration="none",
            ),
            rx.spacer(),
            center_links,
            rx.spacer(),
            # Right side: auth buttons or user menu
            rx.cond(
                AuthState.is_logged_in,
                user_menu(),
                auth_nav_buttons(),
            ),
            align="center",
            width="100%",
        ),
        position="fixed",
        top="0", left="0", right="0",
        z_index="100",
        background=BG_HEADER,
        backdrop_filter="blur(20px) saturate(180%)",
        border_bottom=f"1px solid {BORDER}",
        padding_x="32px",
        height="56px",
        display="flex",
        align_items="center",
    )
