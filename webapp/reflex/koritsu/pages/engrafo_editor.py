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


# ── Tag type badge ────────────────────────────────────────────────────────

_TYPE_COLORS = {
    "global": ("#3b82f6", "rgba(59,130,246,0.12)", "Профиль"),
    "doc":    ("#22c55e", "rgba(34,197,94,0.12)",  "Документ"),
    "ai":     ("#a855f7", "rgba(168,85,247,0.12)", "AI"),
    "raw":    ("#94a3b8", "rgba(148,163,184,0.10)", "Вручную"),
}


def _tag_type_badge(tag_type: str) -> rx.Component:
    """Маленький бейдж типа тега."""
    # Используем rx.cond цепочкой для динамического определения цвета
    color = rx.cond(
        tag_type == "global", _TYPE_COLORS["global"][0],
        rx.cond(tag_type == "doc", _TYPE_COLORS["doc"][0],
        rx.cond(tag_type == "ai", _TYPE_COLORS["ai"][0],
        _TYPE_COLORS["raw"][0]))
    )
    bg = rx.cond(
        tag_type == "global", _TYPE_COLORS["global"][1],
        rx.cond(tag_type == "doc", _TYPE_COLORS["doc"][1],
        rx.cond(tag_type == "ai", _TYPE_COLORS["ai"][1],
        _TYPE_COLORS["raw"][1]))
    )
    label = rx.cond(
        tag_type == "global", _TYPE_COLORS["global"][2],
        rx.cond(tag_type == "doc", _TYPE_COLORS["doc"][2],
        rx.cond(tag_type == "ai", _TYPE_COLORS["ai"][2],
        _TYPE_COLORS["raw"][2]))
    )
    return rx.box(
        rx.text(label, font_size="9px", font_weight="700",
                color=color, font_family=SANS, letter_spacing="0.5px"),
        background=bg,
        border_radius="4px",
        padding="1px 6px",
        flex_shrink="0",
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
                flex="1",
            ),
            _tag_type_badge(entry["type"]),
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
    Tag editor — contenteditable div с inline-картинками.
    Изображения вставляются в позицию курсора через JS.
    Sync через engrafo-html-proxy при blur.
    """
    has_value = entry["value"] != ""

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
            _tag_type_badge(entry["type"]),
            # Кнопка "Сгенерировать" только для raw_ тегов
            rx.cond(
                entry["type"] == "raw",
                rx.box(
                    rx.icon("wand-sparkles", size=13, color="rgba(148,163,184,0.60)"),
                    on_click=EngrafoState.open_ai_prompt_dialog(entry["key"]),
                    border_radius="8px", padding="5px",
                    cursor="pointer",
                    title="Сгенерировать с помощью AI",
                    _hover={"background": "rgba(148,163,184,0.12)"},
                    transition="all 0.2s ease",
                    display="flex", align_items="center",
                    flex_shrink="0",
                ),
            ),
            # Image insert button — JS handles cursor insertion
            rx.el.button(
                rx.icon("image-plus", size=14, color="rgba(201,35,248,0.55)"),
                class_name="tag-img-btn",
                data_img_key=entry["key"],
                title="Вставить изображение в позицию курсора (или Ctrl+V)",
                style={
                    "background": "transparent",
                    "border": "none",
                    "border_radius": "8px",
                    "padding": "5px",
                    "cursor": "pointer",
                    "display": "flex",
                    "align_items": "center",
                    "flex_shrink": "0",
                    "transition": "all 0.2s ease",
                },
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
        # ── Quill rich-text editor ──────────────────────────────
        rx.el.div(
            class_name="tag-quill",
            data_tag_key=entry["key"],
            data_init_html=entry["value"],
            data_form_key=EngrafoState.form_key.to_string(),
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
                # ── Quill expand editor ──────────────────────────────
                # Обёртка нужна: Quill вставляет toolbar как sibling перед
                # .expand-quill, поэтому нужен общий родитель для CSS-правила
                # .expand-quill-wrap .ql-toolbar { display: block }
                rx.el.div(
                    rx.el.div(
                        class_name="expand-quill",
                        data_tag_key="__EXPAND__",
                        data_init_html=EngrafoState.expand_html,
                        data_form_key=EngrafoState.form_key.to_string(),
                    ),
                    class_name="expand-quill-wrap",
                    style={"width": "100%"},
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


def _global_popup_dialog() -> rx.Component:
    """Popup предлагающий применить глобальные теги из профиля пользователя."""
    tag_list = rx.vstack(
        rx.foreach(
            EngrafoState.global_popup_tags,
            lambda k: rx.hstack(
                rx.icon("user", size=12, color="#3b82f6"),
                rx.text(k, font_size="12px", font_family=MONO, color=C_TEXT),
                spacing="2", align="center",
            ),
        ),
        gap="4px", align_items="flex_start",
    )
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon("user-check", size=18, color="#3b82f6"),
                    rx.text(
                        "Найдены глобальные теги",
                        font_size="15px", font_weight="700",
                        color=C_TEXT, font_family=SANS,
                    ),
                    spacing="2", align="center",
                ),
                rx.text(
                    "В шаблоне найдены теги из вашего профиля. Хотите применить сохранённые значения?",
                    font_size="13px", color=C_MUTED, font_family=SANS, line_height="1.5",
                ),
                tag_list,
                rx.hstack(
                    rx.button(
                        "Применить",
                        on_click=EngrafoState.apply_global_tags,
                        background="#3b82f6",
                        color="white",
                        border_radius="8px",
                        padding="8px 20px",
                        font_size="13px",
                        font_family=SANS,
                        font_weight="600",
                        cursor="pointer",
                        _hover={"background": "#2563eb"},
                    ),
                    rx.button(
                        "Пропустить",
                        on_click=EngrafoState.skip_global_tags,
                        background="transparent",
                        color=C_MUTED,
                        border=f"1px solid {C_BORDER}",
                        border_radius="8px",
                        padding="8px 20px",
                        font_size="13px",
                        font_family=SANS,
                        cursor="pointer",
                        _hover={"background": "rgba(255,255,255,0.04)"},
                    ),
                    spacing="3",
                ),
                gap="16px", padding="24px",
                background=C_DIALOG,
                border_radius="16px",
                border=f"1px solid {C_BORDER}",
                min_width="360px",
                max_width="480px",
            ),
            background="transparent",
            padding="0",
        ),
        open=EngrafoState.show_global_popup,
    )


def _ai_prompt_dialog() -> rx.Component:
    """Диалог для ввода кастомного промпта для неизвестного тега."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon("bot", size=16, color=C_PURPLE),
                    rx.text("Промпт для тега", font_size="14px",
                            font_weight="700", color=C_TEXT, font_family=SANS),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.icon("x", size=16, color=C_MUTED, cursor="pointer"),
                        on_click=EngrafoState.close_ai_prompt_dialog,
                    ),
                    spacing="3", align="center", width="100%",
                ),
                rx.text(
                    "Тег «",
                    rx.text.span(EngrafoState.ai_prompt_tag_key,
                                 color=C_CYAN, font_weight="700"),
                    "» не найден в prompts.yaml. Опишите что нужно сгенерировать.",
                    font_size="12px", color=C_MUTED, font_family=SANS,
                ),
                rx.text("Системный промпт", font_size="11px", color=C_MUTED,
                        font_weight="600", font_family=SANS, text_transform="uppercase",
                        letter_spacing="0.6px"),
                rx.el.textarea(
                    placeholder="Ты — технический писатель академических отчётов.",
                    value=EngrafoState.ai_prompt_system,
                    on_change=EngrafoState.set_ai_prompt_system,
                    rows="3",
                    style={
                        "width": "100%", "background": C_CARD,
                        "border": f"1px solid {C_BORDER}", "border_radius": "10px",
                        "color": C_TEXT, "font_family": SANS, "font_size": "13px",
                        "padding": "10px", "resize": "vertical", "outline": "none",
                    },
                ),
                rx.text("Задание", font_size="11px", color=C_MUTED,
                        font_weight="600", font_family=SANS, text_transform="uppercase",
                        letter_spacing="0.6px"),
                rx.el.textarea(
                    placeholder="Напиши раздел «...» объёмом 100-200 слов на основе предоставленного контекста.",
                    value=EngrafoState.ai_prompt_user_text,
                    on_change=EngrafoState.set_ai_prompt_user_text,
                    rows="4",
                    style={
                        "width": "100%", "background": C_CARD,
                        "border": f"1px solid {C_BORDER}", "border_radius": "10px",
                        "color": C_TEXT, "font_family": SANS, "font_size": "13px",
                        "padding": "10px", "resize": "vertical", "outline": "none",
                    },
                ),
                rx.hstack(
                    rx.text("Уровень контекста:", font_size="12px", color=C_MUTED, font_family=SANS),
                    rx.select(
                        ["full", "global"],
                        value=EngrafoState.ai_prompt_context_level,
                        on_change=EngrafoState.set_ai_prompt_context_level,
                        size="1",
                    ),
                    rx.text("OCR:", font_size="12px", color=C_MUTED, font_family=SANS),
                    rx.switch(
                        checked=EngrafoState.ai_prompt_include_ocr,
                        on_change=EngrafoState.set_ai_prompt_include_ocr,
                        size="1",
                    ),
                    spacing="2", align="center",
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            "Отмена",
                            on_click=EngrafoState.close_ai_prompt_dialog,
                            background="transparent",
                            border=f"1px solid {C_BORDER}",
                            border_radius="10px", color=C_MUTED,
                            font_family=SANS, font_size="13px", cursor="pointer",
                        ),
                    ),
                    rx.dialog.close(
                        rx.button(
                            rx.icon("sparkles", size=13),
                            rx.text("Генерировать", font_family=SANS),
                            spacing="2", align="center",
                            on_click=EngrafoState.save_ai_prompt_and_run,
                            background=f"linear-gradient(135deg, {C_PURPLE} 0%, #7c3aed 100%)",
                            border_radius="10px", color="white",
                            font_size="13px", cursor="pointer",
                            padding_x="16px", padding_y="8px",
                            _hover={"opacity": "0.85"},
                        ),
                    ),
                    spacing="2", justify="end", width="100%",
                ),
                spacing="3", width="100%",
            ),
            background=C_DIALOG,
            border=f"1px solid {C_BORDER}",
            border_radius="16px",
            padding="24px",
            max_width="520px",
            width="90vw",
            backdrop_filter="blur(20px)",
        ),
        open=EngrafoState.show_ai_prompt_dialog,
    )


def _sidebar_context() -> rx.Component:
    """Секция контекстных файлов и AI-генерации в сайдбаре."""
    return rx.vstack(
        rx.hstack(
            _label("Контекст & AI", "bot", C_PURPLE),
            rx.spacer(),
            rx.cond(
                EngrafoState.context_files.length() > 0,
                rx.text(
                    EngrafoState.context_files.length().to_string(),
                    font_size="11px", font_weight="700",
                    color=C_CYAN, font_family=SANS,
                ),
            ),
            align="center", width="100%",
        ),
        # Статус AI
        rx.cond(
            EngrafoState.ai_status_msg != "",
            rx.hstack(
                rx.icon("info", size=12, color=C_PURPLE),
                rx.text(EngrafoState.ai_status_msg,
                        font_size="11px", color=C_PURPLE, font_family=SANS,
                        flex="1", no_of_lines=2),
                spacing="1", align="start", width="100%",
                padding="8px", border_radius="8px",
                background="rgba(139,92,246,0.08)",
            ),
        ),
        # Кнопки AI
        rx.vstack(
            rx.button(
                rx.cond(
                    EngrafoState.ai_loading,
                    rx.hstack(
                        rx.spinner(size="2"),
                        rx.text("Генерация...", font_family=SANS, font_size="14px",
                                font_weight="700"),
                        spacing="2", align="center",
                    ),
                    rx.hstack(
                        rx.icon("sparkles", size=16),
                        rx.text("Сгенерировать", font_family=SANS, font_size="14px",
                                font_weight="700"),
                        spacing="2", align="center",
                    ),
                ),
                on_click=rx.cond(
                    EngrafoState.ai_loading,
                    EngrafoState.noop,
                    EngrafoState.open_generate_modal,
                ),
                disabled=EngrafoState.ai_loading,
                background=rx.cond(
                    EngrafoState.ai_loading,
                    "rgba(139,92,246,0.15)",
                    f"linear-gradient(135deg, {C_PURPLE} 0%, #7c3aed 100%)",
                ),
                border_radius="12px", color="white", width="100%",
                font_size="14px", cursor="pointer", padding_y="12px",
                box_shadow=rx.cond(
                    EngrafoState.ai_loading,
                    "none",
                    "0 4px 16px rgba(139,92,246,0.35)",
                ),
                _hover={"opacity": "0.88", "box_shadow": "0 6px 20px rgba(139,92,246,0.45)"},
                transition="all 0.2s",
            ),
            rx.button(
                rx.hstack(
                    rx.icon("check-circle", size=13),
                    rx.text("Применить к тегам", font_family=SANS, font_size="12px"),
                    spacing="2", align="center",
                ),
                on_click=EngrafoState.apply_ai_steps,
                disabled=EngrafoState.ai_loading,
                background="rgba(34,197,94,0.1)",
                border=f"1px solid rgba(34,197,94,0.3)",
                border_radius="10px", color=C_GREEN, width="100%",
                font_size="12px", cursor="pointer", padding_y="8px",
                _hover={"background": "rgba(34,197,94,0.18)"},
                transition="all 0.2s",
            ),
            spacing="2", width="100%",
        ),
        # needs_prompt теги
        rx.cond(
            EngrafoState.needs_prompt_tags.length() > 0,
            rx.vstack(
                rx.text("Нужен промпт:", font_size="10px", color=C_MUTED,
                        font_weight="600", font_family=SANS,
                        text_transform="uppercase", letter_spacing="0.8px"),
                rx.foreach(
                    EngrafoState.needs_prompt_tags,
                    lambda tag: rx.button(
                        rx.hstack(
                            rx.icon("edit-3", size=10),
                            rx.text(tag, font_size="11px", font_family=SANS),
                            spacing="1", align="center",
                        ),
                        on_click=EngrafoState.open_ai_prompt_dialog(tag),
                        background="rgba(251,146,60,0.1)",
                        border="1px solid rgba(251,146,60,0.3)",
                        border_radius="8px", color="#fb923c",
                        font_size="11px", cursor="pointer", width="100%",
                        padding_y="5px",
                        _hover={"background": "rgba(251,146,60,0.18)"},
                    ),
                ),
                spacing="1", width="100%",
            ),
        ),
        rx.divider(border_color=C_BORDER, opacity="0.5"),
        # Файлы контекста
        rx.cond(
            EngrafoState.context_files.length() > 0,
            rx.vstack(
                rx.foreach(
                    EngrafoState.context_files,
                    lambda f: rx.hstack(
                        rx.box(
                            rx.text(
                                f["ext"].upper().replace(".", ""),
                                font_size="8px", font_weight="700",
                                color=C_CYAN, font_family=SANS,
                            ),
                            background="rgba(34,242,239,0.10)",
                            border="1px solid rgba(34,242,239,0.20)",
                            border_radius="4px", padding="1px 4px",
                            flex_shrink="0",
                        ),
                        rx.text(f["name"], font_size="11px", color=C_TEXT,
                                font_family=SANS, flex="1", no_of_lines=1),
                        rx.box(
                            rx.icon("x", size=10, color=C_ERROR),
                            on_click=EngrafoState.delete_context_file(f["name"]),
                            cursor="pointer", border_radius="4px", padding="2px",
                            _hover={"background": "rgba(255,77,106,0.12)"},
                            display="flex", align_items="center", flex_shrink="0",
                        ),
                        spacing="2", align="center", width="100%",
                    ),
                ),
                spacing="1", width="100%",
            ),
        ),
        rx.button(
            rx.hstack(
                rx.icon("upload-cloud", size=12),
                rx.text("Загрузить файлы", font_size="12px", font_family=SANS),
                spacing="1", align="center",
            ),
            on_click=EngrafoState.open_context_upload,
            background="rgba(34,242,239,0.07)",
            border="1px solid rgba(34,242,239,0.20)",
            border_radius="10px", color=C_CYAN,
            padding="7px 12px", cursor="pointer",
            width="100%",
            _hover={"background": "rgba(34,242,239,0.13)"},
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
            _card(_sidebar_context(), padding="16px", width="100%"),
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
                rx.cond(
                    EngrafoState.visible_tag_entries.length() > 0,
                    rx.vstack(
                        rx.foreach(EngrafoState.visible_tag_entries, _tag_field),
                        spacing="2",
                        padding="4px 14px 24px",
                        width="100%",
                        key=EngrafoState.form_key.to_string(),
                    ),
                    # All tags deselected — hint
                    rx.vstack(
                        rx.box(
                            rx.icon("tag", size=32, color=C_MUTED2),
                            background="rgba(255,255,255,0.03)",
                            border_radius="16px", padding="18px",
                            display="flex", align_items="center",
                        ),
                        rx.text("Выберите тег для редактирования",
                                font_size="13px", font_weight="600",
                                color=C_MUTED, font_family=SANS),
                        rx.text("Нажмите на один из чипов выше",
                                font_size="12px", color=C_MUTED2, font_family=SANS),
                        spacing="2", align="center", padding="40px 24px",
                    ),
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


# ── Generate modal ─────────────────────────────────────────────────────────

def _gen_tag_chip(row: dict) -> rx.Component:
    """Чип тега в левой колонке модала генерации."""
    is_selected = row["selected"] == "true"
    has_prompt  = row["has_prompt"] == "true"

    return rx.hstack(
        # Checkbox
        rx.box(
            rx.cond(
                is_selected,
                rx.icon("check", size=10, color=C_CYAN),
                rx.box(),
            ),
            width="16px", height="16px", flex_shrink="0",
            border_radius="4px",
            border=rx.cond(is_selected, f"1px solid {C_CYAN}", "1px solid rgba(255,255,255,0.15)"),
            background=rx.cond(is_selected, "rgba(34,242,239,0.12)", "transparent"),
            display="flex", align_items="center", justify_content="center",
            transition="all 0.15s ease",
        ),
        rx.vstack(
            rx.text(row["label"], font_size="12px", font_weight="600",
                    color=rx.cond(is_selected, C_TEXT, C_MUTED),
                    font_family=SANS, no_of_lines=1),
            rx.text(row["key"], font_size="9px", color=C_MUTED2, font_family=MONO),
            spacing="0", align="start", flex="1",
        ),
        rx.cond(
            has_prompt,
            rx.box(width="6px", height="6px", border_radius="50%",
                   background=C_GREEN, flex_shrink="0"),
            rx.box(width="6px", height="6px", border_radius="50%",
                   background="#fb923c", flex_shrink="0"),
        ),
        spacing="2", align="center", width="100%",
        padding="7px 10px", border_radius="8px",
        cursor="pointer",
        background=rx.cond(is_selected, "rgba(34,242,239,0.05)", "transparent"),
        border=rx.cond(
            is_selected,
            "1px solid rgba(34,242,239,0.14)",
            "1px solid transparent",
        ),
        transition="all 0.12s ease",
        on_click=EngrafoState.toggle_generate_key(row["key"]),
        _hover={"background": "rgba(34,242,239,0.07)", "border_color": "rgba(34,242,239,0.18)"},
    )


def _gen_custom_prompt_row(row: dict) -> rx.Component:
    """Поле кастомного промпта для тега без системного (в правой части)."""
    is_selected = row["selected"] == "true"
    has_no_prompt = row["has_prompt"] == "false"

    return rx.cond(
        is_selected & has_no_prompt,
        rx.vstack(
            rx.hstack(
                rx.icon("triangle-alert", size=11, color="#fb923c"),
                rx.text(row["label"], font_size="11px", font_weight="700",
                        color="#fb923c", font_family=SANS),
                rx.text("— нет промпта", font_size="11px", color=C_MUTED, font_family=SANS),
                spacing="1", align="center",
            ),
            rx.el.textarea(
                placeholder="Опиши что нужно сгенерировать...",
                value=row["custom_prompt"],
                on_change=EngrafoState.set_generate_custom_prompt(row["key"]),
                rows="3",
                style={
                    "width": "100%", "background": "rgba(251,146,60,0.04)",
                    "border": "1px solid rgba(251,146,60,0.25)",
                    "border_radius": "8px", "color": C_TEXT,
                    "font_family": SANS, "font_size": "12px",
                    "padding": "8px 10px", "resize": "vertical", "outline": "none",
                },
            ),
            spacing="2", width="100%",
            padding="10px 12px",
            background="rgba(251,146,60,0.04)",
            border="1px solid rgba(251,146,60,0.15)",
            border_radius="10px",
        ),
    )


def _generate_modal() -> rx.Component:
    """Модальное окно выбора тегов для AI-генерации или ручного режима. 2-колоночный layout."""
    is_ai     = EngrafoState.generate_mode == "ai"
    is_manual = EngrafoState.generate_mode == "manual"
    has_ctx_url = EngrafoState.manual_context_url != ""

    # ── Правая панель: AI режим ──
    _right_ai = rx.vstack(
        # Переключатель режима
        rx.hstack(
            rx.box(
                rx.hstack(
                    rx.icon("bot", size=13, color=rx.cond(is_ai, C_PURPLE, C_MUTED)),
                    rx.text("AI (авто)", font_size="12px",
                            font_weight=rx.cond(is_ai, "700", "500"),
                            color=rx.cond(is_ai, C_TEXT, C_MUTED), font_family=SANS),
                    spacing="1", align="center",
                ),
                on_click=EngrafoState.set_generate_mode("ai"),
                background=rx.cond(is_ai, "rgba(201,35,248,0.12)", "transparent"),
                border=rx.cond(is_ai, "1px solid rgba(201,35,248,0.30)", f"1px solid {C_BORDER}"),
                border_radius="8px", padding="7px 14px",
                cursor="pointer", flex="1", display="flex", justify_content="center",
                transition="all 0.15s ease",
            ),
            rx.box(
                rx.hstack(
                    rx.icon("file-pen-line", size=13, color=rx.cond(is_manual, C_CYAN, C_MUTED)),
                    rx.text("Ручной", font_size="12px",
                            font_weight=rx.cond(is_manual, "700", "500"),
                            color=rx.cond(is_manual, C_TEXT, C_MUTED), font_family=SANS),
                    spacing="1", align="center",
                ),
                on_click=EngrafoState.set_generate_mode("manual"),
                background=rx.cond(is_manual, "rgba(34,242,239,0.08)", "transparent"),
                border=rx.cond(is_manual, f"1px solid rgba(34,242,239,0.30)", f"1px solid {C_BORDER}"),
                border_radius="8px", padding="7px 14px",
                cursor="pointer", flex="1", display="flex", justify_content="center",
                transition="all 0.15s ease",
            ),
            spacing="2", width="100%",
        ),

        # Поля кастомных промптов для тегов без промпта
        rx.box(
            rx.vstack(
                rx.foreach(EngrafoState.generate_tag_rows, _gen_custom_prompt_row),
                spacing="2", width="100%",
            ),
            max_height="220px",
            overflow_y="auto",
            width="100%",
            class_name="hide-scrollbar",
        ),

        rx.spacer(),

        # Кнопки AI
        rx.vstack(
            rx.button(
                rx.hstack(
                    rx.icon("sparkles", size=16),
                    rx.text("Сгенерировать", font_size="14px", font_family=SANS,
                            font_weight="700"),
                    spacing="2", align="center",
                ),
                on_click=EngrafoState.run_generate,
                background=f"linear-gradient(135deg, {C_PURPLE} 0%, #7c3aed 100%)",
                color="white", border="none",
                border_radius="12px", font_family=SANS,
                padding="10px 0", cursor="pointer", width="100%",
                _hover={"opacity": "0.88"},
                transition="all 0.2s",
            ),
            rx.dialog.close(
                rx.button(
                    "Отмена",
                    on_click=EngrafoState.close_generate_modal,
                    background="transparent",
                    border=f"1px solid {C_BORDER}",
                    border_radius="10px", color=C_MUTED,
                    font_family=SANS, padding="8px 0",
                    cursor="pointer", width="100%",
                    _hover={"background": "rgba(255,255,255,0.06)"},
                ),
            ),
            spacing="2", width="100%",
        ),
        spacing="3", width="100%", height="100%",
    )

    # ── Правая панель: Ручной режим ──
    _right_manual = rx.vstack(
        rx.box(
            rx.hstack(
                rx.icon("info", size=12, color=C_CYAN),
                rx.text(
                    "Создайте файл контекста, отправьте его в свою нейросеть, "
                    "затем загрузите ответный ans.md",
                    font_size="11px", color=C_MUTED, font_family=SANS, line_height="1.5",
                ),
                spacing="2", align="start",
            ),
            padding="10px 12px",
            background="rgba(34,242,239,0.05)",
            border="1px solid rgba(34,242,239,0.15)",
            border_radius="8px", width="100%",
        ),

        # Шаг 1
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.text("1", font_size="11px", font_weight="700",
                            color=C_CYAN, font_family=SANS),
                    width="22px", height="22px", border_radius="50%",
                    background="rgba(34,242,239,0.12)",
                    border="1px solid rgba(34,242,239,0.25)",
                    display="flex", align_items="center",
                    justify_content="center", flex_shrink="0",
                ),
                rx.text("Создать файл контекста для нейросети",
                        font_size="12px", font_weight="600",
                        color=C_TEXT, font_family=SANS),
                spacing="2", align="center",
            ),
            rx.hstack(
                rx.button(
                    rx.hstack(
                        rx.icon("file-plus", size=13),
                        rx.text("Создать ai_context.md", font_family=SANS, font_size="12px"),
                        spacing="1", align="center",
                    ),
                    on_click=EngrafoState.build_ai_context_file,
                    background="rgba(34,242,239,0.08)",
                    border="1px solid rgba(34,242,239,0.25)",
                    border_radius="10px", color=C_CYAN,
                    padding="7px 14px", cursor="pointer", flex="1",
                    _hover={"background": "rgba(34,242,239,0.15)"},
                ),
                rx.cond(
                    has_ctx_url,
                    rx.el.a(
                        rx.hstack(
                            rx.icon("download", size=13),
                            rx.text("Скачать", font_family=SANS, font_size="12px"),
                            spacing="1", align="center",
                        ),
                        href=EngrafoState.manual_context_url,
                        download="ai_context.md",
                        style={
                            "background": f"linear-gradient(135deg, {C_CYAN}, #0FA3A0)",
                            "color": "#040A0A", "border": "none",
                            "border_radius": "10px", "font_family": SANS,
                            "font_weight": "700", "font_size": "12px",
                            "padding": "7px 14px", "cursor": "pointer",
                            "text_decoration": "none", "display": "flex",
                            "align_items": "center", "flex_shrink": "0",
                        },
                    ),
                ),
                spacing="2", align="center", width="100%",
            ),
            spacing="2", width="100%",
            padding="12px", border_radius="10px",
            background="rgba(34,242,239,0.03)",
            border=f"1px solid rgba(34,242,239,0.10)",
        ),

        # Шаг 2
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.text("2", font_size="11px", font_weight="700",
                            color=C_PURPLE, font_family=SANS),
                    width="22px", height="22px", border_radius="50%",
                    background="rgba(201,35,248,0.12)",
                    border="1px solid rgba(201,35,248,0.25)",
                    display="flex", align_items="center",
                    justify_content="center", flex_shrink="0",
                ),
                rx.text("Загрузить ответ нейросети",
                        font_size="12px", font_weight="600",
                        color=C_TEXT, font_family=SANS),
                spacing="2", align="center",
            ),
            rx.hstack(
                rx.upload(
                    rx.hstack(
                        rx.icon("upload", size=13,
                                color=rx.cond(
                                    rx.selected_files("ans_upload").length() > 0,
                                    C_PURPLE, C_MUTED,
                                )),
                        rx.text(
                            rx.cond(
                                rx.selected_files("ans_upload").length() > 0,
                                rx.selected_files("ans_upload")[0],
                                "ans.md / .txt",
                            ),
                            font_family=SANS, font_size="12px",
                            color=rx.cond(
                                rx.selected_files("ans_upload").length() > 0,
                                C_TEXT, C_MUTED,
                            ),
                            no_of_lines=1,
                        ),
                        spacing="1", align="center",
                    ),
                    id="ans_upload",
                    accept={".md": ["text/markdown", "text/plain"], ".txt": ["text/plain"]},
                    max_files=1,
                    border=rx.cond(
                        rx.selected_files("ans_upload").length() > 0,
                        "1px dashed rgba(201,35,248,0.40)",
                        f"1px dashed {C_BORDER}",
                    ),
                    border_radius="10px", background="transparent",
                    padding="7px 12px", cursor="pointer", flex="1",
                    _hover={"border_color": "rgba(201,35,248,0.35)"},
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("check", size=13),
                        rx.text("Применить", font_family=SANS, font_size="12px"),
                        spacing="1", align="center",
                    ),
                    on_click=EngrafoState.upload_ans_md(
                        rx.upload_files(upload_id="ans_upload")  # type: ignore
                    ),
                    background=f"linear-gradient(135deg, {C_PURPLE} 0%, #7c3aed 100%)",
                    color="white", border="none", border_radius="10px",
                    font_family=SANS, font_weight="600", font_size="12px",
                    padding="7px 14px", cursor="pointer", flex_shrink="0",
                    _hover={"opacity": "0.85"},
                ),
                spacing="2", align="center", width="100%",
            ),
            spacing="2", width="100%",
            padding="12px", border_radius="10px",
            background="rgba(201,35,248,0.03)",
            border=f"1px solid rgba(201,35,248,0.10)",
        ),

        rx.spacer(),
        rx.dialog.close(
            rx.button(
                "Закрыть",
                on_click=EngrafoState.close_generate_modal,
                background="transparent",
                border=f"1px solid {C_BORDER}",
                border_radius="10px", color=C_MUTED,
                font_family=SANS, padding="8px 0",
                cursor="pointer", width="100%",
                _hover={"background": "rgba(255,255,255,0.06)"},
            ),
        ),
        spacing="3", width="100%", height="100%",
    )

    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # ── Header ────────────────────────────────────────────────
                rx.hstack(
                    rx.box(
                        rx.icon("sparkles", size=18, color=C_PURPLE),
                        background="rgba(201,35,248,0.10)",
                        border_radius="10px", padding="9px",
                        display="flex", align_items="center",
                    ),
                    rx.vstack(
                        rx.dialog.title(
                            "Генерация тегов",
                            font_size="17px", font_weight="700",
                            font_family=SANS, color=C_TEXT, margin="0",
                        ),
                        rx.text("Выберите теги слева — теги из never_generate скрыты",
                                font_size="11px", color=C_MUTED, font_family=SANS),
                        spacing="0", align="start",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.icon("x", size=16, color=C_MUTED, cursor="pointer"),
                        on_click=EngrafoState.close_generate_modal,
                    ),
                    spacing="3", align="center", width="100%",
                ),

                # ── 2-колоночный body ─────────────────────────────────────
                rx.hstack(
                    # Левая: список тегов
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.text("Теги", font_size="10px", font_weight="700",
                                        color=C_MUTED, font_family=SANS,
                                        text_transform="uppercase", letter_spacing="0.8px"),
                                rx.spacer(),
                                rx.hstack(
                                    rx.box(width="8px", height="8px", border_radius="50%",
                                           background=C_GREEN),
                                    rx.text("есть промпт", font_size="9px",
                                            color=C_MUTED, font_family=SANS),
                                    rx.box(width="8px", height="8px", border_radius="50%",
                                           background="#fb923c"),
                                    rx.text("нет промпта", font_size="9px",
                                            color=C_MUTED, font_family=SANS),
                                    spacing="1", align="center",
                                ),
                                align="center", width="100%",
                                padding_bottom="6px",
                                border_bottom=f"1px solid {C_BORDER}",
                            ),
                            rx.box(
                                rx.vstack(
                                    rx.foreach(EngrafoState.generate_tag_rows, _gen_tag_chip),
                                    spacing="1", width="100%",
                                ),
                                overflow_y="auto",
                                flex="1",
                                class_name="hide-scrollbar",
                            ),
                            spacing="2", width="100%", height="100%",
                        ),
                        width="220px",
                        flex_shrink="0",
                        height="420px",
                        padding="14px",
                        background="rgba(255,255,255,0.02)",
                        border=f"1px solid {C_BORDER}",
                        border_radius="14px",
                        display="flex",
                        flex_direction="column",
                    ),

                    # Правая: настройки + кнопки
                    rx.box(
                        rx.cond(is_ai, _right_ai, _right_manual),
                        flex="1",
                        height="420px",
                        padding="14px",
                        background="rgba(255,255,255,0.01)",
                        border=f"1px solid {C_BORDER}",
                        border_radius="14px",
                        display="flex",
                        flex_direction="column",
                    ),

                    spacing="3", align="start", width="100%",
                ),

                spacing="4", width="100%",
            ),
            background=C_CARD,
            border=f"1px solid {C_BORDER}",
            border_radius="20px",
            padding="24px",
            max_width="760px",
            width="94vw",
            backdrop_filter="blur(20px)",
        ),
        open=EngrafoState.show_generate_modal,
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
        rx.el.link(rel="stylesheet", href="/quill.snow.css"),
        rx.el.link(rel="stylesheet", href="/engrafo.css"),
        rx.script(src="/quill.js"),
        rx.script(src="/engrafo_editor.js"),
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
        _global_popup_dialog(),
        _ai_prompt_dialog(),
        _generate_modal(),
        _image_picker(),
        _toasts(),

        # ── Hidden proxies for JS → Reflex sync ───────────────────────────────
        # HTML content proxy: JS writes 'KEY|||html' here on contenteditable blur
        rx.el.textarea(
            id="engrafo-html-proxy",
            on_change=EngrafoState.handle_html_update,
            style={"display": "none"},
            aria_hidden="true",
        ),
        # Hidden file input for image insertion at cursor (handled entirely in JS)
        rx.el.input(
            id="engrafo-img-file-input",
            type="file",
            accept="image/png,image/jpeg,image/webp,image/gif",
            style={"display": "none"},
            aria_hidden="true",
        ),

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
