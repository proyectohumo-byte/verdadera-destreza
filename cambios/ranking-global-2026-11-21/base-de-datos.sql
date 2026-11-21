-- Ranking global: tablas y funciones de Supabase (ya ejecutado en el proyecto de Néstor el 21/11/2026).
create table if not exists jugadores (
  id_cliente uuid primary key,
  apodo text not null check (char_length(apodo) between 1 and 24),
  primera_vez timestamptz not null default now(),
  ultima_vez timestamptz not null default now(),
  visitas int not null default 1
);
create table if not exists partidas (
  id bigint generated always as identity primary key,
  creada timestamptz not null default now(),
  id_cliente uuid not null references jugadores(id_cliente),
  nivel text not null check (nivel in ('bisono','discipulo','diestro','preboste','maestro')),
  gano boolean not null,
  tocados_dados smallint not null check (tocados_dados between 0 and 200),
  tocados_recibidos smallint not null check (tocados_recibidos between 0 and 200),
  dobles smallint not null check (dobles between 0 and 100),
  subitas smallint not null check (subitas between 0 and 50),
  duracion_s int not null check (duracion_s between 0 and 14400),
  version text
);
alter table jugadores enable row level security;
alter table partidas enable row level security;
revoke all on jugadores, partidas from anon, authenticated;

create or replace function registrar_visita(p_cliente uuid, p_apodo text)
returns void language plpgsql security definer set search_path = public as $$
begin
  p_apodo := left(btrim(coalesce(p_apodo, '')), 24);
  if p_apodo = '' then p_apodo := 'Anónimo'; end if;
  insert into jugadores(id_cliente, apodo) values (p_cliente, p_apodo)
  on conflict (id_cliente) do update
    set apodo = excluded.apodo, ultima_vez = now(), visitas = jugadores.visitas + 1;
end $$;

create or replace function registrar_partida(
  p_cliente uuid, p_nivel text, p_gano boolean, p_dados int, p_recibidos int,
  p_dobles int, p_subitas int, p_duracion int, p_version text)
returns void language plpgsql security definer set search_path = public as $$
begin
  if not exists (select 1 from jugadores where id_cliente = p_cliente) then
    raise exception 'jugador desconocido';
  end if;
  if exists (select 1 from partidas where id_cliente = p_cliente and creada > now() - interval '10 seconds') then
    raise exception 'demasiado rápido';
  end if;
  insert into partidas(id_cliente, nivel, gano, tocados_dados, tocados_recibidos, dobles, subitas, duracion_s, version)
  values (p_cliente, p_nivel, p_gano, p_dados, p_recibidos, p_dobles, p_subitas, p_duracion, left(p_version, 20));
  update jugadores set ultima_vez = now() where id_cliente = p_cliente;
end $$;

create or replace function ranking_global()
returns table(apodo text, partidas bigint, ganadas bigint, puntos bigint, tocados bigint, ultima timestamptz)
language sql stable security definer set search_path = public as $$
  select j.apodo, count(*), count(*) filter (where p.gano),
         coalesce(sum(case when p.gano then
           case p.nivel when 'bisono' then 1 when 'discipulo' then 2 when 'diestro' then 3
                        when 'preboste' then 4 else 5 end end), 0),
         coalesce(sum(p.tocados_dados), 0), max(p.creada)
  from jugadores j join partidas p using (id_cliente)
  group by j.id_cliente, j.apodo
  order by 4 desc, 3 desc
  limit 50
$$;

grant execute on function registrar_visita(uuid, text) to anon;
grant execute on function registrar_partida(uuid, text, boolean, int, int, int, int, int, text) to anon;
grant execute on function ranking_global() to anon;

-- Consulta para el autor (SQL Editor): quién entra, cuánto y cuándo.
-- select j.apodo, j.primera_vez, j.ultima_vez, j.visitas, count(p.id) as partidas,
--        coalesce(sum(p.duracion_s)/60, 0) as minutos
-- from jugadores j left join partidas p using (id_cliente)
-- group by j.id_cliente order by j.ultima_vez desc;
