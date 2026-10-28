# Verificación del agente independiente

Este informe corresponde al arranque inicial, antes de copiar la sesión y
conectar Bazarr+. El resultado posterior está en [Migración](MIGRATION.md).

Prueba aislada realizada el 27 de octubre de 2026, con autorización para
construir y arrancar un contenedor nuevo. Código:
`e5270e8c69345e53bbd141fa0029806aa3941f82`.

Imagen local `bazarr-plus-disneyplus-agent:0.2.1`:
`sha256:7dadb1b917c2fe653c5676eeb6e8da172dc81148da916285a037f586aaffda42`.
Base Playwright resuelta durante la construcción:
`sha256:a7f6cf3ae520c9d670ad956572c13747ed5abdbba5123a01526f873ed1662528`.

## Resultados

- Compose válido; construcción completada.
- Contenedor `healthy`, cero reinicios durante la comprobación.
- Usuario `pwuser`, raíz de solo lectura, dos volúmenes nuevos de navegador/estado.
- Sin montajes de biblioteca ni reutilización del perfil del agente anterior.
- API 8787 sin publicación en el host; noVNC enlazado a 127.0.0.1:6082.
- Salud autenticada: HTTP 200; token incorrecto: HTTP 401.
- Ruta antigua `/v1/scan`: HTTP 404.
- Caché sintética: ausencia inicial, escritura de prueba, resultado listo,
  descarga con bytes y SHA-256 correctos. Se retiró únicamente el SRT sintético.
- Cola vacía al terminar; ninguna extracción Disney+ ni importación a biblioteca.
- noVNC HTTP 200 y protocolo VNC disponible.
- Chromium con interfaz gráfica abrió `about:blank` y ejecutó JavaScript.
  El perfil temporal de esta comprobación se eliminó al cerrar el navegador.
- Los contenedores existentes conservaron sus IDs y tiempos de arranque.

Las 42 pruebas offline del repositorio también pasaron antes del despliegue.
Estas comprobaciones no prueban autenticación Disney+, extracción real,
integración del nuevo agente con Bazarr+ ni migración del perfil anterior.
La sesión nueva permanece `no_validada`. La imagen HI del laboratorio sigue
siendo necesaria; no se actualizó Bazarr+.

## Estado y reversión

El agente aislado se deja funcionando con política `unless-stopped`.
Las credenciales generadas permanecen únicamente en el `.env` privado del
host; no se publican en este repositorio. No hay búsquedas programadas.

Para detener esta prueba, desde su directorio de despliegue:

```shell
docker compose stop disney-agent
```

Para retirar el contenedor y sus redes, preservando volúmenes y configuración:

```shell
docker compose down
```

No usar `--volumes` si se quieren conservar sus datos. Estos comandos son
instrucciones de reversión: no se ejecutaron durante la verificación.
