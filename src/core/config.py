"""
servicio de configuración que maneja variables de entorno y aws secrets manager
"""
import os
import json
import boto3
from typing import Dict, Any, Optional
from functools import lru_cache
from botocore.exceptions import ClientError


class ConfigService:
    """
    servicio para obtener configuración con preferencia a aws secrets manager
    """

    def __init__(self, secrets_client: Optional[Any] = None):
        """
        inicializa el servicio de configuración

        Args:
            secrets_client: cliente de secrets manager (opcional para testing)
        """
        self._secrets_client = secrets_client
        self._cache: Dict[str, Any] = {}
        self._secrets_cache: Dict[str, Any] = {}  # cache para el secreto completo
        self._secrets_prefix = os.environ.get('SECRETS_PREFIX', 'markdown-converter')
        self._use_secrets_manager = os.environ.get('USE_SECRETS_MANAGER', 'true').lower() == 'true'
        self._stage = os.environ.get('STAGE', 'prod')

    @property
    def secrets_client(self):
        """lazy initialization del cliente de secrets manager"""
        if self._secrets_client is None and self._use_secrets_manager:
            self._secrets_client = boto3.client('secretsmanager')
        return self._secrets_client

    def _load_config_secret(self) -> Dict[str, Any]:
        """
        carga el secreto de configuración completo

        Returns:
            diccionario con toda la configuración o vacío si no existe
        """
        if not self._use_secrets_manager or not self.secrets_client:
            return {}

        # si ya está en cache, devolverlo
        if self._secrets_cache:
            return self._secrets_cache

        # construir el nombre del secreto
        secret_name = f"{self._secrets_prefix}/{self._stage}/config"

        try:
            response = self.secrets_client.get_secret_value(SecretId=secret_name)

            if 'SecretString' in response:
                secret_value = response['SecretString']

                # parsear como json
                try:
                    self._secrets_cache = json.loads(secret_value)
                    return self._secrets_cache
                except json.JSONDecodeError:
                    print(f"Error parsing secret {secret_name} as JSON")
                    return {}

            return {}

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')

            # si el secreto no existe, es normal
            if error_code == 'ResourceNotFoundException':
                return {}

            # para otros errores, loggear pero no fallar
            print(f"Error getting secret {secret_name}: {error_code}")
            return {}
        except Exception as e:
            print(f"Unexpected error getting secret {secret_name}: {str(e)}")
            return {}

    def _get_from_secrets_manager(self, key: str) -> Optional[str]:
        """
        intenta obtener un valor de aws secrets manager

        Args:
            key: nombre de la variable

        Returns:
            valor del secreto o None si no existe
        """
        if not self._use_secrets_manager or not self.secrets_client:
            return None

        # cargar el secreto completo (solo una vez, está cacheado)
        config = self._load_config_secret()

        # buscar la clave en el secreto
        if key in config:
            value = config[key]
            # convertir a string si no lo es
            if value is not None and not isinstance(value, str):
                return str(value)
            return value

        # si no está en el secreto, retornar None
        return None

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        obtiene una variable de configuración

        prioridad:
        1. cache interno
        2. aws secrets manager (si está habilitado)
        3. variable de entorno
        4. valor por defecto

        Args:
            key: nombre de la variable
            default: valor por defecto si no se encuentra

        Returns:
            valor de la configuración o default
        """
        # verificar cache
        if key in self._cache:
            return self._cache[key]

        # intentar secrets manager primero
        value = self._get_from_secrets_manager(key)

        # si no está en secrets manager, buscar en variables de entorno
        if value is None:
            value = os.environ.get(key)

        # si tampoco está en env vars, usar default
        if value is None:
            value = default

        # cachear el resultado
        if value is not None:
            self._cache[key] = value

        return value

    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        obtiene una variable de configuración como booleano

        Args:
            key: nombre de la variable
            default: valor por defecto

        Returns:
            valor booleano
        """
        value = self.get(key)
        if value is None:
            return default

        return value.lower() in ('true', '1', 'yes', 'on')

    def get_int(self, key: str, default: int = 0) -> int:
        """
        obtiene una variable de configuración como entero

        Args:
            key: nombre de la variable
            default: valor por defecto

        Returns:
            valor entero
        """
        value = self.get(key)
        if value is None:
            return default

        try:
            return int(value)
        except ValueError:
            print(f"Invalid integer value for {key}: {value}")
            return default

    def get_json(self, key: str, default: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        obtiene una variable de configuración como json

        Args:
            key: nombre de la variable
            default: valor por defecto

        Returns:
            diccionario o default
        """
        value = self.get(key)
        if value is None:
            return default

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            print(f"Invalid JSON value for {key}: {value}")
            return default

    def clear_cache(self):
        """limpia la cache de configuración"""
        self._cache.clear()
        self._secrets_cache.clear()

    def refresh(self, key: str) -> Optional[str]:
        """
        refresca un valor específico de la cache

        Args:
            key: nombre de la variable

        Returns:
            nuevo valor o None
        """
        # eliminar de cache
        self._cache.pop(key, None)

        # obtener valor fresco
        return self.get(key)


# instancia global del servicio
_config_service: Optional[ConfigService] = None


def get_config_service() -> ConfigService:
    """
    obtiene la instancia global del servicio de configuración

    Returns:
        ConfigService: instancia del servicio
    """
    global _config_service
    if _config_service is None:
        _config_service = ConfigService()
    return _config_service


@lru_cache(maxsize=128)
def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    función helper para obtener configuración

    Args:
        key: nombre de la variable
        default: valor por defecto

    Returns:
        valor de configuración
    """
    return get_config_service().get(key, default)


def get_config_bool(key: str, default: bool = False) -> bool:
    """
    función helper para obtener configuración booleana

    Args:
        key: nombre de la variable
        default: valor por defecto

    Returns:
        valor booleano
    """
    return get_config_service().get_bool(key, default)


def get_config_int(key: str, default: int = 0) -> int:
    """
    función helper para obtener configuración entera

    Args:
        key: nombre de la variable
        default: valor por defecto

    Returns:
        valor entero
    """
    return get_config_service().get_int(key, default)


def get_config_json(key: str, default: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    función helper para obtener configuración json

    Args:
        key: nombre de la variable
        default: valor por defecto

    Returns:
        diccionario o default
    """
    return get_config_service().get_json(key, default)
