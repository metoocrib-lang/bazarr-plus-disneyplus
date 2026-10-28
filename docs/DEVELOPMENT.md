# Desarrollo y empaquetado

[Volver al inicio](../README.md)

## Estructura

| Ruta | Contenido |
|---|---|
| `provider/` | Adaptador y manifiesto del Provider Hub. Es lo que instala Bazarr+. |
| `extractor/` | API, navegador Disney+, correspondencia de episodios y caché del agente. |
| `extractor/tests/` | Pruebas offline con datos sintéticos. |
| `scripts/build_bazarr_plus_bundle.py` | Generador del ZIP reproducible. |
| `Dockerfile`, `compose.yml` | Imagen y despliegue del agente. |
| `patches/` | Propuesta de corrección para el guardado HI en Bazarr+. |
| `docs/` | Guías y resultados de verificación. |

El código se separó de `Jellyfin.Plugin.SubtitleBridge`, revisión local de
origen `d6c181241aa51feaa630882c592160a43b4d21e5`. No se trasladaron credenciales
ni perfiles. La API antigua de carga directa a Bazarr se eliminó.

## Ejecutar las pruebas

Desde la raíz del repositorio:

```shell
python -m unittest discover -s extractor/tests
```

Las pruebas existentes usan la biblioteca estándar y Git para las pruebas
de empaquetado. No necesitan Docker, una cuenta Disney+ ni acceso a la
biblioteca. Algunas abren un servidor HTTP en loopback y usan carpetas
temporales. La extracción mediante navegador requiere Playwright en la
imagen, pero no se ejecuta en estas pruebas.

## Generar un ZIP

Borrador desde los archivos locales:

```shell
python scripts/build_bazarr_plus_bundle.py --output dist/disneyplus-draft.zip
```

Paquete con procedencia verificable, desde un commit completo ya publicado:

```shell
git rev-parse HEAD
python scripts/build_bazarr_plus_bundle.py --commit SHA_COMPLETO --output dist/disneyplus-release.zip
```

Sustituye `SHA_COMPLETO` por el resultado de Git. El modo `--commit` toma los
archivos del commit, no las modificaciones sin guardar en Git. Fija `source.ref`
y `source.commit`, recalcula los hashes e incluye exclusivamente `provider.py`
y `provider.json`. No sobrescribe paquetes existentes.

El manifiesto fuente utiliza ceros como marcador de desarrollo. Un ZIP sin
`--commit` sigue siendo un borrador. El generador no crea commits ni los
publica; verifica que la revisión sea accesible en GitHub antes de distribuir.
El ZIP generado tiene metadatos de procedencia diferentes al manifiesto fuente;
conserva su SHA-256 junto al artefacto.

## Cambios compatibles

Conserva el identificador `moonfinbridge` para las actualizaciones existentes.
No introduzcas código de instalación o herramientas auxiliares en `provider/`:
el host valida el contenido declarado del paquete. Si cambias `provider.py`,
actualiza versión y hashes del manifiesto antes de publicar.

El agente ofrece `/health`, `/v1/status`, `/v1/login`, `/v1/provider/lookup` y
`/v1/provider/download`, protegidos con `X-Bridge-Key`. La consulta de caché
usa `enqueue=false`; los sondeos no deben volver a encolar trabajo.
La versión 0.2.1 no distingue un fallo pasado de un trabajo pendiente durante
todo el intervalo de reintento: consulta [los pendientes](ROADMAP.md).

El SDK oficial describe el contrato:
[Provider Hub SDK](https://github.com/LavX/bazarr-provider-catalog/blob/main/sdk/README.md).
La corrección HI se prueba por separado en el repositorio del host; generar
el ZIP no la instala ni modifica Bazarr+.
