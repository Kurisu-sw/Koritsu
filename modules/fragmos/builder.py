import drawpyo
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_CFG = {

    # Общее
    "gap_y":               40,   # вертикальный зазор между элементами

    # IF
    "if_branch_gap":        20,   # горизонт. расстояние от края ромба до центра ветки
    "if_branch_vgap":       15,   # вертикальный зазор: низ ромба → верх первого блока ветки
    "if_branch_min_gap":    40,  # мин. зазор между bbox-ами веток (не между центрами!)

    # WHILE — коридоры (пространство между крайним блоком bbox и линией стрелки)
    "while_corridor_base":  80,   # базовый коридор на глубине 0
    "while_corridor_step":  20,   # уменьшение коридора на каждый уровень вложенности
    "while_corridor_min":   30,   # минимальная ширина коридора

    # WHILE — зазоры возвратной стрелки от блоков
    "while_back_turn_gap":  20,   # вертикальный зазор: низ последнего блока → перемычка
    "while_back_top_gap":   15,   # вертикальный зазор: линия коридора → верх ромба

    # BBox: True = рисовать (IF=жёлтый, WHILE=синий, FOR=фиолетовый), False = скрыть
    "show_bbox":            True,
}


def _while_corridor(cfg, depth):
    """Ширина коридора для WHILE/FOR на заданной глубине вложенности."""
    val = cfg["while_corridor_base"] - depth * cfg["while_corridor_step"]
    return max(val, cfg["while_corridor_min"])


# ═══════════════════════════════════════════════════════════════════════════
# ФИГУРЫ
# ═══════════════════════════════════════════════════════════════════════════

class Base(drawpyo.diagram.Object):
    def __init__(self, page, value, cx, y):
        super().__init__(page=page)
        self.value = value
        self.width = 120
        self.height = 50
        self.position = (cx - 60, y)
        self.apply_style_string(
            "rounded=1;arcSize=50;whiteSpace=wrap;html=1;")


class Execute(drawpyo.diagram.Object):
    def __init__(self, page, value, cx, y):
        super().__init__(page=page)
        self.value = value
        m = (len(value) // 50) + 1
        self.width = 120 * m
        self.height = 40 * m
        self.position = (cx - self.width // 2, y)
        self.apply_style_string("rounded=0;whiteSpace=wrap;html=1;")

class Io(drawpyo.diagram.Object):
    def __init__(self, page, value, cx, y):
        super().__init__(page=page)
        self.value = value
        m = (len(value) // 50) + 1
        self.width = 120 * m
        self.height = 40 * m
        self.position = (cx - self.width // 2, y)
        self.apply_style_string("shape=parallelogram;perimeter=parallelogramPerimeter;whiteSpace=wrap;html=1;fixedSize=1;")


class ProcessShape(drawpyo.diagram.Object):
    def __init__(self, page, value, cx, y):
        super().__init__(page=page)
        self.value = value
        m = (len(value) // 50) + 1
        self.width = 120 * m
        self.height = 40 * m
        self.position = (cx - self.width // 2, y)
        self.apply_style_string(
            "shape=process;whiteSpace=wrap;html=1;backgroundOutline=1;")


class IfShape(drawpyo.diagram.Object):
    def __init__(self, page, value, cx, y):
        super().__init__(page=page)
        self.value = value
        m = (len(value) // 50) + 1
        self.width = 200 * m
        self.height = 80 * m
        self.position = (cx - self.width // 2, y)
        self.apply_style_string("whiteSpace=wrap;html=1;shape=rhombus;")


class WhileShape(drawpyo.diagram.Object):
    def __init__(self, page, value, cx, y):
        super().__init__(page=page)
        self.value = value
        m = (len(value) // 50) + 1
        self.width = 200 * m
        self.height = 80 * m
        self.position = (cx - self.width // 2, y)
        self.apply_style_string("whiteSpace=wrap;html=1;shape=rhombus;")


class ForDefault(drawpyo.diagram.Object):
    def __init__(self, page, value, cx, y):
        super().__init__(page=page)
        self.value = value
        m = (len(value) // 50) + 1
        self.width = 120 * m
        self.height = 40 * m
        self.position = (cx - self.width // 2, y)
        self.apply_style_string(
            "shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;fixedSize=1;")


class LoopLimitStart(drawpyo.diagram.Object):
    def __init__(self, page, value, cx, y):
        super().__init__(page=page)
        self.value = value
        m = (len(value) // 50) + 1
        self.width = 120 * m
        self.height = 40 * m
        self.position = (cx - self.width // 2, y)
        self.apply_style_string("shape=loopLimit;whiteSpace=wrap;html=1;")


class LoopLimitEnd(drawpyo.diagram.Object):
    def __init__(self, page, value, cx, y):
        super().__init__(page=page)
        self.value = value
        m = (len(value) // 50) + 1
        self.width = 120 * m
        self.height = 40 * m
        self.position = (cx - self.width // 2, y)
        self.apply_style_string(
            "shape=loopLimit;whiteSpace=wrap;html=1;flipV=1;")


class WaypointShape(drawpyo.diagram.Object):
    """Невидимая точка для маршрутизации стрелок."""
    def __init__(self, page, cx, y):
        super().__init__(page=page)
        self.width = 4
        self.height = 4
        self.position = (cx - 2, y - 2)
        self.apply_style_string(
            "shape=waypoint;sketch=0;fillStyle=solid;size=6;pointerEvents=1;"
            "points=[];fillColor=none;resizable=0;rotatable=0;"
            "perimeter=centerPerimeter;snapToPoint=1;shadow=1;opacity=0;")


class LabelShape(drawpyo.diagram.Object):
    """Текстовая подпись (без рамки)."""
    def __init__(self, page, text, x, y, w=44, h=20):
        super().__init__(page=page)
        self.value = text
        self.width = w
        self.height = h
        self.position = (x, y)
        self.apply_style_string(
            "text;html=1;whiteSpace=wrap;strokeColor=none;fillColor=none;"
            "align=center;verticalAlign=middle;rounded=0;fontSize=11;")


class BBoxShape(drawpyo.diagram.Object):
    """Цветной полупрозрачный прямоугольник — визуализация bounding box."""
    def __init__(self, page, x, y, w, h, color="#dae8fc", opacity=25):
        super().__init__(page=page)
        self.width = max(int(w), 4)
        self.height = max(int(h), 4)
        self.position = (int(x), int(y))
        self.apply_style_string(
            f"rounded=0;whiteSpace=wrap;html=1;fillColor={color};"
            f"strokeColor=#888888;opacity={opacity};dashed=1;"
            f"pointerEvents=0;")


# ═══════════════════════════════════════════════════════════════════════════
# УТИЛИТЫ
# ═══════════════════════════════════════════════════════════════════════════

def _edge(page, src, dst, style, pts=None):
    """Создать стрелку с заданным стилем и промежуточными точками."""
    e = drawpyo.diagram.Edge(page=page)
    e.source = src
    e.target = dst
    e.apply_style_string(style)
    for p in (pts or []):
        e.add_point_pos(p)
    return e


# Стиль вниз по центру
_DOWN = ("endArrow=none;html=1;rounded=0;"
         "exitX=0.5;exitY=1;entryX=0.5;entryY=0;")


def _bot(obj):
    """Нижняя координата объекта."""
    return obj.position[1] + obj.height


def _cx(obj):
    """Центр объекта по X."""
    return obj.position[0] + obj.width // 2


# ═══════════════════════════════════════════════════════════════════════════
# ВЫЧИСЛЕНИЕ BOUNDING BOX
# ═══════════════════════════════════════════════════════════════════════════

def _node_dims(node):
    """Возвращает (ширина, высота) для одного узла (без детей)."""
    t = node['type']
    v = node.get('value', '')
    m = (len(v) // 50) + 1
    table = {
        'start':   (120, 50), 'stop':    (120, 50),
        'execute': (120*m, 40*m), 'process': (120*m, 40*m),
        'io':      (120*m, 40*m),
        'if':      (200*m, 80*m), 'while':   (200*m, 80*m),
        'for_default':      (120*m, 40*m),
        'for_gost':         (120*m, 40*m),
        'loop_limit_start': (120*m, 40*m),
        'loop_limit_end':   (120*m, 40*m),
    }
    return table.get(t, (120, 40))


def compute_bbox(nodes, cfg, depth=0):
    """
    Рекурсивно вычисляет (L, R, H) для списка узлов:
      L — максимальный отступ влево от center_x
      R — максимальный отступ вправо от center_x
      H — суммарная высота от верха первого элемента до низа последнего

    depth — глубина вложенности WHILE/FOR (влияет на ширину коридоров).
    """
    gap = cfg['gap_y']
    if_vgap = cfg['if_branch_vgap']
    min_gap = cfg['if_branch_min_gap']

    L = R = H = 0

    for i, node in enumerate(nodes):
        t = node['type']
        nw, nh = _node_dims(node)

        if i > 0:
            H += gap

        L = max(L, nw // 2)
        R = max(R, nw // 2)

        if t == 'if':
            yn = node.get('children', [])
            nn = node.get('else_children', [])
            yl, yr, yh  = compute_bbox(yn, cfg, depth) if yn else (60, 60, 0)
            nl, nr, nh2 = compute_bbox(nn, cfg, depth) if nn else (60, 60, 0)

            rh_w2 = nw // 2
            d_min_bbox = (yl + nr + min_gap) / 2
            d_min_rhombus = rh_w2 + cfg.get('if_branch_gap', 0)
            d = max(d_min_bbox, d_min_rhombus)
            d = int(d) + 1

            R = max(R, d + yr)   
            L = max(L, d + nl)   

            bh = max(yh if yn else 0, nh2 if nn else 0)
            H += nh + if_vgap + bh + gap

        elif t in ('while', 'for_default', 'for_gost'):
            # WHILE и FOR используют одинаковую логику коридоров
            cn = node.get('children', [])
            child_depth = depth + 1
            cl, cr, ch = (compute_bbox(cn, cfg, child_depth)
                          if cn else (nw // 2, nw // 2, 0))
            wc = _while_corridor(cfg, depth)
            fr_w2 = nw // 2

            L = max(L, max(cl, fr_w2) + wc)
            R = max(R, max(cr, fr_w2) + wc)
            H += nh + gap + ch + gap * 2 + gap

        elif t == 'switch':
            _CASE_GAP      = 20
            _MIN_CASE_HALF = 60   # половина ширины Execute-блока (120px)
            cases = node.get('cases', [])
            n_cases = len(cases)

            if n_cases == 0:
                L = max(L, 100)
                R = max(R, 100)
                H += 80 + gap
            else:
                case_halves = []
                max_col_h = 0
                for case in cases:
                    body = case.get('body', [])
                    if body:
                        cl, cr, ch = compute_bbox(body, cfg, depth + 1)
                    else:
                        cl, cr, ch = 0, 0, 0
                    # Симметричная полуширина колонки: берём max(L,R) тела
                    hw = max(cl, cr, _MIN_CASE_HALF)
                    case_halves.append(hw)
                    col_h = 40 + (gap + ch if body else 0)
                    max_col_h = max(max_col_h, col_h)

                total_w = sum(2 * hw for hw in case_halves) + (n_cases - 1) * _CASE_GAP
                half = max(total_w, 200) // 2

                L = max(L, half)
                R = max(R, half)
                H += 80 + gap + max_col_h + gap   # ромб + gap + кейсы + gap

        else:
            # loop_limit_start, loop_limit_end и другие простые блоки
            H += nh

    return L, R, H


# ═══════════════════════════════════════════════════════════════════════════
# РЕНДЕРЕР
# ═══════════════════════════════════════════════════════════════════════════

class Renderer:
    """
    Рекурсивный рендерер списка узлов.

    center_x — центральная ось всех элементов этой ветки
    start_y  — верхняя координата первого элемента
    cfg      — словарь конфигурации (DEFAULT_CFG)
    depth    — глубина вложенности WHILE/FOR (0 = корень)
    """

    def __init__(self, page, nodes, center_x, start_y, cfg=None, depth=0):
        self.page = page
        self.nodes = nodes
        self.cx = center_x
        self.y = start_y
        self.cfg = cfg or DEFAULT_CFG
        self.depth = depth

    # ── Основной цикл ────────────────────────────────────────────────────

    def render(self, prev_obj=None):
        """
        Обходит nodes и рендерит каждый элемент.
        Возвращает (first_obj, last_obj).
        """
        first = None

        for node in self.nodes:
            t = node['type']

            if t in ('start', 'stop'):
                obj = Base(self.page, node['value'], self.cx, self.y)
                if prev_obj:
                    _edge(self.page, prev_obj, obj, _DOWN)
                first = first or obj
                prev_obj = obj
                self.y = _bot(obj) + self.cfg['gap_y']

            elif t == 'process':
                obj = ProcessShape(self.page, node['value'], self.cx, self.y)
                if prev_obj:
                    _edge(self.page, prev_obj, obj, _DOWN)
                first = first or obj
                prev_obj = obj
                self.y = _bot(obj) + self.cfg['gap_y']

            elif t == 'execute':
                obj = Execute(self.page, node['value'], self.cx, self.y)
                if prev_obj:
                    _edge(self.page, prev_obj, obj, _DOWN)
                first = first or obj
                prev_obj = obj
                self.y = _bot(obj) + self.cfg['gap_y']

            elif t == 'io':
                obj = Io(self.page, node['value'], self.cx, self.y)
                if prev_obj:
                    _edge(self.page, prev_obj, obj, _DOWN)
                first = first or obj
                prev_obj = obj
                self.y = _bot(obj) + self.cfg['gap_y']

            elif t == 'loop_limit_start':
                # Обработка блока начала цикла (ГОСТ) — просто блок в потоке
                obj = LoopLimitStart(self.page, node['value'], self.cx, self.y)
                if prev_obj:
                    _edge(self.page, prev_obj, obj, _DOWN)
                first = first or obj
                prev_obj = obj
                self.y = _bot(obj) + self.cfg['gap_y']

            elif t == 'loop_limit_end':
                # Обработка блока конца цикла (ГОСТ) — просто блок в потоке
                obj = LoopLimitEnd(self.page, node['value'], self.cx, self.y)
                if prev_obj:
                    _edge(self.page, prev_obj, obj, _DOWN)
                first = first or obj
                prev_obj = obj
                self.y = _bot(obj) + self.cfg['gap_y']

            elif t == 'for_default':
                if self.cfg.get('build_model') == 1:
                    fst, lst = self._render_for_gost(node, prev_obj)
                else:
                    fst, lst = self._render_for_default(node, prev_obj)
                first = first or fst
                prev_obj = lst

            elif t == 'if':
                fst, lst = self._render_if(node, prev_obj)
                first = first or fst
                prev_obj = lst

            elif t == 'switch':
                fst, lst = self._render_switch(node, prev_obj)
                first = first or fst
                prev_obj = lst

            elif t == 'while':
                fst, lst = self._render_while(node, prev_obj)
                first = first or fst
                prev_obj = lst

        return first, prev_obj

    # ── IF ───────────────────────────────────────────────────────────────

    def _render_if(self, node, prev_obj):
        """
        Рендерит IF-блок (ромб) с двумя ветками и точкой слияния.
        """
        cfg = self.cfg
        gap = cfg['gap_y']

        # ── Ромб ──────────────────────────────────────────
        rh = IfShape(self.page, node['value'], self.cx, self.y)
        if prev_obj:
            _edge(self.page, prev_obj, rh, _DOWN)

        cx     = self.cx
        rh_w2  = rh.width  // 2
        rh_h2  = rh.height // 2
        rh_top = rh.position[1]
        rh_mid = rh_top + rh_h2
        rh_bot = _bot(rh)

        yn = node.get('children', [])
        nn = node.get('else_children', [])

        # Bbox каждой ветки (с учётом коридоров WHILE внутри)
        yl, yr, yh  = compute_bbox(yn, cfg, self.depth) if yn else (60, 60, 0)
        nl, nr, nh2 = compute_bbox(nn, cfg, self.depth) if nn else (60, 60, 0)

        # ── Вычисляем d: расстояние от cx до центра каждой ветки ─────────
        min_gap = cfg['if_branch_min_gap']
        d_bbox = (yl + nr + min_gap) / 2   # от bbox-ов
        d_rh   = rh_w2 + cfg.get('if_branch_gap', 0)  # минимум — край ромба + зазор
        d = int(max(d_bbox, d_rh)) + 1

        yes_cx = cx + d   # центр правой ветки (ДА)
        no_cx  = cx - d   # центр левой ветки (НЕТ)

        bh  = max(yh if yn else 0, nh2 if nn else 0)
        bsy = rh_bot + cfg['if_branch_vgap']

        # ── BBox всего IF-блока ───────────────────────────
        if cfg.get('show_bbox'):
            R_bb = d + yr   # правый край правой ветки от cx
            L_bb = d + nl   # левый край левой ветки от cx
            BBoxShape(
                self.page,
                cx - L_bb - 10, rh_top - 6,
                L_bb + R_bb + 20, rh.height + cfg['if_branch_vgap'] + bh + gap + 12,
                color="#fff2cc", opacity=25)

        # ── Ветка ДА (вправо) ────────────────────────────
        yes_last  = None
        yes_first = None
        if yn:
            r = Renderer(self.page, yn, yes_cx, bsy, cfg, depth=self.depth)
            yes_first, yes_last = r.render()
            _edge(self.page, rh, yes_first,
                  "endArrow=none;html=1;rounded=0;"
                  "exitX=1;exitY=0.5;entryX=0.5;entryY=0;",
                  pts=[(yes_cx, rh_mid)])
            LabelShape(self.page, "Да", cx + rh_w2 + 4, rh_mid - 18)

        # ── Ветка НЕТ (влево) ────────────────────────────
        no_last  = None
        no_first = None
        LabelShape(self.page, "Нет", cx - rh_w2 - 48, rh_mid - 18)
        if nn:
            r = Renderer(self.page, nn, no_cx, bsy, cfg, depth=self.depth)
            no_first, no_last = r.render()
            _edge(self.page, rh, no_first,
                  "endArrow=none;html=1;rounded=0;"
                  "exitX=0;exitY=0.5;entryX=0.5;entryY=0;",
                  pts=[(no_cx, rh_mid)])

        # ── Точка слияния (строго под ромбом) ────────────
        merge_y = bsy + bh + gap
        wp = WaypointShape(self.page, cx, merge_y)

        # Конец ветки ДА → merge
        if yes_last:
            _edge(self.page, yes_last, wp,
                  "endArrow=none;html=1;rounded=0;exitX=0.5;exitY=1;",
                  pts=[(yes_cx, merge_y)])
        elif not yn:
            _edge(self.page, rh, wp,
                  "endArrow=none;html=1;rounded=0;exitX=1;exitY=0.5;",
                  pts=[(yes_cx, rh_mid),
                       (yes_cx, merge_y),
                       (cx, merge_y)])

        # Конец ветки НЕТ → merge
        if no_last:
            _edge(self.page, no_last, wp,
                  "endArrow=none;html=1;rounded=0;exitX=0.5;exitY=1;",
                  pts=[(no_cx, merge_y)])
        elif not nn:
            _edge(self.page, rh, wp,
                  "endArrow=none;html=1;rounded=0;exitX=0;exitY=0.5;",
                  pts=[(no_cx, rh_mid),
                       (no_cx, merge_y),
                       (cx, merge_y)])

        self.y = merge_y + gap
        return rh, wp

    # ── SWITCH (match/case, только ГОСТ) ─────────────────────────────────

    def _render_switch(self, node, prev_obj):
        """
        Рендерит switch-блок: ромб (subject) → N прямоугольников кейсов
        горизонтально → тела кейсов вниз → точка слияния.
        Ширина каждой колонки определяется реальным bbox тела кейса.
        """
        _CASE_GAP      = 20
        _MIN_CASE_HALF = 60   # минимальная полуширина колонки (Execute = 120px)

        cfg         = self.cfg
        gap         = cfg['gap_y']
        cx          = self.cx
        child_depth = self.depth + 1

        # ── Ромб с субъектом ──────────────────────────────
        rh = IfShape(self.page, node['value'], cx, self.y)
        if prev_obj:
            _edge(self.page, prev_obj, rh, _DOWN)
        rh_bot = _bot(rh)

        cases = node.get('cases', [])
        n     = len(cases)

        if n == 0:
            self.y = rh_bot + gap
            return rh, rh

        # ── Предварительный расчёт реальных ширин и высот кейсов ──────────
        # Нужен до рендера чтобы: 1) правильно расставить центры, 2) нарисовать bbox
        case_halves = []
        case_body_bboxes = []   # (cl, cr, ch) для каждого кейса
        for case in cases:
            body = case.get('body', [])
            if body:
                cl, cr, ch = compute_bbox(body, cfg, child_depth)
            else:
                cl, cr, ch = 0, 0, 0
            hw = max(cl, cr, _MIN_CASE_HALF)
            case_halves.append(hw)
            case_body_bboxes.append((cl, cr, ch))

        # ── Горизонтальные центры кейсов ──────────────────
        total_w = sum(2 * hw for hw in case_halves) + (n - 1) * _CASE_GAP
        case_cxs = []
        cur_x = cx - total_w // 2
        for hw in case_halves:
            case_cxs.append(cur_x + hw)
            cur_x += 2 * hw + _CASE_GAP

        case_top_y = rh_bot + gap

        # ── BBox (рисуется ДО кейсов → оказывается позади в z-order) ─────
        if cfg.get('show_bbox'):
            max_body_h = max((b[2] for b in case_body_bboxes), default=0)
            _RECT_H    = 40   # высота Execute-блока с паттерном
            bb_h = (rh.height + gap
                    + _RECT_H
                    + (gap + max_body_h if max_body_h else 0)
                    + gap)
            BBoxShape(
                self.page,
                cx - total_w // 2 - 10, rh.position[1] - 6,
                total_w + 20,            bb_h + 12,
                color="#fff2cc", opacity=22)   # жёлтый для match/switch

        # ── Рендерим каждый кейс ──────────────────────────
        last_objs = []
        max_bot_y = case_top_y

        for i, case in enumerate(cases):
            ccx     = case_cxs[i]
            pattern = case.get('pattern', '')
            body    = case.get('body', [])

            # Прямоугольник с паттерном
            rect = Execute(self.page, pattern, ccx, case_top_y)
            _edge(self.page, rh, rect,
                  "endArrow=block;html=1;rounded=0;"
                  "exitX=0.5;exitY=1;entryX=0.5;entryY=0;")

            if body:
                sub = Renderer(self.page, body, ccx,
                               _bot(rect) + gap, cfg, child_depth)
                _, last_b = sub.render(rect)
                last_obj = last_b or rect
            else:
                last_obj = rect

            last_objs.append(last_obj)
            max_bot_y = max(max_bot_y, _bot(last_obj))

        # ── Точка слияния ─────────────────────────────────
        merge_y = max_bot_y + gap
        wp = WaypointShape(self.page, cx, merge_y)

        for lo in last_objs:
            lo_cx = _cx(lo)
            _edge(self.page, lo, wp,
                  "endArrow=none;html=1;rounded=0;exitX=0.5;exitY=1;",
                  pts=[(lo_cx, merge_y), (cx, merge_y)])

        self.y = merge_y + gap
        return rh, wp

    # ── WHILE ────────────────────────────────────────────────────────────

    def _render_while(self, node, prev_obj):
        """
        Рендерит WHILE-цикл (ромб) с телом цикла и возвратной стрелкой.
        """
        cfg   = self.cfg
        gap   = cfg['gap_y']
        depth = self.depth

        wc = _while_corridor(cfg, depth)

        # ── Ромб ──────────────────────────────────────────
        rh = WhileShape(self.page, node['value'], self.cx, self.y)
        if prev_obj:
            _edge(self.page, prev_obj, rh, _DOWN)

        cx     = self.cx
        rh_w2  = rh.width  // 2
        rh_top = rh.position[1]
        rh_mid = rh_top + rh.height // 2
        rh_bot = _bot(rh)

        children    = node.get('children', [])
        child_depth = depth + 1

        cl, cr, ch = (compute_bbox(children, cfg, child_depth)
                      if children else (rh_w2, rh_w2, 0))

        back_x = cx - max(cl, rh_w2) - wc
        no_x   = cx + max(cr, rh_w2) + wc

        # ── BBox ──────────────────────────────────────────
        if cfg.get('show_bbox'):
            L_bb    = max(cl, rh_w2) + wc
            R_bb    = max(cr, rh_w2) + wc
            total_h = rh.height + gap + ch + gap * 2
            BBoxShape(
                self.page,
                cx - L_bb - 10, rh_top - 6,
                L_bb + R_bb + 20, total_h + 12,
                color="#dae8fc", opacity=22)

        # ── Ветка ДА (вниз) ───────────────────────────────
        last_child  = None
        first_child = None

        if children:
            r = Renderer(self.page, children, cx, rh_bot + gap, cfg,
                         depth=child_depth)
            first_child, last_child = r.render()
            _edge(self.page, rh, first_child, _DOWN)
            LabelShape(self.page, "Да", cx + 4, rh_bot + 4)

        LabelShape(self.page, "Нет", cx + rh_w2 + 4, rh_mid - 18)

        # ── Обратная стрелка: последний_ребёнок → верх ромба ─────────────
        if last_child:
            lc_bot   = _bot(last_child)
            lc_cx    = _cx(last_child)
            turn_y   = lc_bot + cfg["while_back_turn_gap"]
            entry_y  = rh_top - cfg["while_back_top_gap"]
            _edge(self.page, last_child, rh,
                  "endArrow=classic;html=1;rounded=0;"
                  "exitX=0.5;exitY=1;entryX=0.5;entryY=0;",
                  pts=[
                      (lc_cx,  turn_y),
                      (back_x, turn_y),
                      (back_x, entry_y),
                  ])

        # ── Стрелка НЕТ → exit waypoint ──────────────────────────────────
        lc_bot_y = _bot(last_child) if last_child else rh_bot
        exit_y   = lc_bot_y + gap * 2
        exit_wp  = WaypointShape(self.page, cx, exit_y)

        _edge(self.page, rh, exit_wp,
              "endArrow=none;html=1;rounded=0;exitX=1;exitY=0.5;",
              pts=[
                  (no_x, rh_mid),
                  (no_x, exit_y),
                  (cx,   exit_y),
              ])

        self.y = exit_y + gap
        return rh, exit_wp

    # ── FOR DEFAULT ────────────────────────────────────────────────────────

    def _render_for_default(self, node, prev_obj):
        """
        Рендерит FOR-цикл (шестиугольник) с телом цикла и возвратной стрелкой.
        Структура аналогична WHILE.
        """
        cfg   = self.cfg
        gap   = cfg['gap_y']
        depth = self.depth

        # Используем ту же систему коридоров, что и для WHILE
        wc = _while_corridor(cfg, depth)

        # ── Шестиугольник FOR ──────────────────────────────────────────
        fr = ForDefault(self.page, node['value'], self.cx, self.y)
        if prev_obj:
            _edge(self.page, prev_obj, fr, _DOWN)

        cx      = self.cx
        fr_w2   = fr.width  // 2
        fr_top  = fr.position[1]
        fr_mid  = fr_top + fr.height // 2
        fr_bot  = _bot(fr)

        children    = node.get('children', [])
        child_depth = depth + 1

        # Вычисляем bbox тела цикла (рекурсивно)
        cl, cr, ch = (compute_bbox(children, cfg, child_depth)
                      if children else (fr_w2, fr_w2, 0))

        # Координаты для возвратной стрелки (слева) и выхода (справа)
        back_x = cx - max(cl, fr_w2) - wc
        exit_x = cx + max(cr, fr_w2) + wc

        # ── BBox визуализация (опционально) ─────────────────────────────
        if cfg.get('show_bbox'):
            L_bb    = max(cl, fr_w2) + wc
            R_bb    = max(cr, fr_w2) + wc
            total_h = fr.height + gap + ch + gap * 2
            BBoxShape(
                self.page,
                cx - L_bb - 10, fr_top - 6,
                L_bb + R_bb + 20, total_h + 12,
                color="#e1d5e7", opacity=22)  # Фиолетовый оттенок для FOR

        # ── Тело цикла (рендеринг дочерних узлов) ───────────────────────
        last_child  = None
        first_child = None

        if children:
            r = Renderer(self.page, children, cx, fr_bot + gap, cfg,
                         depth=child_depth)
            first_child, last_child = r.render()
            # Соединяем вход FOR → первый элемент тела
            _edge(self.page, fr, first_child, _DOWN)

        # ── Обратная стрелка: последний элемент тела → верх FOR ─────────
        if last_child:
            lc_bot   = _bot(last_child)
            lc_cx    = _cx(last_child)
            turn_y   = lc_bot + cfg["while_back_turn_gap"]      # зазор снизу
            entry_y  = fr_top - cfg["while_back_top_gap"]       # зазор сверху
            _edge(self.page, last_child, fr,
                  "endArrow=classic;html=1;rounded=0;"
                  "exitX=0.5;exitY=1;entryX=0;entryY=0.5;",
                  pts=[
                      (lc_cx,  turn_y),   # вниз от последнего блока
                      (back_x, entry_y),  # вверх к вершине FOR
                  ])

        # ── Стрелка выхода из цикла → waypoint ──────────────────────────
        lc_bot_y = _bot(last_child) if last_child else fr_bot
        exit_y   = lc_bot_y + gap * 2
        exit_wp  = WaypointShape(self.page, cx, exit_y)

        _edge(self.page, fr, exit_wp,
              "endArrow=none;html=1;rounded=0;exitX=1;exitY=0.5;",
              pts=[
                  (exit_x, fr_mid),   # выход справа от шестиугольника
                  (exit_x, exit_y),   # вниз до уровня слияния
                  (cx,   exit_y),     # к центру
              ])

        # Обновляем текущую Y-координату для следующих элементов
        self.y = exit_y + gap
        return fr, exit_wp

    # ── FOR GOST (LoopLimit) ─────────────────────────────────────────────

    def _render_for_gost(self, node, prev_obj):
        """
        Рендерит FOR-цикл в стиле ГОСТ 19.701-90:
        LoopLimitStart → тело цикла → LoopLimitEnd.
        Все соединены обычными стрелками вниз.
        Возвращает (loop_start, loop_end).
        """
        cfg = self.cfg
        gap = cfg['gap_y']

        # ── LoopLimitStart (трапеция сверху) ──────────────────────────────
        loop_start = LoopLimitStart(self.page, node['value'], self.cx, self.y)
        if prev_obj:
            _edge(self.page, prev_obj, loop_start, _DOWN)
        self.y = _bot(loop_start) + gap

        # ── Тело цикла ───────────────────────────────────────────────────
        children = node.get('children', [])
        last_child = loop_start

        if children:
            r = Renderer(self.page, children, self.cx, self.y, cfg,
                         depth=self.depth + 1)
            first_child, last_child = r.render()
            _edge(self.page, loop_start, first_child, _DOWN)
            self.y = r.y

        # ── LoopLimitEnd (перевёрнутая трапеция снизу) ────────────────────
        loop_end = LoopLimitEnd(self.page, node['value'], self.cx, self.y)
        _edge(self.page, last_child, loop_end, _DOWN)
        self.y = _bot(loop_end) + gap

        # ── BBox (опционально) ────────────────────────────────────────────
        if cfg.get('show_bbox'):
            cl, cr, _ = (compute_bbox(children, cfg, self.depth + 1)
                         if children else (0, 0, 0))
            hw_start = loop_start.width // 2
            hw_end = loop_end.width // 2
            max_left = max(hw_start, hw_end, cl)
            max_right = max(hw_start, hw_end, cr)
            bbox_top = loop_start.position[1]
            bbox_bot = _bot(loop_end)
            BBoxShape(
                self.page,
                self.cx - max_left - 10, bbox_top - 6,
                max_left + max_right + 20, bbox_bot - bbox_top + 12,
                color="#e1d5e7", opacity=22)

        return loop_start, loop_end


# ═══════════════════════════════════════════════════════════════════════════
# РАЗБИВКА НА ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════════════════

def _split_functions(nodes):
    """
    Разбивает список узлов на группы по границам START/STOP.
    Возвращает список (page_name, nodes).
    Каждая группа начинается с узла 'start' и заканчивается 'stop'.
    """
    result = []
    current = []
    current_name = "Схема"

    for node in nodes:
        if node['type'] == 'start':
            if current:
                result.append((current_name, current))
            current = [node]
            current_name = node['value']
        elif node['type'] == 'stop':
            current.append(node)
            result.append((current_name, current))
            current = []
            current_name = "Схема"
        else:
            current.append(node)

    if current:
        result.append((current_name, current))

    return result if result else [("Схема", nodes)]


# ═══════════════════════════════════════════════════════════════════════════
# ЗАПУСК
# ═══════════════════════════════════════════════════════════════════════════

def generate_from_code(code: str, language: str = 'python', out_path: str = '/tmp/fragmos_out.xml',
                        mode_id: str = 'default', cfg_overrides: dict = None) -> str:
    """
    Полный pipeline: исходный код → XML flowchart.

    Args:
        code:          исходный код
        language:      'python' | 'csharp' | 'cpp'
        out_path:      путь для сохранения XML
        mode_id:       'default' | 'loopLimit'
        cfg_overrides: перегрузки конфигурации

    Returns:
        Путь к созданному XML-файлу.
    """
    import sys
    _pkg_root = os.path.dirname(os.path.abspath(__file__))
    if _pkg_root not in sys.path:
        sys.path.insert(0, _pkg_root)

    from ast_generators import get_ast_generator
    from parser import parse_ast_to_flowchart

    ast_dict = get_ast_generator(language).generate(code)

    cfg, nodes = parse_ast_to_flowchart(ast_dict, mode_id=mode_id)
    if cfg_overrides:
        cfg.update(cfg_overrides)

    if os.path.exists(out_path):
        os.remove(out_path)

    f = drawpyo.File()
    f.file_name = os.path.basename(out_path)
    f.file_path = os.path.dirname(os.path.abspath(out_path))

    for page_name, func_nodes in _split_functions(nodes):
        page = drawpyo.Page(file=f)
        page.name = page_name
        Renderer(page, func_nodes, center_x=500, start_y=20, cfg=cfg).render()

    f.write()
    print(f"Готово! Файл: {out_path}")
    return out_path


def generate(frg_path, out_path=None, cfg_overrides=None):
    import sys
    _pkg_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _pkg_root not in sys.path:
        sys.path.insert(0, _pkg_root)
    base_cfg = None
    if cfg_overrides:
        base_cfg = dict(DEFAULT_CFG)
        base_cfg.update(cfg_overrides)

    from parser import parse_frg_file
    cfg, nodes = parse_frg_file(frg_path, base_cfg=base_cfg)

    if out_path is None:
        base = os.path.splitext(frg_path)[0]
        out_path = base + ".xml"

    if os.path.exists(out_path):
        os.remove(out_path)

    f = drawpyo.File()
    f.file_name = os.path.basename(out_path)
    f.file_path = os.path.dirname(os.path.abspath(out_path))

    for page_name, func_nodes in _split_functions(nodes):
        page = drawpyo.Page(file=f)
        page.name = page_name
        Renderer(page, func_nodes, center_x=500, start_y=20, cfg=cfg).render()

    f.write()

    print(f"Готово! Файл: {out_path}")
    return out_path
