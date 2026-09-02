// Private, opt-in rain push storage. No GPS history; seven-day expiry.
begin;
create schema if not exists floodsafe_rain_private;
revoke all on schema floodsafe_rain_private from public,anon,authenticated,service_role;
create table if not exists floodsafe_rain_private.config(
 id smallint primary key check(id=1), public_key text, private_secret_id uuid,
 last_tick timestamptz, last_success timestamptz, last_result jsonb
);
insert into floodsafe_rain_private.config(id) values(1) on conflict do nothing;
create table if not exists floodsafe_rain_private.subscriptions(
 id uuid primary key default gen_random_uuid(), endpoint_hash text unique not null,
 subscription jsonb not null, token_hash text not null,
 lat double precision not null check(lat between -90 and 90),
 lon double precision not null check(lon between -180 and 180),
 point_key text not null, lang text not null check(lang in ('en','ne')),
 created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
 expires_at timestamptz not null, last_sent_at timestamptz, last_test_at timestamptz
);
create index if not exists rain_subscriptions_expiry on floodsafe_rain_private.subscriptions(expires_at);
create table if not exists floodsafe_rain_private.forecasts(
 point_key text primary key, payload jsonb, fetched_at timestamptz, attempted_at timestamptz not null default now()
);
create table if not exists floodsafe_rain_private.deliveries(
 subscription_id uuid not null references floodsafe_rain_private.subscriptions(id) on delete cascade,
 tag text not null, attempted_at timestamptz not null, status text not null,
 attempts integer not null default 1, primary key(subscription_id,tag)
);
alter table floodsafe_rain_private.config enable row level security;
alter table floodsafe_rain_private.subscriptions enable row level security;
alter table floodsafe_rain_private.forecasts enable row level security;
alter table floodsafe_rain_private.deliveries enable row level security;
revoke all on all tables in schema floodsafe_rain_private from public,anon,authenticated,service_role;
alter default privileges in schema floodsafe_rain_private revoke all on tables from public,anon,authenticated,service_role;
do $block$
begin
 if not exists(select 1 from vault.secrets where name='floodsafe-rain-cron-v1') then
  perform vault.create_secret(encode(extensions.gen_random_bytes(32),'hex'),'floodsafe-rain-cron-v1','Authenticates only the rain push scheduler');
 end if;
end
$block$;
select cron.schedule('floodsafe-rain-push-minute','* * * * *',$job$
 select net.http_post(
  url:='https://camkoacuokffryyrygda.supabase.co/functions/v1/rain-alerts',
  headers:=jsonb_build_object('Content-Type','application/json','x-rain-cron-key',(select decrypted_secret from vault.decrypted_secrets where name='floodsafe-rain-cron-v1')),
  body:='{"action":"tick"}'::jsonb,timeout_milliseconds:=55000
 )
 where exists(select 1 from floodsafe_rain_private.subscriptions)
$job$);
commit;
