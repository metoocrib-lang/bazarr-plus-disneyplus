# Configuración y mapa de episodios

[Volver al inicio](../README.md) · [Instalación](INSTALLATION.md)

## Los cinco ajustes del proveedor

| Ajuste | Qué significa | Ejemplo o valor inicial |
|---|---|---|
| `agent_url` | Dirección que Bazarr+ utiliza para llegar al agente dentro de Docker. | `http://bazarrplus-disneyplus-disney-agent-1:8787` |
| `bridge_token` | Credencial compartida con el agente; debe coincidir con `BRIDGE_API_TOKEN` de `.env`. | Tu valor privado, de al menos 32 caracteres. |
| `series_json` | Lista de series que permites consultar y sus equivalencias. | Los ejemplos de esta página, sustituyendo sus datos ficticios. |
| `enable_requests` | Permite solicitar extracciones que todavía no están en caché. | `false` inicialmente. |
| `wait_seconds` | Tiempo de espera durante una búsqueda que acaba de encolar trabajo. | `75`; admite enteros de 0 a 90. |

Con `wait_seconds=0` la búsqueda vuelve inmediatamente, pero puede encolar
la extracción si `enable_requests=true`. El worker del host debe tener un
timeout de al menos 120 segundos para utilizar la espera recomendada.

## Qué datos necesitas de una serie

1. **ID TVDB:** el identificador de la serie que Bazarr+ recibe de tu biblioteca.
   No es el número interno de Sonarr ni el identificador de un episodio.
2. **URL de catálogo Disney+:** la página de la serie, no el enlace `/play/`
   de un episodio. Admite rutas `/browse/entity-UUID` y `/series/...`.
3. **Equivalencias:** temporada y episodio de la biblioteca, y su posición
   correspondiente en Disney+. Comprueba los títulos; no te guíes solo por
   el orden de las tarjetas.

Usa una URL HTTPS de `disneyplus.com` o `www.disneyplus.com`. Elimina parámetros
de seguimiento después de `?` y fragmentos después de `#`. El proveedor los
rechaza para evitar aceptar destinos ambiguos.

## Ejemplo 1: la numeración coincide

Los datos de estos ejemplos son ficticios. Sustituye `123456` y la URL antes
de utilizarlos. Pega la lista completa en `series_json`:

```json
[
  {
    "tvdb_id": 123456,
    "series_url": "https://www.disneyplus.com/series/example/abc123",
    "mapping": ""
  }
]
```

Un `mapping` vacío conserva la numeración: T1E3 de la biblioteca consulta
T1E3 de Disney+. Úsalo solo si has comprobado que coinciden.

## Ejemplo 2: una temporada local se divide en dos en Disney+

```json
[
  {
    "tvdb_id": 123456,
    "series_url": "https://www.disneyplus.com/series/example/abc123",
    "mapping": "17x1-13=1x1\n17x14-26=2x1"
  }
]
```

Cada regla se lee **biblioteca = Disney+**:

| Regla | Qué hace |
|---|---|
| `17x1-13=1x1` | T17E1–E13 de la biblioteca corresponden a T1E1–E13 de Disney+. |
| `17x14-26=2x1` | T17E14–E26 corresponden a T2E1–E13. |
| `17x14=2x1` | Una regla para un solo episodio: T17E14 corresponde a T2E1. |

En ese mapa, T17E15 consulta T2E2. T17E27 no tiene regla y no se busca.
Cuando defines reglas, los episodios no incluidos se omiten: no hay una
equivalencia automática de respaldo. No repitas reglas ni destinos.

`\n` representa un salto de línea dentro de la cadena JSON. No pongas un
salto literal dentro de las comillas ni una coma después del último campo.

## Varias series

Añade objetos separados por comas dentro de la misma lista. Usa un objeto
por ID TVDB. El proveedor admite hasta 32 entradas y un máximo de 16.384
caracteres en `series_json`.

```json
[
  {"tvdb_id": 123456, "series_url": "https://www.disneyplus.com/series/example/abc123", "mapping": "1x1-12=1x1"},
  {"tvdb_id": 654321, "series_url": "https://www.disneyplus.com/series/another/def456", "mapping": ""}
]
```

## Validar antes de pegar en Bazarr+

Guarda solo la lista `series_json` en un archivo UTF-8 llamado `series.json`.
No incluyas tokens ni el resto de la configuración. Desde el repositorio,
con Python instalado:

```shell
python scripts/validate_series.py series.json
python scripts/validate_series.py series.json --episode 123456 17 15
```

El segundo comando muestra qué episodio de Disney+ corresponde a T17E15.
Con el ejemplo 2 devuelve T2E2. Si falta una regla, indica que el proveedor
omitirá el episodio. No abre el navegador, consulta servicios ni modifica el
archivo: valida sintaxis, URLs, límites, TVDB duplicados y solapamientos usando
las reglas del proveedor. Además rechaza campos desconocidos y tipos ambiguos
para detectar errores de edición antes de guardar la configuración.

Códigos de salida: `0` válido, `1` error de entrada, `2` episodio sin equivalencia.
Una validación correcta no confirma que la serie o los subtítulos existan en
Disney+: todavía debes comprobar la correspondencia de títulos.

## Uso manual recomendado durante las pruebas

Mantén desactivadas las búsquedas programadas y la mejora automática de
subtítulos de Bazarr+. Selecciona episodios sin español. Activa
`enable_requests` solo cuando quieras solicitar extracciones y desactívalo
para volver a consultar únicamente la caché.

El proveedor recibe el mismo tipo de solicitud para búsquedas manuales y
automáticas. No puede imponer por sí solo «solo si no tiene español».
Si cambias el mapa, una caché creada con otras equivalencias no se reutiliza
automáticamente: la identidad del SRT incluye las coordenadas de Disney+.
