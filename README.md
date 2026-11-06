# FIUFIU - Marketplace con interfaz gráfica en Python

Este proyecto es una adaptación del archivo **fiufiu_netbeans** (Java, Apache NetBeans)
a **Python + Tkinter**, manteniendo la lógica orientada a objetos. No requiere Java,
NetBeans, bases de datos, conexión a internet ni librerías externas de Python.

## Requisitos
- Windows 10/11 con **Python 3.10 o posterior** y el componente Tkinter.
- También funciona en sistemas Linux con Tkinter instalado y entorno gráfico.

## Cómo ejecutar
1. **Descomprime la carpeta completa** del ZIP; no ejecutes el programa desde la vista previa del ZIP.
2. En Windows, haz doble clic en `FIUFIU.pyw` (cuando los archivos `.pyw` estén asociados a Python).
3. Alternativamente, abre la carpeta en una terminal y ejecuta `python iniciar.py`.
4. Se abrirá la ventana gráfica y se creará `datos_fiufiu.json` con tres usuarios y tres artículos de demostración (solo en el primer inicio si no existe otro guardado).

En algunos equipos Windows, el comando correcto es `py -3 iniciar.py`.
La consola, si se utiliza para abrir el programa, **no forma parte de la interfaz del juego**.

## Crear un producto nuevo o usado
1. Selecciona arriba el usuario que publicará el producto.
2. Entra en **Catálogo > Publicar artículo**.
3. Escribe código, nombre, precio en pesos y stock.
4. Escoge el vendedor y el campo **Condición del artículo**:
   - **Nuevo:** ingresa **meses de garantía** (0 o más).
   - **Usado:** escribe un **estado de conservación** (p. ej., "Buen estado").
5. Pulsa **Publicar producto**. El catálogo mostrará tipo y detalle.

## Comprar y procesar una transacción
1. Cambia el **Usuario activo** al comprador.
2. En **Catálogo**, selecciona un artículo de otro vendedor y pulsa **Agregar al carrito**.
3. Desde **Carrito**, crea la transacción.
4. Desde **Pagos y envíos**, selecciónala y pulsa **Autorizar pago**.
5. Escoge tarjeta o billetera digital y simula el saldo/cupo.
6. Pulsa **Verificar pago**. Recién en este paso se reduce el stock y se abona el valor de
   productos a los vendedores.
7. Procesa en orden **Preparar**, **Despachar** y **Entregar**.

El **5 % de comisión** se suma al subtotal y se cobra al comprador; FIUFIU registra
esa comisión solo cuando se ha verificado el pago. No hay transacciones bancarias reales.

## Funciones incluidas
- Registrar usuarios que compran y venden.
- Publicar productos **nuevos y usados**; visualizar detalles, stock y precios.
- Buscar publicaciones, reponer stock y cambiar el precio siendo el vendedor.
- Carrito por usuario, eliminación de líneas y cálculo de subtotales.
- Favoritos por usuario: marcar, quitar y agregar al carrito.
- Transacciones, autorización, verificación, rechazo y envío por etapas.
- Resumen de operaciones, saldos de vendedores y comisiones cobradas.
- Guardado automático **JSON**, exportación, importación y restablecimiento de demo.

## Archivo JSON y persistencia de perfiles y productos
Al **abrir el programa por primera vez**, se crea en la **misma carpeta** de
`iniciar.py` un archivo llamado `datos_fiufiu.json`. Es un archivo JSON de texto
que contiene los perfiles (ID, nombre, correo y saldo), todos los productos
(incluyendo Nuevo/Usado, garantía o conservación, vendedor, precio y stock),
favoritos, carritos y transacciones.

**No necesitas hacer nada para guardar:** cualquier cambio se guarda
**automáticamente**, también al registrar usuarios y publicar productos.
Puedes pulsar el botón **Guardar JSON** en la barra superior, o **Guardar JSON ahora**
en **Ayuda y datos**, para guardar manualmente y ver la ruta exacta.

Cada edición tiene **su propio JSON** porque está en una carpeta diferente.
Para pasar datos de una a otra, pulsa **Ayuda y datos > Exportar JSON...** y
luego **Importar JSON...** en la otra edición; importar sustituye los datos
actuales. Al actualizar un ZIP sobre otro, conserva tu `datos_fiufiu.json`.

**Importante:** descomprime el ZIP en una carpeta donde tengas permiso de
escritura (por ejemplo, Documentos). No ejecutes el proyecto directamente
adentro del ZIP. Los perfiles no tienen contraseñas: es una simulación y el
JSON contiene datos en texto legible. Usa datos de prueba, no información privada.

**Compatibilidad:** si ya usabas una versión anterior, en el primer arranque
se intentará leer el antiguo guardado de `%USERPROFILE%\.fiufiu\` y copiar
su contenido al nuevo archivo sin borrar el guardado viejo.

## Estructura del código
| Archivo | Función |
|---|---|
| `FIUFIU.pyw` | Inicia la ventana sin consola en Windows (si hay asociación Python). |
| `iniciar.py` | Alternativa para iniciar desde terminal o IDE. |
| `interfaz.py` | Ventanas, pestañas, tablas, formularios y eventos. |
| `modelos.py` | Clases, herencia, polimorfismo, inventario, pagos, carrito y envíos. |
| `persistencia.py` | Exporta e importa JSON de forma segura. |
| `estilos.py` | Estilos y colores de esta edición. |
| `test_fiufiu.py` | 14 pruebas automáticas del modelo y la persistencia. |
| `vista_previa.png` | Captura de la interfaz. |
| `datos_fiufiu.json` | Se crea automáticamente en el primer inicio y conserva los datos al cerrar. |

## Ejecutar las pruebas automáticas
Desde la carpeta del proyecto: `python -m unittest -v`

## Diferencia corregida respecto del proyecto Java
El código fuente Java declaraba `PORCENTAJE_COMISION = 0.1` (**10 %**), aunque
el README y los mensajes de la clase indicaban **5 %**. En Python se fijó **5 %**
para respetar la documentación funcional original. El sistema de pagos es simulado.

## Restricciones
- No existe login con contraseña en el programa original; el "Usuario activo" es un
  selector de identidad para la simulación, no un mecanismo de autenticación.
- Un pago rechazado queda rechazado. Para intentar de nuevo, agrega los artículos
  al carrito y crea una nueva transacción.
- La aplicación no interactúa con servicios bancarios ni de envío reales.
- El proyecto **requiere Python instalado**: no se entrega un archivo EXE autónomo.

La documentación técnica y la guía paso a paso están en el PDF entregado por separado. Esta edición mantiene una interfaz deliberadamente sencilla, sin paneles decorativos.
