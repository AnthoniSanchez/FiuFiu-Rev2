"""Modelo de negocio de FIUFIU, adaptación comentada del proyecto Java.

No depende de Tkinter: esto permite probar las reglas del marketplace sin abrir
ventanas. Conserva la herencia, el polimorfismo y las interfaces mediante ABC.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


# Utilizamos enteros (pesos chilenos) para no introducir errores con decimales.
PORCENTAJE_COMISION = 5  # Cinco por ciento. El Java tenía 10 en el código y 5 en su README.


def dinero(valor: int) -> str:
    """Da formato legible a un monto entero, por ejemplo: $35.000."""
    return '$' + f'{valor:,}'.replace(',', '.')


class EstadoPago(str, Enum):
    """Etapas posibles de la autorización y verificación de un pago."""
    PENDIENTE = 'Pendiente'
    AUTORIZADO = 'Autorizado'
    VERIFICADO = 'Verificado'
    RECHAZADO = 'Rechazado'


class EstadoEnvio(str, Enum):
    """Etapas consecutivas del envío de una compra verificada."""
    PENDIENTE = 'Pendiente'
    PREPARANDO = 'Preparando'
    DESPACHADO = 'Despachado'
    ENTREGADO = 'Entregado'


class Articulo(ABC):
    """Clase abstracta: reúne los datos compartidos por artículos nuevos y usados."""

    def __init__(self, codigo: str, nombre: str, precio: int, stock: int,
                 vendedor: Usuario):
        if not codigo.strip() or not nombre.strip():
            raise ValueError('El código y el nombre del artículo son obligatorios.')
        if precio <= 0:
            raise ValueError('El precio debe ser mayor que cero.')
        if stock < 0:
            raise ValueError('El stock no puede ser negativo.')
        if vendedor is None:
            raise ValueError('Selecciona un vendedor para el artículo.')
        self.codigo = codigo.strip()
        self.nombre = nombre.strip()
        self.precio = precio
        self.stock = stock
        self.vendedor = vendedor

    def hay_stock(self, cantidad: int) -> bool:
        """Comprueba unidades disponibles sin modificar el inventario."""
        return cantidad > 0 and cantidad <= self.stock

    def descontar_stock(self, cantidad: int) -> None:
        """Descuenta unidades solo al verificar el pago."""
        if not self.hay_stock(cantidad):
            raise ValueError(f'Stock insuficiente para «{self.nombre}».')
        self.stock -= cantidad

    def agregar_stock(self, cantidad: int) -> None:
        """Permite reponer unidades sin alterar compras anteriores."""
        if cantidad <= 0:
            raise ValueError('La reposición debe ser mayor que cero.')
        self.stock += cantidad

    def cambiar_precio(self, nuevo_precio: int) -> None:
        """Actualiza el precio para futuras compras; no afecta carritos previos."""
        if nuevo_precio <= 0:
            raise ValueError('El precio debe ser mayor que cero.')
        self.precio = nuevo_precio

    @abstractmethod
    def obtener_tipo(self) -> str:
        """Cada clase hija debe identificar su propio tipo."""

    @abstractmethod
    def obtener_detalle(self) -> str:
        """Cada clase hija muestra información específica."""

    def __str__(self) -> str:
        return (f'[{self.codigo}] {self.nombre} | {self.obtener_tipo()} | '
                f'{dinero(self.precio)} | Stock: {self.stock} | '
                f'Vendedor: {self.vendedor.nombre} | {self.obtener_detalle()}')


class ArticuloNuevo(Articulo):
    """Hereda de Articulo y añade meses de garantía."""

    def __init__(self, codigo: str, nombre: str, precio: int, stock: int,
                 vendedor: Usuario, meses_garantia: int):
        super().__init__(codigo, nombre, precio, stock, vendedor)
        if meses_garantia < 0:
            raise ValueError('La garantía no puede ser negativa.')
        self.meses_garantia = meses_garantia

    def obtener_tipo(self) -> str:
        return 'Nuevo'

    def obtener_detalle(self) -> str:
        return f'Garantía: {self.meses_garantia} meses'


class ArticuloUsado(Articulo):
    """Hereda de Articulo y describe su estado de conservación."""

    def __init__(self, codigo: str, nombre: str, precio: int, stock: int,
                 vendedor: Usuario, estado_conservacion: str):
        super().__init__(codigo, nombre, precio, stock, vendedor)
        if not estado_conservacion.strip():
            raise ValueError('Indica el estado de conservación del artículo.')
        self.estado_conservacion = estado_conservacion.strip()

    def obtener_tipo(self) -> str:
        return 'Usado'

    def obtener_detalle(self) -> str:
        return f'Conservación: {self.estado_conservacion}'


@dataclass
class ItemCarrito:
    """Una línea del carrito; conserva el precio cuando se agregó el producto."""
    articulo: Articulo
    cantidad: int
    precio_unitario: int

    def __post_init__(self) -> None:
        if self.cantidad <= 0 or self.precio_unitario <= 0:
            raise ValueError('Cantidad y precio unitario deben ser positivos.')

    @property
    def subtotal(self) -> int:
        """Monto de la línea, sin alterar el stock."""
        return self.cantidad * self.precio_unitario

    def copiar(self) -> ItemCarrito:
        """Copia cantidad y precio para congelar los detalles de una compra."""
        return ItemCarrito(self.articulo, self.cantidad, self.precio_unitario)


class Carrito:
    """Colección de artículos del comprador, pendiente de pago."""

    def __init__(self) -> None:
        self.items: list[ItemCarrito] = []

    def agregar_articulo(self, articulo: Articulo, cantidad: int) -> None:
        """Agrega unidades o incrementa una línea existente, comprobando el stock."""
        if cantidad <= 0:
            raise ValueError('La cantidad debe ser mayor que cero.')
        existente = next((i for i in self.items
                         if i.articulo.codigo.casefold() == articulo.codigo.casefold()), None)
        total_solicitado = cantidad + (existente.cantidad if existente else 0)
        if not articulo.hay_stock(total_solicitado):
            raise ValueError('No hay stock suficiente para agregar esa cantidad.')
        if existente:
            existente.cantidad = total_solicitado
        else:
            self.items.append(ItemCarrito(articulo, cantidad, articulo.precio))

    def eliminar_articulo(self, codigo: str) -> None:
        """Quita un producto del carrito, si existe."""
        anterior = len(self.items)
        self.items = [i for i in self.items if i.articulo.codigo.casefold() != codigo.casefold()]
        if len(self.items) == anterior:
            raise ValueError('El artículo no estaba en el carrito.')

    @property
    def subtotal(self) -> int:
        """Suma los subtotales de todas las líneas."""
        return sum(i.subtotal for i in self.items)

    def copiar_items(self) -> list[ItemCarrito]:
        """Genera una instantánea de las líneas del carrito."""
        return [i.copiar() for i in self.items]

    def vaciar(self) -> None:
        self.items.clear()


class Usuario:
    """Una sola persona puede comprar y vender, igual que en el proyecto Java."""

    def __init__(self, id_usuario: str, nombre: str, correo: str):
        if not id_usuario.strip() or not nombre.strip() or not correo.strip():
            raise ValueError('ID, nombre y correo son obligatorios.')
        if '@' not in correo or correo.startswith('@') or correo.endswith('@'):
            raise ValueError('Escribe un correo electrónico válido.')
        self.id = id_usuario.strip()
        self.nombre = nombre.strip()
        self.correo = correo.strip()
        self.saldo_ventas = 0
        self.carrito = Carrito()
        self.favoritos: set[str] = set()  # Guardamos códigos únicos, no copias del artículo.

    def agregar_al_carrito(self, articulo: Articulo, cantidad: int) -> None:
        """Impide que un usuario compre su propia publicación."""
        if articulo.vendedor is self:
            raise ValueError('No puedes comprar tu propio artículo.')
        self.carrito.agregar_articulo(articulo, cantidad)

    def agregar_favorito(self, articulo: Articulo) -> None:
        """Marca un producto como favorito, sin duplicarlo."""
        self.favoritos.add(articulo.codigo)

    def quitar_favorito(self, codigo: str) -> None:
        """Elimina un artículo de favoritos, si está marcado."""
        self.favoritos.discard(codigo)

    def recibir_venta(self, monto: int) -> None:
        """Aumenta los ingresos del vendedor después de verificar el pago."""
        if monto > 0:
            self.saldo_ventas += monto


class MetodoPago(ABC):
    """Interfaz abstracta: tarjeta y billetera deben autorizar y cobrar."""

    def __init__(self, saldo: int):
        if saldo < 0:
            raise ValueError('El saldo o cupo no puede ser negativo.')
        self.saldo = saldo

    def autorizar(self, monto: int) -> bool:
        """Solo comprueba fondos; aquí NO se descuenta dinero."""
        return 0 < monto <= self.saldo

    def cobrar(self, monto: int) -> None:
        """Descuenta el total cuando la transacción se verifica."""
        if not self.autorizar(monto):
            raise ValueError(f'Fondos insuficientes en {self.obtener_nombre()}.')
        self.saldo -= monto

    @abstractmethod
    def obtener_nombre(self) -> str:
        """Retorna el nombre visible del medio de pago."""


class Tarjeta(MetodoPago):
    """Medio de pago simulado que usa cupo disponible."""
    def obtener_nombre(self) -> str:
        return 'Tarjeta'


class BilleteraDigital(MetodoPago):
    """Medio de pago simulado que utiliza saldo digital."""
    def obtener_nombre(self) -> str:
        return 'Billetera digital'


class Enviable(ABC):
    """Interfaz que exige las tres transiciones de un envío."""

    @abstractmethod
    def preparar_envio(self) -> None:
        pass

    @abstractmethod
    def despachar(self) -> None:
        pass

    @abstractmethod
    def confirmar_entrega(self) -> None:
        pass


class Transaccion(Enviable):
    """Captura el carrito y controla autorización, cobro y envío por etapas."""

    def __init__(self, id_transaccion: str, comprador: Usuario,
                 items: list[ItemCarrito]):
        if not items:
            raise ValueError('No se puede crear una transacción con el carrito vacío.')
        self.id = id_transaccion
        self.comprador = comprador
        self.items = [i.copiar() for i in items]
        self.metodo_pago: Optional[MetodoPago] = None
        self.estado_pago = EstadoPago.PENDIENTE
        self.estado_envio = EstadoEnvio.PENDIENTE
        self.subtotal = sum(i.subtotal for i in self.items)
        # Redondeo de mitades hacia arriba para montos positivos (como Math.round).
        self.comision = (self.subtotal * PORCENTAJE_COMISION + 50) // 100
        self.total_cobrado = self.subtotal + self.comision

    def validar_stock(self) -> None:
        """Comprueba disponibilidad antes de autorizar y verificar el pago."""
        for item in self.items:
            if not item.articulo.hay_stock(item.cantidad):
                raise ValueError(f'Stock insuficiente para «{item.articulo.nombre}».')

    def autorizar_pago(self, metodo: MetodoPago) -> None:
        """Primera etapa: verifica stock y fondos, pero no descuenta nada."""
        if self.estado_pago != EstadoPago.PENDIENTE:
            raise ValueError('El pago ya fue procesado.')
        self.validar_stock()
        self.metodo_pago = metodo
        if not metodo.autorizar(self.total_cobrado):
            self.estado_pago = EstadoPago.RECHAZADO
            raise ValueError('Pago rechazado: saldo o cupo insuficiente.')
        self.estado_pago = EstadoPago.AUTORIZADO

    def verificar_pago(self) -> None:
        """Segunda etapa: cobra, reduce stock y paga a los vendedores."""
        if self.estado_pago != EstadoPago.AUTORIZADO or self.metodo_pago is None:
            raise ValueError('Primero debes autorizar el pago.')
        # Validamos todo ANTES de comenzar los descuentos.
        self.validar_stock()
        if not self.metodo_pago.autorizar(self.total_cobrado):
            raise ValueError('El medio de pago ya no dispone de fondos suficientes.')
        self.metodo_pago.cobrar(self.total_cobrado)
        for item in self.items:
            item.articulo.descontar_stock(item.cantidad)
            item.articulo.vendedor.recibir_venta(item.subtotal)
        self.estado_pago = EstadoPago.VERIFICADO

    def preparar_envio(self) -> None:
        """Solo se permite empezar el envío con pago verificado."""
        if self.estado_pago != EstadoPago.VERIFICADO:
            raise ValueError('Verifica el pago antes de preparar el envío.')
        self._pasar_envio(EstadoEnvio.PENDIENTE, EstadoEnvio.PREPARANDO)

    def despachar(self) -> None:
        """Avanza de Preparando a Despachado."""
        self._pasar_envio(EstadoEnvio.PREPARANDO, EstadoEnvio.DESPACHADO)

    def confirmar_entrega(self) -> None:
        """Avanza de Despachado a Entregado."""
        self._pasar_envio(EstadoEnvio.DESPACHADO, EstadoEnvio.ENTREGADO)

    def _pasar_envio(self, esperado: EstadoEnvio, siguiente: EstadoEnvio) -> None:
        if self.estado_envio != esperado:
            raise ValueError(f'No se puede pasar de «{self.estado_envio.value}» '
                             f'a «{siguiente.value}».')
        self.estado_envio = siguiente

    @property
    def tiene_comision_cobrada(self) -> bool:
        """Las comisiones pendientes o rechazadas no generan ingresos."""
        return self.estado_pago == EstadoPago.VERIFICADO


class Marketplace:
    """Coordina usuarios, publicaciones y transacciones del sistema."""

    def __init__(self):
        self.usuarios: dict[str, Usuario] = {}
        self.articulos: dict[str, Articulo] = {}
        self.transacciones: dict[str, Transaccion] = {}
        self.siguiente_transaccion = 1

    @staticmethod
    def _clave(valor: str) -> str:
        """Permite búsquedas sin diferenciar mayúsculas/minúsculas."""
        return valor.strip().casefold()

    def registrar_usuario(self, usuario: Usuario) -> None:
        if self.buscar_usuario(usuario.id):
            raise ValueError('Ya existe un usuario con ese ID.')
        self.usuarios[self._clave(usuario.id)] = usuario

    def publicar_articulo(self, articulo: Articulo) -> None:
        if self.buscar_articulo(articulo.codigo):
            raise ValueError('Ya existe un artículo con ese código.')
        self.articulos[self._clave(articulo.codigo)] = articulo

    def buscar_usuario(self, id_usuario: str) -> Optional[Usuario]:
        return self.usuarios.get(self._clave(id_usuario))

    def buscar_articulo(self, codigo: str) -> Optional[Articulo]:
        return self.articulos.get(self._clave(codigo))

    def buscar_transaccion(self, id_transaccion: str) -> Optional[Transaccion]:
        return self.transacciones.get(self._clave(id_transaccion))

    def crear_transaccion(self, comprador: Usuario) -> Transaccion:
        """Conserva una copia del carrito y lo vacía al iniciar la transacción."""
        if not comprador.carrito.items:
            raise ValueError('El carrito está vacío.')
        transaccion = Transaccion(f'T{self.siguiente_transaccion:03}',
                                 comprador, comprador.carrito.copiar_items())
        self.siguiente_transaccion += 1
        self.transacciones[self._clave(transaccion.id)] = transaccion
        comprador.carrito.vaciar()
        return transaccion

    def calcular_comisiones_cobradas(self) -> int:
        """Suma únicamente las comisiones de pagos verificados."""
        return sum(t.comision for t in self.transacciones.values()
                   if t.tiene_comision_cobrada)


def cargar_demostracion() -> Marketplace:
    """Crea los mismos tres usuarios y tres artículos del proyecto Java."""
    market = Marketplace()
    ana = Usuario('U001', 'Ana', 'ana@fiufiu.cl')
    benjamin = Usuario('U002', 'Benjamín', 'benja@fiufiu.cl')
    camila = Usuario('U003', 'Camila', 'camila@fiufiu.cl')
    for usuario in (ana, benjamin, camila):
        market.registrar_usuario(usuario)
    for articulo in (
        ArticuloNuevo('A001', 'Teclado mecánico', 35000, 5, benjamin, 12),
        ArticuloUsado('A002', 'Audífonos gamer', 18000, 3, camila, 'Buen estado'),
        ArticuloNuevo('A003', 'Mouse inalámbrico', 15000, 8, ana, 6),
    ):
        market.publicar_articulo(articulo)
    return market
