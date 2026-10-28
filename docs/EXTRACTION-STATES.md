# Estados de extracción: 0.2.2

[Volver al inicio](../README.md)

La versión 0.2.1 respondía `pending` durante 24 horas después de solicitar
un episodio, aunque la extracción hubiera fallado. La versión 0.2.2 guarda
el resultado del intento y distingue estos estados en `/v1/provider/lookup`:

| Estado | Significado |
|---|---|
| `absent` | No existe caché ni intento registrado; una consulta sin permiso de encolar no inicia nada. |
| `queued` | Trabajo pendiente, incluido el tiempo de espera del navegador. |
| `processing` | El trabajador adquirió el navegador y está procesando el episodio. |
| `ready` | El SRT ya está en caché; tiene prioridad sobre cualquier estado anterior. |
| `failed` | El intento terminó sin guardar un SRT. Consulta los eventos para la causa. |
| `interrupted` | Había trabajo activo al detenerse el proceso. No se reanuda automáticamente. |
| `cooldown` | Intento antiguo sin resultado conocido, o caché retirada tras completar el trabajo. |
| `busy` | La cola está llena; no se registró un intento nuevo. |

Los resultados terminales incluyen `retry_after_seconds`. El intervalo sigue
siendo de 24 horas desde la solicitud original. Cuando llega a cero, **solo
una nueva solicitud con `enqueue=true`** puede reintentar. Las consultas de
estado y la carga del historial no crean trabajos. Un trabajo todavía activo
no se duplica aunque hayan pasado 24 horas.

El proveedor 0.2.2 termina su espera al recibir `failed`, `interrupted` o
`cooldown`, y no ofrece subtítulos incompletos. Sigue entendiendo `pending`
y las consultas `absent` de agentes anteriores. El proveedor 0.2.1 no entiende
todos los estados nuevos: actualizar primero el proveedor, después el agente.

## Persistencia y comprobaciones

`attempts.json` ahora guarda objetos con `at` y `state` por identificador.
El agente acepta las marcas de tiempo antiguas y las interpreta como
`cooldown`. Al arrancar, los trabajos registrados como activos se consideran
interrumpidos; la cola no se recupera automáticamente. No se persisten URLs,
cookies, tokens ni mensajes de excepción en los registros de intentos.
Las escrituras de estado se serializan para evitar colisiones entre solicitudes
y el trabajador. Los eventos de diagnóstico siguen siendo temporales.

47 pruebas offline pasaron localmente en Windows/Python 3.13, incluyendo
fallos de extracción, navegador ocupado, reinicio, lectura del formato antiguo,
reintento con permiso, deduplicación y finalización de espera. El navegador
se simula en estas pruebas: no se accede a Disney+ ni a la biblioteca.

## Actualización propuesta y reversión

El laboratorio se actualizó con autorización el 28 de octubre de 2026.
Para otras instalaciones, estos pasos requieren autorización antes
de detener, reiniciar o recrear servicios:

1. Mantener solicitudes nuevas y tareas automáticas desactivadas; comprobar
   que no haya extracción en curso.
2. Respaldar en almacenamiento privado el volumen de estado, configuración,
   bundle del proveedor y base de Bazarr+. Conservar la imagen anterior.
3. Construir el ZIP desde el commit publicado de 0.2.2. Instalarlo en Provider
   Hub conservando ID, token y mapa, y reiniciar únicamente Bazarr+ para activarlo.
4. Construir la imagen 0.2.2 y recrear únicamente el agente independiente,
   conservando volúmenes, usuario, redes y puertos. En el laboratorio usar su
   configuración de despliegue, no sustituirla con un Compose genérico.
5. Verificar API autenticada y salud; usar datos sintéticos para los estados
   y la caché. No repetir importaciones ni extracciones reales.

Para volver atrás, detener el agente nuevo y restaurar **su respaldo de estado
0.2.1** antes de iniciar la imagen anterior. El formato nuevo no es entendido
por 0.2.1: reutilizarlo sin restaurar perdería los intervalos de reintento.
El proveedor 0.2.2 puede permanecer con el agente anterior; también se puede
restaurar el bundle previo y reiniciar Bazarr+ si se necesita una reversión completa.
No eliminar volúmenes ni modificar la biblioteca para revertir.

## Resultado del despliegue autorizado

Código: `e954d94a3c44a6fe7d9ab0c486dbe2bbce4b3bc8`. Proveedor 0.2.2 activo,
sin reinicio pendiente; prueba del worker aprobada. Agente 0.2.2 `healthy`,
con conexión privada autenticada desde Bazarr+ y rechazo HTTP 401 sin token.

Imagen: `sha256:fcd78e041cfad4605a6d3c43c742e0cb36940e9119bb04ec7a3be07cde21cce2`.
ZIP: `sha256:0e81ab762b9a9db92e415cf12674df6d7aef427a0b8af62b8035e58437dde90b`.

Se respaldaron configuración, base SQLite, bundle, estado y credenciales en
almacenamiento privado. Se conservaron imagen y carpeta de despliegue 0.2.1.
Un problema inicial de acceso a la carpeta privada se resolvió ejecutando el
respaldo con UID 999:1000 de Bazarr+, sin ampliar permisos.

Los estados `failed` e `interrupted`, su persistencia y la lectura de un SRT
sintético se probaron en un proceso separado dentro de la imagen nueva, con
estado temporal en `/tmp`. Esos datos se eliminaron al terminar; no entraron
en la cola del servicio ni en la biblioteca. No se abrió Disney+.

Los 17 SRT de caché conservan sus hashes. El historial de importación, mapa,
volúmenes, puertos y redes se conservaron. Los otros 30 contenedores registrados
conservaron ID, estado y tiempo de arranque. Solicitudes nuevas, tareas
programadas y sincronización siguen desactivadas. La reversión está preparada,
pero no se ha ejecutado.
