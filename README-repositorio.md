# rdesk2021_api

Herramientas para interactuar con RadiusDesk 2021 (OVA) por API, con foco en:

- descubrimiento de endpoints funcionales
- consultas por API token
- exportacion completa de datos (realms, permanent users, devices)

## Objetivo del repositorio

Este proyecto facilita automatizar tareas operativas de RadiusDesk sin exponer credenciales en el codigo.

Incluye un script principal en Python:

- `radiusdesk_api_probe.py`

## Que problema resuelve

- Evita exportaciones incompletas por paginacion (la API suele devolver 50 registros por pagina)
- Permite validar rapidamente endpoints disponibles en una instancia concreta
- Genera archivos CSV o JSON listos para analisis y respaldo

## Seguridad

- No se deben versionar llaves API
- Se usa `.env.example` como plantilla publica
- `.env` esta excluido por `.gitignore`

## Inicio rapido

```bash
cp .env.example .env
# Edita .env con tu IP/host y tu API key

python3 radiusdesk_api_probe.py --base-url http://TU_IP export --format csv --outdir exports
```

## Documentacion de uso

El manual completo del script esta en:

- `README.md`

## Estado actual

Validado contra RadiusDesk 2021 OVA con exportacion completa de:

- devices
- permanent-users
- realms

## Licencia

Este repositorio se distribuye bajo la licencia GNU General Public License v3.0 (GPL-3.0).

Consulta el archivo `LICENSE` para el texto completo.
