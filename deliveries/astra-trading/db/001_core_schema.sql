-- Astra Trading — core schema (v1)
-- Applied via Supabase Management API. Idempotent.

-- ---------- enums ----------
do $$ begin
  create type setup_status as enum
    ('proposed','triggered','tp1_hit','tp2_hit','tp3_hit','stopped','breakeven','expired','invalidated','cancelled');
exception when duplicate_object then null; end $$;

do $$ begin
  create type setup_direction as enum ('long','short');
exception when duplicate_object then null; end $$;

do $$ begin
  create type user_role as enum ('user','support','admin','owner');
exception when duplicate_object then null; end $$;

do $$ begin
  create type sub_status as enum ('trialing','active','past_due','canceled','expired');
exception when duplicate_object then null; end $$;

do $$ begin
  create type pay_status as enum ('pending','confirmed','rejected','duplicate');
exception when duplicate_object then null; end $$;

-- ---------- profiles ----------
create table if not exists public.profiles (
  id            uuid primary key references auth.users(id) on delete cascade,
  email         text,
  full_name     text,
  locale        text not null default 'ar' check (locale in ('ar','en','tr')),
  role          user_role not null default 'user',
  disabled      boolean not null default false,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path=public as $$
begin
  insert into public.profiles (id, email, full_name, locale)
  values (new.id, new.email,
          coalesce(new.raw_user_meta_data->>'full_name',''),
          coalesce(new.raw_user_meta_data->>'locale','ar'))
  on conflict (id) do nothing;
  return new;
end $$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ---------- subscriptions ----------
create table if not exists public.subscriptions (
  id                uuid primary key default gen_random_uuid(),
  user_id           uuid not null references public.profiles(id) on delete cascade,
  plan              text not null default 'pro',
  status            sub_status not null default 'trialing',
  trial_started_at  timestamptz not null default now(),
  trial_ends_at     timestamptz not null default (now() + interval '7 days'),
  period_ends_at    timestamptz,
  provider          text,
  provider_ref      text,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now(),
  unique (user_id)
);

create or replace function public.handle_new_profile()
returns trigger language plpgsql security definer set search_path=public as $$
begin
  insert into public.subscriptions (user_id, status, trial_started_at, trial_ends_at)
  values (new.id, 'trialing', now(), now() + interval '7 days')
  on conflict (user_id) do nothing;
  return new;
end $$;

drop trigger if exists on_profile_created on public.profiles;
create trigger on_profile_created
  after insert on public.profiles
  for each row execute function public.handle_new_profile();

-- ---------- setups (AI-proposed) ----------
create table if not exists public.setups (
  id                uuid primary key default gen_random_uuid(),
  symbol            text not null default 'XAUUSD',
  direction         setup_direction not null,
  entry_type        text not null default 'limit' check (entry_type in ('market','limit','stop')),
  entry             numeric(14,5) not null,
  stop_loss         numeric(14,5) not null,
  tp1               numeric(14,5),
  tp2               numeric(14,5),
  tp3               numeric(14,5),
  risk_reward       numeric(6,2),
  timeframe         text not null default '1h',
  session           text,
  confidence        numeric(4,3) check (confidence >= 0 and confidence <= 1),
  rationale_ar      text,
  rationale_en      text,
  rationale_tr      text,
  factors           jsonb not null default '[]'::jsonb,
  validity_until    timestamptz,
  invalidation      text,
  status            setup_status not null default 'proposed',
  source_agent      text not null default 'astra-analysis',
  idempotency_key   text not null unique,
  created_at        timestamptz not null default now(),
  triggered_at      timestamptz,
  closed_at         timestamptz,
  outcome_price     numeric(14,5),
  outcome_r         numeric(6,2),
  published         boolean not null default false,
  check (
    (direction = 'long'  and stop_loss < entry) or
    (direction = 'short' and stop_loss > entry)
  )
);
create index if not exists setups_status_idx  on public.setups(status, created_at desc);
create index if not exists setups_symbol_idx  on public.setups(symbol, created_at desc);

-- ---------- setup lifecycle events ----------
create table if not exists public.setup_events (
  id          bigserial primary key,
  setup_id    uuid not null references public.setups(id) on delete cascade,
  from_status setup_status,
  to_status   setup_status not null,
  price       numeric(14,5),
  reason      text,
  at          timestamptz not null default now()
);
create index if not exists setup_events_setup_idx on public.setup_events(setup_id, at);

-- ---------- payments ----------
create table if not exists public.payments (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid references public.profiles(id) on delete set null,
  provider       text not null default 'usdt_trc20',
  network        text,
  tx_hash        text,
  to_address     text,
  amount         numeric(18,6),
  currency       text not null default 'USDT',
  confirmations  integer not null default 0,
  status         pay_status not null default 'pending',
  raw            jsonb,
  created_at     timestamptz not null default now(),
  verified_at    timestamptz,
  unique (provider, tx_hash)
);
create index if not exists payments_user_idx on public.payments(user_id, created_at desc);

-- ---------- agent API keys ----------
create table if not exists public.agent_keys (
  id           uuid primary key default gen_random_uuid(),
  name         text not null,
  key_hash     text not null unique,
  scopes       text[] not null default array['setups:write'],
  created_at   timestamptz not null default now(),
  last_used_at timestamptz,
  revoked_at   timestamptz
);

-- ---------- audit log ----------
create table if not exists public.audit_log (
  id        bigserial primary key,
  actor     text,
  action    text not null,
  target    text,
  meta      jsonb not null default '{}'::jsonb,
  at        timestamptz not null default now()
);

-- ---------- alerts ----------
create table if not exists public.alerts (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references public.profiles(id) on delete cascade,
  channel    text not null default 'email' check (channel in ('email','telegram','push')),
  address    text,
  enabled    boolean not null default true,
  created_at timestamptz not null default now(),
  unique (user_id, channel)
);

-- ================= ROW LEVEL SECURITY =================
alter table public.profiles      enable row level security;
alter table public.subscriptions enable row level security;
alter table public.setups        enable row level security;
alter table public.setup_events  enable row level security;
alter table public.payments      enable row level security;
alter table public.agent_keys    enable row level security;
alter table public.audit_log     enable row level security;
alter table public.alerts        enable row level security;

create or replace function public.is_staff()
returns boolean language sql stable security definer set search_path=public as $$
  select exists (select 1 from public.profiles p
                 where p.id = auth.uid() and p.role in ('support','admin','owner'));
$$;

drop policy if exists profiles_self_read on public.profiles;
create policy profiles_self_read on public.profiles for select using (id = auth.uid() or public.is_staff());
drop policy if exists profiles_self_update on public.profiles;
create policy profiles_self_update on public.profiles for update using (id = auth.uid()) with check (id = auth.uid());

drop policy if exists subs_self_read on public.subscriptions;
create policy subs_self_read on public.subscriptions for select using (user_id = auth.uid() or public.is_staff());

drop policy if exists setups_read on public.setups;
create policy setups_read on public.setups for select using (
  public.is_staff()
  or (
    auth.uid() is not null
    and exists (
      select 1 from public.subscriptions s
      where s.user_id = auth.uid()
        and s.status in ('trialing','active')
        and (s.status = 'active' or s.trial_ends_at > now())
    )
  )
);

drop policy if exists setup_events_read on public.setup_events;
create policy setup_events_read on public.setup_events for select using (
  exists (select 1 from public.setups st where st.id = setup_id)
);

drop policy if exists payments_self_read on public.payments;
create policy payments_self_read on public.payments for select using (user_id = auth.uid() or public.is_staff());

drop policy if exists alerts_self_all on public.alerts;
create policy alerts_self_all on public.alerts for all using (user_id = auth.uid() or public.is_staff())
  with check (user_id = auth.uid() or public.is_staff());

-- ---------- public track record view (no PII) ----------
create or replace view public.track_record as
select
  count(*) filter (where status in ('tp1_hit','tp2_hit','tp3_hit')) as wins,
  count(*) filter (where status = 'stopped')                      as losses,
  count(*) filter (where status = 'breakeven')                    as breakevens,
  count(*) filter (where status in ('proposed','triggered'))      as open,
  count(*)                                                        as total,
  round(avg(outcome_r) filter (where outcome_r is not null), 2)   as avg_r
from public.setups
where published = true;
grant select on public.track_record to anon, authenticated;
