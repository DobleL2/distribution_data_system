from app.models.user import Base
from app.utils.database import engine

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

