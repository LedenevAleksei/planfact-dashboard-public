#!/usr/bin/env python3
"""
Веб-обёртка CEO-дашборда (Фаза 2).

Схема безопасности (см. ARCHITECTURE.md):
    Браузер (логин/пароль) → этот backend → API ПланФакта (ключ только на сервере)

Ключ API и логин/пароль берутся ТОЛЬКО из переменных окружения:
    PLANFACT_API_KEY   — ключ ПланФакта (в браузер не попадает)
    DASH_USER          — логин для входа в дашборд
    DASH_PASS          — пароль для входа в дашборд
Локально можно положить их в .env (файл в .gitignore).

Эндпоинты:
    GET  /          — сам дашборд (index.html), за Basic-Auth
    POST /refresh   — пересобрать данные (fetch_data + build), за Basic-Auth
    GET  /health    — проверка живости (без авторизации), для healthcheck Railway

Автообновление: ежедневно в 10:00 по времени Europe/Belgrade.
fetch_data.py и build.py вызываются как отдельные процессы — переиспользуются без изменений.
API остаётся ТОЛЬКО ДЛЯ ЧТЕНИЯ (правило №1).
"""
import os, sys, json, subprocess, threading, functools
from flask import Flask, send_file, Response, jsonify

ROOT = os.path.dirname(os.path.abspath(__file__))
DASH = os.path.join(ROOT, "dashboard")
INDEX = os.path.join(DASH, "index.html")   # build.py пишет index.html внутрь dashboard/
DATA = os.path.join(DASH, "data", "dashboard.json")
TZ = os.environ.get("DASH_TZ", "Europe/Belgrade")

# Локально подхватываем .env (на PaaS переменные заданы в панели, python-dotenv не обязателен)
def _load_dotenv():
    p = os.path.join(ROOT, ".env")
    if not os.path.exists(p):
        return
    for line in open(p):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
_load_dotenv()

app = Flask(__name__)
_refresh_lock = threading.Lock()


def run_pipeline():
    """Пересобрать dashboard.json и index.html. Возвращает (ok, log)."""
    if not _refresh_lock.acquire(blocking=False):
        return False, "уже выполняется"
    try:
        out = []
        for script in ("fetch_data.py", "build.py"):
            r = subprocess.run([sys.executable, os.path.join(DASH, script)],
                               capture_output=True, text=True, cwd=ROOT, timeout=600)
            out.append(r.stdout.strip())
            if r.returncode != 0:
                return False, (r.stdout + "\n" + r.stderr).strip()
        return True, "\n".join(out)
    finally:
        _refresh_lock.release()


def ensure_built():
    """При старте: index.html закоммичен, поэтому обычно ничего не делаем — старт не блокируем.
    Если index.html вдруг нет — собираем в ФОНЕ (сетевой сбой не должен мешать воркеру подняться).
    Данные обновляются через /refresh и cron."""
    if os.path.exists(INDEX):
        return
    def _bg():
        ok, log = run_pipeline()
        print("Первая сборка:", "ok" if ok else "ОШИБКА", log, flush=True)
    threading.Thread(target=_bg, daemon=True).start()


# ---------- авторизация ----------
# Доступ разрешён, если ЛИБО валиден JWT Cloudflare Access (вход на домене за Cloudflare,
# без второго пароля), ЛИБО прошёл Basic-Auth (защищает прямой Railway-URL от обхода Access).
import time as _time
CF_TEAM = os.environ.get("CF_ACCESS_TEAM_DOMAIN", "").strip().replace("https://", "").rstrip("/")
CF_AUD = os.environ.get("CF_ACCESS_AUD", "").strip()
_cf_certs = {"keys": None, "at": 0.0}

def cf_enabled():
    return bool(CF_TEAM and CF_AUD)

def _cf_jwks():
    import urllib.request as _u
    if _cf_certs["keys"] and (_time.time() - _cf_certs["at"] < 3600):
        return _cf_certs["keys"]
    with _u.urlopen(f"https://{CF_TEAM}/cdn-cgi/access/certs", timeout=10) as r:
        data = json.loads(r.read().decode())
    _cf_certs["keys"] = data.get("keys", [])
    _cf_certs["at"] = _time.time()
    return _cf_certs["keys"]

def cf_access_ok(req):
    if not cf_enabled():
        return False
    token = req.headers.get("Cf-Access-Jwt-Assertion") or req.cookies.get("CF_Authorization")
    if not token:
        return False
    try:
        import jwt
        hdr = jwt.get_unverified_header(token)
        key = None
        for k in _cf_jwks():
            if k.get("kid") == hdr.get("kid"):
                key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(k)); break
        if key is None:
            return False
        jwt.decode(token, key=key, algorithms=["RS256"], audience=CF_AUD,
                   issuer=f"https://{CF_TEAM}")
        return True
    except Exception:
        return False

def check_auth(u, p):
    return (u == os.environ.get("DASH_USER") and p == os.environ.get("DASH_PASS")
            and bool(os.environ.get("DASH_USER")))

def require_auth(fn):
    @functools.wraps(fn)
    def wrap(*a, **kw):
        from flask import request
        if cf_enabled() and cf_access_ok(request):
            return fn(*a, **kw)
        auth = request.authorization
        if auth and check_auth(auth.username, auth.password):
            return fn(*a, **kw)
        return Response("Требуется авторизация", 401,
                        {"WWW-Authenticate": 'Basic realm="CEO Dashboard"'})
    return wrap


@app.route("/")
@require_auth
def index():
    if not os.path.exists(INDEX):
        # Дашборд ещё не собран (свежий клон / первый запуск). Запускаем сборку в фоне
        # и показываем заставку, а не ошибку. Страница сама обновится, когда данные готовы.
        ensure_built()
        return Response(
            "<!doctype html><html lang=ru><head><meta charset=utf-8>"
            "<meta http-equiv=refresh content=15>"
            "<title>Собираю данные…</title></head>"
            "<body style='font:16px/1.5 system-ui,sans-serif;max-width:560px;margin:60px auto;padding:0 20px;color:#1f2a2e'>"
            "<h2>Собираю данные из ПланФакта…</h2>"
            "<p>Страница обновится сама через несколько секунд. Первая сборка занимает пару минут.</p>"
            "<p style='color:#5f6a72'>Если заставка не пропадает — проверьте, что задан ключ "
            "<code>PLANFACT_API_KEY</code> (локально в файле <code>.env</code>, на сервере — в переменных окружения).</p>"
            "</body></html>",
            200, {"Content-Type": "text/html; charset=utf-8"})
    return send_file(INDEX)


_refresh_state = {"running": False, "ok": None, "log": ""}

def _do_refresh():
    _refresh_state.update(running=True, ok=None)
    try:
        ok, log = run_pipeline()
        _refresh_state.update(ok=ok, log=(log or "")[-800:])
    except Exception as e:
        _refresh_state.update(ok=False, log=str(e))
    finally:
        _refresh_state["running"] = False

@app.route("/refresh", methods=["POST"])
@require_auth
def refresh():
    # запускаем пересборку в ФОНЕ и сразу отвечаем — воркер не блокируется
    if not _refresh_state["running"]:
        threading.Thread(target=_do_refresh, daemon=True).start()
    return jsonify(ok=True, running=True)

@app.route("/refresh-status")
@require_auth
def refresh_status():
    return jsonify(running=_refresh_state["running"], ok=_refresh_state["ok"])


@app.route("/health")
def health():
    return "ok", 200


# ---------- реестры одобрения платежей (хранятся в Supabase) ----------
# Браузер ходит СЮДА (за Basic-Auth), а сервер — в Supabase сервисным ключом.
# Ни anon-, ни service-ключ Supabase в браузер не попадают.
import urllib.request as _urq, urllib.error as _ure, urllib.parse as _urp
SB_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SB_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
SB_TABLE = "pf_payment_registers"

def sb_enabled():
    return bool(SB_URL and SB_KEY)

def sb(table, method, query="", body=None, prefer=None):
    url = f"{SB_URL}/rest/v1/{table}{query}"
    headers = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
               "Content-Type": "application/json", "Accept": "application/json"}
    if prefer:
        headers["Prefer"] = prefer
    data = json.dumps(body).encode() if body is not None else None
    req = _urq.Request(url, data=data, headers=headers, method=method)
    with _urq.urlopen(req, timeout=30) as r:
        raw = r.read().decode() or "[]"
        return json.loads(raw) if raw.strip() else []

def _clean(reg):
    # оставляем только поля, которые храним; items — как есть (jsonb)
    return {"id": str(reg.get("id")), "ts": reg.get("ts"),
            "total": reg.get("total") or 0, "items": reg.get("items") or []}

@app.route("/api/registers", methods=["GET"])
@require_auth
def registers_list():
    if not sb_enabled():
        return jsonify(error="supabase_not_configured"), 501
    try:
        rows = sb(SB_TABLE, "GET", "?select=id,ts,total,items&order=ts.asc")
        return jsonify(rows)
    except Exception as e:
        return jsonify(error=str(e)), 502

@app.route("/api/registers", methods=["POST"])
@require_auth
def registers_create():
    if not sb_enabled():
        return jsonify(error="supabase_not_configured"), 501
    from flask import request
    reg = _clean(request.get_json(force=True) or {})
    if not reg["id"] or not reg["ts"]:
        return jsonify(error="bad_register"), 400
    try:
        rows = sb(SB_TABLE, "POST", body=reg, prefer="return=representation,resolution=merge-duplicates")
        return jsonify(rows[0] if isinstance(rows, list) and rows else reg)
    except Exception as e:
        return jsonify(error=str(e)), 502

@app.route("/api/registers/<rid>", methods=["PUT"])
@require_auth
def registers_update(rid):
    if not sb_enabled():
        return jsonify(error="supabase_not_configured"), 501
    from flask import request
    p = request.get_json(force=True) or {}
    body = {"total": p.get("total") or 0, "items": p.get("items") or []}
    try:
        q = "?id=eq." + _urp.quote(rid, safe="")
        sb(SB_TABLE, "PATCH", q, body=body, prefer="return=minimal")
        return jsonify(ok=True)
    except Exception as e:
        return jsonify(error=str(e)), 502

@app.route("/api/registers/<rid>", methods=["DELETE"])
@require_auth
def registers_delete(rid):
    if not sb_enabled():
        return jsonify(error="supabase_not_configured"), 501
    try:
        q = "?id=eq." + _urp.quote(rid, safe="")
        sb(SB_TABLE, "DELETE", q, prefer="return=minimal")
        return jsonify(ok=True)
    except Exception as e:
        return jsonify(error=str(e)), 502


# ---------- общие настройки дашборда (напр. ручной остаток банка) ----------
SB_SETTINGS = "pf_settings"

@app.route("/api/settings", methods=["GET"])
@require_auth
def settings_list():
    if not sb_enabled():
        return jsonify(error="supabase_not_configured"), 501
    try:
        rows = sb(SB_SETTINGS, "GET", "?select=key,value")
        return jsonify({r["key"]: r["value"] for r in (rows or [])})
    except Exception as e:
        return jsonify(error=str(e)), 502

@app.route("/api/settings/<key>", methods=["PUT"])
@require_auth
def settings_put(key):
    if not sb_enabled():
        return jsonify(error="supabase_not_configured"), 501
    from flask import request
    value = request.get_json(force=True, silent=True)
    try:
        sb(SB_SETTINGS, "POST", body={"key": key, "value": value},
           prefer="resolution=merge-duplicates,return=minimal")
        return jsonify(ok=True)
    except Exception as e:
        return jsonify(error=str(e)), 502


# ---------- планировщик (10:00 ежедневно) ----------
def start_scheduler():
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo(TZ)
        except Exception:
            tz = None
        sched = BackgroundScheduler(timezone=tz) if tz else BackgroundScheduler()
        hour = int(os.environ.get("DASH_REFRESH_HOUR", "10"))
        sched.add_job(lambda: run_pipeline(), "cron", hour=hour, minute=0, id="daily")
        sched.start()
        print(f"Планировщик: ежедневно в {hour:02d}:00 ({TZ})", flush=True)
    except Exception as e:
        print("Планировщик не запущен:", e, flush=True)


ensure_built()
start_scheduler()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
