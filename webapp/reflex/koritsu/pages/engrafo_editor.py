"""
engrafo_editor.py — страница /engrafo/editor: редактор отчёта.

Layout:
  [Header]
  ┌─────────────┬──────────────────────────┬─┬──────────────────┐
  │ Sidebar     │  Теги (CodeMirror 6)     │║│  PDF Preview     │
  │ 260px fixed │  flex-grow               │║│  resizable       │
  └─────────────┴──────────────────────────┴─┴──────────────────┘

CodeMirror 6 — через CDN (assets/engrafo_editor.js)
Resize  — drag divider между Tags и Preview
Images  — кнопка выбора файла → base64 в значение тега
"""

import reflex as rx
from koritsu.components.header import header
from koritsu.state.engrafo_state import EngrafoState
from koritsu.theme import (
    E_BG as C_BG, E_CARD as C_CARD, E_CARD2 as C_CARD2,
    E_BORDER as C_BORDER, E_GREEN as C_GREEN, E_PURPLE as C_PURPLE,
    E_PURPLE_DARK as C_PURPLE_DARK, E_CYAN as C_CYAN, E_TEXT as C_TEXT,
    E_MUTED as C_MUTED, E_MUTED2 as C_MUTED2, E_ERROR as C_ERROR,
    E_DIALOG as C_DIALOG,
)

SANS = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif"
MONO = "'SF Mono','Fira Code','Cascadia Code',monospace"
# Layout widths now controlled via CSS classes (engrafo.css) for responsiveness


# ── Helpers ────────────────────────────────────────────────────────────────

def _label(text: str, icon_name: str, color: str = C_CYAN) -> rx.Component:
    return rx.hstack(
        rx.icon(icon_name, size=11, color=color),
        rx.text(
            text,
            font_size="10px", font_weight="700",
            font_family=SANS, color=C_MUTED,
            letter_spacing="1.2px", text_transform="uppercase",
        ),
        spacing="1", align="center",
    )


def _card(*children, **props) -> rx.Component:
    d = dict(
        background=C_CARD,
        border=f"1px solid {C_BORDER}",
        border_radius="16px",
    )
    d.update(props)
    return rx.box(*children, **d)


def _badge(icon_name: str, color: str, bg: str) -> rx.Component:
    return rx.box(
        rx.icon(icon_name, size=14, color=color),
        background=bg, border_radius="10px",
        padding="7px", display="flex", align_items="center", flex_shrink="0",
    )


# ── Tag field ──────────────────────────────────────────────────────────────

def _tag_chip(entry: dict) -> rx.Component:
    """Chip-кнопка для выбора тега."""
    is_selected = EngrafoState.selected_tags.contains(entry["key"])
    has_value = entry["value"] != ""

    return rx.box(
        rx.hstack(
            # Индикатор заполнения
            rx.box(
                width="5px", height="5px",
                border_radius="50%",
                background=rx.cond(has_value, C_GREEN, "rgba(255,255,255,0.12)"),
                flex_shrink="0",
            ),
            rx.text(
                entry["label"],
                font_size="11px", font_weight="500",
                color=rx.cond(is_selected, C_TEXT, C_MUTED),
                font_family=SANS,
                white_space="nowrap",
            ),
            spacing="1", align="center",
        ),
        on_click=EngrafoState.toggle_tag_selection(entry["key"]),
        background=rx.cond(
            is_selected,
            "rgba(34,242,239,0.10)",
            "transparent",
        ),
        border=rx.cond(
            is_selected,
            "1px solid rgba(34,242,239,0.25)",
            "1px solid rgba(255,255,255,0.06)",
        ),
        border_radius="8px",
        padding="4px 10px",
        cursor="pointer",
        transition="all 0.15s ease",
        _hover={"background": "rgba(34,242,239,0.06)", "border_color": "rgba(34,242,239,0.18)"},
        flex_shrink="0",
    )



def _tag_toolbar() -> rx.Component:
    """Toolbar placeholder — future: rich-text formatting buttons."""
    return rx.el.div(
        # Bold
        rx.el.button("B", class_name="tag-toolbar-btn",
                      title="Жирный (скоро)",
                      disabled=True,
                      style={"font_weight": "800", "opacity": "0.35", "cursor": "not-allowed"}),
        # Italic
        rx.el.button("I", class_name="tag-toolbar-btn",
                      title="Курсив (скоро)",
                      disabled=True,
                      style={"font_style": "italic", "opacity": "0.35", "cursor": "not-allowed"}),
        # Underline
        rx.el.button("U", class_name="tag-toolbar-btn",
                      title="Подчёркнутый (скоро)",
                      disabled=True,
                      style={"text_decoration": "underline", "opacity": "0.35", "cursor": "not-allowed"}),
        # Separator
        rx.el.div(class_name="tag-toolbar-sep"),
        # Font picker placeholder
        rx.el.button("A", class_name="tag-toolbar-btn",
                      title="Шрифт (скоро)",
                      disabled=True,
                      style={"font_size": "14px", "opacity": "0.35", "cursor": "not-allowed"}),
        # Separator
        rx.el.div(class_name="tag-toolbar-sep"),
        # Image button (functional)
        class_name="tag-toolbar",
    )


# ── Context file upload dialog ─────────────────────────────────────────────

def _context_upload_dialog() -> rx.Component:
    """Диалог загрузки файлов контекста (PDF, PNG, ZIP и др.)."""
    file_selected = rx.selected_files("context_upload").length() > 0

    def _file_row(f: dict) -> rx.Component:
        return rx.hstack(
            rx.box(
                rx.text(
                    f["ext"].upper().replace(".", ""),
                    font_size="9px", font_weight="700",
                    color=C_CYAN, font_family=SANS,
                ),
                background="rgba(34,242,239,0.10)",
                border="1px solid rgba(34,242,239,0.20)",
                border_radius="5px", padding="2px 5px",
                flex_shrink="0",
            ),
            rx.text(f["name"], font_size="12px", color=C_TEXT,
                    font_family=SANS, flex="1", no_of_lines=1),
            rx.text(f["size"], font_size="11px", color=C_MUTED2,
                    font_family=SANS, flex_shrink="0"),
            rx.box(
                rx.icon("x", size=11, color=C_ERROR),
                on_click=EngrafoState.delete_context_file(f["name"]),
                cursor="pointer", border_radius="5px", padding="3px",
                _hover={"background": "rgba(255,77,106,0.12)"},
                display="flex", align_items="center", flex_shrink="0",
            ),
            spacing="2", align="center", width="100%",
            padding="6px 10px",
            background="rgba(255,255,255,0.03)",
            border=f"1px solid {C_BORDER}",
            border_radius="8px",
        )

    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # Header
                rx.hstack(
                    rx.box(
                        rx.icon("folder-open", size=18, color=C_CYAN),
                        background="rgba(34,242,239,0.10)",
                        border_radius="10px", padding="8px",
                        display="flex", align_items="center",
                    ),
                    rx.vstack(
                        rx.dialog.title(
                            "Файлы контекста",
                            font_size="16px", font_weight="700",
                            font_family=SANS, color=C_TEXT, margin="0",
                        ),
                        rx.text("PDF, PNG, ZIP, DOCX — источники для заполнения тегов",
                                font_size="11px", color=C_MUTED, font_family=SANS),
                        spacing="0", align="start",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.icon("x", size=16, color=C_MUTED, cursor="pointer"),
                        on_click=EngrafoState.close_context_upload,
                    ),
                    spacing="3", align="center", width="100%",
                ),

                # Upload zone
                rx.upload(
                    rx.vstack(
                        rx.cond(
                            EngrafoState.loading,
                            rx.vstack(
                                rx.spinner(size="3", color=C_CYAN),
                                rx.text("Загружаю...", font_size="13px",
                                        color=C_CYAN, font_family=SANS),
                                spacing="3", align="center",
                            ),
                            rx.cond(
                                file_selected,
                                rx.vstack(
                                    rx.icon("file-check", size=32, color=C_CYAN),
                                    rx.text(rx.selected_files("context_upload")[0],
                                            font_size="12px", color=C_CYAN,
                                            font_family=SANS, text_align="center",
                                            max_width="300px", no_of_lines=1),
                                    rx.text("Можно добавить ещё файлы",
                                            font_size="10px", color=C_MUTED2, font_family=SANS),
                                    spacing="2", align="center",
                                ),
                                rx.vstack(
                                    rx.icon("upload-cloud", size=36, color=C_MUTED2),
                                    rx.text("Перетащите файлы или нажмите",
                                            font_size="13px", color=C_MUTED, font_family=SANS),
                                    rx.text("PDF · PNG · JPG · ZIP · DOCX · TXT  (макс. 20 MB)",
                                            font_size="11px", color=C_MUTED2, font_family=SANS),
                                    spacing="2", align="center",
                                ),
                            ),
                        ),
                        align="center", justify="center",
                        width="100%", min_height="120px",
                    ),
                    id="context_upload",
                    accept={
                        ".pdf":  ["application/pdf"],
                        ".png":  ["image/png"],
                        ".jpg":  ["image/jpeg"],
                        ".jpeg": ["image/jpeg"],
                        ".webp": ["image/webp"],
                        ".zip":  ["application/zip"],
                        ".docx": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
                        ".txt":  ["text/plain"],
                    },
                    multiple=True,
                    border=rx.cond(
                        file_selected,
                        f"2px dashed {C_CYAN}",
                        f"2px dashed {C_BORDER}",
                    ),
                    border_radius="12px",
                    background=rx.cond(
                        file_selected, "rgba(34,242,239,0.05)", "transparent",
                    ),
                    padding="20px", width="100%",
                    cursor=rx.cond(EngrafoState.loading, "default", "pointer"),
                    transition="all 0.2s",
                    _hover=rx.cond(
                        EngrafoState.loading, {},
                        {"border_color": C_CYAN, "background": "rgba(34,242,239,0.05)"},
                    ),
                ),

                # Existing files
                rx.cond(
                    EngrafoState.context_files.length() > 0,
                    rx.vstack(
                        rx.text("Загруженные файлы", font_size="10px",
                                font_weight="600", color=C_MUTED,
                                font_family=SANS, letter_spacing="0.8px",
                                text_transform="uppercase"),
                        rx.vstack(
                            rx.foreach(EngrafoState.context_files, _file_row),
                            spacing="1", width="100%",
                        ),
                        spacing="2", width="100%",
                    ),
                ),

                # Error banner
                rx.cond(
                    EngrafoState.error_msg != "",
                    rx.box(
                        rx.text(EngrafoState.error_msg, font_size="12px",
                                color=C_ERROR, font_family=SANS),
                        padding="8px 12px",
                        background="rgba(255,77,106,0.10)",
                        border="1px solid rgba(255,77,106,0.25)",
                        border_radius="8px", width="100%",
                    ),
                ),

                # Buttons
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            "Закрыть",
                            on_click=EngrafoState.close_context_upload,
                            background="transparent",
                            border=f"1px solid {C_BORDER}",
                            border_radius="10px", color=C_MUTED,
                            font_family=SANS, padding="7px 18px",
                            cursor="pointer",
                            _hover={"background": "rgba(255,255,255,0.06)"},
                        ),
                    ),
                    rx.button(
                        rx.cond(
                            EngrafoState.loading,
                            rx.hstack(rx.spinner(size="2"),
                                      rx.text("Загружаю...", font_family=SANS),
                                      spacing="2", align="center"),
                            rx.hstack(rx.icon("upload", size=14),
                                      rx.text("Загрузить", font_family=SANS),
                                      spacing="2", align="center"),
                        ),
                        on_click=EngrafoState.upload_context_files(
                            rx.upload_files(upload_id="context_upload")  # type: ignore
                        ),
                        background=rx.cond(
                            file_selected,
                            f"linear-gradient(135deg, {C_CYAN}, #0FA3A0)",
                            "rgba(255,255,255,0.07)",
                        ),
                        color=rx.cond(file_selected, "#040A0A", C_MUTED),
                        border="none", border_radius="10px",
                        font_family=SANS, font_weight="600",
                        padding="7px 20px", cursor="pointer",
                        disabled=EngrafoState.loading | ~file_selected,
                        _hover=rx.cond(file_selected, {"opacity": "0.88"}, {}),
                    ),
                    spacing="2", justify="end", width="100%",
                ),

                spacing="4", width="100%",
            ),
            background=C_CARD,
            border=f"1px solid {C_BORDER}",
            border_radius="20px",
            padding="24px",
            max_width="500px",
            width="92vw",
            backdrop_filter="blur(20px)",
        ),
        open=EngrafoState.show_context_upload,
    )


def _tag_field(entry: dict) -> rx.Component:
    """
    Tag editor — native textarea для текста + миниатюра картинки.
    Textarea нативная (rx.el.textarea) — on_blur для сохранения.
    Ctrl+V картинка через JS proxy.
    """
    has_value = entry["value"] != ""
    has_image = entry["image_src"] != ""

    return rx.el.div(
        # ── Label row ─────────────────────────────────────────
        rx.hstack(
            rx.box(
                width="3px", height="14px",
                border_radius="2px",
                background=rx.cond(has_value, C_GREEN, "rgba(255,255,255,0.08)"),
                flex_shrink="0",
                transition="background 0.3s ease",
            ),
            rx.text(
                entry["label"],
                font_size="12.5px", font_weight="600",
                color=rx.cond(has_value, "rgba(232,234,240,0.85)", "rgba(232,234,240,0.40)"),
                font_family=SANS,
                letter_spacing="0.2px",
                flex="1",
                transition="color 0.25s ease",
            ),
            rx.box(
                rx.icon("image-plus", size=14, color="rgba(201,35,248,0.55)"),
                on_click=EngrafoState.open_image_picker(entry["key"]),
                border_radius="8px", padding="5px",
                cursor="pointer",
                _hover={"background": "rgba(201,35,248,0.10)"},
                transition="all 0.2s ease",
                display="flex", align_items="center",
                flex_shrink="0",
                title="Вставить изображение (или Ctrl+V)",
            ),
            rx.box(
                rx.icon("maximize-2", size=13, color="rgba(232,234,240,0.30)"),
                on_click=EngrafoState.open_expand_editor(entry["key"]),
                border_radius="8px", padding="5px",
                cursor="pointer",
                _hover={"background": "rgba(255,255,255,0.06)"},
                transition="all 0.2s ease",
                display="flex", align_items="center",
                flex_shrink="0",
            ),
            spacing="2", align="center", width="100%",
            padding="12px 14px 0",
        ),
        _tag_toolbar(),
        # ── Textarea (нативная, uncontrolled, on_blur сохраняет) ──
        rx.el.textarea(
            default_value=entry["text"],
            placeholder=entry["label"],
            class_name="tag-textarea",
            on_blur=EngrafoState.set_tag_text(entry["key"]),
            data_tag_key=entry["key"],
        ),
        # ── Миниатюра картинки (если есть) ──────────────────────
        rx.cond(
            has_image,
            rx.box(
                rx.el.img(
                    src=entry["image_src"],
                    style={"max_width": "100%", "max_height": "120px",
                           "border_radius": "8px", "display": "block", "margin": "0 auto"},
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.box(
                        rx.icon("x", size=11, color=C_ERROR),
                        rx.text("Удалить фото", font_size="10px",
                                color=C_ERROR, font_family=SANS),
                        on_click=EngrafoState.clear_tag_image(entry["key"]),
                        display="flex", align_items="center", gap="4px",
                        cursor="pointer", padding="4px 8px", border_radius="6px",
                        _hover={"background": "rgba(255,77,106,0.10)"},
                    ),
                    padding="4px 10px", width="100%",
                ),
                padding="4px 14px 8px",
                border_top="1px solid rgba(255,255,255,0.05)",
            ),
        ),
        # ── Counter row ──────────────────────────────────────────
        rx.hstack(
            rx.spacer(),
            rx.cond(
                has_image,
                rx.text(
                    "+ фото",
                    font_size="10px",
                    color="rgba(201,35,248,0.65)",
                    font_family=SANS,
                    margin_right="6px",
                ),
            ),
            rx.text(
                entry["text"].length(),
                font_size="10px", font_family=SANS,
                color=rx.cond(entry["text"].length() > 480, C_ERROR, C_MUTED2),
            ),
            padding="0 14px 6px", width="100%",
        ),
        class_name="tag-field-apple",
        style={"width": "100%"},
    )


# ── Sidebar sections ───────────────────────────────────────────────────────

def _sidebar_template() -> rx.Component:
    return rx.vstack(
        _label("Шаблон", "layout-template", C_PURPLE),
        rx.cond(
            EngrafoState.has_templates,
            rx.select.root(
                rx.select.trigger(
                    placeholder="Выберите шаблон...",
                    width="100%",
                    background="rgba(255,255,255,0.04)",
                    border=f"1px solid {C_BORDER}",
                    border_radius="10px",
                    color=C_TEXT, font_family=SANS,
                    font_size="13px", height="40px",
                    cursor="pointer",
                    _hover={"border_color": "rgba(201,35,248,0.40)"},
                ),
                rx.select.content(
                    rx.foreach(
                        EngrafoState.templates,
                        lambda t: rx.select.item(t["name"], value=t["id"]),
                    ),
                    background=C_CARD,
                    border=f"1px solid {C_BORDER}",
                    border_radius="12px",
                ),
                on_change=EngrafoState.select_template,
                value=EngrafoState.selected_template_id,
                width="100%",
            ),
            rx.text("Нет шаблонов", font_size="12px", color=C_MUTED2, font_family=SANS),
        ),
        spacing="2", width="100%",
    )


def _profile_item(profile: dict) -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.box(
                rx.icon("bookmark", size=10, color=C_PURPLE),
                background="rgba(201,35,248,0.10)",
                border_radius="5px", padding="4px",
                display="flex", align_items="center",
            ),
            rx.text(profile["name"], font_size="12px", color=C_TEXT,
                    font_family=SANS, no_of_lines=1, flex="1"),
            spacing="2", align="center", flex="1",
        ),
        rx.hstack(
            rx.button(
                rx.icon("download", size=10),
                on_click=EngrafoState.load_profile(profile["id"]),
                background="rgba(201,35,248,0.10)",
                border="1px solid rgba(201,35,248,0.20)",
                border_radius="6px", padding="3px 7px",
                cursor="pointer", color=C_PURPLE,
                title="Загрузить",
                _hover={"background": "rgba(201,35,248,0.22)"},
            ),
            rx.button(
                rx.icon("trash-2", size=10, color=C_ERROR),
                on_click=EngrafoState.confirm_delete_profile(profile["id"]),
                background="transparent",
                border=f"1px solid {C_BORDER}",
                border_radius="6px", padding="3px 7px",
                cursor="pointer",
                _hover={"background": "rgba(255,77,106,0.10)", "border_color": C_ERROR},
            ),
            spacing="1",
        ),
        align="center", width="100%",
    )


def _save_profile_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title(
                    "Сохранить профиль",
                    font_size="16px", font_weight="700",
                    font_family=SANS, color=C_TEXT,
                ),
                rx.input(
                    placeholder="Название профиля",
                    value=EngrafoState.new_profile_name,
                    on_change=EngrafoState.set_new_profile_name,
                    background="rgba(255,255,255,0.05)",
                    border=f"1px solid {C_BORDER}",
                    border_radius="10px",
                    color=C_TEXT, font_family=SANS,
                    _focus={
                        "border_color": C_PURPLE,
                        "outline": "none",
                        "box_shadow": "0 0 0 2px rgba(201,35,248,0.20)",
                    },
                    width="100%",
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            "Отмена",
                            on_click=EngrafoState.close_save_profile_dialog,
                            background="transparent",
                            border=f"1px solid {C_BORDER}",
                            border_radius="10px", color=C_MUTED,
                            font_family=SANS, padding="7px 18px",
                            cursor="pointer",
                            _hover={"background": "rgba(255,255,255,0.06)"},
                        ),
                    ),
                    rx.button(
                        "Сохранить",
                        on_click=EngrafoState.save_profile,
                        background=f"linear-gradient(135deg, {C_PURPLE}, {C_PURPLE_DARK})",
                        color="white", border="none",
                        border_radius="10px", font_family=SANS,
                        font_weight="600", padding="7px 18px",
                        cursor="pointer",
                        _hover={"opacity": "0.85"},
                    ),
                    spacing="2", justify="end", width="100%",
                ),
                spacing="3", width="100%",
            ),
            background=C_DIALOG,
            border=f"1px solid {C_BORDER}",
            border_radius="20px", padding="24px",
            max_width="360px",
            backdrop_filter="blur(20px)",
        ),
        open=EngrafoState.show_save_profile_dialog,
    )


def _delete_profile_confirm_dialog() -> rx.Component:
    """Диалог подтверждения удаления профиля."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon("triangle-alert", size=20, color=C_ERROR),
                    rx.dialog.title(
                        "Удалить профиль?",
                        font_size="16px", font_weight="700",
                        font_family=SANS, color=C_TEXT,
                    ),
                    spacing="2", align="center",
                ),
                rx.text(
                    "Удалить профиль? Это действие необратимо.",
                    font_size="13px", color=C_MUTED, font_family=SANS,
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            "Отмена",
                            on_click=EngrafoState.cancel_delete_profile,
                            background="transparent",
                            border=f"1px solid {C_BORDER}",
                            border_radius="10px", color=C_MUTED,
                            font_family=SANS, padding="7px 18px",
                            cursor="pointer",
                            _hover={"background": "rgba(255,255,255,0.06)"},
                        ),
                    ),
                    rx.button(
                        rx.hstack(
                            rx.icon("trash-2", size=14),
                            rx.text("Удалить", font_size="14px", font_family=SANS),
                            spacing="1", align="center",
                        ),
                        on_click=EngrafoState.do_delete_profile,
                        background=C_ERROR,
                        color="white", border="none",
                        border_radius="10px", font_family=SANS,
                        font_weight="600", padding="7px 18px",
                        cursor="pointer",
                        _hover={"opacity": "0.85"},
                    ),
                    spacing="2", justify="end", width="100%",
                ),
                spacing="3", width="100%",
            ),
            background=C_DIALOG,
            border=f"1px solid {C_BORDER}",
            border_radius="20px", padding="24px",
            max_width="400px",
            backdrop_filter="blur(20px)",
        ),
        open=EngrafoState.show_delete_profile_confirm,
    )


def _restore_version_confirm_dialog() -> rx.Component:
    """Диалог подтверждения восстановления версии."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon("rotate-ccw", size=20, color=C_CYAN),
                    rx.dialog.title(
                        "Восстановить версию?",
                        font_size="16px", font_weight="700",
                        font_family=SANS, color=C_TEXT,
                    ),
                    spacing="2", align="center",
                ),
                rx.text(
                    "Восстановить версию? Текущие значения тегов будут заменены.",
                    font_size="13px", color=C_MUTED, font_family=SANS,
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            "Отмена",
                            on_click=EngrafoState.cancel_restore_version,
                            background="transparent",
                            border=f"1px solid {C_BORDER}",
                            border_radius="10px", color=C_MUTED,
                            font_family=SANS, padding="7px 18px",
                            cursor="pointer",
                            _hover={"background": "rgba(255,255,255,0.06)"},
                        ),
                    ),
                    rx.button(
                        rx.hstack(
                            rx.icon("rotate-ccw", size=14),
                            rx.text("Восстановить", font_size="14px", font_family=SANS),
                            spacing="1", align="center",
                        ),
                        on_click=EngrafoState.do_restore_version,
                        background=f"linear-gradient(135deg, {C_CYAN}, #0FA3A0)",
                        color="#040A0A", border="none",
                        border_radius="10px", font_family=SANS,
                        font_weight="600", padding="7px 18px",
                        cursor="pointer",
                        _hover={"opacity": "0.85"},
                    ),
                    spacing="2", justify="end", width="100%",
                ),
                spacing="3", width="100%",
            ),
            background=C_DIALOG,
            border=f"1px solid {C_BORDER}",
            border_radius="20px", padding="24px",
            max_width="420px",
            backdrop_filter="blur(20px)",
        ),
        open=EngrafoState.show_restore_confirm,
    )


def _expand_editor_dialog() -> rx.Component:
    """Модальный expand-редактор: отдельные поля для текста и картинки."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # ── Header ──────────────────────────────────────────
                rx.hstack(
                    rx.icon("maximize-2", size=18, color=C_CYAN),
                    rx.dialog.title(
                        EngrafoState.expand_label,
                        font_size="16px", font_weight="700",
                        font_family=SANS, color=C_TEXT,
                        margin="0",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.icon("x", size=16, color=C_MUTED, cursor="pointer"),
                        on_click=EngrafoState.close_expand_editor,
                    ),
                    spacing="2", align="center", width="100%",
                ),
                # ── Textarea для текста (нативная) ──────────────────
                rx.el.textarea(
                    value=EngrafoState.expand_text,
                    on_change=EngrafoState.set_expand_text,
                    placeholder="Введите текст...",
                    class_name="expand-textarea",
                    data_tag_key="__EXPAND__",
                ),
                # ── Миниатюра картинки ──────────────────────────────
                rx.cond(
                    EngrafoState.expand_image_src != "",
                    rx.box(
                        rx.el.img(
                            src=EngrafoState.expand_image_src,
                            style={"max_width": "100%", "max_height": "220px",
                                   "border_radius": "8px", "display": "block",
                                   "margin": "0 auto"},
                        ),
                        rx.hstack(
                            rx.spacer(),
                            rx.box(
                                rx.icon("x", size=11, color=C_ERROR),
                                rx.text("Удалить фото", font_size="10px",
                                        color=C_ERROR, font_family=SANS),
                                on_click=EngrafoState.clear_expand_image,
                                display="flex", align_items="center", gap="4px",
                                cursor="pointer", padding="4px 8px",
                                border_radius="6px",
                                _hover={"background": "rgba(255,77,106,0.10)"},
                            ),
                            padding="4px 0", width="100%",
                        ),
                        padding="10px",
                        background="rgba(255,255,255,0.02)",
                        border=f"1px solid {C_BORDER}",
                        border_radius="10px",
                        width="100%",
                    ),
                ),
                # ── Кнопка добавить картинку ─────────────────────────
                rx.cond(
                    EngrafoState.expand_image_src == "",
                    rx.button(
                        rx.hstack(
                            rx.icon("image-plus", size=13),
                            rx.text("Добавить изображение",
                                    font_size="12px", font_family=SANS),
                            spacing="1", align="center",
                        ),
                        on_click=EngrafoState.open_image_picker("__EXPAND__"),
                        background="rgba(201,35,248,0.08)",
                        border="1px solid rgba(201,35,248,0.20)",
                        border_radius="8px", color=C_PURPLE,
                        padding="5px 12px", cursor="pointer",
                        font_family=SANS,
                        _hover={"background": "rgba(201,35,248,0.16)"},
                        width="fit-content",
                    ),
                ),
                # ── Кнопки ──────────────────────────────────────────
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            "Отмена",
                            on_click=EngrafoState.close_expand_editor,
                            background="transparent",
                            border=f"1px solid {C_BORDER}",
                            border_radius="10px", color=C_MUTED,
                            font_family=SANS, padding="7px 18px",
                            cursor="pointer",
                            _hover={"background": "rgba(255,255,255,0.06)"},
                        ),
                    ),
                    rx.button(
                        rx.hstack(
                            rx.icon("check", size=14),
                            rx.text("Сохранить", font_size="14px", font_family=SANS),
                            spacing="1", align="center",
                        ),
                        on_click=EngrafoState.save_expand_and_close,
                        background=f"linear-gradient(135deg, {C_CYAN}, #0FA3A0)",
                        color="#040A0A", border="none",
                        border_radius="10px", font_family=SANS,
                        font_weight="600", padding="7px 18px",
                        cursor="pointer",
                        _hover={"opacity": "0.85"},
                    ),
                    spacing="2", justify="end", width="100%",
                ),
                spacing="3", width="100%",
            ),
            background=C_DIALOG,
            border=f"1px solid {C_BORDER}",
            border_radius="20px", padding="24px",
            max_width="640px", width="92vw",
            backdrop_filter="blur(20px)",
        ),
        open=EngrafoState.expand_key != "",
    )


def _sidebar_profiles() -> rx.Component:
    return rx.vstack(
        _label("Профили", "bookmark", C_PURPLE),
        rx.cond(
            EngrafoState.has_profiles,
            rx.vstack(
                rx.foreach(EngrafoState.profiles, _profile_item),
                spacing="1", width="100%",
            ),
            rx.text("Нет профилей", font_size="11px",
                    color=C_MUTED2, font_family=SANS, font_style="italic"),
        ),
        rx.button(
            rx.hstack(
                rx.icon("bookmark-plus", size=12),
                rx.text("Сохранить профиль", font_size="12px", font_family=SANS),
                spacing="1", align="center",
            ),
            on_click=EngrafoState.open_save_profile_dialog,
            background="rgba(201,35,248,0.08)",
            border="1px solid rgba(201,35,248,0.20)",
            border_radius="10px", color=C_PURPLE,
            padding="7px 12px", cursor="pointer",
            width="100%",
            _hover={"background": "rgba(201,35,248,0.16)"},
        ),
        spacing="2", width="100%",
    )


def _version_item(v: dict) -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.icon("git-commit-horizontal", size=10, color=C_CYAN),
            rx.text(v["saved_at"], font_size="11px", color=C_MUTED, font_family=MONO),
            spacing="1", align="center",
        ),
        rx.spacer(),
        rx.button(
            rx.icon("rotate-ccw", size=10),
            on_click=EngrafoState.confirm_restore_version(v["id"]),
            background="rgba(34,242,239,0.08)",
            border="1px solid rgba(34,242,239,0.20)",
            border_radius="6px", padding="3px 7px",
            cursor="pointer", color=C_CYAN,
            title="Восстановить",
            _hover={"background": "rgba(34,242,239,0.16)"},
        ),
        align="center", width="100%",
    )


def _sidebar_versions() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            _label("Версии", "git-branch", C_CYAN),
            rx.spacer(),
            rx.hstack(
                rx.cond(
                    EngrafoState.autosave_pending,
                    rx.hstack(
                        rx.spinner(size="2", color=C_CYAN),
                        rx.text("авто...", font_size="12px",
                                color=C_MUTED, font_family=SANS),
                        spacing="1", align="center",
                    ),
                ),
                rx.button(
                    rx.icon("save", size=11),
                    on_click=EngrafoState.save_version,
                    background="rgba(34,242,239,0.08)",
                    border="1px solid rgba(34,242,239,0.20)",
                    border_radius="6px", padding="3px 8px",
                    cursor="pointer", color=C_CYAN,
                    title="Сохранить версию",
                    _hover={"background": "rgba(34,242,239,0.16)"},
                ),
                spacing="2", align="center",
            ),
            align="center", width="100%",
        ),
        rx.cond(
            EngrafoState.has_versions,
            rx.vstack(
                rx.foreach(EngrafoState.versions, _version_item),
                spacing="1", width="100%",
            ),
            rx.text("Нет версий", font_size="11px",
                    color=C_MUTED2, font_family=SANS, font_style="italic"),
        ),
        spacing="2", width="100%",
    )


def _sidebar() -> rx.Component:
    return rx.box(
        rx.vstack(
            # Report title chip
            rx.hstack(
                _badge("file-text", C_GREEN, "rgba(73,220,122,0.12)"),
                rx.text(
                    EngrafoState.current_report_title,
                    font_size="13px", font_weight="600",
                    font_family=SANS, color=C_TEXT,
                    no_of_lines=2, flex="1", line_height="1.4",
                ),
                spacing="2", align="start",
                padding="14px 16px",
                background=C_CARD2,

                border=f"1px solid {C_BORDER}",
                border_radius="14px", width="100%",
            ),
            _card(_sidebar_template(), padding="16px", width="100%"),
            _card(_sidebar_profiles(), padding="16px", width="100%"),
            _card(_sidebar_versions(), padding="16px", width="100%"),
            spacing="3",
            width="100%",
            align="start",
        ),
        class_name="engrafo-sidebar hide-scrollbar",
        overflow_y="auto",
        padding_bottom="24px",
    )


# ── Tags panel ─────────────────────────────────────────────────────────────

def _tags_panel() -> rx.Component:
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                _badge("tag", C_CYAN, "rgba(34,242,239,0.10)"),
                rx.text("Поля шаблона", font_size="14px", font_weight="700",
                        font_family=SANS, color=C_TEXT),
                rx.spacer(),
                # Кнопка загрузки файлов контекста
                rx.button(
                    rx.hstack(
                        rx.icon("folder-open", size=13),
                        rx.text("Контекст", font_size="11px", font_family=SANS, font_weight="500"),
                        spacing="1", align="center",
                    ),
                    on_click=EngrafoState.open_context_upload,
                    background="rgba(34,242,239,0.07)",
                    border=f"1px solid rgba(34,242,239,0.20)",
                    border_radius="8px", color=C_CYAN,
                    padding="4px 10px", cursor="pointer",
                    _hover={"background": "rgba(34,242,239,0.13)"},
                    margin_right="1",
                ),
                rx.cond(
                    EngrafoState.has_tags,
                    rx.hstack(
                        # Кнопка все/ничего
                        rx.box(
                            rx.cond(
                                EngrafoState.all_tags_selected,
                                rx.text("Скрыть все", font_size="10px", color=C_MUTED,
                                        font_family=SANS, font_weight="500"),
                                rx.text("Показать все", font_size="10px", color=C_CYAN,
                                        font_family=SANS, font_weight="500"),
                            ),
                            on_click=rx.cond(
                                EngrafoState.all_tags_selected,
                                EngrafoState.deselect_all_tags,
                                EngrafoState.select_all_tags,
                            ),
                            cursor="pointer",
                            padding="2px 8px",
                            border_radius="6px",
                            _hover={"background": "rgba(255,255,255,0.04)"},
                        ),
                        rx.text(
                            EngrafoState.tag_entries.length().to_string(),
                            font_size="12px", font_weight="700",
                            color=C_CYAN, font_family=MONO,
                        ),
                        spacing="2", align="center",
                    ),
                ),
                align="center", width="100%",
                padding="14px 16px 8px",
            ),
            # Tag chips — выбор тегов
            rx.cond(
                EngrafoState.has_tags,
                rx.box(
                    rx.foreach(EngrafoState.tag_entries, _tag_chip),
                    display="flex",
                    flex_wrap="wrap",
                    gap="6px",
                    padding="0 16px 10px",
                    width="100%",
                ),
            ),
            # Fields — только выбранные
            rx.cond(
                EngrafoState.has_tags,
                rx.vstack(
                    rx.foreach(EngrafoState.visible_tag_entries, _tag_field),
                    spacing="2",
                    padding="4px 14px 24px",
                    width="100%",
                    key=EngrafoState.form_key.to_string(),
                ),
                rx.vstack(
                    rx.box(
                        rx.icon("file-search", size=40, color=C_MUTED2),
                        background="rgba(255,255,255,0.03)",
                        border_radius="20px", padding="24px",
                        display="flex", align_items="center",
                    ),
                    rx.text("Выберите шаблон", font_size="14px",
                            font_weight="600", color=C_MUTED, font_family=SANS),
                    rx.text("Теги появятся здесь автоматически",
                            font_size="12px", color=C_MUTED2, font_family=SANS),
                    spacing="2", align="center", padding="60px 24px",
                ),
            ),
            spacing="0", width="100%",
        ),
        id="engrafo-tags-panel",
        background=C_CARD,
        border=f"1px solid {C_BORDER}",
        border_radius="20px",
        overflow_y="auto",
        class_name="engrafo-tags hide-scrollbar",
    )


# ── Resize divider ─────────────────────────────────────────────────────────

def _resize_divider() -> rx.Component:
    return rx.box(
        rx.box(
            width="2px", height="40px",
            background="rgba(34,242,239,0.35)",
            border_radius="2px",
        ),
        id="engrafo-resize-divider",
        display="flex",
        align_items="center",
        justify_content="center",
        width="14px",
        height="100%",
        cursor="col-resize",
        flex_shrink="0",
        border_radius="6px",
        _hover={"background": "rgba(34,242,239,0.08)"},
        transition="background 0.15s ease",
        user_select="none",
    )


# ── Preview panel ──────────────────────────────────────────────────────────

def _preview_panel() -> rx.Component:
    return rx.box(
     rx.vstack(
        # Header
        rx.hstack(
            _badge("eye", C_GREEN, "rgba(73,220,122,0.10)"),
            rx.text("Предпросмотр", font_size="13px", font_weight="600",
                    color=C_TEXT, font_family=SANS),
            rx.spacer(),
            rx.cond(
                EngrafoState.preview_loading,
                rx.hstack(
                    rx.spinner(size="1", color=C_CYAN),
                    rx.text("Генерация...", font_size="11px",
                            color=C_MUTED, font_family=SANS),
                    spacing="1", align="center",
                ),
            ),
            rx.button(
                rx.icon("refresh-cw", size=13),
                on_click=EngrafoState.generate_preview,
                background="rgba(34,242,239,0.08)",
                border="1px solid rgba(34,242,239,0.20)",
                border_radius="8px", color=C_CYAN,
                padding="6px 10px", cursor="pointer",
                title="Обновить preview",
                _hover={"background": "rgba(34,242,239,0.16)"},
            ),
            width="100%", align="center", padding="12px 16px",
            background=C_CARD,
            border=f"1px solid {C_BORDER}",
            border_radius="16px 16px 0 0",
        ),
        # PDF iframe
        rx.box(
            rx.cond(
                EngrafoState.has_preview,
                rx.el.iframe(
                    src=EngrafoState.preview_url,
                    width="100%", height="100%",
                    style={"border": "none"},
                ),
                rx.vstack(
                    rx.box(
                        rx.icon("file-search", size=36, color=C_MUTED2),
                        background="rgba(255,255,255,0.04)",
                        border_radius="16px", padding="20px",
                        display="flex", align_items="center",
                    ),
                    rx.text("PDF появится здесь",
                            font_size="14px", font_weight="600",
                            color=C_MUTED, font_family=SANS),
                    rx.text("Заполните теги и нажмите кнопку обновления",
                            font_size="12px", color=C_MUTED2,
                            font_family=SANS, text_align="center"),
                    spacing="2", align="center",
                ),
            ),
            flex="1",
            background="rgba(0,0,0,0.35)",
            border=f"1px solid {C_BORDER}",
            border_top="none",
            overflow="hidden",
            display="flex",
            align_items="center",
            justify_content="center",
            width="100%",
        ),
        # Export buttons
        rx.hstack(
            rx.button(
                rx.hstack(rx.icon("file-text", size=13),
                          rx.text("DOCX", font_size="12px", font_family=SANS),
                          spacing="1", align="center"),
                on_click=EngrafoState.download_docx,
                background="rgba(255,255,255,0.05)",
                border=f"1px solid {C_BORDER}",
                border_radius="10px", color=C_TEXT,
                padding="7px 14px", cursor="pointer", flex="1",
                _hover={"background": "rgba(255,255,255,0.09)"},
            ),
            rx.button(
                rx.hstack(rx.icon("download", size=13),
                          rx.text("PDF", font_size="12px", font_family=SANS),
                          spacing="1", align="center"),
                on_click=EngrafoState.download_pdf,
                background=f"linear-gradient(135deg, {C_GREEN}, #2ECC71)",
                color="#040A0A", border="none",
                border_radius="10px", font_weight="700",
                padding="7px 18px", cursor="pointer", flex="1",
                _hover={"opacity": "0.88"},
            ),
            rx.button(
                rx.hstack(rx.icon("check-circle", size=13),
                          rx.text("Завершить", font_size="12px", font_family=SANS),
                          spacing="1", align="center"),
                on_click=EngrafoState.finalize_report,
                background="rgba(73,220,122,0.08)",
                border="1px solid rgba(73,220,122,0.22)",
                border_radius="10px", color=C_GREEN,
                padding="7px 14px", cursor="pointer", flex="1",
                _hover={"background": "rgba(73,220,122,0.15)"},
            ),
            spacing="2", width="100%",
            padding="10px 12px",
            background=C_CARD,
            border=f"1px solid {C_BORDER}",
            border_radius="0 0 16px 16px",
            border_top="none",
        ),
        spacing="0",
        width="100%",
        height="100%",
        align="start",
     ),
     id="engrafo-preview-panel",
     class_name="engrafo-preview",
    )


# ── Image picker modal ─────────────────────────────────────────────────────

def _image_picker() -> rx.Component:
    return rx.cond(
        EngrafoState.image_picker_key != "",
        rx.fragment(
            # Overlay
            rx.box(
                on_click=EngrafoState.close_image_picker,
                position="fixed", top="0", left="0",
                width="100vw", height="100vh",
                background="rgba(0,0,0,0.65)",
                z_index="499",
                backdrop_filter="blur(4px)",
            ),
            # Modal
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.text("Вставить картинку",
                                font_size="15px", font_weight="700",
                                font_family=SANS, color=C_TEXT),
                        rx.spacer(),
                        rx.button(
                            rx.icon("x", size=14),
                            on_click=EngrafoState.close_image_picker,
                            background="transparent", border="none",
                            color=C_MUTED, cursor="pointer", padding="4px",
                        ),
                        width="100%", align="center",
                    ),
                    rx.cond(
                        EngrafoState.image_picker_key == "__EXPAND__",
                        rx.text("Для расширенного редактора",
                                font_size="12px", color=C_MUTED2, font_family=SANS),
                        rx.text(
                            "Тег: " + EngrafoState.image_picker_key,
                            font_size="12px", color=C_MUTED2, font_family=MONO,
                        ),
                    ),
                    rx.upload(
                        rx.vstack(
                            rx.icon("upload-cloud", size=32, color=C_MUTED2),
                            rx.text("Перетащите или кликните для выбора",
                                    font_size="13px", color=C_MUTED, font_family=SANS),
                            rx.text("PNG, JPG, WEBP, GIF",
                                    font_size="11px", color=C_MUTED2, font_family=SANS),
                            spacing="2", align="center", padding="32px",
                        ),
                        id="engrafo-image-upload",
                        accept={"image/png": [".png"],
                                "image/jpeg": [".jpg", ".jpeg"],
                                "image/webp": [".webp"],
                                "image/gif": [".gif"]},
                        max_files=1,
                        border="1px dashed rgba(34,242,239,0.30)",
                        border_radius="12px",
                        background="rgba(34,242,239,0.04)",
                        cursor="pointer",
                        width="100%",
                        _hover={"background": "rgba(34,242,239,0.08)"},
                    ),
                    rx.hstack(
                        rx.button(
                            "Отмена",
                            on_click=EngrafoState.close_image_picker,
                            background="transparent",
                            border=f"1px solid {C_BORDER}",
                            border_radius="10px", color=C_MUTED,
                            font_family=SANS, padding="7px 18px",
                            cursor="pointer",
                            _hover={"background": "rgba(255,255,255,0.06)"},
                        ),
                        rx.button(
                            "Вставить",
                            on_click=EngrafoState.handle_image_upload(
                                rx.upload_files(upload_id="engrafo-image-upload")
                            ),
                            background=f"linear-gradient(135deg, {C_PURPLE}, {C_PURPLE_DARK})",
                            color="white", border="none",
                            border_radius="10px", font_family=SANS,
                            font_weight="600", padding="7px 18px",
                            cursor="pointer",
                            _hover={"opacity": "0.85"},
                        ),
                        spacing="2", justify="end", width="100%",
                    ),
                    spacing="3", width="100%",
                ),
                position="fixed",
                top="50%", left="50%",
                transform="translate(-50%, -50%)",
                z_index="500",
                background=C_DIALOG,
                border=f"1px solid {C_BORDER}",
                border_radius="20px", padding="24px",
                max_width="420px", width="92vw",
                backdrop_filter="blur(20px)",
                box_shadow="0 20px 60px rgba(0,0,0,0.60)",
            ),
        ),
    )


# ── Toasts ─────────────────────────────────────────────────────────────────

def _toasts() -> rx.Component:
    return rx.fragment(
        rx.cond(
            EngrafoState.success_msg != "",
            rx.box(
                rx.hstack(
                    rx.box(
                        rx.icon("check-circle", size=14, color=C_GREEN),
                        background="rgba(73,220,122,0.15)",
                        border_radius="6px", padding="4px",
                    ),
                    rx.text(EngrafoState.success_msg,
                            font_size="13px", color=C_TEXT, font_family=SANS, flex="1"),
                    rx.button(
                        rx.icon("x", size=12),
                        on_click=EngrafoState.clear_messages,
                        background="transparent", border="none",
                        color=C_MUTED, cursor="pointer", padding="0",
                    ),
                    spacing="2", align="center", width="100%",
                ),
                position="fixed", bottom="24px", right="24px", z_index="300",
                background=C_CARD2,
                border="1px solid rgba(73,220,122,0.30)",
                border_radius="14px", padding="12px 16px", max_width="360px",
                backdrop_filter="blur(20px)",
                box_shadow="0 8px 32px rgba(0,0,0,0.40)",
            ),
        ),
        rx.cond(
            EngrafoState.error_msg != "",
            rx.box(
                rx.hstack(
                    rx.box(
                        rx.icon("triangle-alert", size=14, color=C_ERROR),
                        background="rgba(255,77,106,0.15)",
                        border_radius="6px", padding="4px",
                    ),
                    rx.text(EngrafoState.error_msg,
                            font_size="13px", color=C_TEXT, font_family=SANS, flex="1"),
                    rx.button(
                        rx.icon("x", size=12),
                        on_click=EngrafoState.clear_messages,
                        background="transparent", border="none",
                        color=C_MUTED, cursor="pointer", padding="0",
                    ),
                    spacing="2", align="center", width="100%",
                ),
                position="fixed", bottom="88px", right="24px", z_index="300",
                background=C_CARD2,
                border="1px solid rgba(255,77,106,0.30)",
                border_radius="14px", padding="12px 16px", max_width="360px",
                backdrop_filter="blur(20px)",
                box_shadow="0 8px 32px rgba(0,0,0,0.40)",
            ),
        ),
    )


# ── Main page ──────────────────────────────────────────────────────────────

def engrafo_editor_page() -> rx.Component:
    return rx.box(
        rx.script(src="/engrafo_editor.js"),
        rx.el.link(rel="stylesheet", href="/engrafo.css"),
        # Proxy-textarea для Ctrl+V картинок (JS пишет сюда, Reflex читает)
        rx.el.textarea(
            id="engrafo-paste-proxy",
            on_change=EngrafoState.handle_clipboard_paste,
            style={
                "position": "fixed", "top": "-9999px", "left": "-9999px",
                "width": "1px", "height": "1px", "opacity": "0",
                "pointer_events": "none", "z_index": "-1",
                "tab_index": "-1",
            },
            aria_hidden="true",
        ),
        header(),
        _save_profile_dialog(),
        _delete_profile_confirm_dialog(),
        _restore_version_confirm_dialog(),
        _expand_editor_dialog(),
        _context_upload_dialog(),
        _image_picker(),
        _toasts(),

        rx.box(
            rx.el.div(
                _sidebar(),
                _tags_panel(),
                _resize_divider(),
                _preview_panel(),
                class_name="engrafo-editor-layout",
            ),
            padding_top="72px",
            padding_x="16px",
            padding_bottom="8px",
            width="100%",
            max_width="100vw",
            class_name="engrafo-editor-outer",
        ),

        background=C_BG,
        width="100vw",
        min_height="100vh",
        overflow_x="hidden",
    )
