# Código fuente de juanradomenech.com

Esta rama (`fuente`) no se publica. La web publicada está en la rama `main`.

- `contenido.json`: todos los textos y datos de la web.
- `construir.py`: genera la web en `publicar/` (y una copia para ver en local en `local/`).
- `actualizar_strava.py` + `strava_resumen.json`: actualizan las cifras de Strava con las salidas nuevas.

## Publicar
1. `python3 construir.py`
2. Copiar `publicar/` a la rama `main`, sin `_headers` ni `_redirects`, manteniendo el archivo `CNAME` (`juanradomenech.com`).
