# Disney+ para Bazarr+

Proveedor de subtítulos de Disney+ para Bazarr+, con un agente independiente
y sesión privada en Docker. **No requiere Jellyfin ni su plugin.**

Estado: experimental. La versión 0.2.1 separa el código del proyecto original.
El flujo anterior se probó con episodios reales; esta separación dispone de
pruebas offline y todavía no se ha desplegado sobre el laboratorio existente.
No está publicada en el Marketplace.

## Funcionamiento

1. Bazarr+ identifica el episodio y consulta el proveedor.
2. El proveedor consulta la caché privada del agente Disney+.
3. Si habilitas nuevas extracciones, el agente usa tu sesión para buscar el
   episodio y preparar el SRT; el proveedor espera hasta 75 segundos por defecto.
4. Bazarr+ muestra el resultado listo e importa el archivo cuando lo seleccionas.

El agente no necesita claves de Bazarr, Sonarr o Jellyfin, no monta la
biblioteca y no importa archivos. Admite episodios y español normal; no
películas ni pistas HI/forced. No obtiene claves DRM ni procesa pistas cifradas.

Las búsquedas nuevas están desactivadas de forma predeterminada. El proveedor
no distingue búsquedas manuales de programadas ni sabe si ya existe español:
mantén las tareas automáticas apagadas y selecciona episodios sin español.
Si una extracción supera el plazo, repite la búsqueda después. El agente
aplica un intervalo de 24 horas para no repetir solicitudes del mismo episodio,
incluso después de un fallo; no implica que siga procesándose todo ese tiempo.

## Instalación y sesión

Consulta [Instalación](docs/INSTALLATION.md),
[Migración desde el laboratorio](docs/MIGRATION.md) y
[Compatibilidad HI](docs/HI-COMPATIBILITY.md).
La versión actual de Bazarr+ requiere la corrección HI descrita antes de
utilizar importaciones sobre una biblioteca real.

## Desarrollo y paquetes

```shell
python -m unittest discover -s extractor/tests
python scripts/build_bazarr_plus_bundle.py --output dist/disneyplus-draft.zip
python scripts/build_bazarr_plus_bundle.py --commit COMMIT_COMPLETO --output dist/disneyplus-release.zip
```

El ZIP contiene únicamente `provider.py` y `provider.json`. El modo `--commit`
lee los archivos del commit, recalcula hashes y fija su procedencia en el
manifiesto del paquete. Los ceros en el manifiesto fuente son un marcador de
desarrollo, no una revisión publicada. No sobrescribe paquetes existentes.

Se conserva `provider_id=moonfinbridge` para que las instalaciones existentes
conserven su identidad y sean compatibles con la protección HI del laboratorio.
El nombre interno no representa una dependencia de Moonfin o Jellyfin.

## Procedencia

Separado de [Jellyfin.Plugin.SubtitleBridge](https://github.com/metoocrib-lang/Jellyfin.Plugin.SubtitleBridge),
revisión `d6c181241aa51feaa630882c592160a43b4d21e5` (revisión local de origen al
separar). Se trasladaron únicamente archivos de código seleccionados; no
sesiones, tokens, configuraciones del servidor, medios ni subtítulos reales.
