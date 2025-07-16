from typing import List, Type, Optional, Any, Dict
from src.handlers.base import EventHandler


class HandlerRegistry:
    """
    registro para administrar y descubrir handlers de eventos
    """

    def __init__(self):
        """
        inicializa el registro con una lista vacía de handlers
        """
        self._handlers: List[EventHandler] = []
        self._handler_classes: List[Type[EventHandler]] = []

    def register(self, handler_class: Type[EventHandler], priority: int = 0) -> None:
        """
        registra una clase de handler

        Args:
            handler_class: La clase del handler a registrar
            priority: Prioridad del handler (mayor = más prioridad)
        """
        # insertar en orden de prioridad
        insert_pos = 0
        for i, (_, p) in enumerate(self._handler_classes):
            if priority > p:
                break
            insert_pos = i + 1

        self._handler_classes.insert(insert_pos, (handler_class, priority))

    def get_handler(self, event: Dict[str, Any]) -> Optional[EventHandler]:
        """
        encuentra el handler apropiado para el evento dado

        Args:
            event: El evento de Lambda

        Returns:
            EventHandler: El handler que puede manejar el evento, o None
        """
        # lazy initialization de handlers
        if not self._handlers and self._handler_classes:
            self._initialize_handlers()

        for handler in self._handlers:
            if handler.can_handle(event):
                return handler

        return None

    def _initialize_handlers(self) -> None:
        """
        inicializa las instancias de handlers desde las clases registradas
        """
        self._handlers = []
        for handler_class, _ in self._handler_classes:
            try:
                handler = handler_class()
                self._handlers.append(handler)
            except Exception as e:
                print(f"Error initializing handler {handler_class.__name__}: {str(e)}")

    def clear(self) -> None:
        """
        limpia todos los handlers registrados
        """
        self._handlers = []
        self._handler_classes = []

    def list_handlers(self) -> List[str]:
        """
        lista los nombres de todos los handlers registrados

        Returns:
            List[str]: Lista de nombres de handlers
        """
        return [handler_class.__name__ for handler_class, _ in self._handler_classes]


# instancia global del registro
_registry = HandlerRegistry()


def register_handler(handler_class: Type[EventHandler], priority: int = 0) -> None:
    """
    registra un handler en el registro global

    Args:
        handler_class: La clase del handler a registrar
        priority: Prioridad del handler (mayor = más prioridad)
    """
    _registry.register(handler_class, priority)


def get_handler_for_event(event: Dict[str, Any]) -> Optional[EventHandler]:
    """
    obtiene el handler apropiado para un evento

    Args:
        event: El evento de Lambda

    Returns:
        EventHandler: El handler que puede manejar el evento, o None
    """
    return _registry.get_handler(event)


def clear_registry() -> None:
    """
    limpia el registro global
    """
    _registry.clear()


def list_registered_handlers() -> List[str]:
    """
    lista los handlers registrados

    Returns:
        List[str]: Lista de nombres de handlers
    """
    return _registry.list_handlers()


# auto-registrar handlers disponibles
def auto_register_handlers():
    """
    auto-registra los handlers disponibles en el módulo
    """
    try:
        from src.handlers.api import ApiHandler
        from src.handlers.s3 import S3Handler

        # registrar con prioridades
        register_handler(S3Handler, priority=10)  # s3 tiene mayor prioridad
        register_handler(ApiHandler, priority=5)   # api gateway es secundario

    except ImportError as e:
        print(f"Warning: Could not auto-register handlers: {str(e)}")
