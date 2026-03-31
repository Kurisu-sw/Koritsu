import re


# ═══════════════════════════════════════════════════════════════════════════
# МАППИНГ КЛЮЧЕВЫХ СЛОВ .frg → внутренние типы
# ═══════════════════════════════════════════════════════════════════════════

_KEYWORD_MAP = {
    'START':      'start',
    'STOP':       'stop',
    'EXEC':       'execute',
    'PROCESS':    'process',
    'IO':         'io',
    'LOOP_START': 'loop_limit_start',
    'LOOP_END':   'loop_limit_end',
    'IF':         'if',
    'WHILE':      'while',
    'FOR':        'for_default',
}

# Ключевые слова, которые открывают блок (закрываются через END)
_BLOCK_KEYWORDS = {'IF', 'WHILE', 'FOR'}

# Регулярка для извлечения текста в кавычках
_QUOTED_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')


# ═══════════════════════════════════════════════════════════════════════════
# ЕДИНАЯ ТОЧКА ВХОДА
# ═══════════════════════════════════════════════════════════════════════════

def parse_frg(text, base_cfg=None):
    """
    Парсит текст .frg формата.
    Возвращает (cfg, nodes).
    """
    from builder import DEFAULT_CFG
    cfg = dict(base_cfg or DEFAULT_CFG)

    lines = _preprocess(text)

    # Парсим CONFIG если есть
    start_idx = 0
    if lines and lines[0][1] == 'CONFIG:':
        start_idx = _parse_config(lines, cfg)

    nodes = _parse_block(lines, start_idx, len(lines))[0]
    return cfg, nodes


def parse_frg_file(path, base_cfg=None):
    """Читает файл и парсит его."""
    with open(path, encoding='utf-8') as f:
        return parse_frg(f.read(), base_cfg)


# Обратная совместимость
parse_frg_json = parse_frg
parse_frg_json_file = parse_frg_file


# ═══════════════════════════════════════════════════════════════════════════
# ПРЕДОБРАБОТКА
# ═══════════════════════════════════════════════════════════════════════════

def _preprocess(text):
    """
    Разбивает текст на строки, убирает пустые, комментарии, лишние пробелы.
    Возвращает список (номер_строки, строка) для сообщений об ошибках.
    """
    result = []
    for i, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        result.append((i, line))
    return result


# ═══════════════════════════════════════════════════════════════════════════
# ПАРСИНГ CONFIG
# ═══════════════════════════════════════════════════════════════════════════

def _parse_config(lines, cfg):
    """
    Парсит секцию CONFIG: ... END.
    Возвращает индекс первой строки после END.
    """
    i = 1  # пропускаем "CONFIG:"
    while i < len(lines):
        lineno, line = lines[i]
        i += 1
        if line.upper() == 'END':
            return i

        # Формат: ключ = значение
        if '=' not in line:
            raise SyntaxError(f"Строка {lineno}: ожидается 'ключ = значение' в CONFIG, получено: {line!r}")

        key, val = line.split('=', 1)
        key = key.strip()
        val = val.strip()

        # Убираем инлайн-комментарий
        if '#' in val:
            val = val[:val.index('#')].strip()

        # Приведение типов
        if val.lower() in ('true', 'false'):
            cfg[key] = val.lower() == 'true'
        else:
            try:
                cfg[key] = int(val)
            except ValueError:
                try:
                    cfg[key] = float(val)
                except ValueError:
                    cfg[key] = val

    raise SyntaxError("CONFIG: не закрыт — отсутствует END")


# ═══════════════════════════════════════════════════════════════════════════
# ОСНОВНОЙ ПАРСЕР БЛОКОВ
# ═══════════════════════════════════════════════════════════════════════════

def _extract_value(line):
    """Извлекает текст в кавычках из строки. Возвращает текст или пустую строку."""
    m = _QUOTED_RE.search(line)
    if m:
        return m.group(1).replace('\\"', '"')
    return ''


def _get_keyword(line):
    """
    Извлекает ключевое слово из строки.
    'IF "условие"' → 'IF'
    'YES:' → 'YES:'
    """
    upper = line.upper()

    # Проверяем двухсловные ключевые слова
    for kw in ('LOOP_START', 'LOOP_END'):
        if upper.startswith(kw):
            return kw

    # Однословные
    word = line.split()[0].upper() if line.split() else ''

    # YES: / NO: — метки веток IF
    if line.rstrip().upper() in ('YES:', 'NO:'):
        return line.rstrip().upper()

    return word


def _parse_block(lines, start, end):
    """
    Парсит линейную последовательность строк [start, end) в список nodes.
    Рекурсивно обрабатывает IF/WHILE/FOR блоки.
    Возвращает (nodes, next_index).
    """
    nodes = []
    i = start

    while i < end:
        lineno, line = lines[i]
        kw = _get_keyword(line)

        if kw == 'END':
            return nodes, i + 1

        if kw == 'IF':
            node, i = _parse_if(lines, i, end)
            nodes.append(node)

        elif kw in ('WHILE', 'FOR'):
            node, i = _parse_loop(lines, i, end, kw)
            nodes.append(node)

        elif kw in _KEYWORD_MAP:
            value = _extract_value(line)
            nodes.append({'type': _KEYWORD_MAP[kw], 'value': value})
            i += 1

        elif kw in ('YES:', 'NO:'):
            # Эти метки обрабатываются внутри _parse_if
            raise SyntaxError(f"Строка {lineno}: {kw} вне блока IF")

        else:
            raise SyntaxError(f"Строка {lineno}: неизвестное ключевое слово: {line.split()[0]!r}")

    return nodes, i


def _parse_if(lines, start, end):
    """
    Парсит IF блок:
        IF "условие"
          YES:
            ...
          NO:
            ...
        END
    """
    lineno, line = lines[start]
    condition = _extract_value(line)
    i = start + 1

    yes_nodes = []
    no_nodes = []

    # Собираем ветки до END
    while i < end:
        lineno_cur, line_cur = lines[i]
        kw = _get_keyword(line_cur)

        if kw == 'END':
            return {
                'type': 'if',
                'value': condition,
                'children': yes_nodes,
                'else_children': no_nodes,
            }, i + 1

        if kw == 'YES:':
            i += 1
            yes_nodes, i = _parse_branch(lines, i, end)

        elif kw == 'NO:':
            i += 1
            no_nodes, i = _parse_branch(lines, i, end)

        else:
            # Если нет YES:/NO: меток — всё тело идёт в YES
            yes_nodes, i = _parse_block(lines, i, end)
            # _parse_block остановится на END
            if i < end:
                lineno_end, line_end = lines[i]
                if _get_keyword(line_end) == 'END':
                    i += 1  # съедаем END

            return {
                'type': 'if',
                'value': condition,
                'children': yes_nodes,
                'else_children': no_nodes,
            }, i

    raise SyntaxError(f"IF на строке {lines[start][0]}: не закрыт — отсутствует END")


def _parse_branch(lines, start, end):
    """
    Парсит содержимое ветки YES: или NO: до следующей метки (NO:, END)
    или до END блока IF.
    """
    nodes = []
    i = start

    while i < end:
        lineno, line = lines[i]
        kw = _get_keyword(line)

        # Ветка заканчивается при NO:, YES: или END
        if kw in ('NO:', 'YES:', 'END'):
            return nodes, i

        if kw == 'IF':
            node, i = _parse_if(lines, i, end)
            nodes.append(node)
        elif kw in ('WHILE', 'FOR'):
            node, i = _parse_loop(lines, i, end, kw)
            nodes.append(node)
        elif kw in _KEYWORD_MAP:
            value = _extract_value(line)
            nodes.append({'type': _KEYWORD_MAP[kw], 'value': value})
            i += 1
        else:
            raise SyntaxError(f"Строка {lineno}: неизвестное ключевое слово: {line.split()[0]!r}")

    return nodes, i


def _parse_loop(lines, start, end, loop_kw):
    """
    Парсит WHILE/FOR блок:
        WHILE "условие"
          ...
        END
    """
    lineno, line = lines[start]
    value = _extract_value(line)
    node_type = _KEYWORD_MAP[loop_kw]

    children, next_i = _parse_block(lines, start + 1, end)

    return {
        'type': node_type,
        'value': value,
        'children': children,
    }, next_i


