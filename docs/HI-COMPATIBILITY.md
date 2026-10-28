# Compatibilidad con clasificación HI

[Volver al inicio](../README.md) · [Instalación](INSTALLATION.md)

**HI/SDH** identifica subtítulos para personas sordas o con dificultades
auditivas; pueden incluir descripciones de sonidos o identificación de voces.
Un archivo `.es.hi.srt` se distingue de un subtítulo normal `.es.srt`.

**Si vas a instalarlo por primera vez:** el ZIP del proveedor no corrige este
problema del host. Antes de importar en tu biblioteca, necesitas una versión
de Bazarr+ cuya compatibilidad se haya comprobado o una imagen con la corrección
aplicada. Este repositorio incluye el parche para revisión técnica, no una
imagen oficial de Bazarr+ ya corregida.

En Bazarr+ `76528c2fb9173442c827405b351f6baaecb37578`, el guardado puede cambiar
un SRT normal a `.es.hi.srt` por detectar paréntesis en el texto. Esto puede
seleccionar como destino un subtítulo HI existente. El proveedor ya declara
explícitamente que su pista es normal y verificable; su código aislado no
controla esta etapa del host.

El laboratorio conserva una imagen con protección específica de
`moonfinbridge`. No retirar esa imagen hasta validar una versión oficial que
incluya la corrección. El nuevo repositorio no elimina esta necesidad.

La propuesta general está en el [PR #789](https://github.com/LavX/bazarr/pull/789),
dirigido a `development` desde `effe5a9cc6e21910ab659ab41e0481479aa5b5f0`.
El [parche incluido](../patches/bazarr-verified-non-hi.patch) corresponde a esa propuesta. Respeta metadatos explícitos verificables,
conserva la heurística cuando faltan datos y no elimina flags HI existentes.
Incluye pruebas aisladas del guardado: cuatro pruebas, once escenarios;
los dos casos no-HI fallan antes de aplicar la corrección y pasan después.
Las pruebas no cubren todo el pipeline de importación del host.

Para revisar el parche en un checkout compatible de Bazarr+:

```shell
git apply --check /ruta/bazarr-verified-non-hi.patch
git apply /ruta/bazarr-verified-non-hi.patch
python tests/test_save_hi_metadata.py
```

El PR está publicado como borrador; no está aceptado ni incluido en una versión
oficial. Su CI requiere aprobación de los mantenedores. No parchea
contenedores automáticamente. La solicitud de incorporación a Bazarr+ es
independiente de la publicación del proveedor en este repositorio.

Contrato oficial consultado:
[Provider Hub SDK](https://github.com/LavX/bazarr-provider-catalog/blob/main/sdk/README.md).
