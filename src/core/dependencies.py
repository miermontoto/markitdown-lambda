from typing import Dict, Any
import boto3
from functools import lru_cache
from src.core.config import get_config


class DependencyContainer:
    """
    contenedor para gestionar dependencias de la aplicación
    """

    def __init__(self):
        """
        inicializa el contenedor de dependencias
        """
        self._services: Dict[str, Any] = {}

    def register(self, name: str, factory_func, singleton: bool = True) -> None:
        """
        registra una dependencia

        Args:
            name: Nombre de la dependencia
            factory_func: Función que crea la dependencia
            singleton: Si True, la dependencia se crea una sola vez
        """
        if singleton:
            # wrap factory function to cache result
            original_factory = factory_func

            @lru_cache(maxsize=1)
            def cached_factory():
                return original_factory()
            factory_func = cached_factory

        self._services[name] = factory_func

    def get(self, name: str) -> Any:
        """
        obtiene una dependencia por nombre

        Args:
            name: Nombre de la dependencia

        Returns:
            La instancia de la dependencia

        Raises:
            KeyError: Si la dependencia no está registrada
        """
        if name not in self._services:
            raise KeyError(f"Dependency '{name}' not registered")

        factory = self._services[name]
        return factory()

    def clear(self) -> None:
        """
        limpia todas las dependencias registradas
        """
        self._services.clear()


# contenedor global
_container = DependencyContainer()


def register_dependency(name: str, factory_func, singleton: bool = True) -> None:
    """
    registra una dependencia en el contenedor global
    """
    _container.register(name, factory_func, singleton)


def get_dependency(name: str) -> Any:
    """
    obtiene una dependencia del contenedor global
    """
    return _container.get(name)


# factory functions para servicios comunes
def create_s3_client():
    """
    crea un cliente s3 de boto3
    """
    import os
    region = os.environ.get('AWS_DEFAULT_REGION') or os.environ.get('AWS_REGION', 'us-east-1')
    return boto3.client('s3', region_name=region)


def create_api_key():
    """
    obtiene la api key desde las variables de entorno
    """
    return get_config('API_KEY')


def create_bucket_name():
    """
    obtiene el nombre del bucket desde las variables de entorno
    """
    return get_config('S3_BUCKET_NAME', get_config('INPUT_BUCKET'))


# registrar dependencias comunes
def register_default_dependencies():
    """
    registra las dependencias por defecto de la aplicación
    """
    register_dependency('s3_client', create_s3_client, singleton=True)
    register_dependency('api_key', create_api_key, singleton=True)
    register_dependency('bucket_name', create_bucket_name, singleton=True)


# auto-registrar al importar el módulo
register_default_dependencies()
