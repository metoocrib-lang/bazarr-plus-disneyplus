# Instalación paso a paso

Al terminar tendrás un agente Docker y un proveedor instalado en Bazarr+.
Esta guía es para una instalación nueva. Si ya usas el agente anterior,
empieza por [Migración](MIGRATION.md).

## Antes de empezar

- Bazarr+ debe tener Provider Hub y reconocer tus series.
- Necesitas Docker con Compose v2 en Linux, Git y Python 3 para empaquetar.
  El entorno probado utiliza Linux x86_64 y Python 3.13.
- Necesitas acceso a Disney+ con tu cuenta y al episodio que quieras consultar.
- Revisa [la compatibilidad HI](HI-COMPATIBILITY.md) antes de importar archivos.

**Dónde ejecutar las órdenes:** salvo indicación contraria, en el host Docker,
dentro de la carpeta del repositorio. Desde Windows puedes conectarte por SSH.
El Compose instala únicamente el agente; no instala ni reemplaza Bazarr+.

```shell
git clone https://github.com/metoocrib-lang/bazarr-plus-disneyplus.git
cd bazarr-plus-disneyplus
```

## 1. Crear las credenciales locales

En el host Linux:

```shell
cp .env.example .env
chmod 600 .env
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
python3 -c "import secrets; print(secrets.token_urlsafe(18))"
```

Abre `.env` en un editor local y configura:

| Campo | Valor |
|---|---|
| `BRIDGE_API_TOKEN` | Primer valor generado; mínimo 32 caracteres. Autentica al proveedor ante el agente. |
| `VNC_PASSWORD` | Segundo valor; mínimo 12 caracteres según la comprobación del agente. Abre el escritorio noVNC. |
| `NOVNC_PORT` | `6082`, o un puerto local libre que elijas. |

Usa valores diferentes; no son tu contraseña Disney+. Conserva `.env` privado:
está excluido de Git y del contexto de construcción Docker.

## 2. Arrancar el agente

```shell
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose exec disney-agent python -m extractor.manage status
```

Espera a que aparezca `healthy`. La última orden devuelve JSON con el estado y
la cola. `no_validada` es normal antes de iniciar sesión. `healthy` confirma
que la API responde, no que Disney+ acepte tu sesión.

El Compose crea dos volúmenes propios: navegador y estado/caché. No monta tu
biblioteca. Publica noVNC únicamente en `127.0.0.1:6082`; la API 8787 permanece
dentro de Docker.

## 3. Conectar Bazarr+ a la red privada

Identifica el nombre de tu contenedor Bazarr+ con `docker ps` y sustituye
el marcador de esta orden:

```shell
docker network connect bazarrplus-disneyplus-private NOMBRE_CONTENEDOR_BAZARRPLUS
```

Si ya está conectado, no repitas la orden. Para conservar la conexión al
recrear Bazarr+, integra este fragmento en **su** Compose, adaptando el nombre
del servicio y conservando también sus redes actuales. Respalda ese archivo:

```yaml
services:
  bazarrplus:
    networks:
      disneyplus_private: {}
networks:
  disneyplus_private:
    external: true
    name: bazarrplus-disneyplus-private
```

El agente del Compose incluido se alcanza mediante:

```text
http://bazarrplus-disneyplus-disney-agent-1:8787
```

Si cambiaste el nombre del proyecto Compose, consulta el nombre real con
`docker compose ps` y adapta la URL. El nombre completo evita confundirlo
con otro servicio `disney-agent`. No uses `localhost`: desde Bazarr+
apuntaría a su propio contenedor. No necesitas conectar Jellyfin.

## 4. Iniciar sesión en Disney+

**En tu equipo personal**, abre un túnel y deja esa terminal abierta:

```shell
ssh -N -L 6082:127.0.0.1:6082 USUARIO@HOST
```

Sustituye `USUARIO@HOST` por tu conexión SSH. Si elegiste otro puerto remoto
en `.env`, cambia el último `6082`; el primero es el puerto en tu equipo.

**En otra terminal del host Docker**, desde este repositorio:

```shell
docker compose exec disney-agent python -m extractor.manage login
```

**En el navegador de tu equipo**, abre
[el escritorio noVNC](http://127.0.0.1:6082/vnc.html), introduce `VNC_PASSWORD`,
inicia sesión directamente en Disney+ y selecciona tu perfil.

La ventana de autenticación dura cuatro minutos. Después se cierra para
liberar el navegador al extractor. Espera a que termine antes de solicitar
una extracción. Si necesitas más tiempo, repite `login` cuando el navegador
quede libre. Un perfil guardado no garantiza que la sesión siga vigente.

## 5. Generar e instalar el proveedor

Si existe una ejecución satisfactoria en **Actions**, puedes obtener el ZIP
desde sus artefactos siguiendo [estas instrucciones](DEVELOPMENT.md).
También puedes reproducir el paquete comprobado con los comandos siguientes.

En el equipo donde tengas el repositorio, Git y Python, genera el ZIP del
código 0.2.1 comprobado. No necesitas instalar Playwright en ese equipo:

```shell
python3 scripts/build_bazarr_plus_bundle.py --commit e5270e8c69345e53bbd141fa0029806aa3941f82 --output dist/disneyplus-0.2.1.zip
```

En Windows usa `python` en lugar de `python3`. El generador no sobrescribe
archivos. El SHA-256 esperado del ZIP es:

```text
1b267bbc413294a495c6d7c6d674eec6c306dbd1f01fac745024809827cd4bc7
```

Si lo generaste en el NAS, transfiere **solo ese ZIP** a tu equipo. En
**Provider Hub**, usa la opción de instalación local y selecciónalo. Reinicia
únicamente Bazarr+ si solicita activación. No comprimas todo el repositorio.

## 6. Configurar y hacer una búsqueda manual

Abre la configuración de **Disney+ (independent agent)**:

| Opción | Valor inicial |
|---|---|
| `agent_url` | La URL privada del paso 3. |
| `bridge_token` | El mismo `BRIDGE_API_TOKEN` de `.env`. |
| `series_json` | Tu mapa de series; consulta [ejemplos explicados](CONFIGURATION.md). |
| `enable_requests` | `false`: solo consulta los SRT ya almacenados. |
| `wait_seconds` | `75`. El worker debe permitir al menos 120 segundos. |

Habilita el proveedor y comprueba su conexión. Esto no valida la sesión
Disney+ ni garantiza un subtítulo para un episodio. Con una caché vacía y
`enable_requests=false`, es normal que no haya resultados.

Para la primera extracción, mantén las tareas programadas de Bazarr+ apagadas,
selecciona un episodio sin español y activa `enable_requests`. Haz una búsqueda
manual. El resultado aparecerá cuando el SRT esté listo; si se supera la
espera, vuelve a buscar más tarde. Si falla, consulta [Solución de problemas](TROUBLESHOOTING.md)
antes de insistir: un intento puede quedar sujeto a una espera de 24 horas.

Solo importa a la biblioteca después de resolver la compatibilidad HI y
confirmar la correspondencia del episodio. Para volver al modo de caché,
desactiva `enable_requests`. La sincronización no se activa durante la instalación.

## Detener, respaldar o retirar

Para detener solo este agente:

```shell
docker compose stop disney-agent
```

Para volver a arrancarlo: `docker compose start disney-agent`.
Respalda `.env`, ambos volúmenes y la revisión del código con el agente
detenido. Antes de actualizar el proveedor, respalda también la configuración
y base de Bazarr+ mediante un procedimiento coherente y conserva el ZIP anterior.

`docker compose down` retira este proyecto y conserva los volúmenes si no
añades `--volumes`. Si Bazarr+ sigue conectado a su red, Docker puede conservar
esa red mientras tenga ese extremo activo. Deshabilita el proveedor si retiras
el agente. Los SRT ya importados no se eliminan.

La migración del laboratorio y su reversión están en [Migración](MIGRATION.md).
No restaures una base antigua sobre cambios nuevos sin revisar sus consecuencias.
