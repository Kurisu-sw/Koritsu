import drawpyo
import os

if os.path.exists("/workspaces/Fragmos/webapp/pages/fragmos/Xuita.xml"):
    os.remove("/workspaces/Fragmos/webapp/pages/fragmos/Xuita.xml")

class Base(drawpyo.diagram.Object):
    def __init__(self, page, value, x, y, center_x=None):
        super().__init__(page=page)
        self.value = value
        self.width = 120
        self.height = 40
        cx = center_x if center_x is not None else x + self.width // 2
        self.position = (cx - self.width // 2, y)
        self.apply_style_string("whiteSpace=wrap;rounded=1;dashed=0; whiteSpace=wrap; html=1; arcSize=50;arcSize=50;")

class Execute(drawpyo.diagram.Object):
    def __init__(self, page, value, x, y, center_x=None):
        super().__init__(page=page)
        self.value = value
        self.width = 120 * ((len(value) // 50) + 1)
        self.height = 40 * ((len(value) // 50) + 1)
        cx = center_x if center_x is not None else x + self.width // 2
        self.position = (cx - self.width // 2, y)
        self.apply_style_string("rounded=0;whiteSpace=wrap;html=1;")

class If(drawpyo.diagram.Object):
    def __init__(self, page, value, x, y, center_x=None):
        super().__init__(page=page)
        self.value = value
        self.width = 200 * ((len(value) // 50) + 1)
        self.height = 80 * ((len(value) // 50) + 1)
        cx = center_x if center_x is not None else x + self.width // 2
        self.position = (cx - self.width // 2, y)
        self.apply_style_string("whiteSpace=wrap;html=1;shape=rhombus;")

class While(drawpyo.diagram.Object):
    def __init__(self, page, value, x, y, center_x=None):
        super().__init__(page=page)
        self.value = value
        self.width = 200 * ((len(value) // 50) + 1)
        self.height = 80 * ((len(value) // 50) + 1)
        cx = center_x if center_x is not None else x + self.width // 2
        self.position = (cx - self.width // 2, y)
        self.apply_style_string("whiteSpace=wrap;html=1;shape=rhombus;")

class For_default(drawpyo.diagram.Object):
    def __init__(self, page, value, x, y, center_x=None):
        super().__init__(page=page)
        self.value = value
        self.width = 120 * ((len(value) // 50) + 1)
        self.height = 40 * ((len(value) // 50) + 1)
        cx = center_x if center_x is not None else x + self.width // 2
        self.position = (cx - self.width // 2, y)
        self.apply_style_string("shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;fixedSize=1;")

class Loop_limit_start(drawpyo.diagram.Object):
    def __init__(self, page, value, x, y, center_x=None):
        super().__init__(page=page)
        self.value = value
        self.width = 120 * ((len(value) // 50) + 1)
        self.height = 40 * ((len(value) // 50) + 1)
        cx = center_x if center_x is not None else x + self.width // 2
        self.position = (cx - self.width // 2, y)
        self.apply_style_string("shape=loopLimit;whiteSpace=wrap;html=1;")

class Loop_limit_end(drawpyo.diagram.Object):
    def __init__(self, page, value, x, y, center_x=None):
        super().__init__(page=page)
        self.value = value
        self.width = 120 * ((len(value) // 50) + 1)
        self.height = 40 * ((len(value) // 50) + 1)
        cx = center_x if center_x is not None else x + self.width // 2
        self.position = (cx - self.width // 2, y)
        self.apply_style_string("shape=loopLimit;whiteSpace=wrap;html=1;direction=west;")

class Proccess(drawpyo.diagram.Object):
    def __init__(self, page, value, x, y, center_x=None):
        super().__init__(page=page)
        self.value = value
        self.width = 120 * ((len(value) // 50) + 1)
        self.height = 40 * ((len(value) // 50) + 1)
        cx = center_x if center_x is not None else x + self.width // 2
        self.position = (cx - self.width // 2, y)
        self.apply_style_string("shape=process;whiteSpace=wrap;html=1;backgroundOutline=1;")

class Pointer(drawpyo.diagram.Edge):
    def __init__(self, page, source, target, root=None, x=None, y=None):
        super().__init__(page=page)
        self.source = source
        self.target = target
        self.root = root
        self.pointer_type()

    def pointer_type(self):
        # возврат вверх (например тело while -> anker)
        if self.source.position[1] > self.target.position[1] and type(self.target) != Waypoint:
            self.add_point_pos((self.source.position[0] + self.source.width // 2, self.source.position[1] + self.source.height + 10))
            self.apply_style_string("endArrow=none;html=1;rounded=0;waypoint=orthogonal;exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
            return

        if type(self.target) == Waypoint:
            self.apply_style_string("endArrow=none;html=1;rounded=0;exitX=0.5;exitY=1;")
            return

        # обычная стрелка вниз или к waypoint
        self.apply_style_string("endArrow=none;html=1;rounded=0;waypoint=orthogonal;exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
    
        if type(self.source) == If and self.root == "yes":
            self.apply_style_string("endArrow=none;html=1;rounded=0;waypoint=orthogonal;exitX=1;exitY=0.5;entryX=0.5;entryY=0;")
        if type(self.source) == If and self.root == "no":
            self.apply_style_string("endArrow=none;html=1;rounded=0;waypoint=orthogonal;exitX=0;exitY=0.5;entryX=0.5;entryY=0;")
        if type(self.source) == While and self.root == "yes":
            self.apply_style_string("endArrow=none;html=1;rounded=0;waypoint=orthogonal;exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
        if type(self.source) == While and self.root == "no":
            self.apply_style_string("endArrow=none;html=1;rounded=0;waypoint=orthogonal;exitX=1;exitY=0.5;entryX=0.5;entryY=0;")

class Waypoint(drawpyo.diagram.Object):
    def __init__(self, page, x, y):
        super().__init__(page=page)
        self.width = 2
        self.height = 2
        self.position = (x, y)
        self.apply_style_string("whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#ffffff;")

class Text_format(drawpyo.diagram.Object):
    def __init__(self, page, value, x, y, width=20, height=15):
        super().__init__(page=page)
        self.value = value
        self.width = width
        self.height = height
        self.position = (x, y)
        self.apply_style_string("text;html=1;whiteSpace=wrap;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;rounded=0;")


class Render():
    def __init__(self, page, nodes, x=0, y=0, prev_obj=None, entry_root=None, center_x=None):
        self.page = page
        self.nodes = nodes
        self.perv_obj_xy = (x, y)
        self.step_y = 75
        self.prev_obj = prev_obj
        self.first_obj = None
        self.entry_root = entry_root
        self.center_x = center_x if center_x is not None else x + 60

    def _place(self, obj):
        if self.first_obj is None:
            self.first_obj = obj
        self.prev_obj = obj
        self.perv_obj_xy = obj.position

    def _connect(self, source, target, root=None):
        if self.first_obj is None:
            root = self.entry_root
        Pointer(self.page, source, target, root=root)

    def render(self):
        for node in self.nodes:

            if node["type"] == "start":
                obj = Base(self.page, node["value"], 0, self.perv_obj_xy[1], center_x=self.center_x)
                if self.prev_obj:
                    self._connect(self.prev_obj, obj)
                self._place(obj)

            elif node["type"] == "stop":
                obj = Base(self.page, node["value"], 0, self.perv_obj_xy[1] + self.step_y, center_x=self.center_x)
                self._connect(self.prev_obj, obj)
                self._place(obj)

            elif node["type"] == "process":
                obj = Proccess(self.page, node["value"], 0, self.perv_obj_xy[1] + self.step_y, center_x=self.center_x)
                self._connect(self.prev_obj, obj)
                self._place(obj)

            elif node["type"] == "execute":
                obj = Execute(self.page, node["value"], 0, self.perv_obj_xy[1] + self.step_y, center_x=self.center_x)
                self._connect(self.prev_obj, obj)
                self._place(obj)

            elif node["type"] == "if":
                if_obj = If(self.page, node["value"], 0, self.perv_obj_xy[1] + self.step_y, center_x=self.center_x)
                if self.prev_obj:
                    self._connect(self.prev_obj, if_obj)
                self._place(if_obj)

                if_cx = if_obj.position[0] + if_obj.width // 2
                if_cy = if_obj.position[1] + if_obj.height // 2

                # ветка YES — правее ромба, center_x на правом краю + отступ + полширины блока
                yes_center_x = if_obj.position[0] + if_obj.width + 80 + 60
                yes_r = Render(self.page, node["children"], x=0, y=if_cy, prev_obj=if_obj, entry_root="yes", center_x=yes_center_x)
                yes_r.render()

                # ветка NO — левее ромба
                if node.get("else_children"):
                    no_center_x = if_obj.position[0] - 80 - 60
                    no_r = Render(self.page, node["else_children"], x=0, y=if_cy, prev_obj=if_obj, entry_root="no", center_x=no_center_x)
                    no_r.render()
                    no_end_obj = no_r.prev_obj
                    no_end_y = no_r.perv_obj_xy[1]
                else:
                    no_end_obj = None
                    no_end_y = if_cy

                merge_y = max(yes_r.perv_obj_xy[1] + 40, no_end_y + 40) + self.step_y
                waypoint = Waypoint(self.page, if_cx - 1, merge_y)

                Pointer(self.page, yes_r.prev_obj, waypoint)

                if no_end_obj:
                    Pointer(self.page, no_end_obj, waypoint)
                else:
                    Pointer(self.page, if_obj, waypoint, root="no")

                self._place(waypoint)

            elif node["type"] == "while":
                while_obj = While(self.page, node["value"], 0, self.perv_obj_xy[1] + self.step_y, center_x=self.center_x)
                if self.prev_obj:
                    self._connect(self.prev_obj, while_obj)
                self._place(while_obj)

                while_cx = while_obj.position[0] + while_obj.width // 2
                while_cy = while_obj.position[1] + while_obj.height // 2

                anker = Waypoint(self.page, while_cx - 1, while_obj.position[1] - 5)

                body_center_x = while_cx
                body_r = Render(self.page, node["children"], x=0, y=while_obj.position[1] + while_obj.height, prev_obj=while_obj, entry_root="yes", center_x=body_center_x)
                body_r.render()

                Pointer(self.page, body_r.prev_obj, anker)

                exit_y = max(body_r.perv_obj_xy[1] + 40, while_obj.position[1] + while_obj.height + 40) + self.step_y
                exit_wp = Waypoint(self.page, while_cx - 1, exit_y)

                Pointer(self.page, while_obj, exit_wp, root="no")

                self._place(exit_wp)

        return self.prev_obj


test = drawpyo.File()
test.file_path = "/workspaces/Fragmos/webapp/pages/fragmos"
test.file_name = "Xuita.xml"

nodes = [
    {"type": "start", "value": "Начало"},
    {"type": "process", "value": "a = yes"},
    {
        "type": "if",
        "value": "a = yes",
        "children": [
            {"type": "process", "value": "b = no"},
            {
                "type": "if",
                "value": "b = no",
                "children": [
                    {"type": "process", "value": "output >> 'both'"},
                ],
                "else_children": [
                    {"type": "process", "value": "output >> 'only a'"},
                ]
            },
        ],
        "else_children": [
            {"type": "process", "value": "output >> 'a is false'"},
        ]
    },
    {"type": "stop", "value": "Конец"}
]

page = drawpyo.Page(file=test)

renderer = Render(page, nodes, x=100, y=0, center_x=200)
renderer.render()

test.write()