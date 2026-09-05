# Архитектура

## Принцип безопасности
API-ключ ПланФакта **никогда не попадает в браузер**. Дашборд не ходит в API из клиентского JS. Схема:

```
Браузер (логин/пароль)  ──>  наш backend  ──>  API ПланФакта
                              (ключ в .env, только на сервере)
```

## Потоки данных дашборда

```
ПланФакт API ──(fetch_data.py, только чтение)──> dashboard/data/dashboard.json ──(build.py)──> dashboard/index.html
```

- `dashboard/fetch_data.py` — единственная точка обращения к API. Читает ключ из `.env`, тянет данные, считает агрегаты, пишет `data/dashboard.json`. Ключ в JSON не попадает.
- `dashboard/build.py` — чистый рендер: берёт `dashboard.json`, генерирует самодостаточный `index.html` (данные вшиты, открывается по `file://`).
- `dashboard/plans.json` — **план продаж по кварталам/категориям** (правится CEO). Читается `fetch_data.py`, сравнивается с фактом. В Фазе 1 форма плана дублирует значения в localStorage браузера; в Фазе 2 форма POST-ит на сервер, который перезаписывает `plans.json`.
- Разделение fetch/build позволяет отлаживать UI на закэшированных данных, не нагружая API.

## Фазы
- **Фаза 1:** локальная отладка HTML. «Обновить» = перезапуск `fetch_data.py` + `build.py`.
- **Фаза 2 (реализована):** веб-сервис `app.py` (Flask) на **Railway** (nixpacks), тот же стек, что у ServiceBot. Страница за Basic-Auth (`DASH_USER`/`DASH_PASS`), эндпоинт `POST /refresh` (серверный запуск `fetch_data.py`+`build.py` через subprocess), `GET /health` для healthcheck, планировщик APScheduler в 10:00 Europe/Belgrade. Ключ и пароль — только из переменных окружения. `fetch_data.py`/`build.py` переиспользуются без изменений. Инструкция — `DEPLOY.md`.

### Веб-схема (Фаза 2)
```
Браузер (Basic-Auth) → Railway: app.py (gunicorn, 1 worker)
                          ├─ GET /         → dashboard/index.html
                          ├─ POST /refresh → subprocess: fetch_data.py → build.py
                          ├─ GET /health   → ok
                          └─ cron 10:00    → refresh
                       ключ PLANFACT_API_KEY только в env сервера
```
`load_key()` читает ключ сперва из переменной окружения (сервер), затем из `.env` (локально).

## Используемые эндпоинты API (все — чтение)
| Эндпоинт | Зачем |
|---|---|
| `GET /api/v1/companies` | проверка ключа, список юрлиц, заголовки лимитов |
| `GET /api/v1/accounts` | список счетов |
| `GET /api/v1/bizinfos/accountshistory` | остатки по счетам (накопленный факт) |
| `POST /api/v1/operations/list` | операции (доходы/расходы) для реестров и гигиены |
| `POST /api/v2/reports/opu` | ОПУ (P&L): начисление и касса, по статьям/месяцам |
| `POST /api/v2/reports/dds` | ДДС (денежный поток) по видам деятельности/месяцам |
| `GET /api/v1/operationcategories` | справочник статей + классификация (`accountCategoryType`, `outcomeClassification`) для строк P&L |
| `GET /api/v1/projects` | справочник проектов: группа (`projectGroup`), статус (`closed`) для вкладки «Проекты» (финансы считаются из операций) |
| `GET /api/v1/operations/get-undistributed-operation-count` | счётчик нераспределённых |

### Классификация строк P&L (маржинальный ОПУ)
По полю `accountCategoryType` статьи: `Income`→Выручка; `IncomeOther`→Прочие доходы; `Outcome`→операционные расходы (далее по `outcomeClassification`: содержит `Fixed`→Постоянные, иначе→Переменные); `OutcomeOther`→Прочие расходы; `OutcomeTax`→Налог; `OutcomeDepreciation`→Амортизация; `OutcomeCreditPercent`→Проценты; `OutcomeUndistributed`→Переменные (нераспределённый расход, как в ОПУ ПланФакта); `CapitalDividends`→Дивиденды. Маржинальная прибыль = Выручка − Переменные. Инвестиции/капитал/активы в P&L не входят.

Технические нюансы (формат дат `YYYY-MM-DD`, `operationType` как массив, поведение пагинации, `value` vs `valueInUserCurrency`, boolean-флаги) — см. `docs/planfact-agent-kit/QUICKSTART.md` и `OPERATIONS.md`.

## Ключевые определения расчётов
- **Касса (факт):** операции с `isCommitted == true`, по `operationDate`.
- **Начисление:** по `isCalculationCommitted == true` / `calculationDate`.
- **Дебиторка:** Income, `isCommitted == false` + `isCalculationCommitted == true` (продано, не получено).
- **Кредиторка:** Outcome, те же флаги (начислено, не оплачено). Контрагент-заглушка «Планир(у)мая себестоимость» исключается.
- **Недельные корзины (деб/кред):** `Просрочено` (до тек. недели) │ `Тек. неделя` │ +6 недель │ `Позже`. Неделя = ожидаемая дата оплаты (`operationDate`). Горизонт задаётся `HORIZON` в `fetch_data.py`.
- Дата отсчёта («сегодня») в `fetch_data.py` — **всегда текущая дата** (`datetime.date.today()`); метка сборки — текущее время. Для теста можно передать аргументом: `python3 dashboard/fetch_data.py 2026-07-01`.

## Лимиты API (тариф на момент написания)
100 запросов/мин, 50 000/мес. Одна пересборка дашборда ≈ 6 запросов.
