"""Descripciones cortas para las categorias que detecta el HUD local."""

OBJECT_LABELS = {
    "person": "PERSONA",
    "bottle": "BOTELLA",
    "cup": "TAZA/POCILLO",
    "laptop": "LAPTOP",
    "keyboard": "TECLADO",
    "tv": "PANTALLA/TV",
    "cat": "GATO",
    "dog": "PERRO",
    "teddy bear": "JUGUETE/PELUCHE",
    "mouse": "MOUSE",
    "chair": "SILLA",
}

OBJECT_DESCRIPTIONS = {
    "person": "Persona detectada; no se intenta identificarla.",
    "bottle": "Recipiente para almacenar y transportar liquidos.",
    "cup": "Recipiente pequeno para beber.",
    "laptop": "Computadora portatil para trabajar y ejecutar programas.",
    "keyboard": "Teclado para escribir e ingresar comandos.",
    "tv": "Pantalla para ver contenido audiovisual.",
    "cat": "Animal domestico; la deteccion solo indica la categoria.",
    "dog": "Animal domestico; la deteccion solo indica la categoria.",
    "teddy bear": "Juguete de peluche para jugar o acompanar.",
    "mouse": "Periferico para mover el cursor y seleccionar.",
    "chair": "Asiento con respaldo para una persona.",
}


def describe_object(category: str) -> str:
    """Devuelve una explicacion breve sin llamar a servicios externos."""
    return OBJECT_DESCRIPTIONS.get(
        category.lower(),
        "Objeto detectado localmente; descripcion general no disponible.",
    )
