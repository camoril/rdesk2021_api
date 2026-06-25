# Manual de Uso: radiusdesk_api_probe.py

Este documento es una guia operativa para usar el script `radiusdesk_api_probe.py` en una instancia RadiusDesk 2021 (OVA).

## 1. Preparacion

### 1.1 Requisitos

- Python 3
- Acceso de red a RadiusDesk
- API key valida

### 1.2 Configuracion local segura

```bash
cp .env.example .env
```

Edita `.env`:

```bash
RADIUSDESK_BASE_URL=http://TU_IP_O_HOST_RADIUSDESK
RADIUSDESK_API_TOKEN=PEGA_AQUI_TU_API_KEY
```

El script carga `.env` automaticamente. Si prefieres, tambien puedes pasar `--base-url` y `--token` por CLI.

## 2. Comandos de operacion diaria

### 2.1 Verificar conectividad minima

```bash
python3 radiusdesk_api_probe.py map
```

Esto prueba realms y profiles, y muestra el payload base para alta de permanent user.

### 2.2 Listados rapidos

```bash
python3 radiusdesk_api_probe.py realms
python3 radiusdesk_api_probe.py profiles
```

### 2.3 Descubrir endpoints funcionales

```bash
python3 radiusdesk_api_probe.py discover
```

### 2.4 Consultar un endpoint puntual

```bash
python3 radiusdesk_api_probe.py query /cake3/rd_cake/devices/index.json
```

## 3. Exportaciones completas

### 3.1 CSV (recomendado para analisis rapido)

```bash
python3 radiusdesk_api_probe.py export --format csv --outdir exports
```

### 3.2 JSON (recomendado para integracion)

```bash
python3 radiusdesk_api_probe.py export --format json --outdir exports
```

### 3.3 Exportar entidades especificas

```bash
python3 radiusdesk_api_probe.py export --format csv --entities devices
python3 radiusdesk_api_probe.py export --format csv --entities realms permanent-users
```

### 3.4 Como funciona la paginacion

El script recorre automaticamente `page`, `start` y `limit` para evitar el limite de la primera pagina.

Validacion esperada:

- Los CSV/JSON deben incluir todos los registros disponibles en cada entidad.
- El numero final de filas depende de cada instancia.

## 4. Alta de usuarios permanentes

### 4.1 Prueba en seco (no crea nada)

```bash
python3 radiusdesk_api_probe.py add-user \
  --username demo2 \
  --password demopassword \
  --realm REALM_EJEMPLO \
  --profile PROFILE_EJEMPLO
```

### 4.2 Envio real

```bash
python3 radiusdesk_api_probe.py add-user \
  --username demo2 \
  --password demopassword \
  --realm REALM_EJEMPLO \
  --profile PROFILE_EJEMPLO \
  --submit
```

## 5. Endpoints confirmados en RadiusDesk 2021

### 5.1 Catalogos

- `GET /cake3/rd_cake/realms/index-ap-create.json?token=...`
- `GET /cake3/rd_cake/realms/index.json?token=...`
- `GET /cake3/rd_cake/realms/index-for-filter.json?token=...`
- `GET /cake3/rd_cake/profiles/index-ap.json?token=...`

### 5.2 Permanent users

- `GET /cake3/rd_cake/permanent-users/index.json?token=...`
- `GET /cake3/rd_cake/permanent-users/export-csv?token=...`
- `GET /cake3/rd_cake/permanent-users/view-basic-info.json?token=...`
- `GET /cake3/rd_cake/permanent-users/view-password.json?token=...`
- `GET /cake3/rd_cake/permanent-users/menu-for-grid.json?token=...`
- `GET /cake3/rd_cake/permanent-users/menu-for-authentication-data.json?token=...`
- `GET /cake3/rd_cake/permanent-users/menu-for-accounting-data.json?token=...`
- `GET /cake3/rd_cake/permanent-users/menu-for-user-devices.json?token=...`
- `GET /cake3/rd_cake/permanent-users/private-attr-index.json?token=...`
- `POST /cake3/rd_cake/permanent-users/add.json`

### 5.3 Devices

- `GET /cake3/rd_cake/devices/index.json?token=...`
- `GET /cake3/rd_cake/devices/export-csv?token=...`
- `GET /cake3/rd_cake/devices/view-basic-info.json?token=...`
- `GET /cake3/rd_cake/devices/edit-basic-info.json?token=...`
- `GET /cake3/rd_cake/devices/menu-for-grid.json?token=...`
- `GET /cake3/rd_cake/devices/menu-for-authentication-data.json?token=...`
- `GET /cake3/rd_cake/devices/menu-for-accounting-data.json?token=...`
- `GET /cake3/rd_cake/devices/private-attr-index.json?token=...`

### 5.4 Vouchers

- `GET /cake3/rd_cake/vouchers/index.json?token=...`
- `GET /cake3/rd_cake/vouchers/view-basic-info.json?token=...`
- `GET /cake3/rd_cake/vouchers/menu-for-grid.json?token=...`

## 6. Solucion de problemas

- `Token missing`: verifica `RADIUSDESK_API_TOKEN` en `.env` o `--token`
- Resultados incompletos: usa `export` (ya pagina automaticamente)
- Endpoint devuelve HTML/CSV: el script muestra preview y `content-type`
- Error de red: valida IP/host, puerto y reachability a RadiusDesk

## 7. Salidas generadas

Por defecto en `exports/`:

- `realms.csv` o `realms.json`
- `permanent-users.csv` o `permanent-users.json`
- `devices.csv` o `devices.json`
