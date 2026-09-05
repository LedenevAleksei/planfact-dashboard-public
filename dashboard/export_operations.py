#!/usr/bin/env python3
"""
Экспорт-бэкап ВСЕХ операций ПланФакта поквартально. ТОЛЬКО ЧТЕНИЕ из API.

Пишет в папку export/:
  export/operations_full.json          — полный «сырой» бэкап (без потерь, вся вложенность)
  export/csv/operations_YYYY-QN.csv    — плоская таблица на квартал (UTF-8 BOM, универсальный импорт)
  export/xlsx/operations_YYYY-QN.xlsx  — Excel на квартал (если установлен openpyxl)
  export/README.md                     — словарь колонок и заметки по форматам

Квартал определяется по дате платежа (operationDate). В строках сохранены обе даты
(платежа и начисления), так что данные не теряются.

Запуск:  python3 dashboard/export_operations.py
Для .xlsx нужен openpyxl (pip install openpyxl); без него собираются CSV и JSON.
"""
import json, os, csv, urllib.request, datetime

BASE = "https://api.planfact.io"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "export")
TYPES = ["Income", "Outcome", "Accrual", "Move", "Shipment", "Supply"]
RU_TYPE = {"Income": "Поступление", "Outcome": "Выплата", "Accrual": "Начисление",
           "Move": "Перемещение", "Shipment": "Отгрузка", "Supply": "Поставка"}

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

def quarter(dstr):
    d = (dstr or "")[:10]
    if len(d) < 7:
        return "unknown"
    y, m = int(d[:4]), int(d[5:7])
    return f"{y}-Q{(m - 1) // 3 + 1}"

# ---------- забрать данные (только чтение) ----------
print("Читаю операции из ПланФакта (только чтение)…")
allops = []
for t in TYPES:
    items = (post("/api/v1/operations/list", {"operationType": [t]}).get("data") or {}).get("items") or []
    if items:
        print(f"  {RU_TYPE.get(t, t)}: {len(items)}")
    allops += items
print(f"Всего операций: {len(allops)}")

cd = get("/api/v1/operationcategories").get("data")
cats = cd.get("items") if isinstance(cd, dict) else cd
CM = {c["operationCategoryId"]: c for c in (cats or [])}

# ---------- колонки плоской таблицы (одна строка = одна часть операции) ----------
COLUMNS = [
    ("Квартал",              lambda o, p: quarter(o.get("operationDate"))),
    ("ID операции",          lambda o, p: o.get("operationId")),
    ("Тип",                  lambda o, p: RU_TYPE.get(o.get("operationType"), o.get("operationType"))),
    ("Тип (код)",            lambda o, p: o.get("operationType")),
    ("Дата платежа",         lambda o, p: (o.get("operationDate") or "")[:10]),
    ("Оплачено",             lambda o, p: o.get("isCommitted")),
    ("Дата начисления",      lambda o, p: (p.get("calculationDate") or "")[:10]),
    ("Начисление подтв.",    lambda o, p: p.get("isCalculationCommitted")),
    ("Сумма (RSD)",          lambda o, p: p.get("valueInUserCurrency") or p.get("value")),
    ("Сумма (валюта опер.)", lambda o, p: p.get("value")),
    ("Валюта",               lambda o, p: title(o.get("accountCurrency")) or (o.get("accountCurrency") if isinstance(o.get("accountCurrency"), str) else None)),
    ("Счёт",                 lambda o, p: title(o.get("account"))),
    ("Юрлицо",               lambda o, p: title(o.get("accountCompany"))),
    ("Контрагент",           lambda o, p: title(p.get("contrAgent")) or title(o.get("contrAgent"))),
    ("Статья",               lambda o, p: title(p.get("operationCategory"))),
    ("Тип статьи",           lambda o, p: (CM.get((p.get("operationCategory") or {}).get("operationCategoryId"), {}) or {}).get("accountCategoryType")),
    ("Классификация",        lambda o, p: (CM.get((p.get("operationCategory") or {}).get("operationCategoryId"), {}) or {}).get("outcomeClassification")),
    ("Проект",               lambda o, p: title(p.get("project"))),
    ("Сделка продажи",       lambda o, p: title(p.get("sellingDeal"))),
    ("Сделка закупки",       lambda o, p: title(p.get("purchaseDeal"))),
    ("Назначение / коммент", lambda o, p: o.get("comment")),
    ("№ документа",          lambda o, p: o.get("documentNumber")),
    ("Учитывать в кассе",    lambda o, p: o.get("isOpuCalculation")),
    ("Парная операция",      lambda o, p: o.get("boundMoveOperationId")),
    ("Внешний ID",           lambda o, p: o.get("externalId")),
    ("ID импорта",           lambda o, p: o.get("importLogId")),
    ("Создано",              lambda o, p: o.get("createDate")),
    ("Изменено",             lambda o, p: o.get("modifyDate") or o.get("lastModificationDate")),
    ("ID части",             lambda o, p: p.get("operationPartId")),
]
HEADERS = [c[0] for c in COLUMNS]
AMOUNT_COLS = {"Сумма (RSD)", "Сумма (валюта опер.)"}

def rows_for(op):
    parts = op.get("operationParts") or [{}]
    return [[fn(op, p) for _, fn in COLUMNS] for p in parts]

by_q = {}
for op in allops:
    for row in rows_for(op):
        by_q.setdefault(row[0], []).append(row)

# ---------- запись ----------
os.makedirs(os.path.join(OUT, "csv"), exist_ok=True)
os.makedirs(os.path.join(OUT, "xlsx"), exist_ok=True)

# 1) полный JSON-бэкап (без потерь)
with open(os.path.join(OUT, "operations_full.json"), "w", encoding="utf-8") as f:
    json.dump({"exportedAt": datetime.datetime.now().isoformat(timespec="seconds"),
               "count": len(allops), "operations": allops}, f, ensure_ascii=False, indent=1)

# 2) CSV на квартал (UTF-8 BOM — корректно открывается в Excel)
for q, rows in sorted(by_q.items()):
    with open(os.path.join(OUT, "csv", f"operations_{q}.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(HEADERS)
        w.writerows(rows)

# 3) XLSX на квартал (если есть openpyxl)
xlsx_ok = False
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    xlsx_ok = True
except Exception:
    print("openpyxl не установлен — .xlsx пропущены (есть CSV и JSON). Установите: pip install openpyxl")

if xlsx_ok:
    amt_idx = [i for i, h in enumerate(HEADERS) if h in AMOUNT_COLS]
    for q, rows in sorted(by_q.items()):
        wb = Workbook(); ws = wb.active; ws.title = "Операции"
        ws.append(HEADERS)
        for r in rows:
            ws.append(r)
        # стиль шапки
        hf = Font(bold=True, color="FFFFFF"); fill = PatternFill("solid", fgColor="0A8A80")
        for c in ws[1]:
            c.font = hf; c.fill = fill; c.alignment = Alignment(vertical="center")
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        # формат сумм + ширины
        for i in amt_idx:
            col = get_column_letter(i + 1)
            for cell in ws[col][1:]:
                cell.number_format = '# ##0.00'
        widths = {"Назначение / коммент": 40, "Статья": 26, "Контрагент": 24, "Счёт": 16,
                  "Проект": 20, "Юрлицо": 14}
        for i, h in enumerate(HEADERS):
            ws.column_dimensions[get_column_letter(i + 1)].width = widths.get(h, 15)
        wb.save(os.path.join(OUT, "xlsx", f"operations_{q}.xlsx"))

# 4) README со словарём колонок
with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as f:
    f.write("# Бэкап операций ПланФакт (поквартально)\n\n")
    f.write(f"Сформировано: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} · операций: {len(allops)} · "
            f"строк (по частям): {sum(len(v) for v in by_q.values())} · кварталов: {len(by_q)}.\n\n")
    f.write("## Форматы\n"
            "- **xlsx/** — Excel на каждый квартал (для людей: фильтры, форматирование).\n"
            "- **csv/** — тот же квартал в CSV (UTF-8 BOM, разделитель `;`) — универсальный импорт в Excel, Google Sheets, БД, Python/pandas.\n"
            "- **operations_full.json** — полный бэкап без потерь (вся вложенность операций) — для программного восстановления/переноса.\n\n")
    f.write("Одна строка таблицы = одна **часть операции** (operationPart): статья/проект/сумма/дата начисления. "
            "Квартал — по **дате платежа** (operationDate).\n\n")
    f.write("## Колонки\n| Колонка | Смысл |\n|---|---|\n")
    desc = {"Квартал":"год-квартал по дате платежа","ID операции":"operationId (уникальный)","Тип":"Поступление/Выплата/Перемещение…",
            "Дата платежа":"когда прошли деньги (для ДДС)","Дата начисления":"когда признан доход/расход (для ОПУ)",
            "Оплачено":"isCommitted","Начисление подтв.":"isCalculationCommitted","Сумма (RSD)":"в валюте учёта",
            "Тип статьи":"accountCategoryType (Income/Outcome/…)","Классификация":"outcomeClassification (Fixed=постоянные)",
            "Парная операция":"boundMoveOperationId (для перемещений/начислений)","ID части":"operationPartId"}
    for h in HEADERS:
        f.write(f"| {h} | {desc.get(h,'')} |\n")

print(f"Готово → {OUT}")
print(f"  operations_full.json + {len(by_q)} CSV" + (f" + {len(by_q)} XLSX" if xlsx_ok else " (XLSX пропущены)"))
