import base64
import datetime
import json
import os
import uuid
import httpx
import reflex as rx

from .auth_state import AuthState

# ── Constants ──────────────────────────────────────────────────────────────────
_STATE_DIR = os.path.dirname(os.path.abspath(__file__))
API_URL    = os.getenv("FASTAPI_URL", "http://localhost:8001")

KLASSIS_COST = 30          # фиксированная стоимость генерации в токенах
LANGUAGES    = ["C++", "C#"]

_EMPTY_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<mxGraphModel><root>'
    '<mxCell id="0"/><mxCell id="1" parent="0"/>'
    '</root></mxGraphModel>'
)

_DRAWIO_URL = (
    "https://embed.diagrams.net/"
    "?embed=1&proto=json&spin=1&noExitBtn=1&dark=1"
)


def _make_diagram_html(xml: str) -> str:
    xml_json = json.dumps(xml)
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<style>*{margin:0;padding:0;box-sizing:border-box}"
        "html,body{width:100%;height:100%;background:#141820;overflow:hidden}"
        "iframe{display:block;width:100%;height:100%;border:none}"
        "</style></head><body>"
        f"<iframe id='f' src='{_DRAWIO_URL}'></iframe>"
        "<script>"
        f"var xml={xml_json};"
        "var f=document.getElementById('f');"
        "window.addEventListener('message',function(e){"
        "if(e.source!==f.contentWindow)return;"
        "try{var m=JSON.parse(e.data);"
        "if(m.event==='init'){"
        "f.contentWindow.postMessage(JSON.stringify({action:'load',xml:xml}),'*');"
        "}}catch(ex){}});"
        "</script></body></html>"
    )


class KlassisState(rx.State):

    # ── Auth ──────────────────────────────────────────────────────────────────
    user_uuid:   str = ""
    user_tokens: int = 0

    # ── Diagrams list ─────────────────────────────────────────────────────────
    chats:            list[dict] = []
    selected_chat_id: str        = ""

    # ── Generation ────────────────────────────────────────────────────────────
    code_input:       str  = ""
    is_generating:    bool = False
    generation_error: str  = ""
    selected_language: str = "C++"

    # ── Delete confirm ────────────────────────────────────────────────────────
    delete_confirm_id:   str  = ""
    delete_confirm_open: bool = False

    # ─────────────────────────────────────────────────────────────────────────
    # Computed vars
    # ─────────────────────────────────────────────────────────────────────────

    @rx.var
    def selected_chat(self) -> dict:
        for c in self.chats:
            if c["id"] == self.selected_chat_id:
                return c
        return {"id": "", "name": "", "xml_content": "", "filename": "", "timestamp": ""}

    @rx.var
    def has_selected(self) -> bool:
        return self.selected_chat_id != ""

    @rx.var
    def can_submit(self) -> bool:
        return len(self.code_input.strip()) > 0

    @rx.var
    def diagram_src(self) -> str:
        if not self.selected_chat_id:
            return ""
        xml     = self.selected_chat.get("xml_content", "")
        html    = _make_diagram_html(xml)
        encoded = base64.b64encode(html.encode("utf-8")).decode("ascii")
        return f"data:text/html;base64,{encoded}"

    @rx.var
    def balance_label(self) -> str:
        return f"{self.user_tokens} токенов"

    @rx.var
    def cost_label(self) -> str:
        return f"Стоимость: {KLASSIS_COST} токенов"

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _diagrams_dir(self) -> str:
        if not self.user_uuid:
            return os.path.normpath(
                os.path.join(_STATE_DIR, "../../../../server/files/users/default/klassis")
            )
        return os.path.normpath(
            os.path.join(_STATE_DIR, f"../../../../server/files/users/{self.user_uuid}/klassis")
        )

    def _reload_diagrams(self):
        d = self._diagrams_dir()
        os.makedirs(d, exist_ok=True)
        result: list[dict] = []
        try:
            files = [f for f in os.listdir(d) if f.endswith(".xml")]
        except OSError:
            files = []
        files.sort(key=lambda f: os.path.getmtime(os.path.join(d, f)), reverse=True)
        for fname in files:
            fpath = os.path.join(d, fname)
            name  = os.path.splitext(fname)[0]
            ts    = datetime.datetime.fromtimestamp(
                os.path.getmtime(fpath)
            ).strftime("%d %b, %H:%M")
            try:
                xml_content = open(fpath, encoding="utf-8").read()
            except Exception:
                xml_content = _EMPTY_XML
            result.append({
                "id":          fname,
                "name":        name,
                "timestamp":   ts,
                "xml_content": xml_content,
                "filename":    fname,
            })
        self.chats = result

    async def _sync_auth(self):
        auth = await self.get_state(AuthState)
        if auth.user_uuid:
            self.user_uuid   = auth.user_uuid
            self.user_tokens = auth.tokens_left

    async def _deduct_tokens(self, amount: int) -> tuple[bool, str]:
        if not self.user_uuid:
            return False, "Не авторизован"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.patch(
                    f"{API_URL}/user/{self.user_uuid}",
                    json={"item": "tokens_left", "olditem": "minus", "newitem": str(amount)},
                    timeout=10,
                )
                data = resp.json()
        except Exception as exc:
            return False, f"Ошибка API: {exc}"

        if "error" in data:
            return False, data["error"]

        # Обновляем локальный баланс
        success_msg = data.get("success", "")
        if ": " in success_msg:
            try:
                self.user_tokens = int(success_msg.split(": ")[1])
            except Exception:
                self.user_tokens -= amount
        else:
            self.user_tokens -= amount

        auth = await self.get_state(AuthState)
        auth.tokens_left = self.user_tokens
        return True, ""

    # ─────────────────────────────────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────────────────────────────────

    async def on_load(self):
        await self._sync_auth()
        self._reload_diagrams()

    # ─────────────────────────────────────────────────────────────────────────
    # Actions
    # ─────────────────────────────────────────────────────────────────────────

    def set_language(self, lang: str):
        self.selected_language = lang

    def on_new_click(self):
        self.selected_chat_id = ""
        self.code_input = ""
        self.generation_error = ""

    def on_select_chat(self, chat_id: str):
        self.selected_chat_id = chat_id

    async def on_submit(self):
        if not self.code_input.strip():
            return
        if not self.user_uuid:
            self.generation_error = "Требуется авторизация"
            return
        if self.user_tokens < KLASSIS_COST:
            self.generation_error = (
                f"Недостаточно токенов. "
                f"Требуется: {KLASSIS_COST}, баланс: {self.user_tokens}"
            )
            return

        saved_code = self.code_input
        self.is_generating    = True
        self.generation_error = ""
        yield

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API_URL}/klassis/generate",
                    json={
                        "code":      saved_code,
                        "language":  self.selected_language,
                        "user_uuid": self.user_uuid,
                    },
                    timeout=30,
                )
                data = resp.json()
        except Exception as exc:
            self.generation_error = f"Ошибка соединения: {exc}"
            self.is_generating = False
            return

        if "error" in data:
            self.generation_error = data["error"]
            self.is_generating = False
            return

        if "xml_filename" not in data:
            self.generation_error = "Неожиданный ответ сервера. Перезапустите сервер и попробуйте снова."
            self.is_generating = False
            return

        # Списываем токены
        ok, err = await self._deduct_tokens(KLASSIS_COST)
        if not ok:
            self.generation_error = f"Ошибка списания токенов: {err}"
            self.is_generating = False
            return

        fname = data.get("xml_filename", "")
        self._reload_diagrams()
        if fname:
            self.selected_chat_id = fname

        self.is_generating = False

    def on_download(self):
        xml      = self.selected_chat.get("xml_content", "")
        name     = self.selected_chat.get("name", "diagram")
        filename = json.dumps(f"{name}.xml")
        xml_js   = json.dumps(xml)
        js = (
            f"(function(){{"
            f"var b=new Blob([{xml_js}],{{type:'text/xml;charset=utf-8'}});"
            f"var u=URL.createObjectURL(b);"
            f"var a=document.createElement('a');"
            f"a.href=u;a.download={filename};"
            f"document.body.appendChild(a);a.click();"
            f"document.body.removeChild(a);URL.revokeObjectURL(u);"
            f"}})();"
        )
        return rx.call_script(js)

    def on_request_delete(self, chat_id: str):
        self.delete_confirm_id   = chat_id
        self.delete_confirm_open = True

    def on_cancel_delete(self):
        self.delete_confirm_open = False
        self.delete_confirm_id   = ""

    def on_confirm_delete(self):
        cid = self.delete_confirm_id
        d   = self._diagrams_dir()
        for c in self.chats:
            if c["id"] == cid:
                fpath = os.path.join(d, c["filename"])
                try:
                    os.remove(fpath)
                except OSError:
                    pass
                break
        if self.selected_chat_id == cid:
            self.selected_chat_id = ""
        self.delete_confirm_open = False
        self.delete_confirm_id   = ""
        self._reload_diagrams()
