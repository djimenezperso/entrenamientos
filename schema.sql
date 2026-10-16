-- Pega esto en Supabase → SQL Editor → Run

create table if not exists public.workouts (
  id           uuid primary key default gen_random_uuid(),
  athlete      text not null,
  date         date not null,
  type         text not null,
  title        text,
  duration_sec integer,
  entries      jsonb not null default '[]'::jsonb,
  notes        text,
  photo_path   text,
  created_at   timestamptz not null default now()
);
create index if not exists workouts_athlete_date on public.workouts (athlete, date desc);

-- Bloquea el acceso público a la tabla: la app usa la service_role key desde el servidor.
alter table public.workouts enable row level security;

-- Bucket para las fotos (público para poder mostrarlas; los nombres son aleatorios).
insert into storage.buckets (id, name, public)
values ('fotos', 'fotos', true)
on conflict (id) do nothing;
