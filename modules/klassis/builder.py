"""
Builder — генерирует draw.io XML для UML-диаграммы классов.
"""
import html as _html
import re as _re
from extractor import ClassInfo, FieldInfo, MethodInfo  # type: ignore

# ── Layout constants ───────────────────────────────────────────────────────────
CLASS_W     = 260   # ширина блока класса (px)
H_GAP       = 70    # горизонтальный отступ между классами
V_GAP       = 90    # вертикальный отступ между рядами
HEADER_H    = 32    # высота заголовка swimlane
ROW_H       = 22    # высота строки (поле/метод)
SEP_H       = 8     # разделитель полей/методов
MIN_H       = 70    # минимальная высота блока
START_X     = 40
START_Y     = 40
MAX_PER_ROW = 4     # макс. классов в одном ряду

# ── Dark-theme palette ─────────────────────────────────────────────────────────
_CLASS_FILL    = "#1e293b"
_IFACE_FILL    = "#0f1729"
_STRUCT_FILL   = "#172033"
_CLASS_STROKE  = "#475569"
_IFACE_STROKE  = "#6366f1"
_STRUCT_STROKE = "#0ea5e9"
_HEADER_FONT   = "#f1f5f9"
_MEMBER_FONT   = "#94a3b8"
_EDGE_COLOR    = "#64748b"

_ACCESS = {"public": "+", "protected": "#", "private": "-", "internal": "~"}

# ── Relationship types ─────────────────────────────────────────────────────────
# INHERITANCE  — class A : B           → hollow triangle, solid line
# REALIZATION  — class A : IB          → hollow triangle, dashed line
# COMPOSITION  — field "B b"           → filled diamond
# AGGREGATION  — field "B* b" / "B& b" → hollow diamond
# DEPENDENCY   — method param/return B → dashed open arrow

_COLOR_INHERIT  = "#60a5fa"   # blue     — наследование
_COLOR_REALIZE  = "#a78bfa"   # violet   — реализация интерфейса
_COLOR_COMPOSE  = "#34d399"   # teal     — композиция
_COLOR_AGGREGATE= "#fbbf24"   # amber    — агрегация
_COLOR_DEPEND   = "#94a3b8"   # slate    — зависимость


def _esc(s: str) -> str:
    return _html.escape(s, quote=True)


def _bare_type(type_str: str) -> str:
    """Extract bare class name from a C++ type string.
    'QList<Employee>' → 'Employee'
    'Database*'       → 'Database'
    'const Foo&'      → 'Foo'
    """
    s = type_str
    # Remove const/volatile/static/mutable
    s = _re.sub(r'\b(const|volatile|static|mutable|explicit|inline)\b', '', s)
    # Extract template argument if present (e.g. QList<Employee> → Employee)
    m = _re.search(r'<([^<>]+)>', s)
    if m:
        s = m.group(1)
    # Strip pointer/ref/array markers and whitespace
    s = _re.sub(r'[*&\[\]\s]', '', s)
    return s.strip()


def _method_types(mth: MethodInfo) -> list[str]:
    """Collect all bare type names referenced in a method signature."""
    types = []
    if mth.return_type:
        types.append(_bare_type(mth.return_type))
    # Parse params: split by comma, strip leading type from each
    params = mth.params.strip("()")
    for part in params.split(","):
        part = part.strip()
        if not part:
            continue
        # Take everything before the last word (which is the param name)
        tokens = part.split()
        if len(tokens) >= 2:
            type_part = " ".join(tokens[:-1])
        else:
            type_part = tokens[0] if tokens else ""
        types.append(_bare_type(type_part))
    return [t for t in types if t]


def _is_pointer_or_ref(type_str: str) -> bool:
    return bool(_re.search(r'[*&]', type_str))


def _detect_relations(classes: list[ClassInfo]) -> list[tuple[str, str, str]]:
    """
    Returns list of (source_name, target_name, rel_type).
    rel_type: "inheritance" | "realization" | "composition" | "aggregation" | "dependency"
    Priority: inheritance > composition > aggregation > dependency
    (no duplicates per source→target pair, highest priority wins)
    """
    names = {c.name for c in classes}
    by_name = {c.name: c for c in classes}
    # (src, tgt) → best priority seen so far (lower = higher priority)
    PRIO = {"inheritance": 0, "realization": 1,
            "composition": 2, "aggregation": 3, "dependency": 4}
    best: dict[tuple[str, str], str] = {}

    def _add(src: str, tgt: str, rel: str):
        if tgt not in names or tgt == src:
            return
        key = (src, tgt)
        if key not in best or PRIO[rel] < PRIO[best[key]]:
            best[key] = rel

    for cls in classes:
        src = cls.name
        tgt_cls_map = by_name

        # 1. Inheritance / realization
        for parent in cls.parents:
            if parent not in names:
                continue
            parent_cls = by_name.get(parent)
            if parent_cls and parent_cls.is_interface:
                _add(src, parent, "realization")
            else:
                _add(src, parent, "inheritance")

        # 2. Fields → composition or aggregation
        for fld in cls.fields:
            tgt = _bare_type(fld.type_str)
            if tgt not in names or tgt == src:
                continue
            if _is_pointer_or_ref(fld.type_str):
                _add(src, tgt, "aggregation")
            else:
                _add(src, tgt, "composition")

        # 3. Methods → dependency
        for mth in cls.methods:
            for tgt in _method_types(mth):
                if tgt not in names or tgt == src:
                    continue
                _add(src, tgt, "dependency")

    return [(src, tgt, rel) for (src, tgt), rel in best.items()]


def _edge_side(sx: int, sy: int, sw: int, sh: int,
               tx: int, ty: int, tw: int, th: int) -> tuple[str, str]:
    """Return (exit_side, entry_side) based on relative positions of two boxes."""
    src_cx = sx + sw / 2
    src_cy = sy + sh / 2
    tgt_cx = tx + tw / 2
    tgt_cy = ty + th / 2
    dx = tgt_cx - src_cx
    dy = tgt_cy - src_cy
    if abs(dy) >= abs(dx):
        return ("top", "bottom") if dy <= 0 else ("bottom", "top")
    else:
        return ("left", "right") if dx <= 0 else ("right", "left")


def _assign_ports(
    relations: list[tuple[str, str, str]],
    positions: dict[str, tuple[int, int]],
    by_name: dict,
) -> dict[tuple[str, str], tuple[float, float, float, float]]:
    """
    For each relation assigns (exitX, exitY, entryX, entryY) so that multiple
    arrows leaving/entering the same side of a class are spread out evenly.
    """
    exit_map: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
    entry_map: dict[tuple[str, str], list[tuple[str, str, str]]] = {}

    for src, tgt, rel in relations:
        if src not in positions or tgt not in positions:
            continue
        sx, sy = positions[src]
        tx, ty = positions[tgt]
        sh = _class_height(by_name[src])
        th = _class_height(by_name[tgt])
        ex_side, en_side = _edge_side(sx, sy, CLASS_W, sh, tx, ty, CLASS_W, th)
        exit_map.setdefault((src, ex_side), []).append((src, tgt, rel))
        entry_map.setdefault((tgt, en_side), []).append((src, tgt, rel))

    def _frac(side: str, f: float) -> tuple[float, float]:
        if side == "top":    return (f, 0.0)
        if side == "bottom": return (f, 1.0)
        if side == "left":   return (0.0, f)
        return (1.0, f)  # right

    exit_frac:  dict[tuple[str, str], tuple[float, float]] = {}
    entry_frac: dict[tuple[str, str], tuple[float, float]] = {}

    for (cls, side), edges in exit_map.items():
        n = len(edges)
        for i, (s, t, _r) in enumerate(edges):
            exit_frac[(s, t)] = _frac(side, (i + 1) / (n + 1))

    for (cls, side), edges in entry_map.items():
        n = len(edges)
        for i, (s, t, _r) in enumerate(edges):
            entry_frac[(s, t)] = _frac(side, (i + 1) / (n + 1))

    result: dict[tuple[str, str], tuple[float, float, float, float]] = {}
    for src, tgt, _rel in relations:
        ex, ey = exit_frac.get((src, tgt), (0.5, 1.0))
        nx, ny = entry_frac.get((src, tgt), (0.5, 0.0))
        result[(src, tgt)] = (ex, ey, nx, ny)
    return result


def _edge_style(rel: str, color: str,
                ex: float, ey: float,
                nx: float, ny: float) -> str:
    """Return a draw.io edge style string for the given UML relationship."""
    pts = (
        f"exitX={ex:.3f};exitY={ey:.3f};exitDx=0;exitDy=0;"
        f"entryX={nx:.3f};entryY={ny:.3f};entryDx=0;entryDy=0;"
    )
    base = f"html=1;rounded=0;{pts}strokeColor={color};strokeWidth=1.5;"
    if rel == "inheritance":
        return base + "endArrow=block;endFill=0;startArrow=none;"
    if rel == "realization":
        return base + "endArrow=block;endFill=0;startArrow=none;dashed=1;"
    if rel == "composition":
        return base + "startArrow=diamond;startFill=1;endArrow=none;"
    if rel == "aggregation":
        return base + "startArrow=diamond;startFill=0;endArrow=none;"
    # dependency
    return base + "endArrow=open;endFill=0;dashed=1;startArrow=none;"


def _class_height(cls: ClassInfo) -> int:
    h = HEADER_H
    if cls.fields:
        h += len(cls.fields) * ROW_H
    if cls.fields and cls.methods:
        h += SEP_H
    if cls.methods:
        h += len(cls.methods) * ROW_H
    return max(h, MIN_H)


# ── Topological layout ─────────────────────────────────────────────────────────

def _layout(classes: list[ClassInfo]) -> dict[str, tuple[int, int]]:
    names = {c.name for c in classes}
    by_name = {c.name: c for c in classes}

    # Build parent→children map (only within diagram)
    children: dict[str, list[str]] = {c.name: [] for c in classes}
    parents_in: dict[str, list[str]] = {}
    for cls in classes:
        in_diag = [p for p in cls.parents if p in names]
        parents_in[cls.name] = in_diag
        for p in in_diag:
            children[p].append(cls.name)

    # BFS to assign levels (inheritance depth)
    levels: dict[str, int] = {}
    roots = [c.name for c in classes if not parents_in.get(c.name)]
    queue = list(roots)
    for n in queue:
        levels[n] = 0

    visited = set(queue)
    while queue:
        nxt = []
        for n in queue:
            for child in children.get(n, []):
                lvl = levels[n] + 1
                if levels.get(child, -1) < lvl:
                    levels[child] = lvl
                if child not in visited:
                    visited.add(child)
                    nxt.append(child)
        queue = nxt

    # Any unvisited (disconnected/circular) → level 0
    for cls in classes:
        if cls.name not in levels:
            levels[cls.name] = 0

    # Group by level
    groups: dict[int, list[str]] = {}
    for n, lvl in levels.items():
        groups.setdefault(lvl, []).append(n)

    positions: dict[str, tuple[int, int]] = {}
    current_y = START_Y

    for lvl in sorted(groups):
        group = groups[lvl]
        # Split into sub-rows of MAX_PER_ROW
        for row_start in range(0, len(group), MAX_PER_ROW):
            sub = group[row_start: row_start + MAX_PER_ROW]
            row_h = max(_class_height(by_name[n]) for n in sub)
            for col, name in enumerate(sub):
                positions[name] = (START_X + col * (CLASS_W + H_GAP), current_y)
            current_y += row_h + V_GAP

    return positions


# ── XML generation ─────────────────────────────────────────────────────────────

def build_xml(classes: list[ClassInfo]) -> str:
    _EMPTY = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<mxGraphModel><root>'
        '<mxCell id="0"/><mxCell id="1" parent="0"/>'
        '</root></mxGraphModel>'
    )
    if not classes:
        return _EMPTY

    positions = _layout(classes)
    cells: list[str] = []
    class_ids: dict[str, str] = {}

    # ── Class blocks ──────────────────────────────────────────────────────────
    for i, cls in enumerate(classes):
        cid = f"c{i}"
        class_ids[cls.name] = cid
        x, y = positions.get(cls.name, (START_X + i * (CLASS_W + H_GAP), START_Y))
        total_h = _class_height(cls)

        if cls.is_interface:
            fill, stroke = _IFACE_FILL, _IFACE_STROKE
            label = f"«interface»&#xa;{_esc(cls.name)}"
        elif cls.is_struct:
            fill, stroke = _STRUCT_FILL, _STRUCT_STROKE
            label = f"«struct»&#xa;{_esc(cls.name)}"
        else:
            fill, stroke = _CLASS_FILL, _CLASS_STROKE
            label = _esc(cls.name)

        cells.append(
            f'<mxCell id="{cid}" value="{label}" '
            f'style="swimlane;fontStyle=1;align=center;startSize={HEADER_H};'
            f'fillColor={fill};strokeColor={stroke};'
            f'fontColor={_HEADER_FONT};fontSize=12;rounded=1;arcSize=4;" '
            f'vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{CLASS_W}" '
            f'height="{total_h}" as="geometry"/></mxCell>'
        )

        cur_y = HEADER_H

        # Fields
        for j, fld in enumerate(cls.fields):
            sym   = _ACCESS.get(fld.access, "~")
            label = _esc(f"{sym} {fld.name}: {fld.type_str}")
            cells.append(
                f'<mxCell id="{cid}_f{j}" value="{label}" '
                f'style="text;strokeColor=none;fillColor=none;align=left;'
                f'verticalAlign=middle;spacingLeft=6;fontSize=11;'
                f'fontColor={_MEMBER_FONT};" '
                f'vertex="1" parent="{cid}">'
                f'<mxGeometry y="{cur_y}" width="{CLASS_W}" '
                f'height="{ROW_H}" as="geometry"/></mxCell>'
            )
            cur_y += ROW_H

        # Separator
        if cls.fields and cls.methods:
            cells.append(
                f'<mxCell id="{cid}_sep" value="" '
                f'style="line;strokeWidth=1;fillColor=none;strokeColor={stroke};" '
                f'vertex="1" parent="{cid}">'
                f'<mxGeometry y="{cur_y}" width="{CLASS_W}" '
                f'height="{SEP_H}" as="geometry"/></mxCell>'
            )
            cur_y += SEP_H

        # Methods
        for j, mth in enumerate(cls.methods):
            sym = _ACCESS.get(mth.access, "~")
            if mth.is_constructor:
                label = _esc(f"{sym} {mth.name}{mth.params}")
            else:
                label = _esc(f"{sym} {mth.name}{mth.params}: {mth.return_type}")
            cells.append(
                f'<mxCell id="{cid}_m{j}" value="{label}" '
                f'style="text;strokeColor=none;fillColor=none;align=left;'
                f'verticalAlign=middle;spacingLeft=6;fontSize=11;'
                f'fontColor={_MEMBER_FONT};" '
                f'vertex="1" parent="{cid}">'
                f'<mxGeometry y="{cur_y}" width="{CLASS_W}" '
                f'height="{ROW_H}" as="geometry"/></mxCell>'
            )
            cur_y += ROW_H

    # ── Edges ─────────────────────────────────────────────────────────────────
    by_name = {c.name: c for c in classes}
    relations = _detect_relations(classes)
    ports = _assign_ports(relations, positions, by_name)

    _REL_COLOR = {
        "inheritance": _COLOR_INHERIT,
        "realization": _COLOR_REALIZE,
        "composition": _COLOR_COMPOSE,
        "aggregation": _COLOR_AGGREGATE,
        "dependency":  _COLOR_DEPEND,
    }

    for ei, (src, tgt, rel) in enumerate(relations):
        if src not in class_ids or tgt not in class_ids:
            continue
        sid = class_ids[src]
        tid = class_ids[tgt]
        ex, ey, nx, ny = ports.get((src, tgt), (0.5, 1.0, 0.5, 0.0))
        color = _REL_COLOR.get(rel, _EDGE_COLOR)
        style = _edge_style(rel, color, ex, ey, nx, ny)
        cells.append(
            f'<mxCell id="e{ei}" value="" style="{style}" '
            f'edge="1" source="{sid}" target="{tid}" parent="1">'
            f'<mxGeometry relative="1" as="geometry"/></mxCell>'
        )

    body = "\n    ".join(cells)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" '
        'tooltips="1" connect="1" arrows="1" fold="1" page="0" pageScale="1" '
        'pageWidth="1654" pageHeight="1169" math="0" shadow="0">\n'
        '  <root>\n'
        '    <mxCell id="0"/>\n'
        '    <mxCell id="1" parent="0"/>\n'
        f'    {body}\n'
        '  </root>\n'
        '</mxGraphModel>'
    )
