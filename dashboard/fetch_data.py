#!/usr/bin/env python3
"""
Слой данных дашборда CEO. ТОЛЬКО ЧТЕНИЕ из API ПланФакта.
Ключ берётся из ../.env (PLANFACT_API_KEY) и НИКОГДА не пишется в вывод/JSON.
Результат: dashboard/data/dashboard.json — всё, что нужно для рендера.

Запуск:  python3 dashboard/fetch_data.py [YYYY-MM-DD]   (дата отсчёта, по умолч. сегодня-стенд 2026-07-04)
"""
import json, os, sys, urllib.request, urllib.parse, datetime
from collections import defaultdict

BASE = "https://api.planfact.io"
PERIOD_START = "2026-04-01"          # P&L и ДДС считаем с апреля 2026 (точка отсчёта дашборда)
TODAY = datetime.date.today()        # всегда текущая дата; можно переопределить аргументом YYYY-MM-DD
if len(sys.argv) > 1:
    TODAY = datetime.date.fromisoformat(sys.argv[1])
HORIZON = 6                          # тек. неделя + 6 недель вперёд, затем «Позже»
# Счета, попадающие в блок «Остатки по счетам» и в KPI «Деньги на счетах» (главная).
# Точные названия счетов из ПланФакта. Отредактируйте при изменении набора.
MAIN_ACCOUNTS = ["DOO (Осн) 51", "DOO (Доп) 82", "КЭШ"]
SALES_START = "2026-04"              # с какого месяца доступны продажи/план в блоке на главной
# Статьи выручки, которые НЕ включаются в план продаж (не показываются в план-блоке)
PLAN_EXCLUDE = ["Поступление Платежа за Столешницы", "Платный Замер"]
# Отображаемые названия статей продаж (убираем «Поступление»)
CATEGORY_RENAME = {"Поступление Платежа за Проект": "Платеж за Проект",
                   "Поступление Платежа за Технику Бытовую": "Платеж за Технику"}
def rn(n): return CATEGORY_RENAME.get(n, n)
PROJECT_EXCLUDE = ["Малярный Цех", "без группы", "Шоурум"]   # проекты/группы, скрытые во вкладке «Проекты»
# Папки ПланФакта (не месячные), которые показываем ОТДЕЛЬНОЙ группой, а не по дате начала.
PROJECT_GROUPS_KEEP = ["Платные Замеры"]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load_key():
    # 1) переменная окружения (сервер/PaaS — Фаза 2), 2) файл .env (локально — Фаза 1)
    env = os.environ.get("PLANFACT_API_KEY")
    if env and env.strip():
        return env.strip()
    path = os.path.join(ROOT, ".env")
    if os.path.exists(path):
        for line in open(path):
            if line.startswith("PLANFACT_API_KEY="):
                v = line.split("=", 1)[1].strip()
                if v:
                    return v
    raise SystemExit("PLANFACT_API_KEY не найден: задайте переменную окружения или .env")
KEY = load_key()
H = {"X-ApiKey": KEY, "Accept": "application/json", "Content-Type": "application/json"}

import time as _time
def _call(req, tries=3):
    # ретраи на сетевые сбои (IncompleteRead / таймаут / обрыв соединения)
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:
            last = e
            if i < tries - 1:
                _time.sleep(2 * (i + 1))
    raise last

def get(path, params=None):
    url = BASE + path + ("?" + urllib.parse.urlencode(params) if params else "")
    return _call(urllib.request.Request(url, headers=H))

def post(path, payload):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers=H, method="POST")
    return _call(req)

# Выгрузка операций ПОРЦИЯМИ по годам: ответы поменьше устойчивее к обрывам
# соединения (IncompleteRead) на медленной сети Railway↔ПланФакт; ретраи в _call.
# Дедуп по operationId. 10 вызовов вместо одного огромного (~900КБ, который рвался).
def list_ops(op_type):
    items, seen = [], set()
    for y in range(2023, TODAY.year + 2):          # с 2023 (первая операция 2023-09) до +1 года (будущие даты)
        batch = (post("/api/v1/operations/list",
                      {"operationType": [op_type], "operationDateStart": f"{y}-01-01", "operationDateEnd": f"{y}-12-31"})
                 .get("data") or {}).get("items") or []
        for o in batch:
            oid = o.get("operationId")
            if oid not in seen:
                seen.add(oid); items.append(o)
    return items

# ---------- недельные корзины ----------
CUR_MON = TODAY - datetime.timedelta(days=TODAY.weekday())
def monday(dstr):
    d = datetime.date.fromisoformat(dstr[:10]); return d - datetime.timedelta(days=d.weekday())
def bucket(dstr):
    # просрочено — по ДНЮ: срок оплаты уже прошёл (включая просрочку внутри текущей недели)
    if datetime.date.fromisoformat(dstr[:10]) < TODAY:
        return -1
    idx = (monday(dstr) - CUR_MON).days // 7
    return 99 if idx > HORIZON else idx
def bucket_labels():
    out = [{"key": -1, "label": "Просрочено", "kind": "overdue"}]
    for i in range(HORIZON + 1):
        mon = CUR_MON + datetime.timedelta(days=7 * i); sun = mon + datetime.timedelta(days=6)
        start = TODAY if i == 0 else mon   # тек. неделя показывается от сегодня (прошлые дни — в просрочке)
        rng = f"{start.day:02d}.{start.month:02d}–{sun.day:02d}.{sun.month:02d}"
        out.append({"key": i, "label": ("Тек. неделя" if i == 0 else rng),
                    "range": rng, "kind": "current" if i == 0 else "week"})
    out.append({"key": 99, "label": "Позже", "kind": "later"})
    return out

# ---------- обязательства (деб/кред) ----------
EXCLUDE_CA = lambda ca: "себестоимост" in (ca or "").lower()   # плановая себестоимость исключается
def obligations(items):
    res = []
    for o in items:
        if o.get("isCommitted") is not False or o["operationType"] == "Move":
            continue
        parts = [p for p in (o.get("operationParts") or []) if p.get("isCalculationCommitted") is True]
        v = sum((p.get("valueInUserCurrency") or p.get("value") or 0) for p in parts)
        if v <= 0:
            continue
        ca = next(((p["contrAgent"] or {}).get("title") for p in parts if p.get("contrAgent")), None) \
             or (o.get("contrAgent") or {}).get("title") or "— без контрагента"
        if EXCLUDE_CA(ca):
            continue
        cat = next(((p["operationCategory"] or {}).get("title") for p in parts if p.get("operationCategory")), None) or "(без статьи)"
        prj = next((t for p in parts for t in [(p.get("project") or {}).get("title")] if t and t != "Не выбран"), "")
        accr = min([p.get("calculationDate") or "9999" for p in parts] or ["9999"])
        res.append({"cat": cat, "ca": ca, "val": round(v, 2), "date": o["operationDate"][:10],
                    "accr": None if accr == "9999" else accr[:10], "cmt": o.get("comment") or "",
                    "prj": prj, "id": o["operationId"], "b": bucket(o["operationDate"])})
    return res

def group_obligations(obs, by):
    """by = 'cat' (по статьям) или 'ca' (по контрагентам)."""
    groups = defaultdict(lambda: {"total": 0.0, "buckets": defaultdict(float), "lines": []})
    for x in obs:
        g = groups[x[by]]; g["total"] += x["val"]; g["buckets"][x["b"]] += x["val"]; g["lines"].append(x)
    out = []
    for name, g in sorted(groups.items(), key=lambda kv: -kv[1]["total"]):
        out.append({"name": name, "total": round(g["total"], 2),
                    "buckets": {str(k): round(v, 2) for k, v in g["buckets"].items()},
                    "lines": sorted(g["lines"], key=lambda l: l["date"])})
    total = round(sum(x["val"] for x in obs), 2)
    overdue = round(sum(x["val"] for x in obs if x["b"] == -1), 2)
    return {"total": total, "overdue": overdue, "n": len(obs),
            "groupLabel": "Контрагент" if by == "ca" else "Статья", "units": len(out),
            "categories": len({x["cat"] for x in obs}), "contragents": len({x["ca"] for x in obs}),
            "groups": out}

# ---------- P&L (OPU, начисление) по статьям и месяцам ----------
def month_list(start, end):
    y, m = int(start[:4]), int(start[5:7]); out = []
    while (y, m) <= (int(end[:4]), int(end[5:7])):
        out.append(f"{y}-{m:02d}"); m += 1
        if m > 12: m = 1; y += 1
    return out
MONTHS = month_list(PERIOD_START, TODAY.isoformat())

def opu_leaves(node_items, income=True):
    """Возвращает {категория: {месяц: сумма}} по листовым статьям."""
    field = "factIncomeValue" if income else "factOutcomeValue"
    out = defaultdict(lambda: defaultdict(float))
    def walk(n):
        dets = n.get("details") or []
        if not dets:
            title = (n.get("operationCategory") or {}).get("title") or "?"
            for tv in (n.get("totalValues") or []):
                m = tv["startDate"][:7]; out[title][m] += tv.get(field) or 0
        else:
            for c in dets: walk(c)
    for top in (node_items or []): walk(top)
    return out

# =========================================================
def main():
    print("Загрузка данных из ПланФакта (только чтение)…")

    # --- операции: все доходы и расходы (порциями по кварталам — устойчиво к обрывам) ---
    inc = list_ops("Income")
    out = list_ops("Outcome")
    print(f"  income={len(inc)} outcome={len(out)}")

    # --- остатки по счетам (accountshistory: накопленный факт) ---
    accts = (get("/api/v1/accounts").get("data") or {}).get("items") or []
    name_by_id = {a["accountId"]: a["title"] for a in accts}
    active_by_id = {a["accountId"]: a.get("active") for a in accts}
    hist = get("/api/v1/bizinfos/accountshistory").get("data") or []
    all_balances = []
    _today = TODAY.isoformat()
    for a in hist:
        # остаток НА СЕГОДНЯ: суммируем дневные факт-движения по дату отсчёта включительно
        # (будущие фактические операции в остаток не тянем — как на экране «Остатки» ПланФакта)
        bal = sum(d.get("factValueInUserCurrency", d.get("factValue", 0))
                  for d in a.get("details", []) if (d.get("date") or "")[:10] <= _today)
        aid = a["accountId"]
        all_balances.append({"account": name_by_id.get(aid, str(aid)), "balance": round(bal, 2),
                             "active": active_by_id.get(aid, True)})
    # На главной — только основные счета (MAIN_ACCOUNTS), в порядке из списка
    order = {t: i for i, t in enumerate(MAIN_ACCOUNTS)}
    balances = sorted([b for b in all_balances if b["account"] in MAIN_ACCOUNTS],
                      key=lambda b: order.get(b["account"], 99))
    cash_total = round(sum(b["balance"] for b in balances), 2)
    missing = [t for t in MAIN_ACCOUNTS if t not in {b["account"] for b in balances}]
    if missing: print(f"  ⚠ не найдены счета для главной: {missing}")

    # --- реестры деб/кред (по категориям, недельные корзины) ---
    receivables = group_obligations(obligations(inc), "cat")   # дебиторка — по статьям
    payables = group_obligations(obligations(out), "ca")       # кредиторка — по контрагентам

    # --- справочник статей: классификация строк ОПУ ---
    cd = get("/api/v1/operationcategories").get("data")
    cat_items = cd.get("items") if isinstance(cd, dict) else cd
    CM = {c["operationCategoryId"]: c for c in (cat_items or [])}
    def opu_line(cid):
        c = CM.get(cid, {}); acc = c.get("accountCategoryType"); cls = c.get("outcomeClassification") or ""
        if acc == "Income": return "revenue"
        if acc in ("IncomeOther", "IncomeOtherExchangeDifference"): return "otherIncome"
        if acc in ("OutcomeOther", "OutcomeOtherExchangeDifference"): return "otherOutcome"
        if acc == "OutcomeTax": return "tax"
        if acc == "OutcomeDepreciation": return "depreciation"
        if acc == "OutcomeCreditPercent": return "interest"
        if acc == "CapitalDividends": return "dividends"
        if acc == "Outcome": return "fixed" if "Fixed" in cls else "variable"
        if acc == "OutcomeUndistributed": return "variable"  # «Нераспределённый расход» — в Переменные, как в ОПУ ПланФакта
        return None  # инвестиции/капитал/активы (AssetsLongFixed и пр.) — не в P&L

    # --- P&L маржинальный (начисление): ДЕРЕВО статей → подстатьи, помесячно ---
    PARENT = {cid: c.get("parentOperationCategoryId") for cid, c in CM.items()}
    TITLE = {cid: (c.get("title") or "").strip() for cid, c in CM.items()}
    GRAND = {cid for cid in CM if PARENT.get(cid) not in CM}   # корневые агрегаты (Доходы/Расходы/…)
    leaf = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))   # line -> catId -> month -> val
    line_month = defaultdict(lambda: defaultdict(float))
    for o in inc + out:
        for p in (o.get("operationParts") or []):
            if not p.get("isCalculationCommitted"): continue
            m = (p.get("calculationDate") or "")[:7]
            if m not in MONTHS: continue
            cid = (p.get("operationCategory") or {}).get("operationCategoryId")
            ln = opu_line(cid)
            if not ln: continue
            v = p.get("valueInUserCurrency") or p.get("value") or 0
            leaf[ln][cid][m] += v; line_month[ln][m] += v
    def lm(ln): return {m: round(line_month[ln].get(m, 0), 2) for m in MONTHS}
    def ltot(ln): return round(sum(line_month[ln].values()), 2)
    def tree(ln):
        node_m = defaultdict(lambda: defaultdict(float)); kids = defaultdict(set); nodes = set()
        for cid, mv in leaf[ln].items():
            chain = []; cur = cid
            while cur in CM and cur not in GRAND:
                chain.append(cur); cur = PARENT.get(cur)
            if not chain: chain = [cid]
            for c in chain:
                for m, v in mv.items(): node_m[c][m] += v
                nodes.add(c)
            for i in range(len(chain) - 1): kids[chain[i + 1]].add(chain[i])
        def mk(cid):
            ch = sorted(kids[cid], key=lambda k: -sum(node_m[k].values()))
            return {"category": rn(TITLE.get(cid) or "(без статьи)"),
                    "months": {m: round(node_m[cid].get(m, 0), 2) for m in MONTHS},
                    "total": round(sum(node_m[cid].values()), 2),
                    "children": [mk(k) for k in ch]}
        tops = [c for c in nodes if PARENT.get(c) in GRAND or PARENT.get(c) not in CM]
        return [mk(t) for t in sorted(tops, key=lambda t: -sum(node_m[t].values()))]
    margin = {m: round(line_month["revenue"].get(m, 0) - line_month["variable"].get(m, 0), 2) for m in MONTHS}
    net = {m: round(line_month["revenue"].get(m, 0) + line_month["otherIncome"].get(m, 0)
                    - sum(line_month[k].get(m, 0) for k in ("variable", "fixed", "otherOutcome", "depreciation", "interest", "tax")), 2)
           for m in MONTHS}
    retained = {m: round(net[m] - line_month["dividends"].get(m, 0), 2) for m in MONTHS}
    revm = lm("revenue")
    def pct(num): return {m: (round(num[m] / revm[m] * 100, 1) if revm.get(m) else None) for m in MONTHS}
    def LN(label, ln): return {"label": label, "kind": "line", "months": lm(ln), "total": ltot(ln), "tree": tree(ln)}
    def RS(label, mo, strong=True): return {"label": label, "kind": "result", "months": {m: round(mo[m], 2) for m in MONTHS}, "total": round(sum(mo.values()), 2), "tree": []}
    def PC(label, mo): return {"label": label, "kind": "percent", "months": mo, "tree": []}
    pnl = {"months": MONTHS,
           "revenueTotal": ltot("revenue"),
           "profitTotal": round(sum(net.values()), 2),
           "lines": [
               LN("Выручка", "revenue"),
               LN("Переменные расходы", "variable"),
               RS("Маржинальная прибыль", margin),
               PC("Маржинальность", pct(margin)),
               LN("Постоянные расходы", "fixed"),
               LN("Прочие доходы", "otherIncome"),
               LN("Прочие расходы", "otherOutcome"),
               LN("Амортизация", "depreciation"),
               LN("Проценты по кредитам и займам", "interest"),
               LN("Налог на прибыль", "tax"),
               RS("Чистая прибыль (убыток)", net),
               PC("Рентабельность чистой прибыли", pct(net)),
               LN("Дивиденды", "dividends"),
               RS("Нераспределённая прибыль", retained),
           ]}

    # --- Продажи по категориям (главная): два базиса — начисление (по договорам) и касса (получено) ---
    SALES_MONTHS = month_list(SALES_START, TODAY.isoformat())
    def sales_by(basis):   # basis: 'accrual' (продано по договорам) | 'cash' (получено за проданное)
        # Обе метрики привязаны к МЕСЯЦУ ПРОДАЖИ (дате начисления проекта), не к дате платежа.
        # 'cash' = оплаченная часть проектов, проданных в этом месяце (предоплаты/доплаты по ним).
        # Учёт денег по датам платежей — в разделе ДДС.
        agg = defaultdict(lambda: defaultdict(float))
        for o in inc:
            committed_pay = o.get("isCommitted")
            for p in (o.get("operationParts") or []):
                cid = (p.get("operationCategory") or {}).get("operationCategoryId")
                if opu_line(cid) != "revenue": continue          # только статьи выручки
                if not p.get("isCalculationCommitted"): continue  # только признанные продажи
                m = (p.get("calculationDate") or "")[:7]          # месяц = когда проект продан
                if m not in SALES_MONTHS: continue
                if basis == "cash" and not committed_pay: continue  # получено = оплаченная часть проданного
                title = (p.get("operationCategory") or {}).get("title") or "(без статьи)"
                agg[title][m] += p.get("valueInUserCurrency") or p.get("value") or 0
        return [{"name": rn(t), "m": {m: round(mv.get(m, 0), 2) for m in SALES_MONTHS}, "total": round(sum(mv.values()), 2)}
                for t, mv in sorted(agg.items(), key=lambda kv: -sum(kv[1].values()))]
    # Неоплаченные доплаты: проекты проданы (начислены), но деньги не получены → заказчик должен.
    # БЕЗ ограничения SALES_MONTHS — чтобы попал и долг за периоды ДО апреля 2026 (колонка «долг за прошлый период»).
    # Каждая строка помечается статьёй продаж (cat) — чтобы разложить по строкам таблицы.
    debt_lines = []
    for o in inc:
        if o.get("isCommitted"): continue        # оплаченные не должны
        for p in (o.get("operationParts") or []):
            cid = (p.get("operationCategory") or {}).get("operationCategoryId")
            if opu_line(cid) != "revenue": continue
            if not p.get("isCalculationCommitted"): continue
            m = (p.get("calculationDate") or "")[:7]
            if not m: continue
            prj = (p.get("project") or {}).get("title") or ""
            if prj == "Не выбран": prj = ""
            debt_lines.append({"m": m, "project": prj,
                               "cat": rn((p.get("operationCategory") or {}).get("title") or "(без статьи)"),
                               "ca": (p.get("contrAgent") or {}).get("title") or "—",
                               "cmt": o.get("comment") or "", "id": o["operationId"],
                               "val": round(p.get("valueInUserCurrency") or p.get("value") or 0, 2)})
    debt_lines.sort(key=lambda x: -x["val"])
    sales = {"months": SALES_MONTHS, "accrual": sales_by("accrual"), "cash": sales_by("cash"),
             "debtLines": debt_lines, "salesStart": SALES_START}

    # --- План продаж (ПОМЕСЯЧНЫЙ): читаем локальный plans.json (правится CEO/бэкендом) ---
    plans_path = os.path.join(ROOT, "dashboard", "plans.json")
    try:
        plans = json.load(open(plans_path, encoding="utf-8"))
    except Exception:
        plans = {}
    plans = {q: {rn(k): v for k, v in mp.items()} for q, mp in plans.items()}   # нормализуем ключи плана под новые названия
    salesplan = {"plans": plans, "months": SALES_MONTHS, "current": TODAY.strftime("%Y-%m"),
                 "exclude": [rn(x) for x in PLAN_EXCLUDE], "rename": CATEGORY_RENAME}

    # --- ДДС (касса) помесячно (первый вариант, скорректируем) ---
    dds = post("/api/v2/reports/dds", {"periodStartDate": PERIOD_START, "periodEndDate": TODAY.isoformat(),
               "reportGenMethod": "OperationCategory", "isPeriodDetail": True, "standardPeriod": "Month",
               "userCurrencyCode": "RSD"})
    dn = (dds.get("data") or {}).get("operationCategoryByPeriod") or {}
    def flow(key):
        n = dn.get(key) or {}
        return {"income": round(n.get("incomeTotalValue") or 0, 2),
                "outcome": round(n.get("outcomeTotalValue") or 0, 2),
                "net": round(n.get("profitTotalValue") or 0, 2),
                "byMonth": [{"m": tv["startDate"][:7],
                             "net": round((tv.get("factIncomeValue") or 0) - (tv.get("factOutcomeValue") or 0), 2),
                             "income": round(tv.get("factIncomeValue") or 0, 2),
                             "outcome": round(tv.get("factOutcomeValue") or 0, 2)}
                            for tv in (n.get("totalValues") or [])]}
    ddsblock = {"operating": flow("operatingCashFlow"), "investment": flow("investmentCashFlow"),
                "financial": flow("financialCashFlow"),
                "generalNet": round((dn.get("generalCashFlow") or {}).get("profitTotalValue") or 0, 2),
                "endBalance": round((dn.get("accountBalance") or {}).get("total") or 0, 2)}

    # --- KPI + напоминания (раздел 0) ---
    # продажи месяца (касса, текущий месяц)
    cur_m = TODAY.strftime("%Y-%m")
    sales_mtd = payables_mtd = 0.0
    for o in inc:
        if o.get("isCommitted") and o["operationType"] != "Move" and o["operationDate"][:7] == cur_m:
            for p in (o.get("operationParts") or []):
                if p.get("operationCategoryActivityType") == "Operating":
                    sales_mtd += p.get("valueInUserCurrency") or p.get("value") or 0
    reminders = []
    for b in all_balances:
        if b["balance"] < 0:
            reminders.append({"type": "danger", "text": f"Отрицательный остаток: «{b['account']}» {b['balance']:,.0f} RSD"})
    if payables["overdue"] > 0:
        reminders.append({"type": "warn", "text": f"Просроченная кредиторка: {payables['overdue']:,.0f} RSD — платить в первую очередь"})
    if receivables["overdue"] > 0:
        reminders.append({"type": "warn", "text": f"Просроченная дебиторка: {receivables['overdue']:,.0f} RSD — напомнить клиентам"})
    # крупнейшая просроченная кредиторка
    over_pay = sorted([l for c in payables["groups"] for l in c["lines"] if l["b"] == -1], key=lambda l: -l["val"])[:3]
    for l in over_pay:
        reminders.append({"type": "info", "text": f"Просрочен платёж {l['ca']} {l['val']:,.0f} RSD ({l['cmt'][:30]})"})

    kpis = {"cashTotal": round(cash_total, 2), "accounts": balances,
            "receivables": receivables["total"], "receivablesOverdue": receivables["overdue"],
            "payables": payables["total"], "payablesOverdue": payables["overdue"],
            "netDebt": round(receivables["total"] - payables["total"], 2),
            "salesMTD": round(sales_mtd, 2), "profitPeriod": pnl["profitTotal"]}

    # --- Проекты: активные (в работе), накопительный P&L (начисление) + неоплаченные начисления (деб/кред) ---
    praw = get("/api/v1/projects").get("data")
    praw = praw.get("items") if isinstance(praw, dict) else praw
    PMETA = {p["projectId"]: {"title": p.get("title") or "—",
                              "group": (p.get("projectGroup") or {}).get("title") or "— без группы",
                              "closed": p.get("closed")} for p in (praw or [])}
    pagg = defaultdict(lambda: {"income": 0.0, "outcome": 0.0, "start": None, "end": None, "pays": []})
    def _acc(o, kind):
        paid = bool(o.get("isCommitted"))
        for pp in (o.get("operationParts") or []):
            if not pp.get("isCalculationCommitted"): continue
            pj = (pp.get("project") or {}).get("projectId")
            if pj is None: continue
            v = pp.get("valueInUserCurrency") or pp.get("value") or 0
            r = pagg[pj]; r[kind] += v; od = o["operationDate"][:10]
            if not r["start"] or od < r["start"]: r["start"] = od
            if not r["end"] or od > r["end"]: r["end"] = od
            r["pays"].append({"kind": kind, "date": od, "ca": (pp.get("contrAgent") or {}).get("title") or "—",
                              "cmt": o.get("comment") or "", "val": round(v, 2), "id": o["operationId"], "paid": paid})
    for o in inc: _acc(o, "income")
    for o in out: _acc(o, "outcome")
    _RU_MON = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль",
               "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    def group_from_start(start):   # папка по месяцу даты начала проекта
        if not start or start < "2026-01-01": return "00 Старые (до 2026)"
        mo = int(start[5:7]); return f"{mo:02d} {_RU_MON[mo - 1]} {start[:4]}"
    def project_group(meta_group, start):
        # «Платные Замеры» в ПланФакте — отдельная папка (не месяц), показываем её так же.
        # Остальное группируем по месяцу даты начала (как на экране «Проекты» — месячные папки).
        if (meta_group or "").strip() in PROJECT_GROUPS_KEEP:
            return meta_group.strip()
        return group_from_start(start)
    pgroups = defaultdict(list)
    for pj, r in pagg.items():
        meta = PMETA.get(pj)
        if not meta: continue
        if any(x in meta["title"] or x in meta["group"] for x in PROJECT_EXCLUDE): continue
        if round(r["income"], 2) == 0 and round(r["outcome"], 2) == 0 and not r["pays"]: continue
        profit = r["income"] - r["outcome"]
        pays = sorted(r["pays"], key=lambda x: -x["val"])
        nd = sum(1 for x in pays if x["kind"] == "income" and not x["paid"])   # неоплаченная дебиторка
        nk = sum(1 for x in pays if x["kind"] == "outcome" and not x["paid"])  # неоплаченная кредиторка
        status = "done" if meta["closed"] else "work"   # завершён = флаг «завершён» в ПланФакте (closed)
        if status == "done" and (r["start"] or "") < "2026-01-01": continue   # завершённые, начатые в 2025 и раньше, не показываем
        # детализацию платежей храним только для проектов в работе; закрытые — архив (лишь строка+итоги)
        pgroups[project_group(meta["group"], r["start"])].append({"title": meta["title"], "start": r["start"], "end": r["end"],
            "income": round(r["income"], 2), "outcome": round(r["outcome"], 2), "profit": round(profit, 2),
            "rent": round(profit / r["income"] * 100, 1) if r["income"] else None, "status": status,
            "nd": (nd if not meta["closed"] else 0), "nk": (nk if not meta["closed"] else 0),
            "payments": (pays if not meta["closed"] else [])})
    proj_groups = []
    for gname in sorted(pgroups):
        plist = sorted(pgroups[gname], key=lambda x: x["title"])
        gi = round(sum(p["income"] for p in plist), 2); go = round(sum(p["outcome"] for p in plist), 2); gp = round(gi - go, 2)
        proj_groups.append({"group": gname, "n": len(plist), "income": gi, "outcome": go, "profit": gp,
                            "rent": round(gp / gi * 100, 1) if gi else None, "projects": plist})
    projects = {"groups": proj_groups}

    data = {"meta": {"generatedAt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                     "asOf": TODAY.isoformat(), "periodStart": PERIOD_START, "company": "Tekstura DOO",
                     "currency": "RSD", "bucketLabels": bucket_labels(), "months": MONTHS},
            "kpis": kpis, "reminders": reminders, "pnl": pnl, "sales": sales, "salesplan": salesplan,
            "receivables": receivables, "payables": payables, "dds": ddsblock, "projects": projects}

    os.makedirs(os.path.join(ROOT, "dashboard", "data"), exist_ok=True)
    outpath = os.path.join(ROOT, "dashboard", "data", "dashboard.json")
    json.dump(data, open(outpath, "w"), ensure_ascii=False, indent=1)
    print(f"Готово → {outpath}")
    print(f"  Касса: {cash_total:,.0f} | Деб: {receivables['total']:,.0f} | Кред: {payables['total']:,.0f} | "
          f"Прибыль(апрель→): {pnl['profitTotal']:,.0f}")

if __name__ == "__main__":
    main()
