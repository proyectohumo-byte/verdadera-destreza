-- Actualización 1 del ranking global: quién está conectado, tiempo abierto, opiniones y funciones del panel.
-- Se puede ejecutar más de una vez. ANTES de ejecutar: cambia CAMBIA_ESTA_CLAVE (en la línea del insert) por una
-- contraseña tuya. No subir al repositorio la versión con la contraseña real.

alter table jugadores add column if not exists segundos int not null default 0;

create table if not exists opiniones (
  id bigint generated always as identity primary key,
  creada timestamptz not null default now(),
  id_cliente uuid not null references jugadores(id_cliente),
  estrellas smallint not null check (estrellas between 1 and 5),
  texto text check (char_length(texto) <= 500)
);
create table if not exists ajustes_admin (clave text not null);
alter table opiniones enable row level security;
alter table ajustes_admin enable row level security;
revoke all on opiniones, ajustes_admin from anon, authenticated;

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

create or replace function registrar_opinion(p_cliente uuid, p_estrellas int, p_texto text) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not exists (select 1 from jugadores where id_cliente = p_cliente) then raise exception 'jugador desconocido'; end if;
  if exists (select 1 from opiniones where id_cliente = p_cliente and creada > now() - interval '30 seconds') then
    raise exception 'demasiado rápido';
  end if;
  insert into opiniones(id_cliente, estrellas, texto)
  values (p_cliente, p_estrellas, nullif(left(btrim(coalesce(p_texto, '')), 500), ''));
end $$;

-- Funciones del panel del autor (panel.html), protegidas con la contraseña.
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

create or replace function opiniones_admin(p_clave text)
returns table(creada timestamptz, apodo text, estrellas smallint, texto text)
language plpgsql security definer set search_path = public as $$
begin
  if not es_admin(p_clave) then raise exception 'no autorizado'; end if;
  return query
    select o.creada, j.apodo, o.estrellas, o.texto
    from opiniones o join jugadores j on j.id_cliente = o.id_cliente
    order by o.creada desc limit 100;
end $$;

grant execute on function latido(uuid) to anon;
grant execute on function registrar_opinion(uuid, int, text) to anon;
grant execute on function resumen_admin(text) to anon;
grant execute on function niveles_admin(text) to anon;
grant execute on function ultimas_admin(text) to anon;
grant execute on function dias_admin(text) to anon;
grant execute on function opiniones_admin(text) to anon;
