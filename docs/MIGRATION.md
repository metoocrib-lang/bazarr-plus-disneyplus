# Migración desde el laboratorio

La separación del repositorio no modifica automáticamente el despliegue.
El laboratorio continúa usando sus imágenes, configuración, sesión y caché.
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
