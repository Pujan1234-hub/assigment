create table public.fs_feedback_push_device (
 slot boolean primary key default true check(slot),
 fcm_token text not null check(length(fcm_token) between 20 and 4096),
 admin_hash text not null check(length(admin_hash)=64)
);
alter table public.fs_feedback_push_device enable row level security;
revoke all on public.fs_feedback_push_device from public,anon,authenticated,service_role;
grant select,insert,update,delete on public.fs_feedback_push_device to service_role;
