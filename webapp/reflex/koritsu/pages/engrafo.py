"""
engrafo.py — страница /engrafo: список отчётов + создание нового.
"""

import reflex as rx
from koritsu.components.header import header
from koritsu.state.engrafo_state import EngrafoState
from koritsu.theme import (
    BG, PANEL, HOVER, BORDER, ACCENT, ACCENT2, TEXT, MUTED,
    SUCCESS, WARNING, ERROR,
)

SANS = "-apple-system,BlinkMacSystemFont,'SF Pro Display','Segoe UI',system-ui,sans-serif"
MONO = "'SF Mono','Fira Code','Cascadia Code',monospace"


# ── Building blocks ────────────────────────────────────────────────────────────

def _badge(label: str, color: str) -> rx.Component:
    return rx.box(
        rx.text(label, font_size="11px", font_weight="600",
                font_family=SANS, color=color),
        padding="2px 8px",
        border_radius="6px",
        background=f"{color}22",
        border=f"1px solid {color}44",
    )


def _report_card(report: dict) -> rx.Component:
    title    = report["title"]
    tpl_name = report["template_name"]
    upd      = report["updated_at"]
    rid      = report["id"]

    date_str = rx.cond(
        upd != "",
        upd[:10],
        "—"
    )

    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.icon("file-text", size=16, color=ACCENT),
                    rx.text(title, font_size="15px", font_weight="600",
                            font_family=SANS, color=TEXT),
                    spacing="2", align="center",
                ),
                rx.hstack(
                    rx.text("Шаблон:", font_size="12px", color=MUTED, font_family=SANS),
                    rx.text(tpl_name, font_size="12px", color=TEXT, font_family=SANS),
                    rx.text("·", color=MUTED, font_size="12px"),
                    rx.text(date_str, font_size="12px", color=MUTED, font_family=SANS),
                    spacing="1", align="center",
                ),
                spacing="1", align="start",
            ),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    rx.hstack(
                        rx.icon("pencil", size=14),
                        rx.text("Открыть", font_size="13px", font_family=SANS),
                        spacing="1", align="center",
                    ),
                    on_click=EngrafoState.open_report(rid),
                    background=f"linear-gradient(135deg,{ACCENT},#2563eb)",
                    color="white",
                    border="none",
                    border_radius="8px",
                    padding="6px 14px",
                    cursor="pointer",
                    _hover={"opacity": "0.85"},
                ),
                rx.button(
                    rx.icon("trash-2", size=14, color=ERROR),
                    on_click=EngrafoState.delete_report(rid),
                    background="transparent",
                    border=f"1px solid {BORDER}",
                    border_radius="8px",
                    padding="6px 10px",
                    cursor="pointer",
                    _hover={"background": f"{ERROR}22", "border_color": ERROR},
                ),
                spacing="2",
            ),
            align="center",
            width="100%",
        ),
        background=PANEL,
        border=f"1px solid {BORDER}",
        border_radius="14px",
        padding="18px 20px",
        width="100%",
        transition="all 0.2s",
        _hover={"border_color": "rgba(255,255,255,0.20)", "background": HOVER},
    )


def _template_option(tpl: dict) -> rx.Component:
    return rx.select.item(tpl["name"], value=tpl["id"])


def _new_report_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon("file-plus", size=20, color=ACCENT),
                    rx.dialog.title(
                        "Новый отчёт",
                        font_size="17px", font_weight="700",
                        font_family=SANS, color=TEXT,
                    ),
                    spacing="2", align="center",
                ),
                rx.text("Выберите шаблон и введите название отчёта",
                        font_size="13px", color=MUTED, font_family=SANS),
                rx.vstack(
                    rx.text("Шаблон", font_size="12px", color=MUTED,
                            font_weight="500", font_family=SANS),
                    rx.cond(
                        EngrafoState.has_templates,
                        rx.select.root(
                            rx.select.trigger(
                                placeholder="Выберите шаблон...",
                                width="100%",
                                background=PANEL,
                                border=f"1px solid {BORDER}",
                                border_radius="10px",
                                color=TEXT,
                                font_family=SANS,
                                font_size="14px",
                                padding_x="12px",
                            ),
                            rx.select.content(
                                rx.foreach(
                                    EngrafoState.templates,
                                    _template_option,
                                ),
                                background="rgba(15,15,25,0.98)",
                                border=f"1px solid {BORDER}",
                                border_radius="10px",
                            ),
                            on_change=EngrafoState.set_selected_template_for_new,
                            value=EngrafoState.selected_template_id,
                        ),
                        rx.box(
                            rx.hstack(
                                rx.icon("alert-circle", size=14, color=WARNING),
                                rx.text("Нет доступных шаблонов",
                                        font_size="13px", color=MUTED, font_family=SANS),
                                spacing="2", align="center",
                            ),
                            padding="10px 14px",
                            border=f"1px solid {BORDER}",
                            border_radius="10px",
                        ),
                    ),
                    spacing="1", width="100%",
                ),
                rx.vstack(
                    rx.text("Название отчёта", font_size="12px", color=MUTED,
                            font_weight="500", font_family=SANS),
                    rx.input(
                        placeholder="Оставьте пустым для авто-названия",
                        value=EngrafoState.new_report_title,
                        on_change=EngrafoState.set_new_report_title,
                        background=PANEL,
                        border=f"1px solid {BORDER}",
                        border_radius="10px",
                        color=TEXT,
                        font_family=SANS,
                        font_size="14px",
                        _focus={"border_color": ACCENT, "outline": "none"},
                        width="100%",
                    ),
                    spacing="1", width="100%",
                ),
                rx.cond(
                    EngrafoState.error_msg != "",
                    rx.box(
                        rx.text(EngrafoState.error_msg, font_size="13px",
                                color=ERROR, font_family=SANS),
                        padding="8px 12px",
                        background=f"{ERROR}15",
                        border=f"1px solid {ERROR}44",
                        border_radius="8px",
                        width="100%",
                    ),
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            "Отмена",
                            on_click=EngrafoState.close_new_report_dialog,
                            background="transparent",
                            border=f"1px solid {BORDER}",
                            border_radius="10px",
                            color=TEXT,
                            font_family=SANS,
                            font_size="14px",
                            padding="8px 20px",
                            cursor="pointer",
                            _hover={"background": HOVER},
                        ),
                    ),
                    rx.button(
                        rx.hstack(
                            rx.icon("plus", size=16),
                            rx.text("Создать", font_size="14px", font_family=SANS),
                            spacing="1", align="center",
                        ),
                        on_click=EngrafoState.create_report,
                        background=f"linear-gradient(135deg,{ACCENT},#2563eb)",
                        color="white",
                        border="none",
                        border_radius="10px",
                        padding="8px 20px",
                        cursor="pointer",
                        _hover={"opacity": "0.85"},
                    ),
                    spacing="2", justify="end", width="100%",
                ),
                spacing="4", width="100%",
            ),
            background="rgba(10,10,20,0.97)",
            border=f"1px solid {BORDER}",
            border_radius="18px",
            padding="28px",
            max_width="480px",
            width="90vw",
            backdrop_filter="blur(20px)",
        ),
        open=EngrafoState.show_new_report_dialog,
    )


def _upload_dialog() -> rx.Component:
    file_selected = rx.selected_files("template_upload").length() > 0

    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # Header
                rx.hstack(
                    rx.icon("file-up", size=20, color=ACCENT),
                    rx.dialog.title(
                        "Загрузить шаблон",
                        font_size="17px", font_weight="700",
                        font_family=SANS, color=TEXT,
                        margin="0",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.icon("x", size=18, color=MUTED, cursor="pointer"),
                        on_click=EngrafoState.close_upload_dialog,
                    ),
                    align="center", width="100%",
                ),

                # Upload zone
                rx.upload(
                    rx.vstack(
                        rx.cond(
                            EngrafoState.loading,
                            # Идёт загрузка
                            rx.vstack(
                                rx.spinner(size="3", color=ACCENT),
                                rx.text("Загружаю файл...",
                                        font_size="14px", font_weight="600",
                                        color=ACCENT, font_family=SANS),
                                spacing="3", align="center",
                            ),
                            rx.cond(
                                file_selected,
                                # Файл выбран
                                rx.vstack(
                                    rx.box(
                                        rx.icon("file-check", size=36, color=ACCENT),
                                        padding="10px",
                                        background=f"rgba(59,130,246,0.12)",
                                        border_radius="50%",
                                    ),
                                    rx.text(
                                        rx.selected_files("template_upload")[0],
                                        font_size="13px", font_weight="600",
                                        color=ACCENT, font_family=SANS,
                                        text_align="center",
                                        max_width="320px",
                                        overflow="hidden",
                                        text_overflow="ellipsis",
                                        white_space="nowrap",
                                    ),
                                    rx.text("Готов к загрузке · нажмите для замены файла",
                                            font_size="11px", color=MUTED, font_family=SANS),
                                    spacing="2", align="center",
                                ),
                                # Файл не выбран
                                rx.vstack(
                                    rx.box(
                                        rx.icon("file-up", size=36, color=MUTED),
                                        padding="10px",
                                        background="rgba(255,255,255,0.04)",
                                        border_radius="50%",
                                        transition="all 0.2s",
                                    ),
                                    rx.text("Перетащите .docx файл сюда",
                                            font_size="14px", color=TEXT, font_family=SANS),
                                    rx.text("или нажмите для выбора",
                                            font_size="12px", color=MUTED, font_family=SANS),
                                    spacing="2", align="center",
                                ),
                            ),
                        ),
                        align="center", justify="center",
                        width="100%", min_height="140px",
                    ),
                    id="template_upload",
                    accept={".docx": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]},
                    border=rx.cond(
                        EngrafoState.loading,
                        f"2px solid {ACCENT}",
                        rx.cond(file_selected, f"2px dashed {ACCENT}", f"2px dashed {BORDER}"),
                    ),
                    border_radius="12px",
                    background=rx.cond(
                        EngrafoState.loading,
                        "rgba(59,130,246,0.08)",
                        rx.cond(file_selected, "rgba(59,130,246,0.07)", "transparent"),
                    ),
                    padding="24px",
                    width="100%",
                    cursor=rx.cond(EngrafoState.loading, "default", "pointer"),
                    transition="all 0.25s",
                    _hover=rx.cond(
                        EngrafoState.loading,
                        {},
                        {"border_color": ACCENT, "background": "rgba(59,130,246,0.07)"},
                    ),
                ),

                # Hint
                rx.text("Теги в шаблоне: {{имя_тега}}",
                        font_size="11px", color=MUTED, font_family=SANS),

                # Buttons
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            "Отмена",
                            on_click=EngrafoState.close_upload_dialog,
                            variant="outline",
                            color_scheme="gray",
                            font_family=SANS,
                            cursor="pointer",
                        ),
                    ),
                    rx.button(
                        rx.cond(
                            EngrafoState.loading,
                            rx.hstack(
                                rx.spinner(size="2"),
                                rx.text("Загружаю...", font_family=SANS),
                                spacing="2", align="center",
                            ),
                            rx.hstack(
                                rx.icon("upload", size=15),
                                rx.text("Загрузить", font_family=SANS),
                                spacing="2", align="center",
                            ),
                        ),
                        on_click=EngrafoState.upload_template(rx.upload_files("template_upload")),  # type: ignore
                        background=rx.cond(file_selected,
                                           f"linear-gradient(135deg,{ACCENT},#2563eb)",
                                           "rgba(255,255,255,0.1)"),
                        color="white",
                        border="none",
                        cursor="pointer",
                        disabled=EngrafoState.loading,
                    ),
                    spacing="2", justify="end", width="100%",
                ),
                spacing="4", width="100%",
            ),
            background="rgba(10,10,20,0.97)",
            border=f"1px solid {BORDER}",
            border_radius="18px",
            padding="24px",
            max_width="460px",
            width="90vw",
            backdrop_filter="blur(20px)",
        ),
        open=EngrafoState.show_upload_dialog,
    )


# ── Main page ──────────────────────────────────────────────────────────────────

def engrafo_page() -> rx.Component:
    return rx.box(
        header(),
        _new_report_dialog(),
        _upload_dialog(),

        # ── Content ──
        rx.box(
            rx.vstack(

                # Title row
                rx.hstack(
                    rx.vstack(
                        rx.hstack(
                            rx.box(
                                rx.icon("file-text", size=20, color=ACCENT),
                                width="38px", height="38px",
                                background=ACCENT2,
                                border=f"1px solid {ACCENT}44",
                                border_radius="12px",
                                display="flex",
                                align_items="center",
                                justify_content="center",
                            ),
                            rx.vstack(
                                rx.text("Engrafo", font_size="22px", font_weight="700",
                                        font_family=SANS, color=TEXT, line_height="1"),
                                rx.text("Генератор отчётов из docx-шаблонов",
                                        font_size="13px", color=MUTED, font_family=SANS),
                                spacing="0", align="start",
                            ),
                            spacing="3", align="center",
                        ),
                        spacing="1", align="start",
                    ),
                    rx.spacer(),
                    rx.hstack(
                        rx.button(
                            rx.hstack(
                                rx.icon("upload", size=15),
                                rx.text("Загрузить шаблон", font_size="13px",
                                        font_family=SANS, font_weight="500"),
                                spacing="1", align="center",
                            ),
                            on_click=EngrafoState.open_upload_dialog,
                            background="transparent",
                            border=f"1px solid {BORDER}",
                            border_radius="10px",
                            color=TEXT,
                            padding="8px 16px",
                            cursor="pointer",
                            _hover={"background": HOVER},
                        ),
                        rx.button(
                            rx.hstack(
                                rx.icon("plus", size=15),
                                rx.text("Новый отчёт", font_size="13px",
                                        font_family=SANS, font_weight="600"),
                                spacing="1", align="center",
                            ),
                            on_click=EngrafoState.open_new_report_dialog,
                            background=f"linear-gradient(135deg,{ACCENT},#2563eb)",
                            color="white",
                            border="none",
                            border_radius="10px",
                            padding="8px 18px",
                            cursor="pointer",
                            _hover={"opacity": "0.85"},
                        ),
                        spacing="2",
                    ),
                    align="center",
                    width="100%",
                ),

                # Success/error banner
                rx.cond(
                    EngrafoState.success_msg != "",
                    rx.box(
                        rx.hstack(
                            rx.icon("check-circle", size=16, color=SUCCESS),
                            rx.text(EngrafoState.success_msg,
                                    font_size="13px", color=SUCCESS, font_family=SANS),
                            spacing="2", align="center",
                        ),
                        padding="10px 16px",
                        background=f"{SUCCESS}15",
                        border=f"1px solid {SUCCESS}44",
                        border_radius="10px",
                        width="100%",
                        on_click=EngrafoState.clear_messages,
                        cursor="pointer",
                    ),
                ),

                # Reports list
                rx.cond(
                    EngrafoState.has_reports,
                    rx.vstack(
                        rx.text(
                            f"Отчёты",
                            font_size="13px", color=MUTED, font_weight="500",
                            font_family=SANS, letter_spacing="0.5px",
                            text_transform="uppercase",
                        ),
                        rx.vstack(
                            rx.foreach(EngrafoState.reports, _report_card),
                            spacing="2", width="100%",
                        ),
                        spacing="3", width="100%", align="start",
                    ),
                    # Empty state
                    rx.box(
                        rx.vstack(
                            rx.icon("inbox", size=48, color=MUTED),
                            rx.text("Нет отчётов", font_size="18px", font_weight="600",
                                    font_family=SANS, color=TEXT),
                            rx.text("Создайте первый отчёт, нажав кнопку выше",
                                    font_size="14px", color=MUTED, font_family=SANS),
                            rx.button(
                                rx.hstack(
                                    rx.icon("plus", size=16),
                                    rx.text("Новый отчёт", font_family=SANS),
                                    spacing="1", align="center",
                                ),
                                on_click=EngrafoState.open_new_report_dialog,
                                background=f"linear-gradient(135deg,{ACCENT},#2563eb)",
                                color="white",
                                border="none",
                                border_radius="10px",
                                padding="10px 24px",
                                cursor="pointer",
                                margin_top="8px",
                                _hover={"opacity": "0.85"},
                            ),
                            spacing="3", align="center",
                        ),
                        padding="64px 32px",
                        background=PANEL,
                        border=f"1px solid {BORDER}",
                        border_radius="16px",
                        width="100%",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                    ),
                ),

                spacing="5",
                width="100%",
                max_width="860px",
                align="start",
            ),
            padding_top="88px",
            padding_x="32px",
            padding_bottom="48px",
            width="100%",
            display="flex",
            justify_content="center",
        ),

        background=BG,
        min_height="100vh",
    )
