# Checklist para armar el cluster G1 con mi nodo cassandra2

## Listo hoy

- Rama local: `entrega-20240060-victor-saravia`. No hay commits ni push.
- Parte 1 conservada: `cassandra1` esta `UN`; `ventas.ventas_por_ciudad` tiene 75000 filas de `ventas_G1.csv`. El `compose.yml` de la raiz sigue siendo el original de la Parte 1.
- Traza completa del Paso 4: `notas/traza-paso4.txt`. Ciudad: linea `Executing single-partition query`, 11 filas leidas. Producto: `Submitting range requests` y `Executing seq scan` repetidos, 75000 filas leidas; 4911 coincidieron con `Miel`.
- Docker Compose v2 y Docker Desktop operativos, con 7.7 GB de RAM. Imagen `cassandra:5.0.8` descargada.
- Compose de la Parte 2 preparado en `entregas/G1/20240060-victor-saravia/compose.yml` con un solo servicio `cassandra2`. Broadcast Tailscale propio: `100.88.43.68`; semilla Tailscale de Juan: `100.71.193.83`. Todavia no arrancar: `tailscale ping 100.71.193.83` devolvio `no matching peer`, asi que falta compartir una tailnet. `docker compose --project-directory . -f entregas/G1/20240060-victor-saravia/compose.yml config` valida su sintaxis y el montaje de `data/` desde la raiz.
- El hotspot del iPhone queda descartado para este intento. Esta Mac ya tiene Tailscale activo con IP `100.88.43.68`; su red Docker actual es `172.19.0.0/16`, sin choque con el rango Tailscale. Confirmar las IP con `tailscale ip -4` en cada laptop antes de arrancar.
- Firewall de macOS apagado. Si esta encendido manana, permitir conexiones entrantes para Docker Desktop/Cassandra en TCP 7000 (entre nodos) y 9042 (CQL), y verificar cualquier firewall adicional.
- Puerto 7000 ocupado ahora por `ControlCenter` (Receptor de AirPlay). Apagarlo en Ajustes del Sistema -> General -> AirDrop y Handoff -> Receptor de AirPlay; repetir `lsof -nP -iTCP:7000 -sTCP:LISTEN` hasta que no muestre ningun proceso.
- Puerto 9042 ocupado ahora por la Parte 1; quedara libre al ejecutar `docker compose down -v` manana.

## Pedir y acordar con el grupo

- A Juan: aceptar/invitar a Victor y cassandra3 a la misma tailnet, confirmar que su IP Tailscale sigue siendo `100.71.193.83` y que `cassandra1` ya esta `UN` antes de arrancar mi nodo. Su IP va en `CASSANDRA_SEEDS`, nunca la mia.
- Al integrante de `cassandra3`: su IP Tailscale para la lectura de E6b y acuerdo sobre los momentos de apagar y encender su nodo.
- Los tres: unirse a la misma tailnet de Tailscale, confirmar que `tailscale status` muestra a los otros nodos y que `tailscale ping <IP-TAILSCALE>` funciona en ambos sentidos; despues comprobar TCP 7000 y 9042. Usar `UFM-G1`, `dc-g1`, `rack1` y el snitch `GossipingPropertyFileSnitch`.
- Juan crea el keyspace y la tabla y carga `ventas_G1.csv` una sola vez. Yo no creo el keyspace ni cargo el CSV en la Parte 2.
- Coordinar turnos de las pruebas: para mi fila, en 8.1 y 9 se apaga `cassandra3`; en 8.2 se apagan `cassandra1` y `cassandra3`. Mi `cassandra2` siempre sigue encendido.
- Fork creado en `VictorSaraviaUFM/Big-Data-Workshops-Cassandra`; `origin` apunta a mi fork y `upstream` al repo del curso. No se ha hecho push.

## Orden de manana

Trabajar desde la raiz del clon de Cassandra. Los comandos `docker compose stop/start` de otro nodo se ejecutan en la laptop de su duenio. Una captura debe mostrar el comando y su salida completa.

1. **Antes de todo, borrar Parte 1 con el compose original:**
   ```bash
   docker compose down -v
   ```
   Esto elimina el volumen con `Test Cluster` y evita `Saved cluster name Test Cluster != configured name UFM-G1`. Confirmar que `lsof -nP -iTCP:9042 -sTCP:LISTEN` ya no muestra Docker. No correr `down -v` con el compose nuevo antes de limpiar el volumen viejo.

2. **Verificar Tailscale y activar mi compose de cassandra2.** Antes de arrancar, ejecutar `tailscale status`, `tailscale ip -4` y `tailscale ping 100.71.193.83`. Juan debe aparecer como par y responder; si cualquiera de las IP Tailscale cambio, actualizar `CASSANDRA_BROADCAST_ADDRESS` o `CASSANDRA_SEEDS` en el compose de mi entrega. Apagar Receptor de AirPlay y comprobar que el 7000 esta libre. Luego, desde la raiz:
   ```bash
   cp entregas/G1/20240060-victor-saravia/compose.yml compose.yml
   docker compose config
   ```
   El `compose.yml` de la raiz queda modificado solo para correr mi nodo; la copia de mi entrega es el archivo que se sube. No arrancar mientras `tailscale ping` diga `no matching peer` ni si las laptops no se alcanzan en ambas direcciones. Actualizar primero el compose de mi entrega y despues copiarlo a la raiz.

3. **Paso 5, arranque secuencial y E1.** Juan arranca `cassandra1` y confirma `UN`; solo entonces yo ejecuto:
   ```bash
   docker compose up -d
   docker exec cassandra2 nodetool status
   docker exec cassandra2 nodetool describecluster
   ```
   Esperar a que `cassandra2` aparezca `UN`; despues arranca `cassandra3`. Repetir los dos comandos hasta ver tres `UN`, `Datacenter: dc-g1` y `Name: UFM-G1`. Tomar `capturas/E1-cluster.png` con ambas salidas.

4. **Paso 6, tres copias y E2.** Juan crea `ventas` con `NetworkTopologyStrategy` y 3 copias en `dc-g1`, crea la tabla y carga el CSV G1 una sola vez. Yo verifico desde `cassandra2`:
   ```bash
   docker exec cassandra2 nodetool getendpoints ventas ventas_por_ciudad Quetzaltenango
   docker exec cassandra2 cqlsh -e "DESCRIBE KEYSPACE ventas;"
   bash scripts/check.sh cluster > entregas/G1/20240060-victor-saravia/check.txt
   ```
   Tomar `capturas/E2-copias.png` con los dos primeros comandos y sus salidas: tres direcciones y RF=3 en `dc-g1`. Guardar `check.txt` solo si el cluster esta completo y la comprobacion sale en verde.

5. **Paso 7, CQL y E3.** Abrir `docker exec -it cassandra2 cqlsh`. Usar `20240060` como `id_venta`, en fechas de enero de 2025. Ejecutar dos `INSERT` con la misma llave primaria y distintos valores, un `SELECT` que muestre una sola fila, un `INSERT ... USING TTL 60` con otra fecha y `SELECT` antes y despues de expirar, y un `INSERT ... IF NOT EXISTS` sobre la primera llave que muestre `[applied] False`. Comandos CQL preparados para la investigacion del Paso 7:
   ```sql
   INSERT INTO ventas.ventas_por_ciudad (ciudad, fecha, id_venta, producto, cantidad)
   VALUES ('Quetzaltenango', '2025-01-01', 20240060, 'Cafe', 1);
   INSERT INTO ventas.ventas_por_ciudad (ciudad, fecha, id_venta, producto, cantidad)
   VALUES ('Quetzaltenango', '2025-01-01', 20240060, 'Miel', 2);
   SELECT fecha, id_venta, producto, cantidad FROM ventas.ventas_por_ciudad
   WHERE ciudad = 'Quetzaltenango' AND fecha = '2025-01-01' AND id_venta = 20240060;

   INSERT INTO ventas.ventas_por_ciudad (ciudad, fecha, id_venta, producto, cantidad)
   VALUES ('Quetzaltenango', '2025-01-02', 20240060, 'Cafe', 1) USING TTL 60;
   SELECT fecha, id_venta, producto, TTL(producto) FROM ventas.ventas_por_ciudad
   WHERE ciudad = 'Quetzaltenango' AND fecha = '2025-01-02' AND id_venta = 20240060;
   -- Repetir el SELECT despues de 60 segundos; debe devolver 0 rows.

   INSERT INTO ventas.ventas_por_ciudad (ciudad, fecha, id_venta, producto, cantidad)
   VALUES ('Quetzaltenango', '2025-01-01', 20240060, 'Chocolate', 3) IF NOT EXISTS;
   ```
   Tomar `capturas/E3-cql.png` con comandos y resultados: una fila tras el upsert, TTL antes y despues, y `[applied] False`. La guia deja la sintaxis de este paso como investigacion; comprobar estas sentencias en el cluster manana.

6. **Paso 8.1, un nodo caido y E4.** El duenio de `cassandra3` ejecuta `docker compose stop cassandra3`. En mi laptop:
   ```bash
   docker exec cassandra2 nodetool status
   docker exec -it cassandra2 cqlsh
   ```
   En `cqlsh`:
   ```sql
   CONSISTENCY QUORUM;
   SELECT count(*) FROM ventas.ventas_por_ciudad WHERE ciudad = 'Quetzaltenango' AND fecha = '2024-08-01';
   CONSISTENCY ALL;
   SELECT count(*) FROM ventas.ventas_por_ciudad WHERE ciudad = 'Quetzaltenango' AND fecha = '2024-08-01';
   ```
   Tomar `capturas/E4-un-nodo-caido.png`: `cassandra3` en `DN`, `QUORUM` responde, `ALL` se rechaza. Salir de `cqlsh`. El duenio vuelve a ejecutar `docker compose start cassandra3` y esperar tres `UN`.

7. **Paso 8.2, dos nodos caidos y E5.** Los duenios de `cassandra1` y `cassandra3` ejecutan `docker compose stop cassandra1` y `docker compose stop cassandra3` en sus propias laptops. En la mia:
   ```bash
   docker exec cassandra2 nodetool status
   docker exec -it cassandra2 cqlsh
   ```
   En `cqlsh`:
   ```sql
   CONSISTENCY ONE;
   SELECT count(*) FROM ventas.ventas_por_ciudad WHERE ciudad = 'Quetzaltenango' AND fecha = '2024-08-01';
   CONSISTENCY QUORUM;
   SELECT count(*) FROM ventas.ventas_por_ciudad WHERE ciudad = 'Quetzaltenango' AND fecha = '2024-08-01';
   ```
   Tomar `capturas/E5-dos-nodos-caidos.png`: dos `DN`, `ONE` responde, `QUORUM` se rechaza. Salir de `cqlsh`; los duenios vuelven a arrancar ambos nodos y se espera tres `UN`.

8. **Paso 8.3.** Repetir esa lectura con `ONE`, `QUORUM` y `ALL` para 0, 1 y 2 nodos caidos; llenar las nueve celdas de la tabla de la bitacora con los resultados reales. No apagar mi nodo.

9. **Paso 9, hint y E6a.** Con tres `UN`, el duenio de `cassandra3` ejecuta `docker compose stop cassandra3`; esperar a verlo `DN`. Yo escribo con mi carné:
   ```bash
   docker exec cassandra2 cqlsh -e "CONSISTENCY QUORUM; INSERT INTO ventas.ventas_por_ciudad (ciudad, fecha, id_venta, pais, producto, cantidad, precio_unitario, canal) VALUES ('Quetzaltenango', '2025-12-31', 20240060, 'Guatemala', 'Cafe', 3, 95.00, 'web');"
   docker exec cassandra2 ls /var/lib/cassandra/hints
   docker exec cassandra2 nodetool status
   ```
   Esperar unos 10 segundos si aun no aparece el archivo `.hints`. Tomar `capturas/E6a-hint.png` cuando el nombre del archivo incluya el Host ID de la fila `DN` de `cassandra3`.

10. **Paso 9, entrega del hint y E6b.** El duenio de `cassandra3` ejecuta `docker compose start cassandra3`. Cuando vuelva a `UN`, yo ejecuto:
    ```bash
    docker logs cassandra2 2>&1 | grep "Finished hinted handoff"
    docker exec cassandra2 cqlsh <IP-DE-CASSANDRA3> -e "CONSISTENCY ONE; SELECT id_venta, producto, cantidad FROM ventas.ventas_por_ciudad WHERE ciudad = 'Quetzaltenango' AND fecha = '2025-12-31';"
    ```
    Sustituir `<IP-DE-CASSANDRA3>` por la IP acordada. Tomar `capturas/E6b-handoff.png` con la linea de handoff y la venta `20240060` leida desde el nodo que volvio.

11. **Cierre y entrega.** Completar mini-reto y bitacora con mis propias respuestas, capturas y datos. Validar con:
    ```bash
    python3 scripts/validar_entrega.py entregas/G1/20240060-victor-saravia
    ```
    Si luego decido subir, hacer `git add entregas/G1/20240060-victor-saravia` solamente, nunca `git add -A`. No agregar el `compose.yml` de la raiz. No hacer commit ni push hasta que yo lo indique. El Paso 10 (`docker compose down -v`) es despues de terminar la bitacora, el mini-reto y la presentacion.

## Si falla al unir las laptops

- `Saved cluster name Test Cluster != configured name UFM-G1`: volumen viejo de la Parte 1. La guia indica `docker compose down -v`; hacerlo antes de activar el compose nuevo.
- `Bootstrap Token collision`: arrancaron nodos a la vez. Esperar a que Juan confirme `cassandra1 UN` y arrancar uno por uno.
- `port is already allocated` en 7000: comprobar `lsof -nP -iTCP:7000 -sTCP:LISTEN` y apagar Receptor de AirPlay. En 9042, confirmar que la Parte 1 ya bajo.
- Mi nodo se detiene: `docker compose logs cassandra2`; revisar la ultima linea `ERROR` y la seccion `Si falla` del Paso 5.
- No se ven tres `UN`: verificar que las tres laptops esten en la misma tailnet, que `tailscale ping` funcione en ambos sentidos, las IP Tailscale actuales en `CASSANDRA_SEEDS` y `CASSANDRA_BROADCAST_ADDRESS`, y alcance por TCP 7000. Si se activo el firewall, permitir Docker Desktop/Cassandra.
- `no matching peer` en `tailscale ping`: la otra maquina aun no esta visible en esta tailnet; resolver invitacion o acceso mutuo antes de iniciar Cassandra.
- `ConfigurationException: Unrecognized strategy option {dc1}`: el datacenter del keyspace no coincide con `dc-g1`; revisar el Paso 6 con Juan.
- E6a sin `.hints`: esperar al menos 10 segundos; si sigue vacio, confirmar que `cassandra3` estaba `DN` antes del `INSERT`.
- E6b sin linea `Finished hinted handoff`: esperar a que `cassandra3` este `UN` y repetir el comando de logs.
