import asyncio
import base64
import datetime
import json
import os
import sys
import tempfile
import uuid
import reflex as rx
from auth_state import AuthState 

# ── Paths ─────────────────────────────────────────────────────────────────────
_STATE_DIR   = os.path.dirname(os.path.abspath(__file__))
SCHEMES_DIR  = os.path.dirname(os.path.join(_STATE_DIR, f"../../server/files/users/{}"))
BUG_DIR      = os.path.normpath(os.path.join(_STATE_DIR, "../../../db/bug_reports"))
_FRAGMOS_DIR = os.path.normpath(os.path.join(_STATE_DIR, "../../../../modules/fragmos"))

API_URL = "http://localhost:8001"
# ── Models ────────────────────────────────────────────────────────────────────
MODELS: dict[str, str] = {
    "Bauman 19.701": "fvt60bpn6f51khbi7jjt",
    "GU 19.701":     "fvtttdmeunp9a9e48npi",
}

_EMPTY_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<mxGraphModel><root>'
    '<mxCell id="0"/><mxCell id="1" parent="0"/>'
    '</root></mxGraphModel>'
)

# ── Draw.io embed (full desktop UI, dark) ────────────────────────────────────
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


def _run_pipeline(
        code: str,
        xml_path: str,
        cfg: dict,
        model_id: str | None,
        token_budget: int | None):
    """Blocking call to the Fragmos pipeline. Runs in a thread."""
    if _FRAGMOS_DIR not in sys.path:
        sys.path.insert(0, _FRAGMOS_DIR)

    tmp_dir   = tempfile.mkdtemp(prefix="fragmos_")
    code_path = os.path.join(tmp_dir, "code.txt")
    json_path = os.path.join(tmp_dir, "code.json")

    with open(code_path, "w", encoding="utf-8") as f:
        f.write(code)

    try:
        from pipeline import run as pipeline_run          # type: ignore
        from pipeline import InsufficientTokensError      # type: ignore

        result_path, tokens = pipeline_run(
            code_path, xml_path,
            cfg_overrides=cfg,
            model_id=model_id,
            token_budget=token_budget,
        )
        ai_json = ""
        try:
            with open(json_path, "r", encoding="utf-8") as jf:
                ai_json = jf.read()
        except OSError:
            pass
        return result_path, tokens, ai_json
    finally:
        for p in (code_path, json_path):
            try:
                os.remove(p)
            except OSError:
                pass
        try:
            os.rmdir(tmp_dir)
        except OSError:
            pass


class FragmosState(rx.State):
    # ── Auth ──────────────────────────────────────────────────────────────────
    user_uuid: str = ""  # UUID текущего пользователя (синхронизируется через localStorage)

    # ── Chats ─────────────────────────────────────────────────────────────────
    chats: list[dict] = []
    selected_chat_id: str = ""
    is_generating: bool = False
    code_input: str = ""
    generation_error: str = ""

    # ── Code modal ────────────────────────────────────────────────────────────
    show_code: bool = False

    # ── Bug report ────────────────────────────────────────────────────────────
    bug_open: bool = False
    bug_text: str = ""
    bug_saved: bool = False
    last_ai_response: str = ""
    last_submitted_code: str = ""
    last_tokens: int = 0   # charged tokens за последнюю генерацию

    # ── Token balance ─────────────────────────────────────────────────────────
    user_tokens: int = 10000   # баланс токенов пользователя

    # ── File upload ───────────────────────────────────────────────────────────
    is_uploading: bool = False
    upload_result: str = ""

    # ── Settings ──────────────────────────────────────────────────────────────
    settings_open: bool = False
    selected_model: str = "Bauman 19.701"

    cfg_show_bbox:            bool = True
    cfg_gap_y:                int  = 40
    cfg_if_branch_gap:        int  = 20
    cfg_while_corridor_base:  int  = 80
    cfg_if_branch_vgap:       int  = 15
    cfg_if_branch_min_gap:    int  = 40
    cfg_while_corridor_step:  int  = 20
    cfg_while_corridor_min:   int  = 30
    cfg_while_back_turn_gap:  int  = 20
    cfg_while_back_top_gap:   int  = 15

    # ── Delete confirmation ───────────────────────────────────────────────────
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
        return {"id": "", "name": "", "code": "", "xml_content": "",
                "filename": "", "timestamp": ""}

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
    def model_list(self) -> list[str]:
        return list(MODELS.keys())

    @rx.var
    def tokens_label(self) -> str:
        """Метка с потраченными токенами последней генерации."""
        if self.last_tokens <= 0:
            return ""
        return f"{self.last_tokens} токенов"

    @rx.var
    def balance_label(self) -> str:
        """Метка с текущим балансом пользователя."""
        return f"{self.user_tokens} токенов"

    # ─────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _reload_schemes(self):
        """Перезагружает список схем из локальной папки"""
        os.makedirs(SCHEMES_DIR, exist_ok=True)
        result: list[dict] = []
        try:
            files = [f for f in os.listdir(SCHEMES_DIR) if f.endswith(".xml")]
        except OSError:
            files = []
        files.sort(
            key=lambda f: os.path.getmtime(os.path.join(SCHEMES_DIR, f)),
            reverse=True,
        )
        for fname in files:
            fpath = os.path.join(SCHEMES_DIR, fname)
            name  = os.path.splitext(fname)[0]
            mtime = os.path.getmtime(fpath)
            ts    = datetime.datetime.fromtimestamp(mtime).strftime("%d %b, %H:%M")
            try:
                xml_content = open(fpath, encoding="utf-8").read()
            except Exception:
                xml_content = _EMPTY_XML
            result.append({
                "id":          fname,
                "name":        name,
                "timestamp":   ts,
                "code":        "",
                "xml_content": xml_content,
                "filename":    fname,
            })
        self.chats = result

    def _cfg_dict(self) -> dict:
        return {
            "gap_y":               self.cfg_gap_y,
            "if_branch_gap":       self.cfg_if_branch_gap,
            "if_branch_vgap":      self.cfg_if_branch_vgap,
            "if_branch_min_gap":   self.cfg_if_branch_min_gap,
            "while_corridor_base": self.cfg_while_corridor_base,
            "while_corridor_step": self.cfg_while_corridor_step,
            "while_corridor_min":  self.cfg_while_corridor_min,
            "while_back_turn_gap": self.cfg_while_back_turn_gap,
            "while_back_top_gap":  self.cfg_while_back_top_gap,
            "show_bbox":           self.cfg_show_bbox,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Page lifecycle
    # ─────────────────────────────────────────────────────────────────────────

    def on_load(self):
        self._reload_schemes()

    def set_user_uuid(self, uuid: str):
        """Устанавливает UUID пользователя"""
        self.user_uuid = uuid

    # ─────────────────────────────────────────────────────────────────────────
    # Chat actions
    # ─────────────────────────────────────────────────────────────────────────

    def on_new_chat_click(self):
        self.selected_chat_id = ""
        self.code_input = ""
        self.show_code = False
        self.generation_error = ""

    async def on_submit_code(self):
        if not self.code_input.strip():
            return

        os.makedirs(SCHEMES_DIR, exist_ok=True)
        slug = str(uuid.uuid4())[:8]
        fname = f"Схема_{slug}.xml"
        xml_path = os.path.join(SCHEMES_DIR, fname)

        saved_code = self.code_input
        self.code_input = ""
        self.is_generating = True
        self.generation_error = ""
        self.last_submitted_code = saved_code
        yield

        success = False
        try:
            _result, tokens, ai_json = await asyncio.to_thread(
                _run_pipeline,
                saved_code,
                xml_path,
                self._cfg_dict(),
                MODELS.get(self.selected_model),
                self.user_tokens,
            )
            self.last_tokens = tokens
            self.last_ai_response = ai_json
            self.user_tokens = max(0, self.user_tokens - tokens)
            success = True
        except Exception as exc:
            self.generation_error = str(exc)
            self.last_tokens = 0
            self.last_ai_response = str(exc)
            try:
                if os.path.exists(xml_path):
                    os.remove(xml_path)
            except OSError:
                pass

        if success:
            self._reload_schemes()
            self.selected_chat_id = fname

        self.is_generating = False

    def on_select_chat(self, chat_id: str):
        self.selected_chat_id = chat_id
        self.show_code = False

    # ─────────────────────────────────────────────────────────────────────────
    # Code modal
    # ─────────────────────────────────────────────────────────────────────────

    def on_toggle_code_modal(self):
        self.show_code = not self.show_code

    def on_close_modal(self):
        self.show_code = False

    # ─────────────────────────────────────────────────────────────────────────
    # Download
    # ─────────────────────────────────────────────────────────────────────────

    def on_download(self):
        xml      = self.selected_chat.get("xml_content", "")
        name     = self.selected_chat.get("name", "scheme")
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

    # ─────────────────────────────────────────────────────────────────────────
    # Upload schemes to Yandex Files API (удалено, т.к. схемы уже в API)
    # ─────────────────────────────────────────────────────────────────────────

    # ─────────────────────────────────────────────────────────────────────────
    # Bug report
    # ─────────────────────────────────────────────────────────────────────────

    def on_open_bug(self):
        self.bug_open  = True
        self.bug_text  = ""
        self.bug_saved = False

    def on_close_bug(self):
        self.bug_open = False

    def on_save_bug(self):
        os.makedirs(BUG_DIR, exist_ok=True)
        rid  = str(uuid.uuid4())
        now  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        md = (
            f"# Bug Report\n\n"
            f"## UUID\n{rid}\n\n"
            f"## Код\n```\n{self.last_submitted_code}\n```\n\n"
            f"## Ответ нейросети (JSON)\n```json\n{self.last_ai_response}\n```\n\n"
            f"## Списано токенов\n{self.last_tokens}\n\n"
            f"## Комментарий\n{self.bug_text}\n\n"
            f"## Дата\n{now}\n"
        )
        path = os.path.join(BUG_DIR, f"bug_{rid[:8]}.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)
        self.bug_saved = True

    # ─────────────────────────────────────────────────────────────────────────
    # Settings
    # ─────────────────────────────────────────────────────────────────────────

    def on_open_settings(self):
        self.settings_open = True

    def on_close_settings(self):
        self.settings_open = False

    def set_model(self, val: str):
        self.selected_model = val

    # ─────────────────────────────────────────────────────────────────────────
    # Delete confirmation
    # ─────────────────────────────────────────────────────────────────────────

    def on_request_delete(self, chat_id: str):
        self.delete_confirm_id   = chat_id
        self.delete_confirm_open = True

    def on_cancel_delete(self):
        self.delete_confirm_open = False
        self.delete_confirm_id   = ""

    def on_confirm_delete(self):
        cid = self.delete_confirm_id
        for c in self.chats:
            if c["id"] == cid:
                fpath = os.path.join(SCHEMES_DIR, c["filename"])
                try:
                    os.remove(fpath)
                except OSError:
                    pass
                break
        if self.selected_chat_id == cid:
            self.selected_chat_id = ""
        self.delete_confirm_open = False
        self.delete_confirm_id = ""
        self._reload_schemes()

    # ─────────────────────────────────────────────────────────────────────────
    # Regenerate / Share (stubs)
    # ─────────────────────────────────────────────────────────────────────────

    def on_share(self): pass

    async def on_regenerate(self):
        if not self.selected_chat_id:
            return
        self.is_generating = True
        yield
        await asyncio.sleep(1)
        self._reload_schemes()
        self.is_generating = False
