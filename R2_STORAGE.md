# R2_STORAGE.md — Migración de media a object storage (Cloudflare R2)

> Nota para tener en cuenta. Aún **no implementado**. Surge tras quedarnos sin disco
> en el VPS (391 GB compartidos entre varios proyectos) y sufrir OOM al comprimir fotos.

## Problema que resuelve (y el que NO)

| Problema | ¿R2 lo resuelve? | Fix real |
|---|---|---|
| **Disco lleno** del VPS | ✅ Sí — saca los archivos del disco local | Object storage (R2) |
| **Ancho de banda / entrega lenta** | ✅ Sí — CDN de Cloudflare integrado, egress gratis | R2 + CDN |
| **OOM al comprimir / generar PDF** | ❌ **No** — el pico de RAM es Pillow decodificando la imagen, venga de donde venga | Swap en el VPS + redimensionar antes de procesar |

> **Importante:** R2 es el fix de fondo para el **disco**, pero el OOM sigue
> necesitando swap (4 GB en `/swapfile`) y procesar imágenes con el pico de RAM
> acotado. No se reemplazan entre sí.

## Por qué R2 (vs S3 / B2)

- **Egress gratis** (servir imágenes no cuesta ancho de banda; S3 cobra ~$0.09/GB de salida).
- **CDN de Cloudflare integrado** → no hace falta montar un CDN aparte.
- **API S3-compatible** → se integra con `django-storages` + `boto3`, sin código propietario.

## Precios R2 (consultados 2026-06-15 — verificar antes de implementar)

| Concepto | Gratis/mes | Excedente |
|---|---|---|
| Almacenamiento (Standard) | 10 GB-mes | $0.015 / GB-mes |
| Class A (subidas, list, write) | 1 millón ops | $4.50 / millón |
| Class B (lecturas / descargas) | 10 millones ops | $0.36 / millón |
| **Egress (servir imágenes)** | **ilimitado** | **$0** |
| Infrequent Access (storage) | — (sin free tier) | $0.01 / GB-mes + $0.01/GB retrieval |

Las operaciones redondean hacia arriba a la unidad de facturación.
Fuente: https://developers.cloudflare.com/r2/pricing/

### Costo estimado (solo almacenamiento; las ops suelen caer en el tier gratis)

| Fotos almacenadas | Costo/mes |
|---|---|
| 50 GB | ~$0.60 |
| 100 GB | ~$1.35 |
| 200 GB | ~$2.85 |

→ ~**1–3 USD/mes** para mover toda la media fuera del VPS, con CDN y sin egress.

## Esquema de implementación (a planificar)

1. Crear bucket(s) en R2 (uno por proyecto, o prefijos) + token de API S3.
2. Configurar `django-storages` con backend S3-compatible apuntando al endpoint de R2
   (`https://<accountid>.r2.cloudflarestorage.com`), como `STORAGES["default"]` / media.
3. Migrar los archivos existentes de `media/` al bucket (script `aws s3 sync` o
   `rclone`, o management command).
4. Servir vía dominio público `*.r2.dev` o dominio custom de Cloudflare (con caché/CDN).
5. Verificar: subir foto → ver thumbnail (`photos/models.py`) → generar PDF
   (`pdf_reports/views.py`, que reduce a 1600px y cachea localmente).

### Consideraciones

- **Migración**: mover archivos + cambiar el storage default. Coordinar para no perder
  referencias de `Photos.imagen`.
- **Procesamiento más lento**: leer desde remoto agrega latencia → cachear localmente
  durante la generación de PDF (ya se hace algo en `pdf_reports/views.py`).
- Los **derivados** (thumbnails, fotos a 1600px para PDF) encajan bien en object storage.
- Patrón **replicable** para los otros proyectos del mismo VPS.

## Estado al 2026-06-15

- Disco recuperado con `docker builder prune -f` (de 100% a 86%, ~54 GB libres).
- Pendiente en VPS: crear swap de 4 GB (`/swapfile`).
- Aplicado en código: `CompressPhotosView` (`photos/views.py`) libera RAM por foto con
  `gc.collect()` e itera con `.iterator()` — mantiene resolución.
- Migración a R2: **pendiente / a planificar**.
