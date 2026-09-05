# Деплой (Фаза 2) — Railway + приватный GitHub

Тот же стек, что у ServiceBot: **Railway** (nixpacks). Дашборд — один Flask-сервис:
отдаёт HTML за логином/паролем, серверный `/refresh`, автообновление в 10:00 (Europe/Belgrade).
Ключ ПланФакта и пароль — только в переменных окружения Railway, в браузер/репозиторий не попадают.

## Статус (уже сделано)
- Приватный репозиторий: **https://github.com/LedenevAleksei/planfact-dashboard**
- Railway-проект **planfact-dashboard** создан и задеплоен. **Рабочий адрес (финальный):**
  **https://planfact-dashboard-production.up.railway.app** (`/health` = 200).
- Переменная `SUPABASE_URL` уже задана.
- **Осталось задать 4 секрета** (см. ниже) — после этого можно логиниться.

### Про кастомный домен (отложено)
Пробовали `tekstura.reply24.pro` (Cloudflare), но Railway не выпустил TLS-сертификат
(похоже, ограничение плана на кастомные домены), а HSTS на `reply24.pro` не даёт открыть
поддомен без валидного HTTPS. **Решение: остаёмся на рабочем Railway-URL.** DNS-запись
`tekstura` в Cloudflare удалена. Код Cloudflare Access (`CF_ACCESS_*`) остаётся в `app.py`
дремлющим — активируется, только если задать переменные; сейчас работает чистый Basic-Auth.
Чтобы вернуться к домену позже — поднять план Railway, заново добавить домен и CNAME.

### Задать секреты (в панели Railway → сервис → Variables, или своим терминалом)
```bash
# из своего терминала (значения подставить свои; НЕ коммитить):
railway variables --service planfact-dashboard \
  --set "DASH_USER=ВАШ_ЛОГИН" \
  --set "DASH_PASS=ВАШ_ПАРОЛЬ" \
  --set "PLANFACT_API_KEY=КЛЮЧ_ПЛАНФАКТА" \
  --set "SUPABASE_SERVICE_KEY=SERVICE_ROLE_КЛЮЧ"
```
`SUPABASE_SERVICE_KEY` — из Supabase → Project Settings → API → service_role.
После сохранения Railway сам передеплоит; открывайте домен и логиньтесь.

## Что уже готово в репозитории
| Файл | Роль |
|---|---|
| `app.py` | Flask: `/` (за Basic-Auth), `POST /refresh`, `GET /health`, планировщик 10:00 |
| `requirements.txt` | Flask, gunicorn, APScheduler, tzdata |
| `railway.toml` | сборка nixpacks, `startCommand`, healthcheck `/health` |
| `Procfile`, `.python-version` | запуск gunicorn, версия Python 3.12 |
| `.gitignore` | `.env` и ключи никогда не коммитятся |

## Шаг 1. Приватный репозиторий GitHub
Локально уже сделан `git init` и первый коммит. Создать приватный репозиторий и запушить:

```bash
cd /Users/alekseiledenev/Documents/PlanFact

# вариант с gh CLI (если установлен и авторизован):
gh repo create planfact-dashboard --private --source=. --remote=origin --push

# или вручную: создайте пустой приватный репозиторий на github.com, затем:
git remote add origin git@github.com:ВАШ_ЛОГИН/planfact-dashboard.git
git branch -M main
git push -u origin main
```

## Шаг 2. Сервис на Railway
1. Railway → **New Project → Deploy from GitHub repo** → выберите `planfact-dashboard`.
2. Railway подхватит `railway.toml` (nixpacks, старт `gunicorn`, healthcheck `/health`).
3. **Variables** (вкладка переменных сервиса) — задайте:
   - `PLANFACT_API_KEY` — ваш ключ ПланФакта (только чтение);
   - `DASH_USER` — логин для входа;
   - `DASH_PASS` — пароль для входа;
   - `SUPABASE_URL` — `https://wrihiaxavnyklectnusd.supabase.co` (проект servicebot);
   - `SUPABASE_SERVICE_KEY` — **service_role** ключ из Supabase → Project Settings → API
     (секрет, только на сервере; без него реестры откатятся на localStorage браузера);
   - *(необязательно)* `DASH_TZ=Europe/Belgrade`, `DASH_REFRESH_HOUR=10`.
4. **Networking → Generate Domain** — получите публичный URL.
5. Откройте URL → браузер спросит логин/пароль (`DASH_USER`/`DASH_PASS`).

При первом старте сервис сам соберёт данные (fetch + build). Дальше — кнопка «Обновить»
в интерфейсе (POST `/refresh`) и автоматически каждый день в 10:00.

## Cloudflare перед Railway (Вариант A — авторизация через Cloudflare Access)
Бэкенд остаётся на Railway; Cloudflare даёт домен + вход через **Cloudflare Access**.
Приложение пускает по ЛИБО валидному Access-JWT (домен, без второго пароля), ЛИБО Basic-Auth
(прямой `*.up.railway.app` остаётся защищён — Access его не прикрывает).

1. **Домен на Railway.** Сервис → Settings → Networking → **Custom Domain** → `dash.вашдомен`.
   Railway покажет CNAME-цель (`...up.railway.app`).
2. **DNS в Cloudflare.** В зоне вашего домена: CNAME `dash` → цель из п.1, **proxied (оранжевое облако)**.
3. **Cloudflare Zero Trust → Access → Applications → Add (Self-hosted).**
   - Application domain: `dash.вашдомен`;
   - политика: разрешить нужные email (у вас «авторизация уже есть» — переиспользуйте её);
   - после создания скопируйте **Application Audience (AUD) tag** и **team-домен**
     (`ваша-команда.cloudflareaccess.com`).
4. **Переменные Railway:** `CF_ACCESS_TEAM_DOMAIN`, `CF_ACCESS_AUD` (из п.3).
   Basic-Auth (`DASH_USER`/`DASH_PASS`) оставьте — он защищает прямой Railway-URL.

Теперь: домен `dash.вашдомен` → Cloudflare Access (логин) → дашборд без второго пароля.

## Обновление после правок кода
```bash
git add -A && git commit -m "..."   # что изменили
git push                            # Railway задеплоит автоматически
```

## Заметки
- **Один worker** (`--workers 1` в `railway.toml`/`Procfile`) — чтобы планировщик 10:00 и
  блокировка одновременных `/refresh` работали в одном процессе. Не увеличивайте без нужды.
- **Правило №1 (только чтение)** соблюдено и на сервере: `/refresh` вызывает те же
  `fetch_data.py`/`build.py`, которые не пишут в API.
- **Реестры одобрения платежей** хранятся в **Supabase** (таблица `pf_payment_registers`,
  проект servicebot). Браузер ходит в наш `/api/registers` (за Basic-Auth), сервер — в Supabase
  сервисным ключом. Ни anon-, ни service-ключ Supabase в браузер не попадают. Если
  `SUPABASE_URL`/`SUPABASE_SERVICE_KEY` не заданы — реестры откатываются на localStorage
  (Фаза 1, `file://`). Таблица создана миграцией, RLS включён (доступ только сервисным ключом).
