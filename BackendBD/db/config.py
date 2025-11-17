"""
Configuración de la base de datos PostgreSQL.
"""

import os
from typing import Optional


class DatabaseConfig:
    """Configuración centralizada de la base de datos."""
    
    def __init__(self):
        self.host: str = os.getenv('DB_HOST', 'localhost')
        self.database: str = os.getenv('DB_NAME', 'aprendizaje')
        self.user: str = os.getenv('DB_USER', 'usuario1')
        self.password: str = os.getenv('DB_PASSWORD', 'password1')
        self.port: int = int(os.getenv('DB_PORT', '5432'))
        self.echo: bool = os.getenv('DB_ECHO', 'False').lower() == 'true'
    
    def get_database_url(self) -> str:
        """
        Retorna la URL de conexión para SQLAlchemy.
        
        Returns:
            String de conexión en formato SQLAlchemy
        """
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    def get_async_database_url(self) -> str:
        """
        Retorna la URL de conexión asíncrona para SQLAlchemy.
        
        Returns:
            String de conexión asíncrona
        """
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


# Instancia global de configuración
db_config = DatabaseConfig()