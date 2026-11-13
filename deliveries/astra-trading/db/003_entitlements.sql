-- 003_entitlements.sql — server-side trial + subscription entitlements.
--
-- The trial used to live in browser localStorage, so it was trivially reset and
-- the UI could show "7 days left" and "trial ended" at the same time. This makes
-- entitlement a server fact keyed by an anonymous device token the API issues.

create table if not exists public.devices (
  id                uuid primary key default gen_random_uuid(),
  token_hash        text not null unique,        -- sha256 of the device token
  created_at        timestamptz not null default now(),
  last_seen_at      timestamptz not null default now(),
  locale            text,
  user_agent        text
);

create index if not exists devices_token_hash_idx on public.devices (token_hash);

create table if not exists public.entitlements (
  id                uuid primary key default gen_random_uuid(),
  device_id         uuid not null references public.devices(id) on delete cascade,
  status            public.sub_status not null default 'trialing',
  plan              text not null default 'trial',
  trial_started_at  timestamptz not null default now(),
  trial_ends_at     timestamptz not null default (now() + interval '7 days'),
  paid_until        timestamptz,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now(),
  unique (device_id)
);

create index if not exists entitlements_device_idx on public.entitlements (device_id);

-- Link payments to a device so a verified payment can activate an entitlement.
alter table public.payments
  add column if not exists device_id uuid references public.devices(id) on delete set null;

alter table public.devices       enable row level security;
alter table public.entitlements  enable row level security;

-- No anon policies: only the service role (the API) touches these tables.
drop policy if exists devices_service_only on public.devices;
drop policy if exists entitlements_service_only on public.entitlements;

-- Resolve an entitlement for a device token hash, starting a trial on first use.
create or replace function public.ensure_entitlement(p_token_hash text)
returns table (
  status public.sub_status,
  plan text,
  trial_started_at timestamptz,
  trial_ends_at timestamptz,
  paid_until timestamptz,
  days_left integer,
  active boolean
)
language plpgsql
security definer
as $$
declare
  v_device_id uuid;
  v_ent public.entitlements;
begin
  insert into public.devices (token_hash)
  values (p_token_hash)
  on conflict (token_hash) do update set last_seen_at = now()
  returning id into v_device_id;

  insert into public.entitlements (device_id, status, plan, trial_started_at, trial_ends_at)
  values (v_device_id, 'trialing', 'trial', now(), now() + interval '7 days')
  on conflict (device_id) do nothing;

  select * into v_ent from public.entitlements where device_id = v_device_id;

  -- Expire a trial whose window has passed and which has no paid coverage.
  if v_ent.status = 'trialing'
     and v_ent.trial_ends_at < now()
     and (v_ent.paid_until is null or v_ent.paid_until < now()) then
    update public.entitlements
       set status = 'expired', updated_at = now()
     where id = v_ent.id
     returning * into v_ent;
  end if;

  return query
  select
    v_ent.status,
    v_ent.plan,
    v_ent.trial_started_at,
    v_ent.trial_ends_at,
    v_ent.paid_until,
    -- Paid coverage wins over the trial window: report days until whichever
    -- end date is later, so a paying user never sees trial days remaining.
    greatest(0, ceil(extract(epoch from (
      greatest(
        coalesce(v_ent.paid_until, to_timestamp(0)),
        v_ent.trial_ends_at
      ) - now()
    )) / 86400))::int,
    (v_ent.status = 'active')
      or (v_ent.status = 'trialing' and v_ent.trial_ends_at > now())
      or (v_ent.paid_until is not null and v_ent.paid_until > now());
end;
$$;

-- Activate paid coverage for a device (called after a payment is verified).
create or replace function public.activate_entitlement(p_token_hash text, p_days integer default 30)
returns void
language plpgsql
security definer
as $$
declare
  v_device_id uuid;
begin
  select id into v_device_id from public.devices where token_hash = p_token_hash;
  if v_device_id is null then
    raise exception 'unknown device';
  end if;
  update public.entitlements
     set status = 'active',
         plan = 'pro',
         paid_until = greatest(coalesce(paid_until, now()), now()) + (p_days || ' days')::interval,
         updated_at = now()
   where device_id = v_device_id;
end;
$$;
