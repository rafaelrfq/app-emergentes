from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render, redirect
from datetime import datetime
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client.emergentes
inventario = db.inventario

def test(req):
    movimientoInventario = {
        "codigoMovimiento": 1,
        "codigoAlmacen": 1,
        "tipoMovimiento": "ENTRADA",
        "codigoArticulo": 1,
        "cantidad": 10
    }
    articulo = {
        "codigoArticulo": 1,
        "descripcion": "Monitor 1080p Full HD",
        "infoAlmacen": [
            {
                "codigoAlmacen": 5,
                "balanceActual": 150
            }
        ],
        "unidadCompra": "RD$"
    }
    articuloSuplidor = {
        "codigoArticulo": 1,
        "codigoSuplidor": 1,
        "tiempoEntrega": 3,
        "precioCompra": 5850
    }
    ordenCompra = {
        "codigoOrdenCompra": 1,
        "codigoSuplidor": 1,
        "fechaOrden": datetime.now(),
        "montoTotal": 29750,
        "articulos": [
            {
                "codigoArticulo": 1,
                "cantidadOrdenada": 4,
                "unidadCompra": "RD$",
                "precioCompra": 5850
            }
        ]
    }
    idArt = inventario.insert_one(articulo).inserted_id
    print(idArt)
    items = inventario.find()
    context = {'title': 'App Emergentes', 'items': items}
    return render(req, 'app.html', context)

def orden(req):
    articulos = inventario.find()
    context = {'title': 'Lista de articulos', 'articulos': articulos}
    return render(req, 'orden.html', context)