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
    "if_branch_gap":        0,   # горизонт. расстояние от края ромба до центра ветки
    "if_branch_vgap":       15,   # вертикальный зазор: низ ромба → верх первого блока ветки
    "if_branch_min_gap":    40,  # мин. зазор между bbox-ами веток (не между центрами!)

    # WHILE — коридоры (пространство между крайним блоком bbox и линией стрелки)
    "while_corridor_base":  80,   # базовый коридор на глубине 0
    "while_corridor_step":  20,   # уменьшение коридора на каждый уровень вложенности
    "while_corridor_min":   30,   # минимальная ширина коридора

    # WHILE — зазоры возвратной стрелки от блоков
    "while_back_turn_gap":  20,   # вертикальный зазор: низ последнего блока → перемычка
    "while_back_top_gap":   15,   # вертикальный зазор: линия коридора → верх ромба

    # BBox: True = рисовать (IF=жёлтый, WHILE=синий), False = скрыть
    "show_bbox":            True,
}


def _while_corridor(cfg, depth):
    """Ширина коридора для WHILE на заданной глубине вложенности."""
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
        self.height = 40
        self.position = (cx - 60, y)
        self.apply_style_string(
            "whiteSpace=wrap;rounded=1;dashed=0;html=1;arcSize=50;")


class Execute(drawpyo.diagram.Object):
    def __init__(self, page, value, cx, y):
        super().__init__(page=page)
        self.value = value
        m = (len(value) // 50) + 1
        self.width = 120 * m
        self.height = 40 * m
        self.position = (cx - self.width // 2, y)
        self.apply_style_string("rounded=0;whiteSpace=wrap;html=1;")


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
            "shape=loopLimit;whiteSpace=wrap;html=1;direction=west;")


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
        'start':   (120, 40), 'stop':    (120, 40),
        'execute': (120*m, 40*m), 'process': (120*m, 40*m),
        'if':      (200*m, 80*m), 'while':   (200*m, 80*m),
        'for_default':      (120*m, 40*m),
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

    depth — глубина вложенности WHILE (влияет на ширину коридоров).
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
            d_min_rhombus = rh_w2  
            d = max(d_min_bbox, d_min_rhombus)
            d = int(d) + 1  


            R = max(R, d + yr)   
            L = max(L, d + nl)   

            bh = max(yh if yn else 0, nh2 if nn else 0)
            H += nh + if_vgap + bh + gap

        elif t == 'while':
            cn = node.get('children', [])
            child_depth = depth + 1
            cl, cr, ch = (compute_bbox(cn, cfg, child_depth)
                          if cn else (nw // 2, nw // 2, 0))
            wc = _while_corridor(cfg, depth)
            rh_w2 = nw // 2

            L = max(L, max(cl, rh_w2) + wc)
            R = max(R, max(cr, rh_w2) + wc)
            H += nh + gap + ch + gap * 2 + gap

        else:
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
    depth    — глубина вложенности WHILE (0 = корень)
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

            elif t == 'for_default':
                obj = ForDefault(self.page, node['value'], self.cx, self.y)
                if prev_obj:
                    _edge(self.page, prev_obj, obj, _DOWN)
                first = first or obj
                prev_obj = obj
                self.y = _bot(obj) + self.cfg['gap_y']

            elif t == 'loop_limit_start':
                obj = LoopLimitStart(self.page, node['value'], self.cx, self.y)
                if prev_obj:
                    _edge(self.page, prev_obj, obj, _DOWN)
                first = first or obj
                prev_obj = obj
                self.y = _bot(obj) + self.cfg['gap_y']

            elif t == 'loop_limit_end':
                obj = LoopLimitEnd(self.page, node['value'], self.cx, self.y)
                if prev_obj:
                    _edge(self.page, prev_obj, obj, _DOWN)
                first = first or obj
                prev_obj = obj
                self.y = _bot(obj) + self.cfg['gap_y']

            elif t == 'if':
                fst, lst = self._render_if(node, prev_obj)
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
        ── ИСПРАВЛЕНИЕ ПОЗИЦИОНИРОВАНИЯ ВЕТОК ──────────────────────────────
          Условие непересечения:
            левый край правой ветки  > правый край левой ветки + min_gap
            (yes_cx - yl)            > (no_cx + nr) + min_gap

          При yes_cx = cx + d, no_cx = cx - d:
            (cx + d - yl) > (cx - d + nr) + min_gap
            2d > yl + nr + min_gap
            d > (yl + nr + min_gap) / 2

          Также d >= rh_w2 (ветка не заходит внутрь ромба).

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
        # Условие: bbox правой ветки не пересекает bbox левой ветки
        # (yes_cx - yl) >= (no_cx + nr) + min_gap
        # При yes_cx = cx+d, no_cx = cx-d:  2d >= yl + nr + min_gap
        min_gap = cfg['if_branch_min_gap']
        d_bbox = (yl + nr + min_gap) / 2   # от bbox-ов
        d_rh   = rh_w2                     # минимум — хотя бы до края ромба
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
        if nn:
            r = Renderer(self.page, nn, no_cx, bsy, cfg, depth=self.depth)
            no_first, no_last = r.render()
            _edge(self.page, rh, no_first,
                  "endArrow=none;html=1;rounded=0;"
                  "exitX=0;exitY=0.5;entryX=0.5;entryY=0;",
                  pts=[(no_cx, rh_mid)])
            LabelShape(self.page, "Нет", cx - rh_w2 - 48, rh_mid - 18)

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

    # ── WHILE ────────────────────────────────────────────────────────────

    def _render_while(self, node, prev_obj):
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


# ═══════════════════════════════════════════════════════════════════════════
# ЗАПУСК
# ═══════════════════════════════════════════════════════════════════════════

file_path = os.path.join(script_dir, "Xuita.xml")
if os.path.exists(file_path):
    os.remove(file_path)



nodes=[]

cfg = DEFAULT_CFG

test = drawpyo.File()
test.file_name = "Xuita.xml"
test.file_path = script_dir

page = drawpyo.Page(file=test)

renderer = Renderer(page, nodes, center_x=500, start_y=20, cfg=cfg)
renderer.render()

test.write()
print("Готово! Файл: Xuita.xml")