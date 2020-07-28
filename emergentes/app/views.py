from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.forms import formset_factory
from django.contrib import messages
from datetime import datetime, date, timedelta
from pymongo import MongoClient
from bson.son import SON
from .forms import ArticuloForm, MovimientoForm, SuplidorForm, OrdenCompraForm, ArticulosCompraForm, ArticulosPreliminaresForm, OrdenAutomaticaForm
from pprint import pprint
from math import ceil

client = MongoClient('mongodb://localhost:27017/')
db = client.emergentes
inventario = db.inventario
movimientos = db.movimientos
suplidores = db.suplidores
ordenes = db.ordenes

def inventory(req):
    if req.method == 'POST':
        form = MovimientoForm(req.POST)
        if form.is_valid():
            cod = movimientos.count_documents({}) + 1
            mov = {
                "codigoMovimiento": cod,
                "codigoAlmacen": form.cleaned_data.get('codigoAlmacen'),
                "tipoMovimiento": form.cleaned_data.get('tipoMovimiento'),
                "codigoArticulo": form.cleaned_data.get('codigoArticulo'),
                "cantidad": form.cleaned_data.get('cantidad'),
                "fechaMovimiento": datetime.fromisoformat(str(form.cleaned_data.get('fechaMovimiento')))
            }

            query = {"codigoArticulo": mov.get("codigoArticulo"), "infoAlmacen.codigoAlmacen": 1}

            if mov.get("tipoMovimiento") == "ENTRADA":
                values = { "$inc": {"infoAlmacen.$.balanceActual": mov.get("cantidad")}}
                inventario.update_one(query, values)

            if mov.get("tipoMovimiento") == "SALIDA":
                values = { "$inc": {"infoAlmacen.$.balanceActual": - mov.get("cantidad")}}
                inventario.update_one(query, values)
            
            movimientos.insert_one(mov)
            return redirect('/')
    else:
        form = MovimientoForm()

    movs = movimientos.find()
    context = {'title': 'App Emergentes', 'form': form, 'movimientos': movs}
    return render(req, 'inventario.html', context)

def movimientoDelete(req, id):
    result = movimientos.delete_one({"codigoMovimiento": id})
    if result.deleted_count > 0:
        return redirect('/')
    else:
        print('Hubo un error')
        return redirect('/')

def articulo(req):
    if req.method == 'POST':
        form = ArticuloForm(req.POST)
        if form.is_valid():
            arti = {
                "codigoArticulo": form.cleaned_data.get('codigoArticulo'),
                "descripcion": form.cleaned_data.get('descripcion'),
                "infoAlmacen": [
                    {
                        "codigoAlmacen": 1,
                        "balanceActual": 0
                    }
                ],
                "unidadCompra": form.cleaned_data.get('unidadCompra')
            }
            inventario.insert_one(arti)
            return redirect('/articulo')
    else:
        form = ArticuloForm()
    articulos = inventario.find()
    context = {'form': form, 'articulos': articulos}
    return render(req, 'articulo.html', context)

def articuloDelete(req, id):
    result = inventario.delete_one({"codigoArticulo": id})
    if result.deleted_count > 0:
        return redirect('/articulo')
    else:
        print('Hubo un error')
        return redirect('/articulo')

def suplidor(req):
    if req.method == 'POST':
        form = SuplidorForm(req.POST)
        if form.is_valid():
            sup = {
                "codigoArticulo": form.cleaned_data.get('codigoArticulo'),
                "codigoSuplidor": form.cleaned_data.get('codigoSuplidor'),
                "tiempoEntrega": form.cleaned_data.get('tiempoEntrega'),
                "precioCompra": form.cleaned_data.get('precioCompra')
            }
            suplidores.insert_one(sup)
            return redirect('/suplidor')
    else:
        form = SuplidorForm()
    suppliers = suplidores.find()
    context = {'form': form, 'suplidores': suppliers}
    return render(req, 'suplidor.html', context)

def suplidorDelete(req, id):
    result = suplidores.delete_one({"codigoSuplidor": id})
    if result.deleted_count > 0:
        return redirect('/suplidor')
    return redirect('/suplidor')

def ordenCompra(req):
    ArticuloFormset = formset_factory(ArticulosCompraForm, extra=3, can_delete=False)
    if req.method == 'POST':
        form = OrdenCompraForm(req.POST)
        formset = ArticuloFormset(req.POST)
        if form.is_valid():
            if formset.is_valid():
                articulos = []
                total = 0
                for forma in formset:
                    condicion = list(suplidores.find({"codigoArticulo": forma.cleaned_data.get('codigoArticulo'), "codigoSuplidor": form.cleaned_data.get('codigoSuplidor')}))
                    if condicion:
                        item = {}
                        if forma.cleaned_data.get('codigoArticulo') != None:
                            pipeline = [
                                { "$match": { "codigoArticulo": forma.cleaned_data.get('codigoArticulo') } },
                                { "$lookup": { "from": "suplidores", "localField": "codigoArticulo", "foreignField": "codigoArticulo", "as": "Suplidor" } }
                            ]
                            tmp = list(inventario.aggregate(pipeline))
                            item = {
                                "codigoArticulo": forma.cleaned_data.get('codigoArticulo'),
                                "cantidadOrdenada": forma.cleaned_data.get('cantidadOrdenada'),
                                "unidadCompra": tmp[0].get("unidadCompra"),
                                "precioCompra": tmp[0].get("Suplidor")[0].get("precioCompra")
                            }
                        if item.get("cantidadOrdenada") != None and item.get("cantidadOrdenada") > 0:
                            total += item.get("cantidadOrdenada") * item.get("precioCompra")
                        if item:
                            articulos.append(item)
                    else:
                        messages.error(req,"Suplidor no tiene disponibilidad de uno o mas articulo/s escogido/s.")
                orden = {
                    "codigoOrdenCompra": ordenes.count_documents({}) + 1,
                    "codigoSuplidor": form.cleaned_data.get('codigoSuplidor'),
                    "fechaOrden": datetime.fromisoformat(str(form.cleaned_data.get('fechaOrden'))),
                    "montoTotal": total,
                    "articulos": articulos
                }
                ordenes.insert_one(orden)
                return redirect('/ordenes')
    else:
        form = OrdenCompraForm()
        formset = ArticuloFormset()
    orders = ordenes.find()
    context = {'form': form, 'formset': formset, 'ordenes': orders}
    return render(req, 'orden.html', context)

articulosPre = []
def articulosPreliminares(req):
    if req.method == 'POST':
        form = ArticulosPreliminaresForm(req.POST)
        form1 = OrdenAutomaticaForm(req.POST)
        if form.is_valid():
            tmp = {
                "codigoArticulo": form.cleaned_data.get('codigoArticulo'),
                "descripcion": "Ejemplo",
                "cantidad": form.cleaned_data.get('cantidad'),
            }
            articulosPre.append(tmp)
            return redirect('/ordenauto')
    else:
        form = ArticulosPreliminaresForm()
        form1 = OrdenAutomaticaForm()
    context = {'form': form, 'form1': form1, 'articulosPre': articulosPre}
    return render(req, 'orden_auto.html', context)

def realizarOrdenAuto(req):
    form = OrdenAutomaticaForm(req.POST)
    if form.is_valid():
        fechaReq = datetime.fromisoformat(str(form.cleaned_data.get('fechaRequerida')))
        diffFecha = (fechaReq - datetime.today()).days + 1
        cantidadesPorPedir = disponibilidad(diffFecha)
        for i, item in enumerate(articulosPre):
            suplidorEscogido = buscarMejorSuplidor(item.get('codigoArticulo'), diffFecha)[0].get('codigoSuplidor')
            fechaOrdenar = fechaReq - timedelta(days=list(suplidores.find({ 'codigoSuplidor': suplidorEscogido }))[0].get('tiempoEntrega'))
            item['codigoSuplidor'] = suplidorEscogido
            item['fechaOrdenar'] = fechaOrdenar
            item['cantidadPorPedir'] = cantidadesPorPedir[i]
        pprint(articulosPre)
        condicion = True
        i=1
        while i < len(articulosPre):
            if articulosPre[i-1].get('codigoSuplidor') != articulosPre[i].get('codigoSuplidor'):
                condicion = False
            i += 1
        if condicion:
            articulos = []
            total = 0
            for item in articulosPre:
                query = list(suplidores.find({ 'codigoSuplidor': item.get('codigoSuplidor'), 'codigoArticulo': item.get('codigoArticulo') }))[0]
                tmp = {
                        "codigoArticulo": item.get('codigoArticulo'),
                        "cantidadOrdenada": item.get('cantidadPorPedir'),
                        "unidadCompra": "RD$",
                        "precioCompra": query.get('precioCompra')
                }
                total += tmp.get('precioCompra') * tmp.get('cantidadOrdenada')
                articulos.append(tmp)
            
            orden = {
                    "codigoOrdenCompra": ordenes.count_documents({}) + 1,
                    "codigoSuplidor": articulosPre[0].get('codigoSuplidor'),
                    "fechaOrden": articulosPre[0].get('fechaOrdenar'),
                    "montoTotal": total,
                    "articulos": articulos
                }
            ordenes.insert_one(orden)
            articulosPre.clear()
        else:
            for item in articulosPre:
                articuloss = []
                query = list(suplidores.find({ 'codigoSuplidor': item.get('codigoSuplidor'), 'codigoArticulo': item.get('codigoArticulo') }))[0]
                tmp = {
                        "codigoArticulo": item.get('codigoArticulo'),
                        "cantidadOrdenada": item.get('cantidadPorPedir'),
                        "unidadCompra": "RD$",
                        "precioCompra": query.get('precioCompra')
                }
                total = tmp.get('precioCompra') * tmp.get('cantidadOrdenada')
                articuloss.append(tmp
                )
                orden = {
                    "codigoOrdenCompra": ordenes.count_documents({}) + 1,
                    "codigoSuplidor": item.get('codigoSuplidor'),
                    "fechaOrden": item.get('fechaOrdenar'),
                    "montoTotal": total,
                    "articulos": articuloss
                }
                pprint(orden)
                ordenes.insert_one(orden)
            articulosPre.clear()
    return redirect('/ordenauto')

def listarOrdenesAgrupadas(req):
    pipeline = [
        { '$project': { '_id':0, 'codigoOrdenCompra': 0 } },
        { '$group': { '_id': { 'Suplidor': "$codigoSuplidor", 'Fecha': "$fechaOrden" }, 'MontoTotal': { '$sum': "$montoTotal" }, 'Articulos': { "$addToSet": "$articulos" } } },
        { '$project': { '_id':0, 'Suplidor': "$_id.Suplidor", 'Fecha': "$_id.Fecha", 'MontoTotal': "$MontoTotal", 'Articulos': "$Articulos" } }
    ]
    agrupadas = ordenes.aggregate(pipeline)
    context = { 'title': 'Listado Agrupado de Ordenes', 'ordenes': agrupadas }
    return render(req, 'ordenes_agrupadas.html', context)

def disponibilidad(diffFecha):
    avg = []
    for item in articulosPre:
        avg.append(calculoAvg(item.get('codigoArticulo')))
    cantidadPedido = []
    for i, item in enumerate(articulosPre):
        balanceActualArticulo = list(inventario.find({'codigoArticulo': item.get('codigoArticulo')}))[0].get('infoAlmacen')[0].get('balanceActual')
        cantidadPedir = item.get('cantidad') - (balanceActualArticulo - (diffFecha * avg[i]))
        cantidadPedido.append(cantidadPedir)
    return cantidadPedido

def calculoAvg(art):
    fechaReq = datetime.today() - timedelta(days=30)
    pipeline = [
        {'$match': { 'codigoArticulo': art, 'tipoMovimiento': "SALIDA", 'fechaMovimiento': { '$gte': fechaReq } }},
        {'$group': { '_id': { 'tipo': "$tipoMovimiento" }, 'cantidad': {'$sum': "$cantidad"} }},
        {'$project': { '_id':0, 'cantidad':1, 'Cantidad': {'$divide': ["$cantidad", 30]}}}
    ]
    avg = ceil(list(movimientos.aggregate(pipeline))[0].get('Cantidad'))
    print('El avg de venta diaria es: ' + str(avg))
    return avg

def buscarMejorSuplidor(art, diffFecha):
    pipeline = [
        { '$match': { 'codigoArticulo': art, 'tiempoEntrega': { '$lte': diffFecha } } },
        { '$sort': { 'precioCompra': 1 } },
        { '$limit': 1 },
        { '$project': { '_id':0, 'codigoSuplidor':1 } }
    ]
    return list(suplidores.aggregate(pipeline))

    # Modelos

    # movimientoInventario = {
    #     "codigoMovimiento": 1,
    #     "codigoAlmacen": 1,
    #     "tipoMovimiento": "ENTRADA",
    #     "codigoArticulo": 1,
    #     "cantidad": 10,
    #     "fechaMovimiento": datettime.now()
    # }
    # articulo = {
    #     "codigoArticulo": 1,
    #     "descripcion": "Monitor 1080p Full HD",
    #     "infoAlmacen": [
    #         {
    #             "codigoAlmacen": 5,
    #             "balanceActual": 150
    #         }
    #     ],
    #     "unidadCompra": "RD$"
    # }
    # articuloSuplidor = {
    #     "codigoArticulo": 1,
    #     "codigoSuplidor": 1,
    #     "tiempoEntrega": 3,
    #     "precioCompra": 5850
    # }
    # ordenCompra = {
    #     "codigoOrdenCompra": 1,
    #     "codigoSuplidor": 1,
    #     "fechaOrden": datetime.now(),
    #     "montoTotal": 29750,
    #     "articulos": [
    #         {
    #             "codigoArticulo": 1,
    #             "cantidadOrdenada": 4,
    #             "unidadCompra": "RD$",
    #             "precioCompra": 5850
    #         }
    #     ]
    # }

    # Queries

    # fechaReq = datetime.today() - timedelta(days=30)

    # pipeline = [
    #     {'$match': { 'codigoArticulo': "MON-001", 'tipoMovimiento': "SALIDA", 'fechaMovimiento': { '$gte': fechaReq } }},
    #     {'$group': { '_id': { 'tipo': "$tipoMovimiento" }, 'cantidad': {'$sum': "$cantidad"} }},
    #     {'$project': { '_id':0, 'cantidad':1, 'Cantidad': {'$divide': ["$cantidad", 30]}}}
    # ]

    # # Obtener la cantidad avg vendida diariamente los ultimos 30 dias
    # db.movimientos.aggregate([
    # { $match: { codigoArticulo: "MON-001", tipoMovimiento: "SALIDA", fechaMovimiento: { $gte: new Date("2020-07-01") } } },
    # { $group: { _id: { tipo: "$tipoMovimiento" }, cantidad: {$sum: "$cantidad"} } },
    # { $project: { _id:0, cantidad:1, Cantidad: {$divide: ["$cantidad", 30]}} }
    # ])

    # Obtener al mejor suplidor
    # db.suplidores.aggregate([
    #     { $match: { codigoArticulo: 'MON-001', tiempoEntrega: { '$lte': 3 } } },
    #     { $sort: { precioCompra: 1 } },
    #     { $limit: 1 },
    #     { $project: { _id:0, codigoSuplidor:1 } }
    # ])

    # Agrupacion de ordenes por suplidor y fecha
    # db.ordenes.aggregate([
    #     { $project: { _id:0, codigoOrdenCompra: 0 } },
    #     { $group: { _id: { Suplidor: "$codigoSuplidor", Fecha: "$fechaOrden" }, MontoTotal: { $sum: "$montoTotal" }, Articulos: { "$addToSet": "$articulos" } } },
    #     { $project: { _id:0, Suplidor: "$_id.Suplidor", Fecha: "$_id.Fecha", MontoTotal: "$MontoTotal", Articulos: "$Articulos" } }
    # ])


# ventasdiarias = lo que retorna el aggregate de arriba
# fechaRequerida = lo marca el usuario
# diferenciaHoyRequerida = dias entre hoy y fecha requerida
# cantidadRequerida = lo marca el usuario
# cantidadPedido = cantidadRequerida - (Balanceactual - (diferenciaHoyRequerida * ventasdiarias))


# suplidor que su tiempoEntrega < diferenciaHoyRequerida, ver cual es el mas barato de todos