# Migración desde el laboratorio

## Resultado del laboratorio: 28 de octubre de 2026 UTC

La migración autorizada se completó con el proveedor 0.2.1, construido desde
`e5270e8c69345e53bbd141fa0029806aa3941f82`. Se detuvieron ambos agentes durante
la copia y se respaldaron perfil, estado, configuración, base de Bazarr+ y
bundle previo en almacenamiento privado del host.

Se verificaron por SHA-256 3298 archivos del perfil y 18 del estado, incluidos
17 SRT. La copia se adaptó a UID/GID 1001:1001 del nuevo agente; los originales
permanecen intactos. Se excluyeron de la copia los bloqueos efímeros de Chromium.
Ambos agentes usan Playwright 1.56.0. El anterior queda detenido para reversión.

Bazarr+ se conectó a la red privada del nuevo agente. Se usa su nombre completo
de contenedor para evitar colisiones con el alias `disney-agent` del anterior.
El mapa se conservó; se instaló el ZIP por Provider Hub y se reinició solamente
Bazarr+ para activarlo. Una búsqueda nativa y una descarga del worker desde la
caché devolvieron el SRT esperado con hash correcto, sin importarlo.

No se hicieron nuevas extracciones. El historial de importaciones no cambió.
Solicitudes nuevas, tareas automáticas y sincronización siguen desactivadas.
El perfil copiado aún no se ha comprobado contra Disney+: una copia íntegra
no garantiza que la sesión sea aceptada por el servicio.

La red añadida está documentada en un override Compose del despliegue y su
wrapper. Las futuras recreaciones de Bazarr+ deben incluir ese override;
recrear usando solo los Compose anteriores podría perder la conexión nueva.

Para revertir la conexión, arrancar el agente anterior y restaurar URL/token
del proveedor desde el respaldo privado. 0.2.1 conserva compatibilidad con
ese agente: no hace falta restaurar toda la base ni eliminar volúmenes para
cambiar de vuelta. No se ha ejecutado esa reversión.

## Procedimiento para otras instalaciones

La separación del repositorio no modifica automáticamente otros despliegues.
No es necesario volver a iniciar sesión ni reinstalar para conservar el estado
actual; una futura actualización del agente sí necesita planificación.

Cambios de 0.2.1:

- Origen Git del paquete: `metoocrib-lang/bazarr-plus-disneyplus`, carpeta `provider`.
- Nombre visible Disney+; identificador interno `moonfinbridge` conservado.
- API antigua `/v1/scan` eliminada, igual que el cliente de carga a Bazarr.
- Solo Disney+ en el estado del agente; sin conectores pendientes de otros servicios.
- API privada de búsqueda/descarga, formato de caché y mapa de episodios conservados.

Para actualizar, respaldar primero y construir/probar la nueva imagen con
volúmenes desechables. Después, con autorización para recrear únicamente el
agente del laboratorio, conservar los montajes, UID/GID y red existentes.
El Compose incluido aquí crea un proyecto nuevo y **no es un reemplazo directo**
del Compose del laboratorio. El UID de la imagen nueva puede diferir del
usuario del despliegue existente: revisar permisos antes de conectar sus datos.
No ejecutar simultáneamente dos navegadores sobre el mismo perfil persistente.

Instalar el ZIP 0.2.1 mediante Provider Hub conservando ID y configuración.
Mantener solicitudes nuevas y automatismos apagados durante las comprobaciones.
La API antigua desaparece: este agente no debe usarse como backend del plugin
de Jellyfin. El agente del proyecto original conserva esa función.
