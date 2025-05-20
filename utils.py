def limpiar_argumentos_comandos(argumentos):
    """
    Limpia los argumentos de un comando, eliminando caracteres no deseados y convirtiendo a minúsculas.
    """
    # Eliminar caracteres no deseados
    argumentos = argumentos.replace("'", "")
    argumentos = argumentos.replace('"', "")
    # Convertir a minúsculas
    argumentos = argumentos.lower()
    return argumentos