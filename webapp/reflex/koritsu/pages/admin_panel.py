"""
Route: /sys/d7f3a1b9e2c4 
"""

import reflex as rx
from koritsu.state.admin_state import AdminState
from koritsu.state.balancer_state import BalancerState
from koritsu.components.header import header

# ── Endfield Palette ─────────────────────────────────────────────────────────
BG = "linear-gradient(135deg, #08080f 0%, #0b0f1a 50%, #07101e 100%)"
PANEL = "rgba(15, 18, 30, 0.85)"
PANEL_LIGHT = "rgba(255, 255, 255, 0.03)"
BORDER = "rgba(240, 192, 64, 0.15)"
BORDER_BRIGHT = "rgba(240, 192, 64, 0.35)"
ACCENT = "#f0c040"
ACCENT_DIM = "rgba(240, 192, 64, 0.6)"
ACCENT_GLOW = "rgba(240, 192, 64, 0.15)"
ACCENT_GLOW_STRONG = "rgba(240, 192, 64, 0.25)"
TEXT = "rgba(255, 255, 255, 0.92)"
TEXT_DIM = "rgba(255, 255, 255, 0.45)"
TEXT_MID = "rgba(255, 255, 255, 0.65)"
DANGER = "#f87171"
SUCCESS = "#34d399"
CYAN = "#22d3ee"
PURPLE = "#c084fc"
MONO = "'SF Mono','Fira Code','Cascadia Code','Consolas',monospace"
SANS = "'Rajdhani','Exo 2','Segoe UI',system-ui,sans-serif"

LABEL_STYLE = {
    "font_size": "9px", "letter_spacing": "1.5px", "text_transform": "uppercase",
    "color": TEXT_DIM, "font_family": SANS, "font_weight": "600",
}
INPUT_STYLE = {
    "background": "rgba(255, 255, 255, 0.03)",
    "border": f"1px solid {BORDER}",
    "color": TEXT, "font_family": MONO, "font_size": "12px",
    "border_radius": "2px", "width": "100%",
    "_focus": {"border_color": ACCENT, "box_shadow": f"0 0 0 2px {ACCENT_GLOW}", "outline": "none"},
}


# ── Reusable Components ──────────────────────────────────────────────────────

def corner_brackets(child: rx.Component, **props) -> rx.Component:
    return rx.box(
        rx.box(position="absolute", top="0", left="0", width="14px", height="14px",
               border_top=f"1px solid {ACCENT}", border_left=f"1px solid {ACCENT}"),
        rx.box(position="absolute", top="0", right="0", width="14px", height="14px",
               border_top=f"1px solid {ACCENT}", border_right=f"1px solid {ACCENT}"),
        rx.box(position="absolute", bottom="0", left="0", width="14px", height="14px",
               border_bottom=f"1px solid {ACCENT}", border_left=f"1px solid {ACCENT}"),
        rx.box(position="absolute", bottom="0", right="0", width="14px", height="14px",
               border_bottom=f"1px solid {ACCENT}", border_right=f"1px solid {ACCENT}"),
        child, position="relative", **props,
    )


def section_label(text: str) -> rx.Component:
    return rx.hstack(
        rx.box(width="3px", height="14px", background=ACCENT),
        rx.text(text, font_size="11px", font_weight="700", letter_spacing="2.5px",
                text_transform="uppercase", color=ACCENT, font_family=SANS),
        rx.box(flex="1", height="1px", background=BORDER),
        align_items="center", gap="10px", width="100%",
    )


def stat_box(label: str, value, color: str = ACCENT) -> rx.Component:
    return rx.box(
        rx.text(label, font_size="9px", letter_spacing="1.5px", text_transform="uppercase",
                color=TEXT_DIM, font_family=SANS, font_weight="600"),
        rx.text(value, font_size="28px", font_weight="700", color=color,
                font_family=MONO, line_height="1.1", text_shadow=f"0 0 20px {ACCENT_GLOW}"),
        padding="12px 16px", background=PANEL_LIGHT,
        border=f"1px solid {BORDER}", border_radius="2px", min_width="120px",
    )


def save_button(label: str, on_click, color: str = ACCENT) -> rx.Component:
    return rx.box(
        rx.text(label, font_size="10px", letter_spacing="1.5px", font_weight="700",
                color="#0b0f1a", font_family=SANS),
        padding="8px 16px", background=color, cursor="pointer",
        transition="all 0.2s", _hover={"opacity": "0.85", "box_shadow": f"0 0 16px {ACCENT_GLOW}"},
        on_click=on_click, display="flex", align_items="center",
        justify_content="center", min_width="80px",
    )


def danger_button(label: str, on_click) -> rx.Component:
    return rx.box(
        rx.text(label, font_size="10px", letter_spacing="1.5px", font_weight="700",
                color=TEXT, font_family=SANS),
        padding="8px 16px", background="rgba(248,113,113,0.15)",
        border=f"1px solid {DANGER}", cursor="pointer",
        transition="all 0.2s", _hover={"background": "rgba(248,113,113,0.3)"},
        on_click=on_click, display="flex", align_items="center",
        justify_content="center", min_width="80px",
    )


def field_row(label: str, value_input: rx.Component, action_btn: rx.Component = None) -> rx.Component:
    return rx.hstack(
        rx.vstack(rx.text(label, **LABEL_STYLE), value_input, gap="4px", flex="1"),
        action_btn if action_btn else rx.fragment(),
        align_items="flex-end", gap="10px", width="100%",
    )


def status_badge(status: rx.Var) -> rx.Component:
    return rx.match(
        status,
        ("pending", rx.badge("PENDING", color_scheme="yellow", variant="outline", size="1")),
        ("running", rx.badge("RUNNING", color_scheme="cyan", variant="outline", size="1")),
        ("completed", rx.badge("DONE", color_scheme="green", variant="outline", size="1")),
        ("failed", rx.badge("FAIL", color_scheme="red", variant="outline", size="1")),
        ("expired", rx.badge("EXPIRED", color_scheme="purple", variant="outline", size="1")),
        ("cancelled", rx.badge("CANCEL", color_scheme="gray", variant="outline", size="1")),
        rx.badge(status, variant="outline", size="1"),
    )


def priority_display(priority: rx.Var) -> rx.Component:
    return rx.match(
        priority,
        (0, rx.text("0", color=TEXT_DIM, font_family=MONO, font_size="13px", font_weight="700")),
        (1, rx.text("1", color="#60a5fa", font_family=MONO, font_size="13px", font_weight="700")),
        (2, rx.text("2", color=ACCENT, font_family=MONO, font_size="13px", font_weight="700")),
        (3, rx.text("3", color=DANGER, font_family=MONO, font_size="13px", font_weight="700",
                     text_shadow="0 0 8px rgba(248,113,113,0.4)")),
        rx.text("?", color=TEXT_DIM, font_family=MONO),
    )


# ── Animated Background ──────────────────────────────────────────────────────

def animated_bg() -> rx.Component:
    return rx.fragment(
        rx.box(
            position="fixed", top="0", left="0", right="0", bottom="0",
            background=(
                "linear-gradient(rgba(240,192,64,0.03) 1px, transparent 1px),"
                "linear-gradient(90deg, rgba(240,192,64,0.03) 1px, transparent 1px)"
            ),
            background_size="60px 60px",
            pointer_events="none", z_index="0",
        ),
        rx.box(
            position="fixed", width="300px", height="300px", border_radius="50%",
            background="radial-gradient(circle, rgba(240,192,64,0.06) 0%, transparent 70%)",
            top="10%", left="5%",
            animation="floatOrb1 20s ease-in-out infinite",
            pointer_events="none", z_index="0",
        ),
        rx.box(
            position="fixed", width="400px", height="400px", border_radius="50%",
            background="radial-gradient(circle, rgba(34,211,238,0.04) 0%, transparent 70%)",
            bottom="15%", right="10%",
            animation="floatOrb2 25s ease-in-out infinite",
            pointer_events="none", z_index="0",
        ),
        rx.box(
            position="fixed", top="0", left="-100%",
            width="50%", height="100%",
            background="linear-gradient(90deg, transparent, rgba(240,192,64,0.03), transparent)",
            transform="skewX(-15deg)",
            animation="scanDiag 8s linear infinite",
            pointer_events="none", z_index="0",
        ),
        rx.box(
            position="fixed", top="0", left="0", right="0", bottom="0",
            background="repeating-linear-gradient(transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px)",
            pointer_events="none", z_index="1",
        ),
        rx.el.style("""
            @keyframes floatOrb1 {
                0%, 100% { transform: translate(0, 0) scale(1); }
                25% { transform: translate(80px, 40px) scale(1.1); }
                50% { transform: translate(30px, -60px) scale(0.95); }
                75% { transform: translate(-50px, 20px) scale(1.05); }
            }
            @keyframes floatOrb2 {
                0%, 100% { transform: translate(0, 0) scale(1); }
                33% { transform: translate(-60px, -40px) scale(1.15); }
                66% { transform: translate(40px, 50px) scale(0.9); }
            }
            @keyframes scanDiag {
                0% { left: -50%; }
                100% { left: 150%; }
            }
            @keyframes pulseGlow {
                0%, 100% { opacity: 0.4; }
                50% { opacity: 1; }
            }
            @keyframes dataFlow {
                0% { stroke-dashoffset: 24; }
                100% { stroke-dashoffset: 0; }
            }
            @keyframes dataFlowReverse {
                0% { stroke-dashoffset: 0; }
                100% { stroke-dashoffset: 24; }
            }
            @keyframes nodePulse {
                0%, 100% { box-shadow: 0 0 8px rgba(52,211,153,0.3); }
                50% { box-shadow: 0 0 20px rgba(52,211,153,0.6); }
            }
            @keyframes nodePulseRed {
                0%, 100% { box-shadow: 0 0 8px rgba(248,113,113,0.3); }
                50% { box-shadow: 0 0 20px rgba(248,113,113,0.6); }
            }
        """),
    )


# ══════════════════════════════════════════════════════════════════════════════
#  TAB: TOPOLOGY
# ══════════════════════════════════════════════════════════════════════════════

def topo_node(name: str, icon_name: str, status: rx.Var, latency: rx.Var,
              address: str, color: str, top: str, left: str) -> rx.Component:
    """A single topology node."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(icon_name, size=20, color=color),
                rx.text(name, font_size="12px", font_weight="700", letter_spacing="1.5px",
                        color=TEXT, font_family=SANS),
                align_items="center", gap="8px",
            ),
            rx.text(address, font_size="10px", font_family=MONO, color=TEXT_DIM),
            rx.hstack(
                rx.box(
                    width="8px", height="8px", border_radius="50%",
                    background=rx.cond(
                        status == "online", SUCCESS,
                        rx.cond(status == "offline", DANGER, ACCENT)
                    ),
                    box_shadow=rx.cond(
                        status == "online", f"0 0 8px {SUCCESS}",
                        rx.cond(status == "offline", f"0 0 8px {DANGER}", f"0 0 8px {ACCENT}")
                    ),
                ),
                rx.text(
                    rx.cond(status == "online", "ONLINE",
                            rx.cond(status == "offline", "OFFLINE", "CHECKING...")),
                    font_size="9px", letter_spacing="1px", font_weight="600",
                    font_family=SANS,
                    color=rx.cond(
                        status == "online", SUCCESS,
                        rx.cond(status == "offline", DANGER, ACCENT)
                    ),
                ),
                rx.cond(
                    latency != "",
                    rx.text(latency, font_size="9px", font_family=MONO, color=TEXT_DIM),
                ),
                align_items="center", gap="6px",
            ),
            gap="6px", align_items="flex-start",
        ),
        position="absolute", top=top, left=left,
        padding="16px 20px",
        background=PANEL,
        border=f"1px solid {BORDER}",
        border_radius="2px",
        min_width="200px",
        z_index="5",
        animation=rx.cond(
            status == "online",
            "nodePulse 3s ease-in-out infinite",
            rx.cond(status == "offline", "nodePulseRed 2s ease-in-out infinite", "none")
        ),
    )


def topology_section() -> rx.Component:
    """Live topology view with animated connections."""
    return rx.box(
        section_label("LIVE TOPOLOGY"),
        rx.box(
            # Refresh button
            rx.box(
                rx.hstack(
                    rx.icon("refresh-cw", size=14, color=ACCENT),
                    rx.text("REFRESH", font_size="10px", letter_spacing="1.5px",
                            color=ACCENT, font_family=SANS, font_weight="600"),
                    gap="6px", align_items="center",
                ),
                padding="8px 16px",
                border=f"1px solid {BORDER_BRIGHT}",
                cursor="pointer", transition="all 0.2s",
                _hover={"background": ACCENT_GLOW, "border_color": ACCENT},
                on_click=AdminState.check_topology,
                position="absolute", top="16px", right="16px", z_index="10",
            ),
            # SVG connections
            rx.el.svg(
                # Reflex → FastAPI
                rx.el.line(
                    x1="200", y1="80", x2="420", y2="180",
                    stroke=CYAN, stroke_width="2",
                    stroke_dasharray="8 4",
                    style={"animation": "dataFlow 1s linear infinite"},
                ),
                # FastAPI → DB
                rx.el.line(
                    x1="580", y1="180", x2="750", y2="80",
                    stroke=SUCCESS, stroke_width="2",
                    stroke_dasharray="8 4",
                    style={"animation": "dataFlow 1.5s linear infinite"},
                ),
                # FastAPI → AI Cloud
                rx.el.line(
                    x1="580", y1="210", x2="750", y2="310",
                    stroke=PURPLE, stroke_width="2",
                    stroke_dasharray="8 4",
                    style={"animation": "dataFlowReverse 2s linear infinite"},
                ),
                # Arrow labels
                rx.el.text("HTTP", x="290", y="120",
                           fill=CYAN, font_size="9", font_family="monospace", opacity="0.7"),
                rx.el.text("SQL", x="660", y="120",
                           fill=SUCCESS, font_size="9", font_family="monospace", opacity="0.7"),
                rx.el.text("API", x="660", y="270",
                           fill=PURPLE, font_size="9", font_family="monospace", opacity="0.7"),
                width="100%", height="100%",
                position="absolute", top="0", left="0",
                pointer_events="none", z_index="2",
            ),
            # Nodes
            topo_node("REFLEX FRONTEND", "monitor",
                      AdminState.topo_reflex_status, AdminState.topo_reflex_latency,
                      "localhost:3000", CYAN, "30px", "20px"),
            topo_node("FASTAPI SERVER", "server",
                      AdminState.topo_fastapi_status, AdminState.topo_fastapi_latency,
                      "localhost:8001", ACCENT, "140px", "350px"),
            topo_node("SQLITE DATABASE", "database",
                      AdminState.topo_db_status, rx.cond(True, "", ""),
                      "koritsu.db", SUCCESS, "30px", "680px"),
            topo_node("AI CLOUD", "cloud",
                      AdminState.topo_ai_status, AdminState.topo_ai_latency,
                      "Yandex AI Studio", PURPLE, "270px", "680px"),
            position="relative",
            width="100%",
            height="420px",
            background=PANEL,
            border=f"1px solid {BORDER}",
            margin_top="12px",
            overflow="hidden",
        ),
        width="100%",
    )


# ══════════════════════════════════════════════════════════════════════════════
#  TAB: BALANCER
# ══════════════════════════════════════════════════════════════════════════════

def filter_tab(label: str, value: str) -> rx.Component:
    is_active = BalancerState.status_filter == value
    return rx.box(
        rx.text(label, font_size="10px", letter_spacing="1.5px", font_weight="600",
                font_family=SANS, color=rx.cond(is_active, ACCENT, TEXT_DIM)),
        padding="6px 14px", cursor="pointer",
        border_bottom=rx.cond(is_active, f"2px solid {ACCENT}", "2px solid transparent"),
        transition="all 0.2s", _hover={"background": ACCENT_GLOW},
        on_click=BalancerState.set_filter(value),
    )


def task_row(task: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.box(priority_display(task["priority"]), min_width="30px", text_align="center"),
        rx.text(task["task_uuid"].to(str)[:8], font_family=MONO, font_size="12px",
                color=TEXT_MID, min_width="80px"),
        rx.box(status_badge(task["status"]), min_width="80px"),
        rx.text(task["task_dest"], font_family=MONO, font_size="12px", color=CYAN, min_width="80px"),
        rx.text(task["username"], font_size="12px", color=TEXT_MID, font_family=SANS, min_width="100px"),
        rx.spacer(),
        rx.cond(
            (task["status"] == "pending") | (task["status"] == "running"),
            rx.box(
                rx.icon("x", size=12, color=DANGER),
                padding="4px", cursor="pointer",
                border=f"1px solid rgba(248,113,113,0.2)",
                _hover={"background": "rgba(248,113,113,0.1)", "border_color": DANGER},
                on_click=BalancerState.cancel_task(task["task_uuid"]),
            ),
        ),
        rx.box(
            rx.icon("chevron-right", size=14, color=TEXT_DIM),
            padding="4px", cursor="pointer", _hover={"background": ACCENT_GLOW},
            on_click=BalancerState.select_task(task),
        ),
        width="100%", padding="10px 16px", align_items="center", gap="12px",
        background=PANEL_LIGHT, border_bottom="1px solid rgba(255,255,255,0.04)",
        transition="all 0.15s", _hover={"background": "rgba(240, 192, 64, 0.04)"},
    )


def balancer_section() -> rx.Component:
    return rx.vstack(
        # Stats
        rx.hstack(
            stat_box("Total", BalancerState.total_count),
            stat_box("Pending", BalancerState.pending_count, color="#f0c040"),
            stat_box("Running", BalancerState.running_count, color=CYAN),
            stat_box("Done", BalancerState.done_count, color=SUCCESS),
            stat_box("Failed", BalancerState.failed_count, color=DANGER),
            gap="12px", width="100%", overflow_x="auto", flex_wrap="wrap",
        ),
        # Search
        rx.hstack(
            rx.icon("search", size=16, color=TEXT_DIM),
            rx.input(
                value=BalancerState.search_query,
                on_change=BalancerState.set_search,
                placeholder="Search by UUID, username, destination...",
                background="transparent", border="none", color=TEXT,
                font_family=MONO, font_size="12px", width="100%", outline="none",
                _focus={"outline": "none", "box_shadow": "none"},
                _placeholder={"color": TEXT_DIM},
            ),
            rx.cond(
                BalancerState.search_query != "",
                rx.box(
                    rx.icon("x", size=12, color=TEXT_DIM),
                    cursor="pointer", padding="4px",
                    _hover={"background": ACCENT_GLOW},
                    on_click=BalancerState.set_search(""),
                ),
            ),
            rx.box(
                rx.hstack(
                    rx.icon("refresh-cw", size=14, color=ACCENT),
                    rx.text("REFRESH", font_size="10px", letter_spacing="1.5px",
                            color=ACCENT, font_family=SANS, font_weight="600"),
                    gap="6px", align_items="center",
                ),
                padding="8px 16px", border=f"1px solid {BORDER_BRIGHT}",
                cursor="pointer", transition="all 0.2s",
                _hover={"background": ACCENT_GLOW, "border_color": ACCENT},
                on_click=BalancerState.load_tasks,
            ),
            width="100%", padding="10px 16px", background=PANEL,
            border=f"1px solid {BORDER}", align_items="center", gap="10px",
            _focus_within={"border_color": ACCENT, "box_shadow": f"0 0 0 2px {ACCENT_GLOW}"},
        ),
        # Filters
        rx.hstack(
            filter_tab("ALL", "all"),
            rx.box(width="1px", height="20px", background=BORDER),
            filter_tab("PENDING", "pending"),
            filter_tab("RUNNING", "running"),
            filter_tab("DONE", "completed"),
            filter_tab("FAILED", "failed"),
            filter_tab("EXPIRED", "expired"),
            filter_tab("CANCELLED", "cancelled"),
            gap="4px", align_items="center", overflow_x="auto", width="100%",
        ),
        # Task list
        rx.box(
            section_label("TASK QUEUE"),
            rx.box(
                corner_brackets(
                    rx.vstack(
                        # Table header
                        rx.hstack(
                            *[rx.text(label, font_size="9px", letter_spacing="1.5px", color=TEXT_DIM,
                                      font_family=SANS, font_weight="600", min_width=w)
                              for label, w in [("PRI", "30px"), ("UUID", "80px"), ("STATUS", "80px"),
                                               ("DEST", "80px"), ("USER", "100px")]],
                            width="100%", padding="8px 16px", gap="12px",
                            border_bottom=f"1px solid {BORDER}",
                        ),
                        rx.cond(
                            BalancerState.filtered_tasks.length() > 0,
                            rx.vstack(
                                rx.foreach(BalancerState.filtered_tasks, task_row),
                                width="100%", gap="0",
                            ),
                            rx.center(
                                rx.vstack(
                                    rx.icon("inbox", size=32, color=TEXT_DIM),
                                    rx.text("NO TASKS FOUND", font_size="11px", letter_spacing="2px",
                                            color=TEXT_DIM, font_family=SANS),
                                    align_items="center", gap="8px",
                                ),
                                padding="48px",
                            ),
                        ),
                        width="100%", gap="0", max_height="600px", overflow_y="auto",
                    ),
                    padding="4px", background=PANEL, border=f"1px solid {BORDER}",
                ),
                margin_top="12px",
            ),
            width="100%",
        ),
        gap="16px", width="100%",
    )


def detail_modal() -> rx.Component:
    row_style = {"font_size": "12px", "font_family": MONO, "color": TEXT}
    lbl = {"font_size": "9px", "letter_spacing": "1.5px", "text_transform": "uppercase",
           "color": TEXT_DIM, "font_family": SANS, "font_weight": "600", "min_width": "80px"}
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.hstack(
                        rx.box(width="3px", height="16px", background=ACCENT),
                        rx.text("TASK DETAIL", font_size="13px", letter_spacing="2px",
                                font_weight="700", color=ACCENT, font_family=SANS),
                        gap="8px", align_items="center",
                    ),
                    rx.spacer(),
                    rx.dialog.close(rx.icon("x", size=16, color=TEXT_DIM, cursor="pointer")),
                    width="100%", align_items="center",
                ),
            ),
            rx.separator(color=BORDER),
            rx.vstack(
                rx.hstack(rx.text("UUID", **lbl),
                          rx.text(BalancerState.selected_task["task_uuid"].to(str), **row_style),
                          align_items="baseline"),
                rx.hstack(rx.text("STATUS", **lbl),
                          status_badge(BalancerState.selected_task["status"].to(str)),
                          align_items="center"),
                rx.hstack(rx.text("PRIORITY", **lbl),
                          priority_display(BalancerState.selected_task["priority"].to(int)),
                          align_items="center"),
                rx.hstack(rx.text("DEST", **lbl),
                          rx.text(BalancerState.selected_task["task_dest"].to(str),
                                  color=CYAN, font_size="12px", font_family=MONO),
                          align_items="baseline"),
                rx.hstack(rx.text("USER", **lbl),
                          rx.text(BalancerState.selected_task["username"].to(str), **row_style),
                          align_items="baseline"),
                rx.hstack(rx.text("ANSW TO", **lbl),
                          rx.text(BalancerState.selected_task["answ_to"].to(str), **row_style),
                          align_items="baseline"),
                rx.cond(
                    BalancerState.selected_task.get("error", None),
                    rx.hstack(rx.text("ERROR", **lbl),
                              rx.text(BalancerState.selected_task["error"].to(str),
                                      color=DANGER, font_size="12px", font_family=MONO),
                              align_items="baseline"),
                ),
                rx.cond(
                    BalancerState.selected_task_result_str != "",
                    rx.vstack(
                        rx.text("RESULT", **lbl),
                        rx.box(
                            rx.text(BalancerState.selected_task_result_str,
                                    font_size="11px", font_family=MONO, color=SUCCESS,
                                    white_space="pre-wrap", word_break="break-all"),
                            padding="8px", background="rgba(255,255,255,0.02)",
                            border=f"1px solid {BORDER}", width="100%",
                            max_height="200px", overflow_y="auto",
                        ),
                        gap="4px", width="100%",
                    ),
                ),
                gap="10px", padding="12px 0", width="100%",
            ),
            background="#0d1020", border=f"1px solid {BORDER_BRIGHT}",
            box_shadow=f"0 0 40px rgba(0,0,0,0.8), 0 0 80px {ACCENT_GLOW}",
            max_width="520px",
        ),
        open=BalancerState.show_detail,
        on_open_change=lambda v: BalancerState.set_show_detail(v),
    )


# ══════════════════════════════════════════════════════════════════════════════
#  TAB: USER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════



def search_results_list() -> rx.Component:
    """Show multiple results from username search."""
    def result_row(user: rx.Var) -> rx.Component:
        return rx.hstack(
            rx.vstack(
                rx.text(user["username"], font_size="13px", font_family=MONO, color=TEXT,
                        font_weight="600"),
                rx.text(user["uuid"], font_size="10px", font_family=MONO, color=TEXT_DIM),
                gap="2px",
            ),
            rx.spacer(),
            rx.hstack(
                rx.cond(
                    user["is_banned"].to(int) == 1,
                    rx.badge("BANNED", color_scheme="red", variant="outline", size="1"),
                ),
                rx.text(user["sub_level"], font_size="10px", font_family=MONO, color=CYAN),
                align_items="center", gap="6px",
            ),
            rx.box(
                rx.icon("arrow-right", size=14, color=ACCENT),
                padding="4px", cursor="pointer",
                _hover={"background": ACCENT_GLOW},
                on_click=AdminState.select_search_result(user["uuid"]),
            ),
            width="100%", padding="10px 16px", align_items="center",
            background=PANEL_LIGHT, border_bottom="1px solid rgba(255,255,255,0.04)",
            transition="all 0.15s", _hover={"background": "rgba(240, 192, 64, 0.04)"},
        )

    return rx.cond(
        AdminState.search_results.length() > 0,
        rx.box(
            section_label(f"SEARCH RESULTS"),
            corner_brackets(
                rx.vstack(
                    rx.foreach(AdminState.search_results, result_row),
                    width="100%", gap="0", max_height="300px", overflow_y="auto",
                ),
                padding="4px", background=PANEL, border=f"1px solid {BORDER}",
            ),
            margin_top="12px", width="100%",
        ),
    )


def user_search_panel() -> rx.Component:
    return rx.box(
        section_label("FIND USER"),
        rx.vstack(
            rx.hstack(
                rx.icon("search", size=16, color=TEXT_DIM),
                rx.input(
                    value=AdminState.search_query,
                    on_change=AdminState.set_search_query,
                    placeholder="UUID or username...",
                    background="transparent", border="none", color=TEXT,
                    font_family=MONO, font_size="12px", width="100%", outline="none",
                    _focus={"outline": "none", "box_shadow": "none"},
                    _placeholder={"color": TEXT_DIM},
                    on_key_down=lambda e: rx.cond(e == "Enter", AdminState.search_user, None),
                ),
                save_button("SEARCH", AdminState.search_user),
                width="100%", padding="8px 14px", background=PANEL,
                border=f"1px solid {BORDER}", align_items="center", gap="10px",
                _focus_within={"border_color": ACCENT, "box_shadow": f"0 0 0 2px {ACCENT_GLOW}"},
            ),
            rx.text(
                "Auto-detects UUID format. Otherwise searches by username.",
                font_size="9px", color=TEXT_DIM, font_family=MONO,
            ),
            rx.cond(
                AdminState.search_error != "",
                rx.text(AdminState.search_error, font_size="11px", color=DANGER, font_family=MONO),
            ),
            gap="8px",
        ),
        search_results_list(),
        width="100%",
    )


def user_info_card() -> rx.Component:
    def info_row(label: str, value) -> rx.Component:
        return rx.hstack(
            rx.text(label, min_width="100px", **LABEL_STYLE),
            rx.text(value, font_size="12px", font_family=MONO, color=TEXT),
            align_items="baseline",
        )

    return rx.box(
        section_label("USER INFO"),
        corner_brackets(
            rx.vstack(
                info_row("UUID", AdminState.user_uuid),
                info_row("USERNAME", AdminState.username),
                info_row("DISPLAY", AdminState.display_name),
                info_row("SUB LEVEL", AdminState.sub_level),
                info_row("EXPIRES", AdminState.sub_expire_date),
                info_row("TOKENS", AdminState.tokens_left),
                rx.cond(
                    AdminState.is_banned == 1,
                    rx.vstack(
                        rx.hstack(
                            rx.text("STATUS", min_width="100px", **LABEL_STYLE),
                            rx.badge("BANNED", color_scheme="red", variant="solid", size="1"),
                            align_items="center",
                        ),
                        rx.cond(
                            AdminState.ban_reason != "",
                            rx.hstack(
                                rx.text("BAN REASON", min_width="100px", **LABEL_STYLE),
                                rx.text(AdminState.ban_reason, font_size="12px", font_family=MONO,
                                        color=DANGER),
                                align_items="baseline",
                            ),
                        ),
                        rx.cond(
                            AdminState.ban_until != "",
                            rx.hstack(
                                rx.text("BAN UNTIL", min_width="100px", **LABEL_STYLE),
                                rx.text(AdminState.ban_until, font_size="12px", font_family=MONO,
                                        color=DANGER),
                                align_items="baseline",
                            ),
                        ),
                        gap="8px", width="100%",
                    ),
                ),
                gap="8px", width="100%",
            ),
            padding="20px", background=PANEL, border=f"1px solid {BORDER}",
        ),
        margin_top="12px", width="100%",
    )


def user_edit_panel() -> rx.Component:
    return rx.box(
        section_label("EDIT USER"),
        corner_brackets(
            rx.vstack(
                # Username
                field_row("USERNAME",
                          rx.input(value=AdminState.edit_username,
                                   on_change=AdminState.set_edit_username, **INPUT_STYLE),
                          save_button("SAVE", AdminState.save_username)),
                # Display name
                field_row("DISPLAY NAME",
                          rx.input(value=AdminState.edit_display_name,
                                   on_change=AdminState.set_edit_display_name, **INPUT_STYLE),
                          save_button("SAVE", AdminState.save_display_name)),
                # Tokens
                field_row("TOKENS",
                          rx.input(value=AdminState.edit_tokens,
                                   on_change=AdminState.set_edit_tokens, **INPUT_STYLE),
                          save_button("SET", AdminState.save_tokens)),
                # Sub level
                field_row("SUB LEVEL",
                          rx.select(
                              ["free", "basic", "pro", "enterprise"],
                              value=AdminState.edit_sub_level,
                              on_change=AdminState.set_edit_sub_level,
                              width="100%",
                          ),
                          save_button("SET", AdminState.save_sub_level)),
                # Password reset
                field_row("NEW PASSWORD",
                          rx.input(value=AdminState.edit_password,
                                   on_change=AdminState.set_edit_password,
                                   placeholder="Enter new password...",
                                   type="password", **INPUT_STYLE),
                          save_button("RESET", AdminState.reset_password)),
                # Feedback
                rx.cond(AdminState.save_success != "",
                        rx.text(AdminState.save_success, font_size="11px",
                                color=SUCCESS, font_family=MONO)),
                rx.cond(AdminState.save_error != "",
                        rx.text(AdminState.save_error, font_size="11px",
                                color=DANGER, font_family=MONO)),
                gap="16px", padding="20px", width="100%",
            ),
            background=PANEL, border=f"1px solid {BORDER}",
        ),
        margin_top="12px", width="100%",
    )


def user_danger_zone() -> rx.Component:
    return rx.box(
        section_label("DANGER ZONE"),
        corner_brackets(
            rx.vstack(
                # Ban section
                rx.cond(
                    AdminState.is_banned == 1,
                    # Unban
                    rx.hstack(
                        rx.vstack(
                            rx.text("USER IS BANNED", font_size="12px", font_weight="700",
                                    color=DANGER, font_family=SANS, letter_spacing="1px"),
                            rx.text("Click unban to restore access",
                                    font_size="10px", color=TEXT_DIM, font_family=MONO),
                            gap="2px",
                        ),
                        rx.spacer(),
                        save_button("UNBAN", AdminState.unban_user, color=SUCCESS),
                        width="100%", align_items="center",
                    ),
                    # Ban controls
                    rx.vstack(
                        rx.hstack(
                            rx.vstack(
                                rx.text("BAN REASON", **LABEL_STYLE),
                                rx.input(value=AdminState.ban_reason_input,
                                         on_change=AdminState.set_ban_reason_input,
                                         placeholder="Reason (optional)...", **INPUT_STYLE),
                                gap="4px", flex="1",
                            ),
                            rx.vstack(
                                rx.text("TIMEOUT (MIN)", **LABEL_STYLE),
                                rx.input(value=AdminState.ban_timeout_minutes,
                                         on_change=AdminState.set_ban_timeout_minutes,
                                         placeholder="0 = permanent", **INPUT_STYLE),
                                gap="4px", width="140px",
                            ),
                            danger_button("BAN", AdminState.ban_user),
                            align_items="flex-end", gap="10px", width="100%",
                        ),
                        gap="8px", width="100%",
                    ),
                ),
                # Separator
                rx.box(width="100%", height="1px", background=BORDER, margin_y="8px"),
                # Delete section
                rx.cond(
                    AdminState.show_delete_confirm,
                    rx.hstack(
                        rx.text("ARE YOU SURE? THIS IS IRREVERSIBLE",
                                font_size="11px", color=DANGER, font_family=MONO,
                                font_weight="700", letter_spacing="1px"),
                        rx.spacer(),
                        danger_button("YES, DELETE", AdminState.delete_user),
                        rx.box(
                            rx.text("CANCEL", font_size="10px", letter_spacing="1.5px",
                                    font_weight="700", color=TEXT_DIM, font_family=SANS),
                            padding="8px 16px", border=f"1px solid {BORDER}",
                            cursor="pointer", transition="all 0.2s",
                            _hover={"background": ACCENT_GLOW},
                            on_click=AdminState.toggle_delete_confirm,
                        ),
                        width="100%", align_items="center", gap="10px",
                    ),
                    rx.hstack(
                        rx.vstack(
                            rx.text("DELETE USER", font_size="12px", font_weight="700",
                                    color=DANGER, font_family=SANS, letter_spacing="1px"),
                            rx.text("Permanently remove user and all their data",
                                    font_size="10px", color=TEXT_DIM, font_family=MONO),
                            gap="2px",
                        ),
                        rx.spacer(),
                        danger_button("DELETE", AdminState.toggle_delete_confirm),
                        width="100%", align_items="center",
                    ),
                ),
                gap="12px", padding="20px", width="100%",
            ),
            background="rgba(248,113,113,0.03)", border=f"1px solid rgba(248,113,113,0.2)",
        ),
        margin_top="12px", width="100%",
    )


def users_section() -> rx.Component:
    return rx.vstack(
        user_search_panel(),
        rx.cond(
            AdminState.user_loaded,
            rx.vstack(
                user_info_card(),
                user_edit_panel(),
                user_danger_zone(),
                gap="20px", width="100%",
            ),
        ),
        gap="20px", width="100%", max_width="750px",
    )


# ══════════════════════════════════════════════════════════════════════════════
#  TAB NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════

def tab_button(label: str, value: str, icon_name: str) -> rx.Component:
    is_active = AdminState.active_tab == value
    return rx.box(
        rx.hstack(
            rx.icon(icon_name, size=16,
                    color=rx.cond(is_active, ACCENT, TEXT_DIM)),
            rx.text(label, font_size="11px", letter_spacing="2px", font_weight="700",
                    font_family=SANS, color=rx.cond(is_active, ACCENT, TEXT_DIM)),
            gap="8px", align_items="center",
        ),
        padding="12px 24px", cursor="pointer",
        border_bottom=rx.cond(is_active, f"2px solid {ACCENT}", "2px solid transparent"),
        background=rx.cond(is_active, ACCENT_GLOW, "transparent"),
        transition="all 0.2s",
        _hover={"background": ACCENT_GLOW},
        on_click=AdminState.set_active_tab(value),
    )


def tab_bar() -> rx.Component:
    return rx.hstack(
        tab_button("TOPOLOGY", "topology", "network"),
        tab_button("BALANCER", "balancer", "list-checks"),
        tab_button("USERS", "users", "users"),
        gap="0", width="100%",
        border_bottom=f"1px solid {BORDER}",
        overflow_x="auto",
    )


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN PAGE
# ══════════════════════════════════════════════════════════════════════════════

def admin_panel_page() -> rx.Component:
    return rx.box(
        animated_bg(),
        header(show_nav_links=True),
        rx.vstack(
            # Header
            rx.hstack(
                rx.hstack(
                    rx.hstack(
                        rx.box(width="3px", height="28px", background=DANGER),
                        rx.box(width="3px", height="28px", background=ACCENT),
                        rx.box(width="3px", height="28px", background=CYAN),
                        gap="2px",
                    ),
                    rx.vstack(
                        rx.text("CONTROL CENTER", font_size="20px", font_weight="700",
                                letter_spacing="3px", color=TEXT, font_family=SANS),
                        rx.text("ADMIN PANEL // RESTRICTED ACCESS", font_size="9px",
                                letter_spacing="2px", color=DANGER, font_family=MONO),
                        gap="0",
                    ),
                    align_items="center", gap="14px",
                ),
                width="100%", padding="20px 28px", align_items="center",
                position="relative", z_index="10",
            ),
            # Warning banner
            rx.hstack(
                rx.icon("triangle-alert", size=16, color=ACCENT),
                rx.text(
                    "ADMIN ACCESS — DO NOT EXPOSE THIS URL IN PRODUCTION.",
                    font_size="10px", letter_spacing="1px", color=ACCENT,
                    font_family=MONO, font_weight="600",
                ),
                padding="10px 20px", background="rgba(240,192,64,0.06)",
                border=f"1px solid {BORDER_BRIGHT}", align_items="center",
                gap="10px", width="100%", margin_x="28px",
                position="relative", z_index="10",
            ),
            # Tabs
            rx.box(
                tab_bar(),
                padding="0 28px", width="100%",
                position="relative", z_index="10",
            ),
            # Content
            rx.box(
                rx.match(
                    AdminState.active_tab,
                    ("topology", topology_section()),
                    ("balancer", balancer_section()),
                    ("users", users_section()),
                    topology_section(),
                ),
                padding="20px 28px 40px 28px",
                width="100%",
                position="relative",
                z_index="10",
            ),
            width="100%", min_height="100vh", gap="0",
            padding_top="56px",
        ),
        detail_modal(),
        background=BG, min_height="100vh",
        position="relative", overflow="hidden",
    )
