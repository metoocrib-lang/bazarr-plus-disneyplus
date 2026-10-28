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
- Búsqueda nativa de Bazarr+ y conservación de la configuración tras actualizar.
- Extracción/importación real comprobada anteriormente con el agente original.

## Pendientes, por prioridad

| Trabajo | Resultado esperado | Estado |
|---|---|---|
| Verificar la sesión migrada | Confirmar que Disney+ acepta el perfil del agente independiente. | Pendiente; no confundir con salud de la API. |
| Corregir HI en el host oficial | Importar pistas normales sin depender de la imagen personalizada. | Parche preparado y probado aisladamente; no enviado ni aceptado por upstream. |
| Clarificar fallos y reintentos | Distinguir en cola, procesando, fallido y bloqueado por intervalo. | Pendiente; actualmente `pending` puede durar 24 horas tras un fallo. |
| Automatizar pruebas y empaquetado | Detectar regresiones en cada cambio y producir un ZIP descargable. | Flujo preparado para Python 3.12–3.14; primera ejecución remota pendiente de comprobar. |
| Distribuir una versión instalable | Publicar un artefacto con revisión y hash, y evaluar incorporación al catálogo. | Código publicado; sin publicación de Marketplace ni release adjunta. |
| Simplificar la configuración | Evitar errores al editar mapas JSON y facilitar el diagnóstico de sesión. | Pendiente. |

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
