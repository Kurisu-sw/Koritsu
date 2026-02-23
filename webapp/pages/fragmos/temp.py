import drawpyo
import os

if os.path.exists("/workspaces/Fragmos/webapp/pages/fragmos/Xuita.xml"):
    os.remove("/workspaces/Fragmos/webapp/pages/fragmos/Xuita.xml")
#========================================================================
#Описание классов для блоков диаграммы
#========================================================================

# Блок начало / конец
class Base(drawpyo.diagram.Object):  
    def __init__(self, page, value, x, y):
        super().__init__(page=page)
        self.value = value
        self.width = 120
        self.height = 40
        self.position = (x, y)
        self.apply_style_string("whiteSpace=wrap;rounded=1;dashed=0; whiteSpace=wrap; html=1; arcSize=50;arcSize=50;")
        

# Блок выполнения
class Execute(drawpyo.diagram.Object):
    def __init__(self, page,  value, x, y):
        super().__init__(page=page)
        self.value = value
        self.width = 120 * (( len(value) // 50 ) + 1)
        self.height = 40 * (( len(value) // 50 ) + 1)
        self.position = (x, y)
        self.apply_style_string("rounded=0;whiteSpace=wrap;html=1;")

# Блок условия
class If(drawpyo.diagram.Object):
    def __init__(self, page,  value, x, y):
        super().__init__(page=page)
        self.value = value
        self.width = 200 * (( len(value) // 50 ) + 1)
        self.height = 80 * (( len(value) // 50 ) + 1)
        self.position = (x, y)
        self.apply_style_string("whiteSpace=wrap;html=1;shape=rhombus;")

class While(drawpyo.diagram.Object):
    def __init__(self, page,  value, x, y):
        super().__init__(page=page)
        self.value = value
        self.width = 200 * (( len(value) // 50 ) + 1)
        self.height = 80 * (( len(value) // 50 ) + 1)
        self.position = (x, y)
        self.apply_style_string("whiteSpace=wrap;html=1;shape=rhombus;")


# Блок цикла
class For_default(drawpyo.diagram.Object):
    def __init__(self, page,  value, x, y):
        super().__init__(page=page)
        self.value = value
        self.width = 120 * (( len(value) // 50 ) + 1)
        self.height = 40 * (( len(value) // 50 ) + 1)
        self.position = (x, y)
        self.apply_style_string("shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;fixedSize=1;")

# Блок цикла с ограничением(начало)
class Loop_limit_start(drawpyo.diagram.Object):
    def __init__(self, page,  value, x, y):
        super().__init__(page=page)
        self.value = value
        self.width = 120 * (( len(value) // 50 ) + 1)
        self.height = 40 * (( len(value) // 50 ) + 1)
        self.position = (x, y)
        self.apply_style_string("shape=loopLimit;whiteSpace=wrap;html=1;")
    
# Блок цикла с ограничением (конец)
class Loop_limit_end(drawpyo.diagram.Object):
    def __init__(self, page,  value, x, y):
        super().__init__(page=page)
        self.value = value
        self.width = 120 * (( len(value) // 50 ) + 1)
        self.height = 40 * (( len(value) // 50 ) + 1)
        self.position = (x, y)
        self.apply_style_string("shape=loopLimit;whiteSpace=wrap;html=1;direction=west;")

# Блок подпрограммы
class Proccess(drawpyo.diagram.Object):
    def __init__(self, page,  value, x, y):
        super().__init__(page=page)
        self.value = value
        self.width = 120 * (( len(value) // 50 ) + 1)
        self.height = 40 * (( len(value) // 50 ) + 1)
        self.position = (x, y)
        self.apply_style_string("shape=process;whiteSpace=wrap;html=1;backgroundOutline=1;")

# Отрисовка стрелок

class Pointer(drawpyo.diagram.Edge):
    def __init__(self, page, source, target,root=None, x=None, y=None):
        super().__init__(page=page,)
        self.source = source
        self.target = target
        self.root = root
        self.pointer_type()
        self.edgeXY = (x,y)

    def pointer_type(self):
        if self.source.position[1] > self.target.position[1]:
            self.add_point_pos((self.source.position[0] - self.source.width//2, self.source.position[1]+ self.source.height + 10))
            self.apply_style_string("endArrow=classic;html=1;rounded=0;waypoint=orthogonal;exitX=0.5;exitY=1;entryX=0.5;entryY=0;") 
        if self.source.position[1] < self.target.position[1]:
            self.apply_style_string("endArrow=none;html=1;rounded=0;waypoint=orthogonal;exitX=0.5;exitY=1;")


        if (type(self.source) == If and self.root == "yes"):
            self.apply_style_string("exitX=1;exitY=0.5;waypoint=orthogonal;")
        if (type(self.source) == If and self.root == "no"):
            self.apply_style_string("exitX=0;exitY=0.5;waypoint=orthogonal;")

        if (type(self.source) == While and self.root == "yes"):
            self.apply_style_string("exitX=0.5;exitY=1;waypoint=orthogonal;")
        if (type(self.source) == While and self.root == "no"):
            self.add_point_pos((self.source.position[0] + self.source.width + 5 , self.source.position[1] + self.source.height//2))
            self.add_point_pos((self.target.position[0] + self.target.width//2, self.target.position[1] - 10))
            self.apply_style_string("exitX=1;exitY=0.5;waypoint=orthogonal;entryX=0.5;entryY=0;")

class Waypoint(drawpyo.diagram.Object):
    def __init__(self, page, x, y):
        super().__init__(page=page)
        self.position = (x, y)
        self.opacity = 0
        self.width = 1
        self.height = 1
        self.apply_style_string("shape=waypoint;sketch=0;fillStyle=solid;size=6;pointerEvents=1;points=[];fillColor=none;resizable=0;rotatable=0;perimeter=centerPerimeter;snapToPoint=1;opacity=0;")

            
    

# TODO : класс форматирования текста 

class Text_format(drawpyo.diagram.Object):
    def __init__(self, page,  value, x, y,width=20,height=15):
        super().__init__(page=page)
        self.value = value
        self.width = width
        self.height = height
        self.position = (x, y)    
        self.apply_style_string("text;html=1;whiteSpace=wrap;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;rounded=0;")





class Render():
    def __init__(self, page, nodes,):
        self.page   = page
        self.nodes  = nodes
        self.perv_obj_xy = (100,0)        
        self.step_x = 0  
        self.step_y = 0 
    def render(self):
        for node in self.nodes:
            if node["type"] == "start":
                Base(self.page, node["value"],self.perv_obj_xy[0] + self.step_x, self.perv_obj_xy[1] + self.step_y)
                self.perv_obj_xy = (self.perv_obj_xy[0] + self.step_x, self.perv_obj_xy[1] + self.step_y)
            if node["type"] == "process":
                Proccess(self.page, node["value"], self.perv_obj_xy[0] + self.step_x, self.perv_obj_xy[1] + self.step_y)
                self.perv_obj_xy = (self.perv_obj_xy[0] + self.step_x, self.perv_obj_xy[1] + self.step_y)
            if node["type"] == "stop":
                Base(self.page, node["value"], self.perv_obj_xy[0] + self.step_x, self.perv_obj_xy[1] + self.step_y)
                self.perv_obj_xy = (self.perv_obj_xy[0] + self.step_x, self.perv_obj_xy[1] + self.step_y)

            self.step_y += 100









# obj_start = Base(page, "Начало", 140,20)

# obj_if1 = If(page, "Если пенис большой", 100, 100)
# obj1_if1_no = Proccess(page, "Выполнение", 10, 280)

# obj_if2_if1_yes = If(page, "Если пенис очень большой", 240, 240) 
# obj_if2_yes = Proccess(page, "Выполнение 3", 350, 360) 
# obj_if2_no = Proccess(page, "Выполнение 4", 140, 360) 

# obj_end = Base(page, "Конец", 140, 510)

# pointer = Pointer(page, obj_start, obj_if1)

# pointer1 = Pointer(page, obj_if1, obj1_if1_no, root="no")
# pointer2 = Pointer(page, obj_if1, obj_if2_if1_yes, root="yes")
# pointer3 = Pointer(page, obj_if2_if1_yes, obj_if2_yes, root="yes")
# pointer4 = Pointer(page, obj_if2_if1_yes, obj_if2_no, root="no")


# pointer5 = Pointer(page, obj1_if1_no, obj_end)
# pointer6 = Pointer(page, obj_if2_yes, obj_end)
# pointer7 = Pointer(page, obj_if2_no, obj_end)

# obj_start = Base(page, "Начало", 450,20)
# obj_end = Base(page, "Конец", 450, 450)


# obj_while = While(page, "Пока ", 410, 110)
# obj1_while = Proccess(page, "Выполнение 1", 450, 220)


# anker = Waypoint(page, obj_while.position[0] + obj_while.width//2, obj_while.position[1] - 5)
# pointer = Pointer(page,obj1_while, anker)

# pointer  = Pointer(page, obj_start, obj_while)
# pointer1 = Pointer(page, obj_while, obj1_while, root="yes")

# pointer5 = Pointer(page, obj_while, obj_end, root="no")
