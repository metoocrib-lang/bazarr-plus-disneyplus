# Estado y próximos pasos

[Volver al inicio](../README.md)

Este documento separa lo comprobado de lo pendiente. No anuncia fechas ni
funciones disponibles antes de que se implementen y prueben.

## Comprobado

- Proveedor 0.2.1 publicado como código en un repositorio independiente.
- Generación reproducible de ZIP desde un commit real.
- Agente Docker aislado, API autenticada, noVNC y Chromium funcionales.
- Búsqueda con espera acotada y descarga desde caché en el worker real.
- Migración de perfil y 17 SRT con verificación de integridad.
- Catálogo Disney+ accesible con una copia temporal del perfil migrado:
  temporadas y control de perfil visibles, sin reproducción ni extracción.
- Búsqueda nativa de Bazarr+ y conservación de la configuración tras actualizar.
- Extracción/importación real comprobada anteriormente con el agente original.
- Pruebas automáticas y documentación aprobadas en Python 3.12, 3.13 y 3.14;
  ZIP con revisión y hash generado por GitHub Actions.
  [Primera ejecución completa](https://github.com/metoocrib-lang/bazarr-plus-disneyplus/actions/runs/40639452649).

## Pendientes, por prioridad

| Trabajo | Resultado esperado | Estado |
|---|---|---|
| Verificar la sesión migrada | Comprobar acceso al catálogo con el perfil del agente independiente. | Comprobado para catálogo; reproducción y nueva extracción no repetidas. Véase [Migración](MIGRATION.md). |
| Corregir HI en el host oficial | Importar pistas normales sin depender de la imagen personalizada. | [PR #789](https://github.com/LavX/bazarr/pull/789) abierto en borrador; CI requiere aprobación de los mantenedores. No incorporado todavía. |
| Clarificar fallos y reintentos | Distinguir en cola, procesando, fallido y bloqueado por intervalo. | Implementado y desplegado en 0.2.2; pruebas offline y sintéticas aprobadas. [Detalles](EXTRACTION-STATES.md). |
| Publicar una versión estable | Ofrecer un paquete de distribución permanente y evaluar incorporación al catálogo. | ZIP disponible como artefacto de CI durante 30 días; sin Marketplace ni release estable adjunta. |
| Simplificar la configuración | Evitar errores al editar mapas JSON y facilitar el diagnóstico de sesión. | Validador offline con vista previa implementado; interfaz y diagnóstico de sesión pendientes. [Uso](CONFIGURATION.md). |

La política «solo episodios sin español» todavía se controla desde Bazarr+,
no desde el proveedor. No se ha habilitado un flujo automático de biblioteca.
La sincronización no es un requisito para terminar el proveedor; se evaluaría
solo cuando un archivo de vídeo concreto la necesite.

## Qué requiere una nueva prueba o autorización en el laboratorio

Cambiar código o documentación no actualiza contenedores por sí solo. Antes
de desplegar otra imagen hay que respaldar y autorizar la actualización de
los servicios afectados. Una nueva extracción o importación real debe tener
un episodio y un destino acordados. No repetir importaciones ya verificadas
como comprobación rutinaria.
