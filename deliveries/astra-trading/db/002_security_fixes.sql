-- Astra Trading — migration 002: fixes found by the security red-team (RLS v1)
--
-- Finding 1 (CRITICAL) privilege escalation: a user could UPDATE their own
--   profiles.role to 'admin', after which public.is_staff() returned true and
--   unlocked every other user's data. Fix: block role/disabled changes unless
--   the actor is already staff, via a BEFORE UPDATE trigger (RLS cannot restrict
--   individual columns).
--
-- Finding 2 (HIGH) shadow-mode leak: the setups read policy let any active
--   subscriber read rows regardless of `published`, so unpublished (unproven)
--   AI setups were visible. Fix: require published = true for non-staff.

-- --------------------------------------------------------------------------- #
-- Finding 1: no self-escalation
-- --------------------------------------------------------------------------- #
create or replace function public.prevent_privilege_escalation()
returns trigger language plpgsql security definer set search_path=public as $$
begin
  if (new.role is distinct from old.role)
     or (new.disabled is distinct from old.disabled)
     or (new.id is distinct from old.id) then
    if not public.is_staff() then
      raise exception 'only staff may change role, disabled or id'
        using errcode = '42501';
    end if;
  end if;
  new.updated_at := now();
  return new;
end $$;

drop trigger if exists profiles_guard on public.profiles;
create trigger profiles_guard
  before update on public.profiles
  for each row execute function public.prevent_privilege_escalation();

-- Belt and braces: the update policy must not let a user change their own row
-- into a staff row. Re-assert it explicitly.
drop policy if exists profiles_self_update on public.profiles;
create policy profiles_self_update on public.profiles
  for update
  using (id = auth.uid() or public.is_staff())
  with check (
    public.is_staff()
    or (
      id = auth.uid()
      and role = (select p.role from public.profiles p where p.id = auth.uid())
      and disabled = false
    )
  );

-- --------------------------------------------------------------------------- #
-- Finding 2: unpublished setups stay hidden from everyone but staff
-- --------------------------------------------------------------------------- #
drop policy if exists setups_read on public.setups;
create policy setups_read on public.setups for select using (
  public.is_staff()
  or (
    published = true
    and auth.uid() is not null
    and exists (
      select 1 from public.subscriptions s
      where s.user_id = auth.uid()
        and s.status in ('trialing','active')
        and (s.status = 'active' or s.trial_ends_at > now())
    )
  )
);

-- setup_events inherit their parent's visibility exactly.
drop policy if exists setup_events_read on public.setup_events;
create policy setup_events_read on public.setup_events for select using (
  exists (
    select 1 from public.setups st
    where st.id = setup_id
      and (public.is_staff() or st.published = true)
  )
);

-- --------------------------------------------------------------------------- #
-- Payments: a user may create their own pending claim, never confirm one.
-- --------------------------------------------------------------------------- #
drop policy if exists payments_self_insert on public.payments;
create policy payments_self_insert on public.payments for insert with check (
  user_id = auth.uid() and status = 'pending'
);

drop policy if exists payments_no_user_update on public.payments;
create policy payments_no_user_update on public.payments for update using (
  public.is_staff()
) with check (public.is_staff());

-- --------------------------------------------------------------------------- #
-- track_record must never expose anything but aggregates
-- --------------------------------------------------------------------------- #
revoke all on public.track_record from anon, authenticated;
grant select on public.track_record to anon, authenticated;
