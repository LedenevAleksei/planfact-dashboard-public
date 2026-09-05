-- Схема Supabase для CEO-дашборда ПланФакта.
-- Нужна ТОЛЬКО для общих «Реестров одобрения платежей» и общих настроек между пользователями.
-- Без Supabase дашборд работает полностью — но реестры и настройки хранятся локально в браузере
-- (не общие). Хотите «как у оригинала» (общие реестры) — создайте свой проект Supabase и примените этот SQL.
--
-- Как применить: Supabase → ваш проект → SQL Editor → вставить всё ниже → Run.
-- Затем задайте в окружении (локально в .env, на хостинге — в переменных):
--   SUPABASE_URL         — Project Settings → API → Project URL
--   SUPABASE_SERVICE_KEY — Project Settings → API → service_role (секретный, только на сервере)

-- Реестры одобрения платежей
create table if not exists public.pf_payment_registers (
  id    text primary key,               -- 'R' + метка времени
  ts    timestamptz not null,           -- когда создан (ISO)
  total numeric      not null default 0, -- сумма реестра
  items jsonb        not null default '[]'::jsonb  -- список платежей
);

-- Общие настройки дашборда (план продаж, валюта, ручной остаток банка и т.п.)
create table if not exists public.pf_settings (
  key   text primary key,
  value jsonb
);

-- Включаем RLS (row level security — построчный доступ). Политик НЕ добавляем:
-- доступ идёт только сервисным ключом (service_role обходит RLS), публичный доступ закрыт.
alter table public.pf_payment_registers enable row level security;
alter table public.pf_settings          enable row level security;
