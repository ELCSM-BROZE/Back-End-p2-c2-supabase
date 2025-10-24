from django.contrib import admin
from .models import Contacto

admin.site.register(Contacto)


from .models import Producto, Cliente, Venta, DetalleVenta

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "sku", "precio", "stock", "activo")
    search_fields = ("nombre", "sku") # texto rápido
    list_filter = ("activo",) # filtros laterales
    ordering = ("nombre",)
    list_per_page = 25
    autocomplete_fields = () # ej.: ("categoria",) si existiera FK grande

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "email")
    search_fields = ("nombre", "email")

class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1
    autocomplete_fields = ("producto",)
    readonly_fields = ("subtotal",)

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    date_hierarchy = "fecha"
    list_display = ("id", "cliente", "fecha", "anulada", "total_display")
    search_fields = ("cliente__nombre", "id") # lookups a relacionadas
    list_filter = ("anulada",)
    inlines = [DetalleVentaInline]

@admin.display(description="Total", ordering="id")
def total_display(self, obj):
    return f"${obj.total:,.0f}"

from django.http import HttpResponse
import csv

@admin.action(description="Anular ventas seleccionadas")
def marcar_anuladas(modeladmin, request, queryset):
    updated = queryset.update(anulada=True)
    modeladmin.message_user(request, f"{updated} ventas anuladas.")
@admin.action(description="Exportar ventas a CSV")
def exportar_ventas_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="ventas.csv"'
    writer = csv.writer(response)
    writer.writerow(["ID", "Cliente", "Fecha", "Anulada", "Total"])
    for v in queryset.select_related('cliente').prefetch_related('detalles__producto'):
        writer.writerow([v.id, v.cliente.nombre, v.fecha, v.anulada, v.total])
    return response

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    # ... (resto)
    actions = [marcar_anuladas, exportar_ventas_csv]
    from django.contrib.admin import SimpleListFilter

class StockBajoFilter(SimpleListFilter):
 title = 'stock'
 parameter_name = 'stock'
 def lookups(self, request, model_admin):
        return (
    ('bajo', 'Menos de 10'),
    ('sin', 'Sin stock'),
    )

def queryset(self, request, queryset):
    if self.value() == 'bajo':
        return queryset.filter(stock__lt=10)
    if self.value() == 'sin':
        return queryset.filter(stock=0)
    return queryset

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    # ... (resto)
    list_filter = ("activo", StockBajoFilter)