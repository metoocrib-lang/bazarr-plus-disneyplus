# Instalación independiente

Este Compose crea únicamente el agente. No instala, detiene ni reemplaza
Bazarr+, Bazarr oficial, Sonarr o Jellyfin. Comprueba previamente puertos,
capacidad disponible y compatibilidad HI; no ejecutes una segunda instalación
sobre los volúmenes del laboratorio existente.

## 1. Configuración privada

Copia `.env.example` a `.env` y genera localmente un token aleatorio de al
menos 32 caracteres y una contraseña VNC de al menos 12. No los publiques.
Por ejemplo, `python -c "import secrets; print(secrets.token_urlsafe(48))"`
genera un valor en tu terminal privada. Usa valores diferentes.

`NOVNC_PORT` usa 6082 por defecto: comprueba que esté libre. La API 8787 no se
publica en el host y noVNC se enlaza únicamente a 127.0.0.1.

```shell
docker compose config --quiet
docker compose up -d --build
```

El agente usa los volúmenes propios `browser` y `state`, usuario no-root,
raíz de solo lectura y red de salida separada de su red privada.
El arranque se validó en un entorno aislado; véase [Verificación](VERIFICATION.md).
Antes de migrar una instalación existente, comprobar permisos y datos según
la guía de migración. La sesión y la extracción real no se validaron en este
contenedor nuevo.

## 2. Conexión de Bazarr+

Conecta solamente el contenedor de Bazarr+ a `bazarrplus-disneyplus-private`.
Para una conexión persistente, declara esa red externa en su propio Compose;
respalda antes dicho archivo. Una conexión manual inicial puede hacerse con:

```shell
docker network connect bazarrplus-disneyplus-private NOMBRE_CONTENEDOR_BAZARRPLUS
```

No es necesario conectar Jellyfin. El proveedor debe alcanzar
`http://disney-agent:8787` desde el contenedor de Bazarr+.

## 3. Inicio de sesión Disney+

Abre un túnel desde tu equipo hacia el host Docker:

```shell
ssh -L 6082:127.0.0.1:6082 USUARIO@HOST
docker compose exec disney-agent python -m extractor.manage login
```

El segundo comando se ejecuta en el host Docker desde este repositorio.
Visita `http://127.0.0.1:6082/vnc.html`, introduce la contraseña VNC e inicia
sesión directamente en Disney+. Selecciona tu perfil. La ventana se cierra
después de cuatro minutos para liberar el navegador al extractor. No se
solicitan credenciales Disney+ mediante el proveedor ni el chat.

```shell
docker compose exec disney-agent python -m extractor.manage status
```

Un perfil guardado no garantiza que la sesión siga vigente. Para renovarla,
repite el inicio de sesión cuando el navegador no esté ocupado.

## 4. Proveedor en Provider Hub

Genera el ZIP desde un commit publicado y cárgalo mediante la instalación
local de Provider Hub. Reinicia únicamente Bazarr+ si solicita activación.
Configura:

- `agent_url`: `http://disney-agent:8787`.
- `bridge_token`: el mismo token privado de `.env`.
- `series_json`: mapa de series TVDB y coordenadas Disney+.
- `enable_requests`: inicialmente `false`.
- `wait_seconds`: 75; máximo 90. El worker necesita un timeout de al menos 120s.

Ejemplo de mapa (sustituye ID, URL y equivalencias por datos comprobados):

```json
[{"tvdb_id":123456,"series_url":"https://www.disneyplus.com/series/example/abc123","mapping":"17x1-13=1x1\n17x14-26=2x1"}]
```

La primera búsqueda no extraerá nada con `enable_requests=false`. Para una
prueba real, habilítalo conscientemente, conserva las búsquedas programadas
apagadas y selecciona un episodio sin español. Desactívalo al terminar si
quieres volver al modo de solo caché. La sincronización es opcional según el
archivo de vídeo; no se activa como parte de esta instalación.

## Respaldo y reversión

Antes de una actualización, respalda la configuración y base de Bazarr+
usando sus mecanismos coherentes, el ZIP anterior y los volúmenes del agente
con el agente detenido. Los respaldos contienen sesión y token: consérvalos
privados. Guarda la revisión anterior del Compose y de la imagen.

Para retirar esta instalación, detén solo este proyecto con `docker compose
down`, sin `--volumes`; deshabilita su proveedor en Bazarr+. Los subtítulos ya
importados no se eliminan. No restaures una base antigua sobre importaciones
posteriores sin revisar las consecuencias. No se ha ensayado una migración
del despliegue existente en esta separación.
