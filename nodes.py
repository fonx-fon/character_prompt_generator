import json
import re
import urllib.error
import urllib.parse
import urllib.request

from .prompts import SYSTEM_PROMPTS

DEFAULT_URL = "http://127.0.0.1:11434"
CATEGORY = "CharacterPromptGenerator"

MAX_SEED = 2**31 - 1  # Ollamaのseedはint32範囲に収める


# ---------------------------------------------------------------------------
# Ollama HTTP ヘルパー (標準ライブラリのみ)
# ---------------------------------------------------------------------------

def _http_json(method, url, payload=None, timeout=120):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            msg = json.loads(body).get("error", body)
        except (json.JSONDecodeError, AttributeError):
            msg = body
        raise RuntimeError(f"Ollama error ({e.code}): {msg}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"Cannot reach Ollama at {url}: {e.reason}") from None
    return json.loads(body) if body else {}


def _fetch_model_names(base_url, timeout=5):
    data = _http_json("GET", f"{base_url.rstrip('/')}/api/tags", timeout=timeout)
    names = []
    for m in data.get("models", []):
        name = m.get("model") or m.get("name")
        if name:
            names.append(name)
    return names


# 起動時に一度だけデフォルトURLからモデル一覧を試みる。
# 失敗してもよい (ノード上の再取得ボタンでいつでも取り直せる)。
_startup_models = None


def _startup_model_list():
    global _startup_models
    if _startup_models is None:
        try:
            _startup_models = _fetch_model_names(DEFAULT_URL, timeout=1.5)
        except Exception:
            _startup_models = []
    return _startup_models


# ---------------------------------------------------------------------------
# ノード定義
# ---------------------------------------------------------------------------

class CPGLLMConnection:
    @classmethod
    def INPUT_TYPES(cls):
        models = _startup_model_list() or [""]
        return {
            "required": {
                "url": ("STRING", {"default": DEFAULT_URL}),
                "model": (models, {}),
                "timeout": ("INT", {"default": 120, "min": 1, "max": 3600}),
            }
        }

    RETURN_TYPES = ("LLM_CONNECTION",)
    FUNCTION = "build"
    CATEGORY = CATEGORY

    @classmethod
    def VALIDATE_INPUTS(cls, model):
        # モデルコンボはJS側で動的に差し替えるため、リスト照合の検証はしない。
        # 実在しないモデル名は実行時にOllamaがエラーを返す。
        return True

    def build(self, url, model, timeout):
        return ({"url": url.rstrip("/"), "model": model, "timeout": timeout},)


class CPGLLMOptions:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "temperature": ("FLOAT", {"default": 0.8, "min": 0.0, "max": 2.0, "step": 0.05}),
                "top_p": ("FLOAT", {"default": 0.9, "min": 0.0, "max": 1.0, "step": 0.01}),
                # think有効時は思考トークンもこの枠を消費するため大きめを既定に
                "num_predict": ("INT", {"default": 4096, "min": 1, "max": 65536}),
                "num_ctx": ("INT", {"default": 8192, "min": 512, "max": 262144}),
                "keep_alive_min": ("INT", {"default": 5, "min": 0, "max": 1440}),
            }
        }

    RETURN_TYPES = ("LLM_OPTIONS",)
    FUNCTION = "build"
    CATEGORY = CATEGORY

    def build(self, temperature, top_p, num_predict, num_ctx, keep_alive_min):
        return ({
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": num_predict,
            "num_ctx": num_ctx,
            "keep_alive_min": keep_alive_min,
        },)


class CPGCharacter:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "name": ("STRING", {"default": ""}),
                "attributes": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "prev": ("CHARACTER_LIST",),
            },
        }

    RETURN_TYPES = ("CHARACTER_LIST",)
    FUNCTION = "build"
    CATEGORY = CATEGORY

    def build(self, name, attributes, prev=None):
        chars = list(prev) if prev else []
        chars.append({"name": name.strip(), "attributes": attributes.strip()})
        return (chars,)


class CPGGenerate:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "connection": ("LLM_CONNECTION",),
                "characters": ("CHARACTER_LIST",),
                "scene": ("STRING", {"multiline": True, "default": ""}),
                "think": ("BOOLEAN", {"default": True}),
                # strict: 服装も含め一切改変しない / adaptive: 服装だけシーンに合わせて可変
                "outfit": (["strict", "adaptive"], {}),
                # seedはOptionsではなくここに置く。ウィジェット値は定数としてキャッシュ判定に
                # 乗るので、fixedならLLMを呼び直さず、randomizeなら毎回再生成される
                "seed": ("INT", {"default": 0, "min": 0, "max": MAX_SEED, "control_after_generate": True}),
            },
            "optional": {
                "options": ("LLM_OPTIONS",),
                "system_prompt": ("STRING", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("prompt", "thinking")
    FUNCTION = "generate"
    CATEGORY = CATEGORY

    def generate(self, connection, characters, scene, think, outfit, seed, options=None, system_prompt=None):
        if not connection.get("model"):
            raise RuntimeError("No model selected on the LLM Connection node.")
        if not characters:
            raise RuntimeError("No characters connected.")

        if options is None:
            options = {
                "temperature": 0.8,
                "top_p": 0.9,
                "num_predict": 4096,
                "num_ctx": 8192,
                "keep_alive_min": 5,
            }

        blocks = []
        for i, ch in enumerate(characters, 1):
            lines = [f"[IMMUTABLE{i}]"]
            if ch.get("name"):
                lines.append(f"Name: {ch['name']}")
            if ch.get("attributes"):
                lines.append(ch["attributes"])
            blocks.append("\n".join(lines))
        blocks.append(f"[SCENE]\n{scene.strip()}")
        user_prompt = "\n\n".join(blocks)

        # system_prompt接続時は内蔵プロンプトを丸ごと差し替える (空なら内蔵プリセットを使う)
        system = system_prompt.strip() if system_prompt and system_prompt.strip() else SYSTEM_PROMPTS[outfit]

        payload = {
            "model": connection["model"],
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            "think": think,
            "keep_alive": f"{options['keep_alive_min']}m",
            "stream": False,
            "options": {
                "temperature": options["temperature"],
                "top_p": options["top_p"],
                "num_predict": options["num_predict"],
                "num_ctx": options["num_ctx"],
                "seed": seed,
            },
        }

        data = _http_json(
            "POST",
            f"{connection['url']}/api/chat",
            payload,
            timeout=connection["timeout"],
        )
        message = data.get("message", {})
        content = message.get("content", "")
        thinking = message.get("thinking", "") or ""
        # 保険: 応答本文に <think>...</think> が混ざった場合は除去し、thinking側に回す
        inline_thinks = re.findall(r"<think>(.*?)</think>", content, flags=re.DOTALL)
        if inline_thinks:
            thinking = "\n\n".join(filter(None, [thinking.strip()] + [t.strip() for t in inline_thinks]))
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()

        if not content and data.get("done_reason") == "length":
            raise RuntimeError(
                "The model spent the entire num_predict budget on thinking and produced no prompt. "
                "Increase num_predict on the LLM Options node, or turn think off."
            )
        return (content, thinking.strip())


class CPGTextConcat:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"forceInput": True}),
                "added_text": ("STRING", {"multiline": True, "default": ""}),
                "position": (["append", "prepend"], {}),
                "separator": ("STRING", {"default": ", "}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "concat"
    CATEGORY = CATEGORY

    def concat(self, text, added_text, position, separator):
        # 1行ウィジェットでは改行を直接入力できないため、\n と \t を解釈する
        separator = separator.replace("\\n", "\n").replace("\\t", "\t")
        # 片方が空ならセパレータを挟まずそのまま返す
        if not text:
            return (added_text,)
        if not added_text:
            return (text,)
        if position == "prepend":
            return (f"{added_text}{separator}{text}",)
        return (f"{text}{separator}{added_text}",)


# ---------------------------------------------------------------------------
# バックエンドルート (モデル一覧プロキシ / アンロード)
# ComfyUI外からのimportでも壊れないよう try/except で囲む
# ---------------------------------------------------------------------------

try:
    from aiohttp import web
    from server import PromptServer

    _routes = PromptServer.instance.routes

    @_routes.get("/character_prompt_generator/models")
    async def cpg_models(request):
        url = request.query.get("url", DEFAULT_URL).rstrip("/")
        try:
            import asyncio
            names = await asyncio.to_thread(_fetch_model_names, url)
            return web.json_response({"models": names})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=502)

    @_routes.post("/character_prompt_generator/unload")
    async def cpg_unload(request):
        try:
            body = await request.json()
            url = body.get("url", DEFAULT_URL).rstrip("/")
            model = body.get("model")
            if not model:
                return web.json_response({"error": "no model specified"}, status=400)
            import asyncio
            await asyncio.to_thread(
                _http_json, "POST", f"{url}/api/generate",
                {"model": model, "keep_alive": 0}, 30,
            )
            return web.json_response({"ok": True})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=502)

except ImportError:
    pass


NODE_CLASS_MAPPINGS = {
    "CPG_LLMConnection": CPGLLMConnection,
    "CPG_LLMOptions": CPGLLMOptions,
    "CPG_Character": CPGCharacter,
    "CPG_Generate": CPGGenerate,
    "CPG_TextConcat": CPGTextConcat,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CPG_LLMConnection": "LLM Connection (Ollama)",
    "CPG_LLMOptions": "LLM Options",
    "CPG_Character": "Character",
    "CPG_Generate": "Generate Character Prompt",
    "CPG_TextConcat": "Text Concat",
}
