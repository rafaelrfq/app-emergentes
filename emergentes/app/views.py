from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.forms import formset_factory
from datetime import datetime, date
from pymongo import MongoClient
from .forms import ArticuloForm, MovimientoForm, SuplidorForm, OrdenCompraForm, ArticulosCompraForm

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
                        "balanceActual": 150
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
                    item = {
                        "codigoArticulo": forma.cleaned_data.get('codigoArticulo'),
                        "cantidadOrdenada": forma.cleaned_data.get('cantidadOrdenada'),
                        "unidadCompra": "RD$",
                        "precioCompra": 550
                    }
                    if item.get("cantidadOrdenada") != None:
                        total += item.get("cantidadOrdenada") * item.get("precioCompra")
                    articulos.append(item)
                orden = {
                    "codigoOrdenCompra": 1,
                    "codigoSuplidor": form.cleaned_data.get('codigoSuplidor'),
                    "fechaOrden": datetime.fromisoformat(str(form.cleaned_data.get('fechaOrden'))),
                    "montoTotal": total,
                    "articulos": articulos
                }
                print(orden)
                return redirect('/ordenes')
    else:
        form = OrdenCompraForm()
        formset = ArticuloFormset()
    orders = ordenes.find()
    context = {'form': form, 'formset': formset, 'ordenes': orders}
    return render(req, 'orden.html', context)



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