from django import forms
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client.emergentes
inventario = db.inventario
suplidores = db.suplidores
tipos = [
    ('ENTRADA', "Entrada"),
    ('SALIDA', "Salida")
]
almacenes = [
    (1, '1'),
    (2, '2')
]

def convertir(x):
    resultado = [ ('', 'Seleccione') ]
    for item in x:
        tupla = tuple([item, item])
        resultado.append(tupla)
    return resultado

class DateInput(forms.DateInput):
    input_type = 'date'

class ArticuloForm(forms.Form):
    codigoArticulo = forms.CharField(label='Codigo Articulo', max_length=15)
    descripcion = forms.CharField(label='Descripcion', widget=forms.Textarea(attrs={'rows': 4, 'cols': 50}), max_length=200)
    unidadCompra = forms.CharField(label='Unidad Compra', max_length=10)

class MovimientoForm(forms.Form):
    codigoAlmacen = forms.ChoiceField(choices=almacenes)
    tipoMovimiento = forms.ChoiceField(choices=tipos)
    codigoArticulo = forms.ChoiceField(choices=convertir(ob.get('codigoArticulo') for ob in inventario.find({}, { "_id": 0,"codigoArticulo": 1 })))
    cantidad = forms.IntegerField(min_value=1)
    fechaMovimiento = forms.DateField(widget = DateInput)

class SuplidorForm(forms.Form):
    codigoArticulo = forms.ChoiceField(choices=convertir(ob.get('codigoArticulo') for ob in inventario.find({}, { "_id": 0,"codigoArticulo": 1 })))
    codigoSuplidor = forms.CharField(label='Codigo Suplidor', max_length=50)
    tiempoEntrega = forms.IntegerField(label='Tiempo Entrega (dias)', min_value=1)
    precioCompra = forms.FloatField(label='Precio Compra (RD$)' ,min_value=0.01)

class OrdenCompraForm(forms.Form):
    codigoSuplidor = forms.ChoiceField(choices=convertir(suplidores.distinct("codigoSuplidor")))
    fechaOrden = forms.DateField(widget= DateInput)

class ArticulosCompraForm(forms.Form):
    codigoArticulo = forms.ChoiceField(choices=convertir(ob.get('codigoArticulo') for ob in inventario.find({}, { "_id": 0,"codigoArticulo": 1 })))
    cantidadOrdenada = forms.IntegerField(label='Cantidad', min_value=1)

class ArticulosPreliminaresForm(forms.Form):
    codigoArticulo = forms.ChoiceField(label='Componente', choices=convertir(ob.get('codigoArticulo') for ob in inventario.find({}, { "_id": 0,"codigoArticulo": 1 })))
    cantidad = forms.IntegerField(min_value=1)

class OrdenAutomaticaForm(forms.Form):
    fechaRequerida = forms.DateField(label='Fecha Requerida', widget = DateInput)