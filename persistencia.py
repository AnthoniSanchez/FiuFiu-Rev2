"""Guardar y recuperar el marketplace como JSON, sin instalar dependencias.

El JSON conserva relaciones mediante identificadores (IDs/códigos) y mantiene
los precios capturados en el carrito y en cada transacción.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

from modelos import (ArticuloNuevo, ArticuloUsado, BilleteraDigital, EstadoEnvio,
                     EstadoPago, ItemCarrito, Marketplace, Tarjeta, Transaccion,
                     Usuario)

VERSION_FORMATO = 1


def _fila_item(item: ItemCarrito) -> dict:
    """Convierte una línea del carrito a un diccionario serializable."""
    return {'articulo': item.articulo.codigo, 'cantidad': item.cantidad,
            'precio_unitario': item.precio_unitario}


def exportar_datos(market: Marketplace) -> dict:
    """Transforma todo el estado del programa a datos JSON simples."""
    usuarios = []
    for u in market.usuarios.values():
        usuarios.append({
            'id': u.id, 'nombre': u.nombre, 'correo': u.correo,
            'saldo_ventas': u.saldo_ventas,
            'favoritos': sorted(u.favoritos),
            'carrito': [_fila_item(item) for item in u.carrito.items],
        })

    articulos = []
    for a in market.articulos.values():
        d = {'codigo': a.codigo, 'nombre': a.nombre, 'precio': a.precio,
             'stock': a.stock, 'vendedor': a.vendedor.id, 'tipo': a.obtener_tipo()}
        if isinstance(a, ArticuloNuevo):
            d['meses_garantia'] = a.meses_garantia
        else:
            d['estado_conservacion'] = a.estado_conservacion
        articulos.append(d)

    transacciones = []
    for t in market.transacciones.values():
        metodo = None
        if t.metodo_pago:
            metodo = {'tipo': t.metodo_pago.obtener_nombre(),
                      'saldo': t.metodo_pago.saldo}
        transacciones.append({
            'id': t.id, 'comprador': t.comprador.id,
            'items': [_fila_item(i) for i in t.items],
            'estado_pago': t.estado_pago.value,
            'estado_envio': t.estado_envio.value,
            'metodo_pago': metodo,
        })

    return {'version': VERSION_FORMATO, 'siguiente_transaccion': market.siguiente_transaccion,
            'usuarios': usuarios, 'articulos': articulos, 'transacciones': transacciones}


def importar_datos(datos: dict) -> Marketplace:
    """Reconstruye objetos y referencias a partir de un archivo guardado."""
    if datos.get('version') != VERSION_FORMATO:
        raise ValueError('Versión del archivo incompatible con esta aplicación.')
    market = Marketplace()

    # 1) Primero los usuarios; los artículos necesitan referencias al vendedor.
    for d in datos['usuarios']:
        usuario = Usuario(d['id'], d['nombre'], d['correo'])
        usuario.saldo_ventas = int(d['saldo_ventas'])
        if usuario.saldo_ventas < 0:
            raise ValueError('Saldo de ventas no válido en el archivo.')
        market.registrar_usuario(usuario)

    # 2) Después las publicaciones, que se vinculan con su vendedor original.
    for d in datos['articulos']:
        vendedor = market.buscar_usuario(d['vendedor'])
        if vendedor is None:
            raise ValueError('Falta un vendedor referenciado en el archivo.')
        campos = (d['codigo'], d['nombre'], int(d['precio']), int(d['stock']), vendedor)
        if d['tipo'] == 'Nuevo':
            articulo = ArticuloNuevo(*campos, int(d['meses_garantia']))
        elif d['tipo'] == 'Usado':
            articulo = ArticuloUsado(*campos, d['estado_conservacion'])
        else:
            raise ValueError('Tipo de artículo desconocido en el archivo.')
        market.publicar_articulo(articulo)

    def recuperar_items(filas: list[dict]) -> list[ItemCarrito]:
        """Restablece líneas de carrito sin sobrescribir precios históricos."""
        items = []
        for d in filas:
            articulo = market.buscar_articulo(d['articulo'])
            if articulo is None:
                raise ValueError('Se encontró un artículo inexistente en el archivo.')
            items.append(ItemCarrito(articulo, int(d['cantidad']),
                                     int(d['precio_unitario'])))
        return items

    # 3) Carritos y favoritos, después de reconstruir artículos.
    for d in datos['usuarios']:
        usuario = market.buscar_usuario(d['id'])
        usuario.carrito.items = recuperar_items(d['carrito'])
        for codigo in d['favoritos']:
            articulo = market.buscar_articulo(codigo)
            if articulo is None:
                raise ValueError('Un favorito se refiere a un artículo inexistente.')
            usuario.agregar_favorito(articulo)

    # 4) Transacciones, incluyendo su medio de pago y etapas ya completadas.
    for d in datos['transacciones']:
        comprador = market.buscar_usuario(d['comprador'])
        if comprador is None:
            raise ValueError('Falta el comprador de una transacción.')
        transaccion = Transaccion(d['id'], comprador, recuperar_items(d['items']))
        transaccion.estado_pago = EstadoPago(d['estado_pago'])
        transaccion.estado_envio = EstadoEnvio(d['estado_envio'])
        forma = d['metodo_pago']
        if forma is not None:
            if forma['tipo'] == 'Tarjeta':
                transaccion.metodo_pago = Tarjeta(int(forma['saldo']))
            elif forma['tipo'] == 'Billetera digital':
                transaccion.metodo_pago = BilleteraDigital(int(forma['saldo']))
            else:
                raise ValueError('Medio de pago desconocido en el archivo.')
        if market.buscar_transaccion(transaccion.id):
            raise ValueError('ID de transacción duplicado en el archivo.')
        market.transacciones[market._clave(transaccion.id)] = transaccion

    market.siguiente_transaccion = int(datos['siguiente_transaccion'])
    if market.siguiente_transaccion < 1:
        raise ValueError('El siguiente ID de transacción no es válido.')
    return market


def guardar(market: Marketplace, ruta: Path) -> None:
    """Escribe un archivo temporal y lo reemplaza para evitar JSON incompletos."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=ruta.parent,
                                         suffix='.tmp', delete=False) as f:
            temporal = Path(f.name)
            json.dump(exportar_datos(market), f, indent=2, ensure_ascii=False)
            f.write('\n')
        os.replace(temporal, ruta)
    finally:
        if temporal is not None and temporal.exists():
            temporal.unlink()


def cargar(ruta: Path) -> Marketplace:
    """Lee un JSON y devuelve un marketplace completo, validando su versión."""
    with Path(ruta).open('r', encoding='utf-8') as f:
        datos = json.load(f)
    return importar_datos(datos)
