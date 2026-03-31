#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# start.sh — запустить Koritsu (Reflex + FastAPI/uvicorn)
#
# Использование (из WSL):
#   ./start.sh          # запуск
#   ./start.sh stop     # остановить все процессы
#   ./start.sh status   # показать статус
#   ./start.sh logs     # показать последние строки логов
# ─────────────────────────────────────────────────────────────────────────────

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Активируем виртуальный окружение
if [[ -f "$ROOT/venv/bin/activate" ]]; then
    source "$ROOT/venv/bin/activate"
fi

LOGS="$ROOT/log"
PIDS="$LOGS/pids"

UVICORN_PORT=8001
REFLEX_DIR="$ROOT/webapp/reflex"
SERVER_DIR="$ROOT/server"

# ── Цвета ─────────────────────────────────────────────────────────────────────
GRN="\033[0;32m"; YLW="\033[1;33m"; RED="\033[0;31m"
BLU="\033[0;34m"; CYN="\033[0;36m"; RST="\033[0m"; BLD="\033[1m"

# ── Вспомогательные функции ───────────────────────────────────────────────────

ensure_dirs() {
    mkdir -p "$LOGS" "$PIDS"
}

rotate_logs() {
    for log in reflex uvicorn; do
        local f="$LOGS/${log}.log"
        if [[ -f "$f" ]] && [[ $(wc -c < "$f") -gt 524288 ]]; then
            mv "$f" "${f}.old"
            echo -e "  ${YLW}↻${RST} $log.log > $log.log.old (превысил 512KB)"
        fi
    done
    # удаляем .old старше 7 дней
    find "$LOGS" -name "*.old" -mtime +7 -delete 2>/dev/null || true
}

pid_alive() {
    [[ -n "$1" ]] && kill -0 "$1" 2>/dev/null
}

read_pid() {
    local f="$PIDS/${1}.pid"
    [[ -f "$f" ]] && cat "$f" || echo ""
}

save_pid() {
    echo "$2" > "$PIDS/${1}.pid"
}

remove_pid() {
    rm -f "$PIDS/${1}.pid"
}

# ── stop ──────────────────────────────────────────────────────────────────────

cmd_stop() {
    echo -e "${YLW}Останавливаем процессы...${RST}"
    local stopped=0

    for key in reflex uvicorn; do
        local pid; pid=$(read_pid "$key")
        if pid_alive "$pid"; then
            kill "$pid" 2>/dev/null && echo -e "  ${GRN}✓${RST} $key (PID $pid) остановлен"
            stopped=$((stopped + 1))
        else
            echo -e "  ${YLW}·${RST} $key не запущен"
        fi
        remove_pid "$key"
    done

    pkill -f "reflex run" 2>/dev/null && stopped=$((stopped + 1)) || true
    pkill -f "uvicorn service_api" 2>/dev/null && stopped=$((stopped + 1)) || true

    echo -e "${GRN}Готово. Остановлено: $stopped процессов.${RST}"
}

# ── status ────────────────────────────────────────────────────────────────────

cmd_status() {
    echo -e "${BLD}Статус Koritsu:${RST}"
    for key in reflex uvicorn; do
        local pid; pid=$(read_pid "$key")
        if pid_alive "$pid"; then
            echo -e "  ${GRN}● $key${RST}  PID=$pid  запущен"
        else
            echo -e "  ${RED}○ $key${RST}  не запущен"
        fi
    done
}

# ── logs ──────────────────────────────────────────────────────────────────────

cmd_logs() {
    echo -e "${BLD}=== Reflex (последние 30 строк) ===${RST}"
    [[ -f "$LOGS/reflex.log" ]] && tail -30 "$LOGS/reflex.log" || echo "  лог пуст"
    echo ""
    echo -e "${BLD}=== FastAPI/uvicorn (последние 30 строк) ===${RST}"
    [[ -f "$LOGS/uvicorn.log" ]] && tail -30 "$LOGS/uvicorn.log" || echo "  лог пуст"
}

# ── start ─────────────────────────────────────────────────────────────────────

cmd_start() {
    ensure_dirs

    # Проверяем не запущено ли уже
    local rpid; rpid=$(read_pid "reflex")
    local upid; upid=$(read_pid "uvicorn")

    if pid_alive "$rpid" || pid_alive "$upid"; then
        echo -e "${YLW}Koritsu уже запущен. Используй ./start.sh stop чтобы остановить.${RST}"
        cmd_status
        return 1
    fi

    rotate_logs

    echo -e "${BLD}${BLU}Koritsu — запуск...${RST}"
    echo ""

    # Загрузить .env
    if [[ -f "$ROOT/.env" ]]; then
        set -a; source "$ROOT/.env"; set +a
    else
        echo -e "  ${YLW}⚠${RST}  Файл .env не найден."
    fi

    # ── FastAPI / uvicorn ─────────────────────────────────────────────────────
    echo -e "${CYN}[1/2]${RST} Запуск uvicorn (service_api:app) на порту ${BLD}$UVICORN_PORT${RST}"

    cd "$SERVER_DIR"
    nohup "$ROOT/venv/bin/python" -m uvicorn service_api:app \
        --host 127.0.0.1 \
        --port "$UVICORN_PORT" \
        --workers 1 \
        >> "$LOGS/uvicorn.log" 2>&1 &
    save_pid "uvicorn" $!
    cd "$ROOT"

    sleep 1
    local upid2; upid2=$(read_pid "uvicorn")
    if pid_alive "$upid2"; then
        echo -e "   ${GRN}✓${RST} uvicorn запущен (PID $upid2)"
    else
        echo -e "   ${RED}✗${RST} uvicorn не стартовал. Смотри: $LOGS/uvicorn.log"
    fi

    # ── Reflex ────────────────────────────────────────────────────────────────
    echo -e "${CYN}[2/2]${RST} Запуск reflex run в ${BLD}$REFLEX_DIR${RST}"

    cd "$REFLEX_DIR"
    nohup reflex run \
        --frontend-port 3000 \
        --backend-port 8002 \
        --backend-host 0.0.0.0 \
        >> "$LOGS/reflex.log" 2>&1 &
    save_pid "reflex" $!
    cd "$ROOT"

    sleep 3
    local rpid2; rpid2=$(read_pid "reflex")
    if pid_alive "$rpid2"; then
        echo -e "   ${GRN}✓${RST} reflex запущен (PID $rpid2)"
    else
        echo -e "   ${YLW}⚡${RST} reflex стартует (первый запуск может занять 10-30с)"
    fi

    # ── Ссылки ────────────────────────────────────────────────────────────────
    echo ""
    echo -e "${BLD}──────────────────────────────────────${RST}"
    echo -e "  ${GRN}Reflex      ${RST}  http://localhost:3000"
    echo -e "  ${BLU}FastAPI     ${RST}  http://localhost:$UVICORN_PORT"
    echo -e "  ${BLU}API Docs    ${RST}  http://localhost:$UVICORN_PORT/docs"
    echo -e "${BLD}──────────────────────────────────────${RST}"
    echo ""
    echo -e "  Логи:   ./start.sh logs"
    echo -e "  Стоп:   ./start.sh stop"
    echo -e "  Статус: ./start.sh status"
    echo ""
}

# ── Точка входа ───────────────────────────────────────────────────────────────

case "${1:-start}" in
    start)  cmd_start  ;;
    stop)   cmd_stop   ;;
    status) cmd_status ;;
    logs)   cmd_logs   ;;
    restart)
        cmd_stop
        sleep 2
        cmd_start
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
