-- Atomic protection: stale/partial concurrent syncs cannot replace a valid observation.
create or replace function public.floodsafe_preserve_river_observation()
returns trigger language plpgsql security invoker set search_path = '' as $$
begin
  if old.measured_at is not null and old.water_level is not null
     and old.measured_at <= now() + interval '5 minutes'
     and (new.measured_at is null or new.water_level is null
          or new.measured_at < old.measured_at
          or new.measured_at > now() + interval '5 minutes') then
    return old;
  end if;
  return new;
end;
$$;
revoke all on function public.floodsafe_preserve_river_observation() from public, anon, authenticated;
create or replace trigger floodsafe_preserve_river_observation
before update on public.river_stations
for each row execute function public.floodsafe_preserve_river_observation();
