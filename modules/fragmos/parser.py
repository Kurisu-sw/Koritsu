"""
parser.py — Трансформирует унифицированный AST (от ast_generators) в список nodes
для Builder, применяя режим отображения из modes/modes.yaml.
"""

import re

from builder import DEFAULT_CFG
from modes import get_mode


# ═══════════════════════════════════════════════════════════════════════════
# ЕДИНАЯ ТОЧКА ВХОДА
# ═══════════════════════════════════════════════════════════════════════════

def parse_ast_to_flowchart(ast_dict: dict, mode_id: str = 'default') -> tuple[dict, list]:
    """
    Преобразует унифицированный AST в (cfg, nodes) для Builder.

    Args:
        ast_dict: {'type': 'program', 'body': [...], 'metadata': {...}}
        mode_id:  ID режима из modes.yaml ('default' | 'loopLimit')

    Returns:
        (cfg, nodes) — конфигурация и список блоков для Builder.

    Raises:
        ValueError: если mode_id не найден.
    """
    mode = get_mode(mode_id)
    cfg = dict(DEFAULT_CFG)
    converter = _Converter(mode, mode_id)
    nodes = converter.convert_program(ast_dict)
    return cfg, nodes


# ═══════════════════════════════════════════════════════════════════════════
# КОНВЕРТЕР
# ═══════════════════════════════════════════════════════════════════════════

class _Converter:
    def __init__(self, mode: dict, mode_id: str = 'default'):
        self._blocks = mode['blocks']
        self._mode_id = mode_id
        self._is_gost = (mode_id == 'loopLimit')

    # ── top level ─────────────────────────────────────────────────────────

    def convert_program(self, ast_dict: dict) -> list:
        """Конвертирует program-узел. Каждая function_def → START…STOP."""
        nodes = []
        for node in ast_dict.get('body', []):
            nodes.extend(self._convert(node))
        # Если нет function_def — оборачиваем всё в START/STOP
        if not any(n.get('type') == 'start' for n in nodes):
            if self._is_gost:
                nodes = (
                    [{'type': 'start', 'value': 'Начало'}]
                    + nodes
                    + [{'type': 'stop', 'value': 'Конец'}]
                )
            else:
                nodes = [{'type': 'start', 'value': ''}] + nodes + [{'type': 'stop', 'value': ''}]
        return nodes

    # ── dispatcher ────────────────────────────────────────────────────────

    def _convert(self, node: dict) -> list:
        t = node.get('type')
        if t == 'function_def':
            return self._function(node)
        if t == 'class_def':
            return self._class_def(node)
        if t == 'if' or t == 'try':
            return [self._if_node(node)]
        if t == 'for':
            return self._for(node)
        if t == 'while':
            return self._while(node)
        if t == 'match':
            if self._is_gost:
                return [self._switch_node(node)]
            return self._match_to_ifs(node)
        if t == 'return':
            return [{'type': 'stop', 'value': node.get('value', '')}]
        if t == 'assignment':
            val = node.get('value', '')
            if self._is_gost:
                val = self._translate_gost(val)
            return [{'type': 'execute', 'value': val}]
        if t == 'call':
            return [{'type': 'process', 'value': node.get('value', '')}]
        if t == 'io':
            return [{'type': 'io', 'value': self._format_io(node.get('value', ''))}]
        if t == 'expression':
            val = node.get('value', '')
            if self._is_gost:
                val = self._translate_gost(val)
            return [{'type': 'execute', 'value': val}]
        return []

    def _convert_body(self, body: list) -> list:
        result = []
        for node in body:
            result.extend(self._convert(node))
        return result

    # ── function_def ──────────────────────────────────────────────────────

    def _function(self, node: dict) -> list:
        name       = node.get('name', '')
        full_value = node.get('value', name)
        body       = node.get('body', [])

        if self._is_gost:
            is_main    = name.lower() in ('main', '__main__')
            start_label = 'Начало' if is_main else f'Начало {name}'
            stop_label  = 'Конец'  if is_main else f'Конец {name}'
        else:
            start_label = full_value
            stop_label  = f'конец {name}'

        nodes = [{'type': 'start', 'value': start_label}]
        body_nodes = self._convert_body(body)
        has_stop = body_nodes and body_nodes[-1].get('type') == 'stop'
        nodes.extend(body_nodes)
        if not has_stop:
            nodes.append({'type': 'stop', 'value': stop_label})
        return nodes

    # ── class_def ─────────────────────────────────────────────────────────

    def _class_def(self, node: dict) -> list:
        """Разворачиваем методы класса как обычные function_def."""
        nodes = []
        for child in node.get('body', []):
            if child.get('type') == 'function_def':
                nodes.extend(self._function(child))
        return nodes

    # ── if / try ──────────────────────────────────────────────────────────

    def _if_node(self, node: dict) -> dict:
        condition = node.get('value', '')
        if self._is_gost:
            condition = self._translate_gost(condition)
        children = self._convert_body(node.get('body', []))
        else_children = self._convert_body(node.get('else_body', []))
        return {
            'type': 'if',
            'value': condition,
            'children': children,
            'else_children': else_children,
        }

    # ── for ───────────────────────────────────────────────────────────────

    def _for(self, node: dict) -> list:
        header = node.get('value', '')
        if self._is_gost:
            header = self._translate_gost(header)
        body = self._convert_body(node.get('body', []))
        block_type = self._blocks.get('for', 'for_default')

        if block_type == 'loop_limit':
            return [
                {'type': 'loop_limit_start', 'value': header},
                *body,
                {'type': 'loop_limit_end', 'value': header},
            ]
        # default: for_default (шестиугольник) с children
        return [{'type': 'for_default', 'value': header, 'children': body}]

    # ── while ─────────────────────────────────────────────────────────────

    def _while(self, node: dict) -> list:
        condition = node.get('value', '')
        if self._is_gost:
            condition = self._translate_gost(condition)
        body = self._convert_body(node.get('body', []))
        block_type = self._blocks.get('while', 'while')

        if block_type == 'loop_limit':
            return [
                {'type': 'loop_limit_start', 'value': condition},
                *body,
                {'type': 'loop_limit_end', 'value': condition},
            ]
        # default: while (ромб с возвратной стрелкой) с children
        return [{'type': 'while', 'value': condition, 'children': body}]

    # ── match → switch (ГОСТ) / вложенные IF (стандарт) ──────────────────

    def _switch_node(self, node: dict) -> dict:
        """ГОСТ: match → switch-блок для специального рендерера."""
        cases = []
        for case in node.get('cases', []):
            pattern = case['pattern']
            body    = self._convert_body(case.get('body', []))
            cases.append({'pattern': pattern, 'body': body})
        return {'type': 'switch', 'value': node.get('value', ''), 'cases': cases}

    def _match_to_ifs(self, node: dict) -> list:
        """Стандарт: match → цепочка вложенных IF."""
        subject = node.get('value', '')
        cases   = node.get('cases', [])

        def build(cases):
            if not cases:
                return None
            case, rest = cases[0], cases[1:]
            body    = self._convert_body(case.get('body', []))
            pattern = case['pattern']
            if pattern == '_':
                return {'_default': body}
            condition = f'{subject} == {pattern}'
            else_body = []
            if rest:
                nxt = build(rest)
                if nxt is not None:
                    else_body = nxt.get('_default', [nxt]) if '_default' in nxt else [nxt]
            return {'type': 'if', 'value': condition, 'body': body, 'else_body': else_body}

        result = build(cases)
        if result is None or '_default' in result:
            return []
        return [result]

    # ═══════════════════════════════════════════════════════════════════════
    # IO ФОРМАТИРОВАНИЕ (оба режима)
    # ═══════════════════════════════════════════════════════════════════════

    def _format_io(self, value: str) -> str:
        """Добавляет префикс 'Вывод:' / 'Ввод:' к IO-блокам для всех языков."""
        v = value.strip()

        # Python: print(...)
        m = re.match(r'^print\s*\((.*)\)$', v, re.DOTALL)
        if m:
            return f'Вывод: {m.group(1).strip()}'

        # Python: a = input() / a = int(input()) / a, b = map(int, input().split())
        m = re.match(r'^([\w\s,\*]+?)\s*=\s*.+\binput\s*\(', v, re.DOTALL)
        if m:
            lhs = m.group(1).strip()
            return f'Ввод: {lhs}'

        # Python: input(...)
        m = re.match(r'^input\s*\((.*)\)$', v, re.DOTALL)
        if m:
            content = m.group(1).strip()
            return f'Ввод: {content}' if content else 'Ввод: данные'

        # C++: cout << ... (с возможной цепочкой << endl / "\n")
        if re.match(r'^cout\s*<<', v):
            content = re.sub(r'^cout\s*<<\s*', '', v)
            content = re.sub(r'\s*<<\s*endl\s*$', '', content)
            content = re.sub(r'\s*<<\s*"\\n"\s*$', '', content)
            content = re.sub(r'\s*<<\s*\'\\n\'\s*$', '', content)
            content = content.rstrip(';').strip()
            return f'Вывод: {content}'

        # C++: cin >> ...
        if re.match(r'^cin\s*>>', v):
            content = re.sub(r'^cin\s*>>\s*', '', v).rstrip(';').strip()
            return f'Ввод: {content}'

        # C++: printf(...)
        m = re.match(r'^printf\s*\((.*)\)$', v, re.DOTALL)
        if m:
            return f'Вывод: {m.group(1).strip()}'

        # C++: scanf(...)
        m = re.match(r'^scanf\s*\((.*)\)$', v, re.DOTALL)
        if m:
            return f'Ввод: {m.group(1).strip()}'

        # C++: puts(...)
        m = re.match(r'^puts\s*\((.*)\)$', v, re.DOTALL)
        if m:
            return f'Вывод: {m.group(1).strip()}'

        # C#: Console.WriteLine(...)
        m = re.match(r'^Console\.WriteLine\s*\((.*)\)$', v, re.DOTALL)
        if m:
            return f'Вывод: {m.group(1).strip()}'

        # C#: Console.Write(...)
        m = re.match(r'^Console\.Write\s*\((.*)\)$', v, re.DOTALL)
        if m:
            return f'Вывод: {m.group(1).strip()}'

        # C#: Console.ReadLine() / Console.Read()
        if re.match(r'^Console\.Read', v):
            return 'Ввод: данные'

        return value

    # ═══════════════════════════════════════════════════════════════════════
    # ГОСТ ПЕРЕВОД ОПЕРАТОРОВ (только режим loopLimit)
    # ═══════════════════════════════════════════════════════════════════════

    def _translate_gost(self, value: str) -> str:
        """Переводит операторы кода в русский псевдокод для режима ГОСТ."""
        v = value

        # Составные присваивания (до замены == и !=)
        v = re.sub(r'(\w+)\s*\+=\s*(.+)',  r'\1 = \1 + \2', v)
        v = re.sub(r'(\w+)\s*-=\s*(.+)',  r'\1 = \1 - \2', v)
        v = re.sub(r'(\w+)\s*\*=\s*(.+)', r'\1 = \1 * \2', v)
        v = re.sub(r'(\w+)\s*/=\s*(.+)',  r'\1 = \1 / \2', v)

        # Инкремент / декремент
        v = re.sub(r'\+\+(\w+)', r'\1 = \1 + 1', v)
        v = re.sub(r'(\w+)\+\+', r'\1 = \1 + 1', v)
        v = re.sub(r'--(\w+)',   r'\1 = \1 - 1', v)
        v = re.sub(r'(\w+)--',   r'\1 = \1 - 1', v)

        # Операторы сравнения (порядок важен: >= до >, <= до <, != до =, == до =)
        v = v.replace('!=', '≠')
        v = v.replace('>=', '≥')
        v = v.replace('<=', '≤')
        v = v.replace('==', '=')

        # Логические операторы
        v = v.replace('&&', 'и')
        v = v.replace('||', 'или')

        # Логическое НЕ: !x → не x (не трогаем уже обработанное ≠)
        v = re.sub(r'!(\w)', r'не \1', v)

        return v
