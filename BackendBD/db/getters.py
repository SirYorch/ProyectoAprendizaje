from .models import listar_productos 


def get_products():
    datos = listar_productos()
    return datos