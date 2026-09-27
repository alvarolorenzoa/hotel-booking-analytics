# Guía paso a paso: dashboard en Power BI

Tiempo estimado: 2–3 horas. Resultado: un informe de 3 páginas guardado como
`dashboard/hotel_booking_analytics.pbix` más 3 capturas en `docs/img/`.

---

## 0. Preparación (10 min)

1. Instala **Power BI Desktop** desde Microsoft Store (gratis).
2. Copia los datos a Windows. En la terminal de Ubuntu, dentro del proyecto
   (cambia `TU_USUARIO` por tu usuario de Windows):
   ```bash
   mkdir -p /mnt/c/Users/TU_USUARIO/Documents/hotel-data
   cp data/processed/*.parquet /mnt/c/Users/TU_USUARIO/Documents/hotel-data/
   ```

## 1. Cargar los datos (10 min)

1. Power BI → **Obtener datos → Más… → Parquet → Conectar**.
2. Pega la ruta del primer archivo, por ejemplo
   `C:\Users\TU_USUARIO\Documents\hotel-data\fact_bookings.parquet` → **Cargar**.
3. Repite para las 6 tablas: `fact_bookings`, `dim_date`, `dim_hotel`,
   `dim_country`, `dim_channel`, `dim_customer`.

## 2. Modelo de datos en estrella (15 min)

Ve a la vista **Modelo** (icono de las tablas unidas, a la izquierda).

1. Borra las relaciones que Power BI haya creado solo (clic derecho → Eliminar).
2. Crea estas relaciones arrastrando la columna de `fact_bookings` a la de la dimensión
   (todas **varios a uno (*:1)**, dirección de filtro **única**):

| Desde `fact_bookings` | Hasta | Activa |
|---|---|---|
| `arrival_date_key` | `dim_date[date_key]` | Sí |
| `booking_date_key` | `dim_date[date_key]` | **No** (desmárcala) |
| `hotel_key` | `dim_hotel[hotel_key]` | Sí |
| `country_key` | `dim_country[country_key]` | Sí |
| `channel_key` | `dim_channel[channel_key]` | Sí |
| `customer_key` | `dim_customer[customer_key]` | Sí |

3. Selecciona `dim_date` → **Herramientas de tabla → Marcar como tabla de fechas** →
   columna `full_date`.
4. Ordenaciones (vista **Datos**, selecciona la columna → **Ordenar por columna**):
   - `dim_date[month_short]` y `dim_date[month_name]` → ordenar por `month`
   - `fact_bookings[lead_time_bucket]` → ordenar por `lead_time_bucket_order`
5. Oculta las columnas `*_key` (clic derecho → Ocultar en la vista de informe): así el
   panel de campos queda limpio.

## 3. Medidas DAX (15 min)

1. **Inicio → Especificar datos** → llama a la tabla `_Measures` → Cargar.
2. Con `_Measures` seleccionada: **Nueva medida** y pega, una a una, las medidas de
   `dashboard/measures.dax`.
3. Formatos (pestaña **Herramientas de medición**):
   - `Cancellation Rate %`, `Revenue at Risk %`, `Revenue YoY %`, `Repeat Guest Share %` → **Porcentaje**, 1 decimal
   - `Realised Revenue`, `Lost Revenue`, `Revenue PY`, `Revenue YTD` → **Moneda €**, 0 decimales
   - `ADR` → Moneda €, 2 decimales
4. Borra la columna vacía `Column1` de `_Measures`.

## 4. Diseño general

- **Vista → Temas**: elige uno sobrio (por ejemplo, "Ejecutivo") o usa azul oscuro `#1F3864` + naranja `#E07A1F`.
- Arriba de cada página: título a la izquierda y 2 segmentadores (slicers) a la derecha:
  `dim_hotel[hotel_name]` y `dim_date[year]` (estilo **Mosaico**).
- **Ver → Sincronizar segmentaciones** para que los filtros se mantengan entre páginas.

## 5. Página 1 – "Executive Overview"

| Visual | Campos |
|---|---|
| 5 **tarjetas** (fila superior) | `Realised Revenue`, `Bookings`, `ADR`, `Cancellation Rate %`, `Lost Revenue` |
| **Gráfico de líneas** (ancho) | Eje X: `dim_date[year_month]` · Valores: `Realised Revenue` y `Revenue PY` |
| **Barras horizontales** | Eje Y: `dim_channel[market_segment]` · Valor: `Realised Revenue` (ordenar descendente) |
| **Anillo** | Leyenda: `dim_hotel[hotel_name]` · Valor: `Realised Revenue` |

## 6. Página 2 – "Cancellation Analysis"

| Visual | Campos |
|---|---|
| 3 **tarjetas** | `Cancellation Rate %`, `Lost Revenue`, `Revenue at Risk %` |
| **Columnas** | Eje X: `fact_bookings[lead_time_bucket]` · Valor: `Cancellation Rate %` |
| **Columnas** | Eje X: `fact_bookings[deposit_type]` · Valor: `Cancellation Rate %` |
| **Matriz** | Filas: `dim_channel[market_segment]` · Columnas: `dim_hotel[hotel_name]` · Valor: `Cancellation Rate %` → **Formato condicional → Escala de colores** (verde bajo, rojo alto) |
| **Barras** | Eje Y: `dim_customer[guest_status]` · Valor: `Cancellation Rate %` |

## 7. Página 3 – "Markets & Seasonality"

| Visual | Campos |
|---|---|
| **Líneas** | Eje X: `dim_date[month_short]` · Leyenda: `dim_hotel[hotel_name]` · Valor: `ADR` |
| **Mapa coroplético** (o Mapa) | Ubicación: `dim_country[country_name]` · Saturación de color: `Realised Revenue` |
| **Tabla** | `dim_country[country_name]`, `Bookings`, `Realised Revenue`, `Cancellation Rate %` → filtro del visual: **N superior = 10** por `Realised Revenue` |
| **Columnas** | Eje X: `dim_date[month_short]` · Valor: `Bookings by Booking Date` (¿cuándo reserva la gente?) |

## 8. Terminar y publicar en GitHub (15 min)

1. Guarda como `dashboard/hotel_booking_analytics.pbix` dentro del proyecto
   (en Windows la carpeta está en `\\wsl.localhost\Ubuntu\home\TU_USUARIO_UBUNTU\projects\hotel-booking-analytics\dashboard`).
2. Haz una captura de cada página (Win + Shift + S) y guárdalas como:
   `docs/img/dashboard_overview.png`, `docs/img/dashboard_cancellations.png`,
   `docs/img/dashboard_markets.png`.
3. En la terminal:
   ```bash
   git add dashboard docs/img
   git commit -m "Add Power BI dashboard and screenshots"
   git push
   ```
Las capturas aparecerán automáticamente en el README.
