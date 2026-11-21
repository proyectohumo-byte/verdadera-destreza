-- Funciones del panel del autor (panel.html). Sustituir CAMBIA_ESTA_CLAVE por una contraseña propia ANTES de ejecutar.
-- No subir al repositorio la versión con la contraseña real.
create or replace function resumen_admin(p_clave text)
returns table(apodo text, primera_vez timestamptz, ultima_vez timestamptz, visitas int,
              n_partidas bigint, n_ganadas bigint, minutos numeric)
language plpgsql security definer set search_path = public as $$
begin
  if p_clave is distinct from 'CAMBIA_ESTA_CLAVE' then perform pg_sleep(1); raise exception 'no autorizado'; end if;
  return query
    select j.apodo, j.primera_vez, j.ultima_vez, j.visitas, count(p.id), count(p.id) filter (where p.gano),
           round(coalesce(sum(p.duracion_s), 0) / 60.0, 1)
    from jugadores j left join partidas p on p.id_cliente = j.id_cliente
    group by j.id_cliente order by j.ultima_vez desc;
end $$;

create or replace function ultimas_admin(p_clave text)
returns table(creada timestamptz, apodo text, nivel text, gano boolean,
              tocados_dados smallint, tocados_recibidos smallint, duracion_s int)
language plpgsql security definer set search_path = public as $$
begin
  if p_clave is distinct from 'CAMBIA_ESTA_CLAVE' then perform pg_sleep(1); raise exception 'no autorizado'; end if;
  return query
    select p.creada, j.apodo, p.nivel, p.gano, p.tocados_dados, p.tocados_recibidos, p.duracion_s
    from partidas p join jugadores j on j.id_cliente = p.id_cliente
    order by p.creada desc limit 50;
end $$;

grant execute on function resumen_admin(text) to anon;
grant execute on function ultimas_admin(text) to anon;
