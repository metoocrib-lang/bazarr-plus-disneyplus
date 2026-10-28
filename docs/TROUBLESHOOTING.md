# Solución de problemas

[Volver al inicio](../README.md) · [Configuración](CONFIGURATION.md)

Empieza por estas comprobaciones en el host Docker, desde este repositorio:

```shell
docker compose ps
docker compose exec disney-agent python -m extractor.manage status
```

El estado de salud comprueba la API. No confirma que la sesión Disney+ siga
vigente ni que una serie tenga subtítulos disponibles.

## Problemas habituales

| Síntoma | Qué revisar |
|---|---|
| El agente no arranca | `.env` debe existir, el token debe tener al menos 32 caracteres y la contraseña VNC al menos 12. Comprueba que el puerto esté libre con las herramientas de tu host. |
| Aparece un error de permisos | El contenedor probado usa UID/GID 1001:1001. Al migrar, adapta la **copia** de los datos al usuario real de la nueva imagen. No cambies toda la biblioteca. |
| Bazarr+ no llega al agente | Ambos deben compartir su red privada. Usa el nombre real del contenedor y el puerto 8787; no `localhost` ni el puerto de noVNC. |
| La API responde 401 | `bridge_token` debe coincidir exactamente con `BRIDGE_API_TOKEN` del agente. No pegues la contraseña VNC en ese campo. |
| La prueba de conexión pasa, pero no hay resultados | Comprueba el idioma español normal, TVDB, URL de serie, mapa y modo de caché. La conexión no valida estos datos ni la sesión Disney+. |
| La caché está vacía y no pasa nada | Con `enable_requests=false` es normal. Para una extracción manual debes activarlo conscientemente. |
| La búsqueda termina antes que la extracción | Si el agente sigue trabajando, repite la búsqueda después. Aumentar `wait_seconds` por encima de 90 no está permitido. |
| No aparece noVNC | Abre el túnel SSH desde tu equipo y mantenlo abierto; revisa los puertos local/remoto. Visita `/vnc.html`. NoVNC no está publicado en la IP de red del NAS. |
| noVNC muestra escritorio sin Disney+ | Ejecuta `python -m extractor.manage login` mediante `docker compose exec disney-agent`. |
| «El navegador está ocupado» | La autenticación dispone de una ventana de cuatro minutos. Espera a que cierre; una extracción también puede estar usando el navegador. |
| No se encuentra el episodio | Verifica la temporada seleccionada, títulos y equivalencias. El extractor rechaza tarjetas ambiguas; no adivina por posición. |
| Aparece un destino `.es.hi.srt` inesperado | Revisa la [corrección HI del host](HI-COMPATIBILITY.md) antes de repetir una importación. |

## Por qué puede quedarse en «pendiente»

La versión 0.2.1 recuerda cada solicitud durante 24 horas para evitar
repeticiones. Esto también ocurre si falló la extracción. Por ello, una
respuesta `pending` no prueba que el episodio siga procesándose.

Consulta `events` en la salida de `status`. Puede indicar
`sin_subtitulo_accesible_o_sesion`, `episodio_no_identificado` o
`pista_cifrada_no_admitida`. El campo `queue` cuenta los trabajos que esperan,
no necesariamente el que ya está procesando el navegador. Reiniciar el
contenedor no elimina el intervalo de espera porque se guarda en el volumen.
No borres el estado o el perfil para forzar reintentos: podrías perder información
útil. Una gestión más clara de fallos y reintentos está [pendiente](ROADMAP.md).

## Qué significa el estado de la sesión

| Estado | Significado |
|---|---|
| `no_validada` | El proceso no ha confirmado una sesión. También puede aparecer después de reiniciar aunque exista un perfil guardado. |
| `abriendo_navegador` | Está arrancando el navegador de autenticación. |
| `autenticacion_en_navegador` | La ventana de autenticación está abierta. |
| `perfil_guardado_sin_verificar` | Se cerró la ventana y se conservó el perfil; no confirma acceso al catálogo. |
| `error_de_navegador` | Falló la apertura o ejecución del navegador. |

## Qué compartir al reportar un problema

Indica la versión del proveedor, sistema/arquitectura, paso que falla y el
mensaje de error. Puedes incluir `docker compose ps` y el estado del agente
después de revisar identificadores de series/episodios que no quieras compartir.
Nunca adjuntes `.env`, cookies, perfiles de navegador, tokens ni respaldos de
la base de datos. Tampoco publiques la salida completa de `docker inspect`
o `docker compose config`: puede contener credenciales.
