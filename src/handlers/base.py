from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class EventHandler(ABC):
    """
    interfaz base para todos los manejadores de eventos lambda
    """

    @abstractmethod
    def can_handle(self, event: Dict[str, Any]) -> bool:
        """
        determina si este handler puede manejar el evento dado

        Args:
            event: El evento de Lambda

        Returns:
            bool: True si este handler puede manejar el evento
        """
        pass

    @abstractmethod
    def handle(self, event: Dict[str, Any], context: Optional[Any] = None) -> Any:
        """
        maneja el evento y retorna una respuesta

        Args:
            event: El evento de Lambda
            context: El contexto de Lambda (opcional)

        Returns:
            Any: La respuesta apropiada para el tipo de evento
        """
        pass

    def format_response(self, result: Any, error: Optional[Exception] = None) -> Any:
        """
        formatea la respuesta según el tipo de handler
        puede ser sobrescrito por implementaciones específicas

        Args:
            result: El resultado exitoso
            error: La excepción si ocurrió un error

        Returns:
            Any: La respuesta formateada
        """
        if error:
            return self._format_error_response(error)
        return result

    def _format_error_response(self, error: Exception) -> Dict[str, Any]:
        """
        formato estándar para respuestas de error

        Args:
            error: La excepción que ocurrió

        Returns:
            Dict: La respuesta de error formateada
        """
        return {
            'error': str(error),
            'error_type': type(error).__name__
        }
