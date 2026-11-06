"""Interfaz gráfica FIUFIU, construida únicamente con Tkinter/ttk.

La interfaz nunca modifica el stock ni procesa pagos por sí sola: invoca
métodos del archivo modelos.py. De este modo se separan interfaz y lógica.
Cada ventana, botón y tabla está explicado en comentarios y docstrings.
"""
from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from modelos import (ArticuloNuevo, ArticuloUsado, BilleteraDigital,
                     Marketplace, Tarjeta, Usuario, cargar_demostracion, dinero)
from persistencia import cargar, guardar
from estilos import CONFIG, preparar_estilos


class AppFiufiu(tk.Tk):
    """Ventana principal: usuarios, catálogo, carrito, favoritos y transacciones."""

    def __init__(self):
        super().__init__()
        self.title(CONFIG['titulo'])
        self.geometry('1110x680')
        self.minsize(900, 550)
        self.configure(bg=CONFIG['fondo'])
        # El archivo JSON se ubica junto a los scripts: es fácil verlo y copiarlo.
        # Cada ZIP tiene su carpeta, por lo que las ediciones son independientes.
        self.ruta_datos = Path(__file__).resolve().parent / 'datos_fiufiu.json'
        self.aviso_carga = ''
        crear_archivo = False

        # Compatibilidad: recupera una instalación anterior guardada en .fiufiu.
        ruta_anterior = Path.home() / '.fiufiu' / CONFIG['archivo']
        try:
            if self.ruta_datos.exists():
                self.market = cargar(self.ruta_datos)
            elif ruta_anterior.exists():
                self.market = cargar(ruta_anterior)
                crear_archivo = True  # Migrar a la carpeta actual, sin borrar el anterior.
            else:
                self.market = cargar_demostracion()
                crear_archivo = True  # Crear JSON incluso en el primer inicio.
        except (OSError, ValueError, KeyError, TypeError) as exc:
            # No sobrescribir automáticamente un archivo que podría recuperarse.
            self.market = cargar_demostracion()
            self.aviso_carga = f'No se pudo cargar el guardado: {exc}'

        if crear_archivo:
            try:
                guardar(self.market, self.ruta_datos)
            except OSError as exc:
                self.aviso_carga = f'No se pudo crear el JSON en la carpeta: {exc}'

        preparar_estilos(self)
        self.usuario_actual = tk.StringVar()
        self.busqueda = tk.StringVar()
        self.busqueda.trace_add('write', lambda *_: self._actualizar_articulos())
        self.mensaje_estado = tk.StringVar(value='FIUFIU listo para usar')
        self._crear_interfaz()
        self._actualizar_todo()
        self.protocol('WM_DELETE_WINDOW', self.destroy)
        if self.aviso_carga:
            self.after(150, lambda: messagebox.showwarning('Archivo no cargado',
                self.aviso_carga + '\n\nSe muestran datos de demostración; '
                'el archivo original no se ha sobrescrito.'))

    # ------------------- onstrucción de la ventana principal -------------------
    def _crear_interfaz(self) -> None:
        """dibuja la cabecera, selector de usuario, pestañas y barra de estado"""
        if CONFIG['decorado']:
            # La variante decorada conserva su cabecera y sus colores.
            cabecera = tk.Frame(self, bg=CONFIG['cabecera'], padx=22, pady=15)
            cabecera.pack(fill='x')
            titulo = tk.Frame(cabecera, bg=CONFIG['cabecera'])
            titulo.pack(side='left', fill='y')
            tk.Label(titulo, text='FIUFIU', bg=CONFIG['cabecera'],
                     fg=CONFIG['titulo_color'], font=('Segoe UI', 21, 'bold')).pack(anchor='w')
            tk.Label(titulo, text='MARKETPLACE  ·  PYTHON', bg=CONFIG['cabecera'],
                     fg=CONFIG['subtitulo'], font=('Segoe UI', 9)).pack(anchor='w')
            lado = tk.Frame(cabecera, bg=CONFIG['cabecera'])
            lado.pack(side='right', pady=9)
            tk.Label(lado, text='Usuario activo:', bg=CONFIG['cabecera'],
                     fg=CONFIG['titulo_color']).pack(side='left', padx=(0, 9))
            self.selector_usuario = ttk.Combobox(lado, state='readonly', width=24,
                                                textvariable=self.usuario_actual)
            self.selector_usuario.pack(side='left')
            ttk.Button(lado, text='Guardar JSON', command=self._guardar_manual).pack(
                side='left', padx=(14, 0))
        else:
            # Edición MUY BÁSICA: solo una fila de controles nativos de Tkinter
            # sin banner, títulos grandes, colores ni elementos decorativos
            barra_superior = ttk.Frame(self, padding=6)
            barra_superior.pack(fill='x')
            ttk.Label(barra_superior, text='FIUFIU').pack(side='left')
            ttk.Label(barra_superior, text='Usuario:').pack(side='left', padx=(14, 4))
            self.selector_usuario = ttk.Combobox(barra_superior, state='readonly',
                                                width=24, textvariable=self.usuario_actual)
            self.selector_usuario.pack(side='left')
            ttk.Button(barra_superior, text='Guardar JSON',
                       command=self._guardar_manual).pack(side='right')
        self.selector_usuario.bind('<<ComboboxSelected>>', self._cambiar_usuario)

        # El Notebook agrupa funciones relacionadas, sin pedir comandos de consola.
        contenedor = ttk.Frame(self, padding=(18, 14, 18, 8) if CONFIG['decorado'] else 5)
        contenedor.pack(fill='both', expand=True)
        self.pestanas = ttk.Notebook(contenedor)
        self.pestanas.pack(fill='both', expand=True)
        self._crear_inicio()
        self._crear_usuarios()
        self._crear_catalogo()
        self._crear_carrito()
        self._crear_favoritos()
        self._crear_compras()
        self._crear_ayuda()

        pie = tk.Frame(self, bg=CONFIG['pie'], padx=17, pady=8)
        pie.pack(fill='x', side='bottom')
        tk.Label(pie, textvariable=self.mensaje_estado, bg=CONFIG['pie'],
                 fg=CONFIG['pie_texto'], anchor='w').pack(fill='x')

    def _nueva_pestana(self, texto: str) -> ttk.Frame:
        """Crea el espacio de una pestaña y lo agrega al menú superior."""
        contenido = ttk.Frame(self.pestanas, padding=14 if CONFIG['decorado'] else 6)
        self.pestanas.add(contenido, text=texto)
        return contenido

    @staticmethod
    def _barra(parent: ttk.Frame, titulo: str, descripcion: str) -> ttk.Frame:
        """Encabezado de sección, con espacio libre para botones a la derecha."""
        zona = ttk.Frame(parent)
        zona.pack(fill='x', pady=(0, 12))
        izquierda = ttk.Frame(zona)
        izquierda.pack(side='left', fill='x', expand=True)
        if CONFIG['decorado']:
            ttk.Label(izquierda, text=titulo, style='Seccion.TLabel').pack(anchor='w')
            ttk.Label(izquierda, text=descripcion, style='Secundaria.TLabel').pack(anchor='w')
        else:
            # Solo una etiqueta con el nombre de la sección.
            ttk.Label(izquierda, text=titulo).pack(anchor='w')
        acciones = ttk.Frame(zona)
        acciones.pack(side='right', padx=(10, 0))
        return acciones

    @staticmethod
    def _boton(padre, texto: str, accion, primario=False) -> None:
        """Agrega un botón con el estilo correspondiente a la variante."""
        ttk.Button(padre, text=texto, command=accion,
                   style='Principal.TButton' if primario else 'TButton').pack(
                       side='left', padx=(6, 0) if CONFIG['decorado'] else (2, 0), pady=2)

    @staticmethod
    def _tabla(padre: ttk.Frame, columnas: list[tuple[str, str, int]]) -> ttk.Treeview:
        """Crea una tabla desplazable y con columnas ajustables."""
        marco = ttk.Frame(padre)
        marco.pack(fill='both', expand=True)
        ids = [c[0] for c in columnas]
        vista = ttk.Treeview(marco, columns=ids, show='headings', selectmode='browse')
        for clave, nombre, ancho in columnas:
            vista.heading(clave, text=nombre)
            vista.column(clave, width=ancho, anchor='w', stretch=True)
        scroll_y = ttk.Scrollbar(marco, orient='vertical', command=vista.yview)
        scroll_x = ttk.Scrollbar(marco, orient='horizontal', command=vista.xview)
        vista.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        marco.rowconfigure(0, weight=1)
        marco.columnconfigure(0, weight=1)
        vista.grid(row=0, column=0, sticky='nsew')
        scroll_y.grid(row=0, column=1, sticky='ns')
        scroll_x.grid(row=1, column=0, sticky='ew')
        return vista

    def _crear_inicio(self):
        """Pantalla de bienvenida y estadísticas resumidas."""
        self.panel_inicio = self._nueva_pestana('Inicio')
        if not CONFIG['decorado']:
            # La versión más simple prescinde completamente de tarjetas,
            # bordes, iconos, banners, guías visuales y estadísticas grandes.
            ttk.Label(self.panel_inicio, text='Resumen').pack(anchor='w', pady=5)
            self.tarjetas = {}
            for clave, nombre in [('usuarios', 'Usuarios'), ('articulos', 'Productos'),
                                  ('transacciones', 'Compras'), ('comisiones', 'Comisiones')]:
                linea = ttk.Frame(self.panel_inicio)
                linea.pack(anchor='w', pady=3)
                ttk.Label(linea, text=nombre + ':', width=20).pack(side='left')
                etiqueta = ttk.Label(linea, text='0')
                etiqueta.pack(side='left')
                self.tarjetas[clave] = etiqueta
            self.resumen_usuario = ttk.Label(self.panel_inicio)
            self.resumen_carrito = ttk.Label(self.panel_inicio)
            self.resumen_favoritos = ttk.Label(self.panel_inicio)
            self.resumen_ventas = ttk.Label(self.panel_inicio)
            for etiqueta in (self.resumen_usuario, self.resumen_carrito,
                             self.resumen_favoritos, self.resumen_ventas):
                etiqueta.pack(anchor='w', pady=5)
            return
        self._barra(self.panel_inicio, 'Resumen del marketplace',
                    'Selecciona arriba quién está usando FIUFIU.')
        contenedor = ttk.Frame(self.panel_inicio)
        contenedor.pack(fill='x', pady=(8, 18))
        self.tarjetas = {}
        campos = [
            ('usuarios', 'Usuarios'), ('articulos', 'Artículos publicados'),
            ('transacciones', 'Transacciones'), ('comisiones', 'Comisiones FIUFIU'),
        ]
        for i, (clave, encabezado) in enumerate(campos):
            # Las tarjetas usan tk.Frame para poder colorearse en la versión decorada.
            tarjeta = tk.Frame(contenedor, bg=CONFIG['tarjeta'], padx=15, pady=17,
                               highlightthickness=1, highlightbackground=CONFIG['borde'])
            tarjeta.grid(row=0, column=i, sticky='nsew', padx=(0, 10 if i < 3 else 0))
            contenedor.columnconfigure(i, weight=1)
            tk.Label(tarjeta, text=encabezado, bg=CONFIG['tarjeta'],
                     fg=CONFIG['texto_secundario'], font=('Segoe UI', 10)).pack(anchor='w')
            etiqueta = tk.Label(tarjeta, bg=CONFIG['tarjeta'], fg=CONFIG['destacado'],
                                font=('Segoe UI', 21, 'bold'))
            etiqueta.pack(anchor='w', pady=(9, 0))
            self.tarjetas[clave] = etiqueta
        self.resumen_usuario = ttk.Label(self.panel_inicio, style='Seccion.TLabel')
        self.resumen_usuario.pack(anchor='w', pady=(8, 10))
        self.resumen_carrito = ttk.Label(self.panel_inicio)
        self.resumen_carrito.pack(anchor='w', pady=5)
        self.resumen_favoritos = ttk.Label(self.panel_inicio)
        self.resumen_favoritos.pack(anchor='w', pady=5)
        self.resumen_ventas = ttk.Label(self.panel_inicio)
        self.resumen_ventas.pack(anchor='w', pady=5)
        ttk.Separator(self.panel_inicio).pack(fill='x', pady=18)
        ttk.Label(self.panel_inicio, text='Recorrido recomendado',
                  style='Seccion.TLabel').pack(anchor='w')
        ttk.Label(self.panel_inicio, text=(
            '1. Registra usuarios o usa los tres de ejemplo.     '
            '2. Publica un artículo indicando NUEVO o USADO.\n'
            '3. Elige un comprador, agrega productos al carrito y crea una transacción.\n'
            '4. Autoriza y verifica el pago simulado.     '
            '5. Prepara, despacha y confirma la entrega.'),
            justify='left').pack(anchor='w', pady=10)

    def _crear_usuarios(self):
        """Pestaña para registrar y revisar compradores/vendedores."""
        panel = self._nueva_pestana('Usuarios')
        barra = self._barra(panel, 'Usuarios registrados',
                            'Cada usuario puede comprar y vender productos.')
        self._boton(barra, 'Registrar usuario', self._registrar_usuario, True)
        self.tabla_usuarios = self._tabla(panel, [
            ('id', 'ID', 90), ('nombre', 'Nombre', 230),
            ('correo', 'Correo', 320), ('ventas', 'Saldo por ventas', 170),
        ])

    def _crear_catalogo(self):
        """Pestaña de productos con buscador y comandos de publicación."""
        panel = self._nueva_pestana('Catálogo')
        barra = self._barra(panel, 'Catálogo de artículos',
                            'Al publicar eliges Nuevo o Usado y su detalle específico.')
        self._boton(barra, 'Publicar artículo', self._publicar_articulo, True)
        self._boton(barra, 'Ver detalles', self._detalles_articulo)
        self._boton(barra, 'Agregar al carrito', self._agregar_carrito)
        self._boton(barra, 'Favorito / quitar', self._alternar_favorito)
        self._boton(barra, 'Reponer stock', self._reponer_stock)
        self._boton(barra, 'Cambiar precio', self._cambiar_precio)
        filtro = ttk.Frame(panel)
        filtro.pack(fill='x', pady=(0, 10))
        ttk.Label(filtro, text='Buscar por nombre, código o tipo: ').pack(side='left')
        ttk.Entry(filtro, textvariable=self.busqueda, width=38).pack(side='left')
        self.tabla_articulos = self._tabla(panel, [
            ('codigo', 'Código', 85), ('nombre', 'Artículo', 240),
            ('tipo', 'Condición', 90), ('detalle', 'Detalle', 190),
            ('precio', 'Precio', 100), ('stock', 'Stock', 65),
            ('vendedor', 'Vendedor', 120),
        ])
        self.tabla_articulos.bind('<Double-1>', lambda _e: self._detalles_articulo())

    def _crear_carrito(self):
        """Pestaña del carrito del usuario activo."""
        panel = self._nueva_pestana('Carrito')
        barra = self._barra(panel, 'Carrito de compras',
                            'Agregar productos no descuenta stock: eso ocurre al verificar un pago.')
        self._boton(barra, 'Quitar seleccionado', self._quitar_carrito)
        self._boton(barra, 'Crear transacción', self._crear_transaccion, True)
        self.tabla_carrito = self._tabla(panel, [
            ('codigo', 'Código', 95), ('nombre', 'Producto', 290),
            ('cantidad', 'Cantidad', 90), ('unitario', 'Precio unitario', 160),
            ('subtotal', 'Subtotal', 150),
        ])
        pie = ttk.Frame(panel)
        pie.pack(fill='x', pady=(12, 0))
        self.etiqueta_subtotal = ttk.Label(pie, style='Seccion.TLabel')
        self.etiqueta_subtotal.pack(side='right')

    def _crear_favoritos(self):
        """Pestaña para consultar y quitar favoritos del usuario activo."""
        panel = self._nueva_pestana('Favoritos')
        barra = self._barra(panel, 'Mis favoritos',
                            'La lista de favoritos pertenece al usuario seleccionado.')
        self._boton(barra, 'Agregar al carrito', self._favorito_a_carrito, True)
        self._boton(barra, 'Quitar favorito', self._quitar_favorito)
        self.tabla_favoritos = self._tabla(panel, [
            ('codigo', 'Código', 100), ('nombre', 'Producto', 320),
            ('tipo', 'Condición', 140), ('precio', 'Precio', 120),
            ('stock', 'Stock', 90),
        ])

    def _crear_compras(self):
        """Pestaña para los pagos y los envíos de todas las transacciones."""
        panel = self._nueva_pestana('Pagos y envíos')
        barra = self._barra(panel, 'Transacciones y entregas',
                            'El flujo es: Autorizar → Verificar → Preparar → Despachar → Entregar.')
        self._boton(barra, 'Detalle', self._detalle_transaccion)
        self._boton(barra, 'Autorizar pago', self._autorizar_pago, True)
        self._boton(barra, 'Verificar pago', self._verificar_pago)
        self._boton(barra, 'Preparar', self._preparar_envio)
        self._boton(barra, 'Despachar', self._despachar)
        self._boton(barra, 'Entregar', self._entregar)
        self.tabla_transacciones = self._tabla(panel, [
            ('id', 'ID', 70), ('comprador', 'Comprador', 160),
            ('subtotal', 'Subtotal', 120), ('comision', 'Comisión 5 %', 120),
            ('total', 'Total', 115), ('pago', 'Pago', 115),
            ('envio', 'Envío', 125),
        ])
        self.tabla_transacciones.bind('<Double-1>', lambda _e: self._detalle_transaccion())

    def _crear_ayuda(self):
        """Pestaña de ayuda con exportación/importación y reinicio de demo."""
        panel = self._nueva_pestana('Ayuda y datos')
        self._barra(panel, 'Ayuda y almacenamiento',
                    'Las dos versiones se ejecutan con Python, sin instalar paquetes.')
        texto = (
            'USO PRINCIPAL\n'
            '1. Cambia el usuario activo desde el selector superior.\n'
            '2. Para vender, entra a Catálogo > Publicar artículo.\n'
            '3. Marca Nuevo para indicar garantía, o Usado para indicar conservación.\n'
            '4. Para comprar, selecciona un producto y pulsa Agregar al carrito.\n'
            '5. Crea la transacción desde Carrito y procésala desde Pagos y envíos.\n\n'
            'IMPORTANTE\n'
            '• El programa es una simulación: no cobra dinero real.\n'
            '• Comisión del marketplace: 5 % del subtotal, pagada por el comprador.\n'
            '• El vendedor recibe solo el valor de sus productos.\n'
            '• Perfiles, productos, carritos y compras se guardan en datos_fiufiu.json.\n'
            '• El archivo aparece junto a los scripts de cada edición.\n'
            '• Cada edición usa su propio archivo JSON.\n\n'
            'COPIA DE SEGURIDAD\n'
            'Puedes exportar tus datos a un JSON y recuperarlos mediante Importar.\n'
            'Restablecer borra el estado actual y recupera los tres usuarios de prueba.'
        )
        ttk.Label(panel, text=texto, justify='left').pack(anchor='w', pady=(8, 18))
        acciones = ttk.Frame(panel)
        acciones.pack(anchor='w')
        self._boton(acciones, 'Guardar JSON ahora', self._guardar_manual, True)
        self._boton(acciones, 'Exportar JSON...', self._exportar_json)
        self._boton(acciones, 'Importar JSON...', self._importar_json)
        self._boton(acciones, 'Restablecer demostración', self._restablecer)
        ttk.Label(panel, text=f'Guardado automático: {self.ruta_datos}',
                  style='Secundaria.TLabel').pack(anchor='w', pady=16)

    # -------------------------- Selección y refresco --------------------------
    @staticmethod
    def _limpiar_tabla(vista: ttk.Treeview) -> None:
        """Borra filas antes de volver a cargarlas con datos actualizados."""
        for fila in vista.get_children():
            vista.delete(fila)

    @staticmethod
    def _restaurar_seleccion(tabla: ttk.Treeview, anterior: tuple) -> None:
        """Conserva la fila marcada cuando una tabla se vuelve a dibujar."""
        if anterior and tabla.exists(anterior[0]):
            tabla.selection_set(anterior[0])
            tabla.focus(anterior[0])
            tabla.see(anterior[0])

    @staticmethod
    def _codigo_seleccionado(tabla: ttk.Treeview, descripcion: str) -> str:
        """Devuelve el ID de la fila seleccionada o explica qué falta."""
        seleccionado = tabla.selection()
        if not seleccionado:
            raise ValueError(f'Selecciona primero {descripcion} en la tabla.')
        return seleccionado[0]

    def _usuario(self) -> Usuario:
        """Busca al usuario activo; esta persona compra y marca favoritos."""
        identificador = self._selecciones_usuarios.get(self.usuario_actual.get(), '')
        usuario = self.market.buscar_usuario(identificador)
        if usuario is None:
            raise ValueError('Selecciona un usuario activo.')
        return usuario

    def _cambiar_usuario(self, _evento=None) -> None:
        """Cambia el comprador activo y actualiza las vistas personales."""
        self._actualizar_carrito()
        self._actualizar_favoritos()
        self._actualizar_dashboard()
        self.mensaje_estado.set('Usuario activo actualizado.')

    def _actualizar_todo(self) -> None:
        """Refresca todas las tablas después de registrar cualquier cambio."""
        self._actualizar_usuarios()
        self._actualizar_articulos()
        self._actualizar_carrito()
        self._actualizar_favoritos()
        self._actualizar_transacciones()
        self._actualizar_dashboard()

    def _actualizar_usuarios(self) -> None:
        """Actualiza tabla y selector conservando el usuario elegido."""
        antiguo = getattr(self, '_selecciones_usuarios', {}).get(self.usuario_actual.get())
        self._selecciones_usuarios = {
            f'{u.id} · {u.nombre}': u.id for u in self.market.usuarios.values()
        }
        opciones = list(self._selecciones_usuarios)
        self.selector_usuario['values'] = opciones
        mantener = next((label for label, id_user in self._selecciones_usuarios.items()
                         if id_user == antiguo), None)
        self.usuario_actual.set(mantener or (opciones[0] if opciones else ''))
        self._limpiar_tabla(self.tabla_usuarios)
        for usuario in self.market.usuarios.values():
            self.tabla_usuarios.insert('', 'end', iid=usuario.id, values=(
                usuario.id, usuario.nombre, usuario.correo, dinero(usuario.saldo_ventas)))

    def _actualizar_articulos(self) -> None:
        """Muestra publicaciones filtradas, incluidos tipo y condición/garantía."""
        if not hasattr(self, 'tabla_articulos'):
            return  # El buscador puede activarse durante la construcción inicial.
        anterior = self.tabla_articulos.selection()
        self._limpiar_tabla(self.tabla_articulos)
        filtro = self.busqueda.get().strip().casefold()
        for a in self.market.articulos.values():
            if filtro and filtro not in (a.codigo + ' ' + a.nombre + ' ' +
                                        a.obtener_tipo() + ' ' + a.obtener_detalle()).casefold():
                continue
            self.tabla_articulos.insert('', 'end', iid=a.codigo, values=(
                a.codigo, a.nombre, a.obtener_tipo(), a.obtener_detalle(),
                dinero(a.precio), a.stock, a.vendedor.nombre))
        self._restaurar_seleccion(self.tabla_articulos, anterior)

    def _actualizar_carrito(self) -> None:
        """Solo muestra las líneas del carrito del usuario activo."""
        self._limpiar_tabla(self.tabla_carrito)
        try:
            usuario = self._usuario()
        except ValueError:
            self.etiqueta_subtotal['text'] = 'Subtotal: $0'
            return
        for item in usuario.carrito.items:
            self.tabla_carrito.insert('', 'end', iid=item.articulo.codigo, values=(
                item.articulo.codigo, item.articulo.nombre, item.cantidad,
                dinero(item.precio_unitario), dinero(item.subtotal)))
        self.etiqueta_subtotal['text'] = f'Subtotal: {dinero(usuario.carrito.subtotal)}'

    def _actualizar_favoritos(self) -> None:
        """Resuelve los códigos favoritos a sus publicaciones originales."""
        self._limpiar_tabla(self.tabla_favoritos)
        try:
            usuario = self._usuario()
        except ValueError:
            return
        for a in self.market.articulos.values():
            if a.codigo in usuario.favoritos:
                self.tabla_favoritos.insert('', 'end', iid=a.codigo,
                    values=(a.codigo, a.nombre, a.obtener_tipo(),
                            dinero(a.precio), a.stock))

    def _actualizar_transacciones(self) -> None:
        """Presenta estados de pago y envío de todas las compras registradas."""
        anterior = self.tabla_transacciones.selection()
        self._limpiar_tabla(self.tabla_transacciones)
        for t in self.market.transacciones.values():
            self.tabla_transacciones.insert('', 'end', iid=t.id, values=(
                t.id, t.comprador.nombre, dinero(t.subtotal), dinero(t.comision),
                dinero(t.total_cobrado), t.estado_pago.value, t.estado_envio.value))
        self._restaurar_seleccion(self.tabla_transacciones, anterior)

    def _actualizar_dashboard(self) -> None:
        """Actualiza las estadísticas globales y las del usuario seleccionado."""
        valores = {
            'usuarios': str(len(self.market.usuarios)),
            'articulos': str(len(self.market.articulos)),
            'transacciones': str(len(self.market.transacciones)),
            'comisiones': dinero(self.market.calcular_comisiones_cobradas()),
        }
        for clave, valor in valores.items():
            self.tarjetas[clave]['text'] = valor
        try:
            u = self._usuario()
        except ValueError:
            self.resumen_usuario['text'] = 'Aún no hay usuarios.'
            return
        self.resumen_usuario['text'] = f'Usuario actual: {u.nombre} ({u.id})'
        self.resumen_carrito['text'] = (f'Carrito: {len(u.carrito.items)} tipos de productos '
                                      f'· Subtotal {dinero(u.carrito.subtotal)}')
        self.resumen_favoritos['text'] = f'Artículos favoritos: {len(u.favoritos)}'
        self.resumen_ventas['text'] = f'Ingresos como vendedor: {dinero(u.saldo_ventas)}'

    def _ejecutar(self, funcion, correcto: str) -> bool:
        """Ejecuta una acción, notifica errores y guarda el nuevo estado."""
        try:
            funcion()
        except (ValueError, KeyError, TypeError) as exc:
            # Una autorización rechazada sí cambia el estado a RECHAZADO.
            # Por eso también guardamos cuando una operación controlada falla.
            self._guardar_automatico()
            self._actualizar_todo()
            messagebox.showerror('No se pudo completar', str(exc))
            return False
        self._guardar_automatico()
        self._actualizar_todo()
        self.mensaje_estado.set(correcto)
        return True

    def _guardar_automatico(self) -> None:
        """Persiste cambios inmediatamente, incluso si no se exporta nada."""
        try:
            guardar(self.market, self.ruta_datos)
        except OSError as exc:
            messagebox.showwarning('No se pudo guardar',
                                   f'Los datos siguen en memoria, pero no se guardaron:\n{exc}')

    # ------------------------------ Formularios -------------------------------
    def _registrar_usuario(self) -> None:
        """Muestra un formulario modal para registrar una persona."""
        dialogo = tk.Toplevel(self)
        self._preparar_dialogo(dialogo, 'Registrar usuario', 425, 285)
        entradas = self._campos_texto(dialogo, [('ID (ej. U004)', 'id'),
                                                ('Nombre', 'nombre'),
                                                ('Correo electrónico', 'correo')])

        def guardar_usuario():
            datos = {k: v.get().strip() for k, v in entradas.items()}
            ok = self._ejecutar(lambda: self.market.registrar_usuario(
                Usuario(datos['id'], datos['nombre'], datos['correo'])),
                'Usuario registrado correctamente.')
            if ok:
                dialogo.destroy()

        self._boton_modal(dialogo, 'Registrar usuario', guardar_usuario, 12)
        entradas['id'].focus_set()

    def _publicar_articulo(self) -> None:
        """Solicita tipo Nuevo/Usado y cambia el campo adicional dinámicamente."""
        if not self.market.usuarios:
            messagebox.showerror('No hay vendedores', 'Registra un usuario antes de publicar.')
            return
        dialogo = tk.Toplevel(self)
        self._preparar_dialogo(dialogo, 'Publicar artículo', 490, 535)
        formulario = ttk.Frame(dialogo, padding=(16, 5))
        formulario.pack(fill='x')
        campos = {}

        def entrada(etiqueta, clave, inicial=''):
            ttk.Label(formulario, text=etiqueta).pack(anchor='w', pady=(8, 2))
            variable = tk.StringVar(value=inicial)
            ttk.Entry(formulario, textvariable=variable).pack(fill='x')
            campos[clave] = variable

        entrada('Código del producto', 'codigo')
        entrada('Nombre del producto', 'nombre')
        entrada('Precio en pesos (entero)', 'precio')
        entrada('Stock inicial', 'stock', '1')

        ttk.Label(formulario, text='Vendedor').pack(anchor='w', pady=(8, 2))
        vendedor_var = tk.StringVar(value=self.usuario_actual.get())
        ttk.Combobox(formulario, values=list(self._selecciones_usuarios),
                     state='readonly', textvariable=vendedor_var).pack(fill='x')

        ttk.Label(formulario, text='Condición del artículo').pack(anchor='w', pady=(8, 2))
        tipo_var = tk.StringVar(value='Nuevo')
        ttk.Combobox(formulario, values=['Nuevo', 'Usado'],
                     textvariable=tipo_var, state='readonly').pack(fill='x')
        ttk.Label(formulario, text='Dato adicional:').pack(anchor='w', pady=(8, 2))
        etiqueta_extra = ttk.Label(formulario, text='Meses de garantía')
        etiqueta_extra.pack(anchor='w')
        extra_var = tk.StringVar(value='12')
        ttk.Entry(formulario, textvariable=extra_var).pack(fill='x')

        def cambiar_condicion(*_):
            # Requisito solicitado: mostrar garantía solo en nuevos y
            # conservación solo en usados, en el momento de crear el producto.
            if tipo_var.get() == 'Nuevo':
                etiqueta_extra.config(text='Meses de garantía (0 o más)')
                extra_var.set('12')
            else:
                etiqueta_extra.config(text='Estado de conservación (ej. Buen estado)')
                extra_var.set('Buen estado')

        tipo_var.trace_add('write', cambiar_condicion)
        cambiar_condicion()

        def publicar():
            def operacion():
                vendedor = self.market.buscar_usuario(
                    self._selecciones_usuarios.get(vendedor_var.get(), ''))
                if vendedor is None:
                    raise ValueError('Selecciona un vendedor válido.')
                try:
                    precio, stock = int(campos['precio'].get()), int(campos['stock'].get())
                except ValueError:
                    raise ValueError('Precio y stock deben ser números enteros.')
                datos = (campos['codigo'].get(), campos['nombre'].get(),
                         precio, stock, vendedor)
                if tipo_var.get() == 'Nuevo':
                    try:
                        garantia = int(extra_var.get())
                    except ValueError:
                        raise ValueError('La garantía debe ser un número entero.')
                    producto = ArticuloNuevo(*datos, garantia)
                else:
                    producto = ArticuloUsado(*datos, extra_var.get())
                self.market.publicar_articulo(producto)
            if self._ejecutar(operacion, 'Artículo publicado correctamente.'):
                dialogo.destroy()

        self._boton_modal(dialogo, 'Publicar producto', publicar, 15)

    def _preparar_dialogo(self, dialogo: tk.Toplevel, titulo: str,
                          ancho: int, alto: int) -> None:
        """Deja el formulario encima de la aplicación y fija su tamaño inicial."""
        dialogo.title(titulo)
        dialogo.geometry(f'{ancho}x{alto}')
        dialogo.resizable(False, False)
        dialogo.configure(bg=CONFIG['fondo'])
        dialogo.transient(self)
        dialogo.grab_set()
        ttk.Label(dialogo, text=titulo, style='Seccion.TLabel').pack(
            anchor='w', padx=17, pady=(15, 5))

    @staticmethod
    def _boton_modal(dialogo: tk.Toplevel, texto: str, accion, margen: int) -> None:
        """Botón Tk nativo en formularios para evitar recortes de texto en ttk."""
        if CONFIG['decorado']:
            tk.Button(dialogo, text=texto, command=accion, font=('DejaVu Sans', 9, 'bold'),
                      bg='#147f8b', fg='white', activebackground='#0c626c',
                      activeforeground='white', bd=1, relief='flat',
                      padx=16, pady=7, cursor='hand2').pack(pady=margen)
        else:
            # Botón por defecto del sistema, sin estilos personalizados.
            ttk.Button(dialogo, text=texto, command=accion).pack(pady=margen)

    @staticmethod
    def _campos_texto(dialogo: tk.Toplevel, definiciones):
        """Construye etiquetas y entradas para un formulario sencillo."""
        panel = ttk.Frame(dialogo, padding=(16, 4))
        panel.pack(fill='x')
        variables = {}
        for texto, clave in definiciones:
            ttk.Label(panel, text=texto).pack(anchor='w', pady=(8, 2))
            var = tk.StringVar()
            ttk.Entry(panel, textvariable=var).pack(fill='x')
            variables[clave] = var
        return variables

    # ----------------------------- Acciones catálogo ---------------------------
    def _articulo_seleccionado(self):
        """Obtiene el objeto completo del artículo marcado en el catálogo."""
        codigo = self._codigo_seleccionado(self.tabla_articulos, 'un artículo')
        return self.market.buscar_articulo(codigo)

    def _detalles_articulo(self) -> None:
        """Muestra una ficha individual del producto."""
        try:
            a = self._articulo_seleccionado()
        except ValueError as exc:
            messagebox.showinfo('Selecciona un artículo', str(exc))
            return
        messagebox.showinfo('Ficha del artículo', str(a))

    def _agregar_carrito_articulo(self, articulo) -> None:
        """Pregunta cantidad y solicita agregarla al carrito del usuario actual."""
        try:
            usuario = self._usuario()
        except ValueError as exc:
            messagebox.showerror('Usuario', str(exc))
            return
        cantidad = simpledialog.askinteger('Agregar al carrito',
                    f'{articulo.nombre}\nCantidad de unidades:',
                    initialvalue=1, minvalue=1, parent=self)
        if cantidad is None:
            return  # Cancelar no altera nada.
        self._ejecutar(lambda: usuario.agregar_al_carrito(articulo, cantidad),
                       f'Se agregó {articulo.nombre} al carrito de {usuario.nombre}.')

    def _agregar_carrito(self) -> None:
        try:
            self._agregar_carrito_articulo(self._articulo_seleccionado())
        except ValueError as exc:
            messagebox.showinfo('Selecciona un artículo', str(exc))

    def _alternar_favorito(self) -> None:
        """Añade o quita el favorito seleccionado para el usuario activo."""
        try:
            a, u = self._articulo_seleccionado(), self._usuario()
        except ValueError as exc:
            messagebox.showinfo('Falta información', str(exc))
            return
        if a.codigo in u.favoritos:
            self._ejecutar(lambda: u.quitar_favorito(a.codigo), 'Se quitó de favoritos.')
        else:
            self._ejecutar(lambda: u.agregar_favorito(a), 'Se agregó a favoritos.')

    def _reponer_stock(self) -> None:
        """Solo el vendedor original puede reponer unidades de su publicación."""
        try:
            a, u = self._articulo_seleccionado(), self._usuario()
            if a.vendedor is not u:
                raise ValueError('Selecciona al vendedor del artículo para reponerlo.')
        except ValueError as exc:
            messagebox.showinfo('Reposición no disponible', str(exc))
            return
        cantidad = simpledialog.askinteger('Reponer stock',
                    f'{a.nombre}\n¿Cuántas unidades agregas?',
                    minvalue=1, parent=self)
        if cantidad is not None:
            self._ejecutar(lambda: a.agregar_stock(cantidad), 'Stock actualizado.')

    def _cambiar_precio(self) -> None:
        """El vendedor puede cambiar el precio de futuras compras."""
        try:
            a, u = self._articulo_seleccionado(), self._usuario()
            if a.vendedor is not u:
                raise ValueError('Solo el vendedor del artículo puede cambiar su precio.')
        except ValueError as exc:
            messagebox.showinfo('Cambio no disponible', str(exc))
            return
        valor = simpledialog.askinteger('Cambiar precio',
                    f'Precio actual: {dinero(a.precio)}\nNuevo precio en pesos:',
                    initialvalue=a.precio, minvalue=1, parent=self)
        if valor is not None:
            self._ejecutar(lambda: a.cambiar_precio(valor), 'Precio actualizado.')

    # -------------------------- Acciones carrito/favoritos ---------------------
    def _quitar_carrito(self) -> None:
        try:
            codigo = self._codigo_seleccionado(self.tabla_carrito, 'una línea del carrito')
            u = self._usuario()
        except ValueError as exc:
            messagebox.showinfo('Carrito', str(exc))
            return
        self._ejecutar(lambda: u.carrito.eliminar_articulo(codigo),
                       'Artículo eliminado del carrito.')

    def _crear_transaccion(self) -> None:
        """Crea compra con el carrito y lleva a la pestaña de transacciones."""
        try:
            u = self._usuario()
        except ValueError as exc:
            messagebox.showerror('Usuario', str(exc))
            return
        if self._ejecutar(lambda: self.market.crear_transaccion(u),
                          'Transacción creada. Autoriza su pago en Pagos y envíos.'):
            self.pestanas.select(5)  # La sexta pestaña es Pagos y envíos.

    def _favorito_a_carrito(self) -> None:
        try:
            codigo = self._codigo_seleccionado(self.tabla_favoritos, 'un favorito')
            self._agregar_carrito_articulo(self.market.buscar_articulo(codigo))
        except ValueError as exc:
            messagebox.showinfo('Favoritos', str(exc))

    def _quitar_favorito(self) -> None:
        try:
            codigo = self._codigo_seleccionado(self.tabla_favoritos, 'un favorito')
            u = self._usuario()
        except ValueError as exc:
            messagebox.showinfo('Favoritos', str(exc))
            return
        self._ejecutar(lambda: u.quitar_favorito(codigo), 'Favorito eliminado.')

    # ------------------------------ Pagos/envíos -------------------------------
    def _transaccion_seleccionada(self):
        """Obtiene la compra marcada en la tabla de transacciones."""
        codigo = self._codigo_seleccionado(self.tabla_transacciones, 'una transacción')
        return self.market.buscar_transaccion(codigo)

    def _detalle_transaccion(self) -> None:
        """Enseña comprador, líneas, montos, método y estados."""
        try:
            t = self._transaccion_seleccionada()
        except ValueError as exc:
            messagebox.showinfo('Transacciones', str(exc))
            return
        filas = '\n'.join(f'- {i.articulo.nombre}: {i.cantidad} × '
                           f'{dinero(i.precio_unitario)} = {dinero(i.subtotal)}'
                           for i in t.items)
        metodo = t.metodo_pago.obtener_nombre() if t.metodo_pago else 'Sin seleccionar'
        messagebox.showinfo(f'Transacción {t.id}',
            f'Comprador: {t.comprador.nombre}\n\n{filas}\n\n'
            f'Subtotal: {dinero(t.subtotal)}\n'
            f'Comisión FIUFIU (5 %): {dinero(t.comision)}\n'
            f'Total: {dinero(t.total_cobrado)}\n\n'
            f'Medio de pago: {metodo}\nEstado pago: {t.estado_pago.value}\n'
            f'Estado envío: {t.estado_envio.value}')

    def _autorizar_pago(self) -> None:
        """Solicita tarjeta o billetera y saldo para una autorización simulada."""
        try:
            t = self._transaccion_seleccionada()
        except ValueError as exc:
            messagebox.showinfo('Transacciones', str(exc))
            return
        dialogo = tk.Toplevel(self)
        self._preparar_dialogo(dialogo, f'Autorizar pago {t.id}', 430, 265)
        panel = ttk.Frame(dialogo, padding=(17, 7))
        panel.pack(fill='x')
        ttk.Label(panel, text=f'Total a autorizar: {dinero(t.total_cobrado)}',
                  style='Seccion.TLabel').pack(anchor='w', pady=(0, 12))
        ttk.Label(panel, text='Medio de pago (simulado)').pack(anchor='w')
        tipo = tk.StringVar(value='Tarjeta')
        ttk.Combobox(panel, state='readonly', textvariable=tipo,
                     values=['Tarjeta', 'Billetera digital']).pack(fill='x', pady=(3, 11))
        ttk.Label(panel, text='Saldo o cupo disponible (pesos)').pack(anchor='w')
        saldo = tk.StringVar(value=str(t.total_cobrado))
        ttk.Entry(panel, textvariable=saldo).pack(fill='x', pady=(3, 0))

        def autorizar():
            def operacion():
                try:
                    monto = int(saldo.get())
                except ValueError:
                    raise ValueError('Ingresa un saldo entero.')
                metodo = Tarjeta(monto) if tipo.get() == 'Tarjeta' else BilleteraDigital(monto)
                t.autorizar_pago(metodo)
            if self._ejecutar(operacion,
                             'Pago autorizado. Aún debes verificarlo para cobrar y descontar stock.'):
                dialogo.destroy()
            elif t.estado_pago.value == 'Rechazado':
                dialogo.destroy()
        self._boton_modal(dialogo, 'Autorizar (no cobra aún)', autorizar, 10)

    def _aplicar_a_transaccion(self, metodo, mensaje: str) -> None:
        """Ejecuta una transición de la compra seleccionada y refresca estados."""
        try:
            t = self._transaccion_seleccionada()
        except ValueError as exc:
            messagebox.showinfo('Transacciones', str(exc))
            return
        self._ejecutar(lambda: getattr(t, metodo)(), mensaje)

    def _verificar_pago(self) -> None:
        self._aplicar_a_transaccion('verificar_pago',
                                   'Pago verificado: se cobró, descontó stock y abonó al vendedor.')

    def _preparar_envio(self) -> None:
        self._aplicar_a_transaccion('preparar_envio', 'Envío en preparación.')

    def _despachar(self) -> None:
        self._aplicar_a_transaccion('despachar', 'Envío despachado.')

    def _entregar(self) -> None:
        self._aplicar_a_transaccion('confirmar_entrega', 'Entrega confirmada.')

    # ----------------------------- Manejo de archivos --------------------------
    def _guardar_manual(self) -> None:
        """Guarda inmediatamente perfiles y artículos en datos_fiufiu.json."""
        try:
            guardar(self.market, self.ruta_datos)
        except OSError as exc:
            messagebox.showerror('No se pudo guardar JSON', str(exc))
            return
        self.mensaje_estado.set(f'Datos guardados: {self.ruta_datos}')
        messagebox.showinfo('Archivo JSON guardado',
                            f'Se guardaron perfiles, artículos y operaciones en:\n{self.ruta_datos}')

    def _exportar_json(self) -> None:
        """Permite guardar una copia manual en la carpeta elegida por el usuario."""
        ruta = filedialog.asksaveasfilename(parent=self, title='Exportar datos de FIUFIU',
                     defaultextension='.json', filetypes=[('Archivo JSON', '*.json')],
                     initialfile='FIUFIU_respaldo.json')
        if ruta:
            try:
                guardar(self.market, Path(ruta))
                self.mensaje_estado.set(f'Copia guardada en: {ruta}')
            except OSError as exc:
                messagebox.showerror('No se pudo exportar', str(exc))

    def _importar_json(self) -> None:
        """Carga una copia de seguridad solo tras pedir confirmación."""
        ruta = filedialog.askopenfilename(parent=self, title='Importar datos de FIUFIU',
                                         filetypes=[('Archivo JSON', '*.json')])
        if not ruta:
            return
        if not messagebox.askyesno('Reemplazar datos',
                 'Importar reemplazará los datos actuales de esta versión. ¿Continuar?'):
            return
        try:
            nuevo_market = cargar(Path(ruta))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            messagebox.showerror('No se pudo importar', str(exc))
            return
        self.market = nuevo_market
        self._guardar_automatico()
        self._actualizar_todo()
        self.mensaje_estado.set('Copia de seguridad importada.')

    def _restablecer(self) -> None:
        """Recupera los datos de ejemplo después de una confirmación explícita."""
        if not messagebox.askyesno('Restablecer demostración',
             'Esta acción reemplazará los datos actuales. ¿Restablecer los datos de prueba?'):
            return
        self.market = cargar_demostracion()
        self._guardar_automatico()
        self._actualizar_todo()
        self.mensaje_estado.set('Se restauraron los usuarios y artículos de demostración.')


def main() -> None:
    """Punto de entrada de la GUI: no hay comandos ni menús de consola."""
    AppFiufiu().mainloop()


if __name__ == '__main__':
    main()
