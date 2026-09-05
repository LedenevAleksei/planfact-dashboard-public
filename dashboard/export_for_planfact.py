#!/usr/bin/env python3
"""
Экспорт операций В ФОРМАТЕ ИМПОРТА ПланФакта (поквартально). ТОЛЬКО ЧТЕНИЕ из API.
Колонки один-в-один с официальным шаблоном ПланФакта (PlanFactCashflowTemplate.xlsx):
  Дата оплаты · Статус оплаты · Дата начисления · Статус начисления · Контрагент ·
  ИНН контрагента · Тип · Счет · № Счета · Банк · Бик · Юрлицо · ИНН юрлица · Статья ·
  Родительские статьи · Вид деятельности · Назначение платежа · Проекты · Сумма · Валюта

Учтено по правилам шаблона:
  • Тип: Поступление / Выплата / Перемещение.
  • Сумма СО ЗНАКОМ: Поступление/зачисление = «+», Выплата/списание = «−».
  • Оплачено/начислено выражается СТАТУСОМ (Подтверждена / Не подтверждена), даты заполняются всегда.
  • Перемещения = ДВЕ строки подряд: счёт списания «[Списание]» (−), ниже счёт зачисления «[Зачисление]» (+).
  • Проекты в формате «Название (100%)».  • Без формул. Сохранять в XLSX.

Пишет в export/planfact_import/:  import_YYYY-QN.xlsx + import_YYYY-QN.csv + README_ИМПОРТ.md
Импортировать через РОДНОЙ импорт ПланФакта (Операции → Импорт), НЕ через API (Правило №1).
"""
import json, os, csv, urllib.request, datetime

BASE = "https://api.planfact.io"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "export", "planfact_import")
ACT = {"Operating": "Операционная деятельность", "Finance": "Финансовая деятельность",
       "Investment": "Инвестиционная деятельность"}

def load_key():
    env = os.environ.get("PLANFACT_API_KEY")
    if env and env.strip():
        return env.strip()
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in open(p):
            if line.startswith("PLANFACT_API_KEY="):
                v = line.split("=", 1)[1].strip()
                if v:
                    return v
    raise SystemExit("PLANFACT_API_KEY не найден: задайте переменную окружения или .env")

KEY = load_key()
H = {"X-ApiKey": KEY, "Accept": "application/json", "Content-Type": "application/json"}

def get(path):
    with urllib.request.urlopen(urllib.request.Request(BASE + path, headers=H), timeout=180) as r:
        return json.load(r)

def post(path, payload):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(), headers=H, method="POST")
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)

def title(o):
    return (o or {}).get("title") if isinstance(o, dict) else None

def dt(s):
    d = (s or "")[:10]
    return f"{d} 00:00:00" if len(d) == 10 else ""

def qof(s):
    d = (s or "")[:10]
    return f"{int(d[:4])}-Q{(int(d[5:7]) - 1) // 3 + 1}" if len(d) >= 7 else "unknown"

def status(flag):
    return "Подтверждена" if flag is True else "Не подтверждена"

# ---------- данные (только чтение) ----------
print("Читаю операции из ПланФакта (только чтение)…")
regular = []
for t in ("Income", "Outcome"):
    regular += (post("/api/v1/operations/list", {"operationType": [t]}).get("data") or {}).get("items") or []
moves = (post("/api/v1/operations/list", {"operationType": ["Move"]}).get("data") or {}).get("items") or []
print(f"  обычных операций: {len(regular)} · плечей перемещений: {len(moves)}")

cd = get("/api/v1/operationcategories").get("data")
cats = cd.get("items") if isinstance(cd, dict) else cd
CM = {c["operationCategoryId"]: c for c in (cats or [])}
def root_title(cid):
    cur, guard = cid, 0
    while cur in CM and CM[cur].get("parentOperationCategoryId") in CM and guard < 12:
        cur = CM[cur]["parentOperationCategoryId"]; guard += 1
    return (CM.get(cur) or {}).get("title") or ""

HEADERS = ["Дата оплаты", "Статус оплаты", "Дата начисления", "Статус начисления", "Контрагент",
           "ИНН контрагента", "Тип", "Счет", "№ Счета", "Банк", "Бик", "Юрлицо", "ИНН юрлица",
           "Статья", "Родительские статьи", "Вид деятельности", "Назначение платежа", "Проекты",
           "Сумма", "Валюта"]

def project_cell(part):
    pr = part.get("project") or {}
    t = pr.get("title")
    if not t or t == "Не выбран" or pr.get("isUndistributed"):
        return ""
    return f"{t} (100%)"

def row(op, part, typ, sign, article=None, is_transfer=False):
    val = part.get("valueInUserCurrency") or part.get("value") or op.get("value") or 0
    cid = (part.get("operationCategory") or {}).get("operationCategoryId")
    return {
        "Дата оплаты": dt(op.get("operationDate")),
        "Статус оплаты": status(op.get("isCommitted")),
        "Дата начисления": "" if is_transfer else dt(part.get("calculationDate")),
        "Статус начисления": "" if is_transfer else status(part.get("isCalculationCommitted")),
        "Контрагент": "" if is_transfer else (title(part.get("contrAgent")) or title(op.get("contrAgent")) or ""),
        "ИНН контрагента": "",
        "Тип": typ,
        "Счет": title(op.get("account")) or "",
        "№ Счета": "", "Банк": "", "Бик": "",
        "Юрлицо": title(op.get("accountCompany")) or "",
        "ИНН юрлица": "",
        "Статья": article if article is not None else (title(part.get("operationCategory")) or ""),
        "Родительские статьи": "" if (is_transfer or not cid) else root_title(cid),
        "Вид деятельности": "" if is_transfer else ACT.get(part.get("operationCategoryActivityType"), ""),
        "Назначение платежа": op.get("comment") or "",
        "Проекты": "" if is_transfer else project_cell(part),
        "Сумма": round(sign * abs(val), 2),
        "Валюта": (op.get("account") or {}).get("currencyCode") or "RSD",
    }

groups = []   # (quarter, sortkey, [rows])
RU = {"Income": ("Поступление", 1), "Outcome": ("Выплата", -1)}
for op in regular:
    typ, sign = RU.get(op.get("operationType"), (op.get("operationType"), 1))
    for p in (op.get("operationParts") or [{}]):
        r = row(op, p, typ, sign)
        groups.append((qof(op.get("operationDate")), dt(op.get("operationDate")) + str(op.get("operationId")), [r]))

# перемещения: пары [Списание](−)/[Зачисление](+)
byId = {o.get("operationId"): o for o in moves}
seen = set()
for leg in moves:
    if leg.get("operationId") in seen:
        continue
    pair = byId.get(leg.get("boundMoveOperationId"))
    out_leg, in_leg = (leg, pair) if leg.get("operationType") == "Outcome" else (pair, leg)
    seen.add(leg.get("operationId"))
    if pair:
        seen.add(pair.get("operationId"))
    rows = []
    if out_leg:
        rows.append(row(out_leg, (out_leg.get("operationParts") or [{}])[0], "Перемещение", -1, "[Списание]", True))
    if in_leg:
        rows.append(row(in_leg, (in_leg.get("operationParts") or [{}])[0], "Перемещение", 1, "[Зачисление]", True))
    anchor = out_leg or in_leg
    groups.append((qof(anchor.get("operationDate")), dt(anchor.get("operationDate")) + str(anchor.get("operationId")), rows))

by_q = {}
for quarter, sk, rows in sorted(groups, key=lambda g: g[1]):
    by_q.setdefault(quarter, []).extend(rows)

# ---------- запись ----------
os.makedirs(OUT, exist_ok=True)
for quarter, rows in sorted(by_q.items()):
    with open(os.path.join(OUT, f"import_{quarter}.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADERS, delimiter=";")
        w.writeheader(); w.writerows(rows)

xlsx_ok = False
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter
    xlsx_ok = True
except Exception:
    print("openpyxl не установлен — .xlsx пропущены (есть CSV). pip install openpyxl")

if xlsx_ok:
    for quarter, rows in sorted(by_q.items()):
        wb = Workbook(); ws = wb.active; ws.title = "Операции"
        ws.append(HEADERS)
        for r in rows:
            ws.append([r[h] for h in HEADERS])
        for c in ws[1]:
            c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="0A8A80")
        ws.freeze_panes = "A2"
        si = HEADERS.index("Сумма") + 1
        for cell in ws[get_column_letter(si)][1:]:
            cell.number_format = '# ##0.00;-# ##0.00'
        widths = {"Назначение платежа": 42, "Статья": 22, "Родительские статьи": 18, "Контрагент": 24,
                  "Счет": 16, "Юрлицо": 14, "Вид деятельности": 24, "Проекты": 20}
        for i, h in enumerate(HEADERS):
            ws.column_dimensions[get_column_letter(i + 1)].width = widths.get(h, 14)
        wb.save(os.path.join(OUT, f"import_{quarter}.xlsx"))

n_unpaid = sum(1 for o in regular if o.get("isCommitted") is False)
n_transfers = sum(1 for r in [x for v in by_q.values() for x in v] if r["Статья"] == "[Списание]")
with open(os.path.join(OUT, "README_ИМПОРТ.md"), "w", encoding="utf-8") as f:
    f.write("# Файлы для импорта в ПланФакт (по шаблону PlanFactCashflowTemplate)\n\n")
    f.write(f"Сформировано: {datetime.datetime.now():%Y-%m-%d %H:%M} · кварталов: {len(by_q)} · строк: "
            f"{sum(len(v) for v in by_q.values())} · переводов: {n_transfers} · неоплаченных: {n_unpaid}.\n\n")
    f.write("## Колонки — один-в-один с шаблоном\n" + " · ".join(f"`{h}`" for h in HEADERS) + "\n\n")
    f.write("## Что учтено\n"
            "- **Сумма со знаком**: Поступление/Зачисление = «+», Выплата/Списание = «−».\n"
            "- **Статусы**: `Статус оплаты`/`Статус начисления` = Подтверждена / Не подтверждена (даты заполнены всегда).\n"
            "- **Перемещения**: две строки подряд — счёт списания `[Списание]` (−), ниже счёт зачисления `[Зачисление]` (+).\n"
            "- **Проекты** в формате «Название (100%)». Вид деятельности переведён (Операционная/Финансовая/Инвестиционная).\n"
            "- Пустые: ИНН, № счёта, Банк, Бик — в API их нет (Сербия). При необходимости добавьте вручную.\n\n")
    f.write("## Как импортировать\n"
            "1. Не добавляйте формулы. Файл уже в XLSX.\n"
            "2. ПланФакт → Операции → Импорт → загрузите нужный квартал.\n"
            "3. На предпросмотре проверьте: переводы распознались как перемещения; неоплаченные не помечены оплаченными; статьи/проекты/контрагенты сопоставились.\n"
            "4. Разбитые на несколько статей операции идут отдельными строками (импортируются как отдельные операции; суммы сохраняются).\n")

print(f"Готово → {OUT}")
print(f"  {len(by_q)} CSV" + (f" + {len(by_q)} XLSX" if xlsx_ok else "") + " + README_ИМПОРТ.md")
