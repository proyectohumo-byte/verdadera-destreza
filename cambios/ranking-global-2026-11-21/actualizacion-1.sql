-- Actualización 1 del ranking global: quién está conectado, tiempo abierto, eventos de uso y funciones del panel.
-- Se puede ejecutar más de una vez. ANTES de ejecutar: cambia CAMBIA_ESTA_CLAVE (en la línea del insert) por una
-- contraseña tuya. No subir al repositorio la versión con la contraseña real.

alter table jugadores add column if not exists segundos int not null default 0;

create table if not exists eventos (
  id bigint generated always as identity primary key,
  creada timestamptz not null default now(),
  id_cliente uuid not null references jugadores(id_cliente),
  tipo text not null check (char_length(tipo) between 1 and 40),
  dato jsonb check (dato is null or pg_column_size(dato) < 3000)
);
create index if not exists eventos_cliente_idx on eventos (id_cliente, creada);
create table if not exists ajustes_admin (clave text not null);
alter table eventos enable row level security;
alter table ajustes_admin enable row level security;
revoke all on eventos, ajustes_admin from anon, authenticated;

delete from ajustes_admin;
insert into ajustes_admin(clave) values ('CAMBIA_ESTA_CLAVE');

create or replace function es_admin(p_clave text) returns boolean
language plpgsql security definer set search_path = public as $$
begin
  if exists (select 1 from ajustes_admin where clave = p_clave) then return true; end if;
  perform pg_sleep(1);
  return false;
end $$;
revoke all on function es_admin(text) from public, anon, authenticated;

-- Pulso del juego abierto (cada minuto): sirve para saber quién está conectado y cuánto tiempo.
create or replace function latido(p_cliente uuid) returns void
language plpgsql security definer set search_path = public as $$
begin
  update jugadores
     set segundos = segundos + least(greatest(extract(epoch from (now() - ultima_vez))::int, 0), 90),
         ultima_vez = now()
   where id_cliente = p_cliente;
end $$;

-- Eventos de uso en lote (qué botones y funciones se usan, estadísticas de cada partida, tipo de pantalla).
create or replace function registrar_eventos(p_cliente uuid, p_eventos jsonb) returns void
language plpgsql security definer set search_path = public as $$
begin
  if jsonb_typeof(p_eventos) is distinct from 'array' or jsonb_array_length(p_eventos) > 100 then
    raise exception 'datos no válidos';
  end if;
  if not exists (select 1 from jugadores where id_cliente = p_cliente) then raise exception 'jugador desconocido'; end if;
  if (select count(*) from eventos where id_cliente = p_cliente and creada > now() - interval '1 hour') > 3000 then
    raise exception 'demasiados eventos';
  end if;
  insert into eventos(id_cliente, tipo, dato, creada)
  select p_cliente, left(e->>'t', 40), e->'d',
         case when (e->>'ts') ~ '^[0-9]{10,14}$'
              then greatest(now() - interval '1 day', least(now(), to_timestamp((e->>'ts')::numeric / 1000.0)))
              else now() end
  from jsonb_array_elements(p_eventos) as e
  where coalesce(e->>'t', '') <> '';
end $$;

drop function if exists resumen_admin(text);
create function resumen_admin(p_clave text)
returns table(apodo text, primera_vez timestamptz, ultima_vez timestamptz, visitas int, abierto_min numeric,
              dias bigint, n_partidas bigint, n_ganadas bigint, dados bigint, recibidos bigint,
              dobles bigint, subitas bigint, minutos numeric)
language plpgsql security definer set search_path = public as $$
begin
  if not es_admin(p_clave) then raise exception 'no autorizado'; end if;
  return query
    select j.apodo, j.primera_vez, j.ultima_vez, j.visitas, round(j.segundos / 60.0, 1),
           count(distinct (p.creada at time zone 'Europe/Madrid')::date) filter (where p.version is distinct from 'historico'),
           count(p.id), count(p.id) filter (where p.gano),
           coalesce(sum(p.tocados_dados), 0), coalesce(sum(p.tocados_recibidos), 0),
           coalesce(sum(p.dobles), 0), coalesce(sum(p.subitas), 0), round(coalesce(sum(p.duracion_s), 0) / 60.0, 1)
    from jugadores j left join partidas p on p.id_cliente = j.id_cliente
    group by j.id_cliente order by j.ultima_vez desc;
end $$;

create or replace function niveles_admin(p_clave text)
returns table(apodo text, nivel text, n_partidas bigint, n_ganadas bigint, dados bigint, recibidos bigint,
              dobles bigint, subitas bigint, minutos numeric)
language plpgsql security definer set search_path = public as $$
begin
  if not es_admin(p_clave) then raise exception 'no autorizado'; end if;
  return query
    select j.apodo, p.nivel, count(p.id), count(p.id) filter (where p.gano), sum(p.tocados_dados), sum(p.tocados_recibidos),
           sum(p.dobles), sum(p.subitas), round(coalesce(sum(p.duracion_s), 0) / 60.0, 1)
    from partidas p join jugadores j on j.id_cliente = p.id_cliente
    group by j.id_cliente, j.apodo, p.nivel order by j.apodo, p.nivel;
end $$;

create or replace function ultimas_admin(p_clave text)
returns table(creada timestamptz, apodo text, nivel text, gano boolean, tocados_dados smallint,
              tocados_recibidos smallint, dobles smallint, subitas smallint, duracion_s int, version text)
language plpgsql security definer set search_path = public as $$
begin
  if not es_admin(p_clave) then raise exception 'no autorizado'; end if;
  return query
    select p.creada, j.apodo, p.nivel, p.gano, p.tocados_dados, p.tocados_recibidos, p.dobles, p.subitas, p.duracion_s, p.version
    from partidas p join jugadores j on j.id_cliente = p.id_cliente
    order by p.creada desc limit 100;
end $$;

-- Actividad por día (hora de Madrid). No cuenta las partidas importadas del histórico.
create or replace function dias_admin(p_clave text)
returns table(dia date, jugadores bigint, n_partidas bigint, minutos numeric)
language plpgsql security definer set search_path = public as $$
begin
  if not es_admin(p_clave) then raise exception 'no autorizado'; end if;
  return query
    select (p.creada at time zone 'Europe/Madrid')::date, count(distinct p.id_cliente), count(p.id),
           round(coalesce(sum(p.duracion_s), 0) / 60.0, 1)
    from partidas p where p.version is distinct from 'historico'
    group by 1 order by 1 desc limit 30;
end $$;

-- Uso de funciones: cuántas veces y cuántos jugadores distintos, por tipo de evento y botón.
create or replace function uso_admin(p_clave text)
returns table(tipo text, detalle text, veces bigint, jugadores bigint)
language plpgsql security definer set search_path = public as $$
begin
  if not es_admin(p_clave) then raise exception 'no autorizado'; end if;
  return query
    select e.tipo, e.dato->>'a', count(*), count(distinct e.id_cliente)
    from eventos e group by e.tipo, e.dato->>'a' order by 3 desc;
end $$;

-- Exportación completa para estudios (hasta 50 000 filas).
create or replace function exportar_partidas(p_clave text)
returns table(creada timestamptz, id_cliente uuid, apodo text, nivel text, gano boolean, tocados_dados smallint,
              tocados_recibidos smallint, dobles smallint, subitas smallint, duracion_s int, version text)
language plpgsql security definer set search_path = public as $$
begin
  if not es_admin(p_clave) then raise exception 'no autorizado'; end if;
  return query
    select p.creada, p.id_cliente, j.apodo, p.nivel, p.gano, p.tocados_dados, p.tocados_recibidos, p.dobles, p.subitas, p.duracion_s, p.version
    from partidas p join jugadores j on j.id_cliente = p.id_cliente
    order by p.creada desc limit 50000;
end $$;

create or replace function exportar_eventos(p_clave text)
returns table(creada timestamptz, id_cliente uuid, apodo text, tipo text, dato jsonb)
language plpgsql security definer set search_path = public as $$
begin
  if not es_admin(p_clave) then raise exception 'no autorizado'; end if;
  return query
    select e.creada, e.id_cliente, j.apodo, e.tipo, e.dato
    from eventos e join jugadores j on j.id_cliente = e.id_cliente
    order by e.creada desc limit 50000;
end $$;

grant execute on function latido(uuid) to anon;
grant execute on function registrar_eventos(uuid, jsonb) to anon;
grant execute on function resumen_admin(text) to anon;
grant execute on function niveles_admin(text) to anon;
grant execute on function ultimas_admin(text) to anon;
grant execute on function dias_admin(text) to anon;
grant execute on function uso_admin(text) to anon;
grant execute on function exportar_partidas(text) to anon;
grant execute on function exportar_eventos(text) to anon;
