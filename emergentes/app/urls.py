from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory, name='inventario'),
    path('<int:id>', views.movimientoDelete, name='mov_delete'),
    path('ordenes/', views.orden, name='orden'),
    path('articulo/', views.articulo, name='articulo'),
    path('articulo/<str:id>', views.articuloDelete, name='articulo_delete'),
    path('suplidor/', views.suplidor, name='suplidor'),
    path('suplidor/<str:id>', views.suplidorDelete, name='suplidor_delete'),
]