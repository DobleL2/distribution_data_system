# Define las rutas relacionadas con los usuarios

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserRead, UserLogin, Token
from app.utils.database import get_db
from app.utils.security import hash_password, verify_password
from app.utils.token import create_access_token
from app.crud.user import get_user_by_username, create_user,create_dataset
from app.crud.user import delete_dataset_by_name  # Ensure the function is imported
import pandas as pd
from datetime import datetime
from sqlalchemy import MetaData, Table, Column, Integer, String, inspect
from sqlalchemy.sql import text
from app.schemas.user import DatasetCreate
from app.models.user import User
import pytz

from pydantic import BaseModel
from typing import Dict, List

class TableRequest(BaseModel):
    data: Dict[str, List]  # Dictionary with column names as keys and lists of values as values
    table_name: str

router = APIRouter()

class UpdateUserRequest(BaseModel):
    fullname: str = None
    password: str = None

@router.put("/users/{username}/update")
def update_user(username: str, request: UpdateUserRequest, db: Session = Depends(get_db)):
    """
    Endpoint para actualizar el fullname y/o contraseña de un usuario.
    
    Args:
        username (int): ID del usuario que se desea actualizar.
        request (UpdateUserRequest): Datos opcionales a actualizar (fullname, password).
        db (Session): Sesión de la base de datos.
        
    Returns:
        dict: Confirmación de la operación.
    """
    # Obtener al usuario de la base de datos
    user = db.query(User).filter(User.username == username,User.role!='super_admin',User.role!='admin').first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    # Verificar qué campos se enviaron en la solicitud y actualizarlos
    if request.fullname is not None:
        user.full_name = request.fullname
    if request.password is not None:
        user.hashed_password = hash_password(request.password)
    
    # Si no se enviaron datos, lanzar una excepción
    if request.fullname is None and request.password is None:
        raise HTTPException(status_code=400, detail="No data provided to update.")
    
    # Guardar los cambios
    try:
        db.commit()
        return {"message": f"User {username} updated successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating user: {e}")


@router.post("/users/", response_model=UserRead)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = hash_password(user.password)
    return create_user(db, user, hashed_password)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/")


@router.post("/login/", response_model=Token)
def login_endpoint(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    # Generar el token de acceso
    access_token = create_access_token(data={"sub": user.username})
    
    # Retornar el token junto con los datos adicionales del usuario
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "fullname": user.full_name,
        "role": user.role,
        "id": user.id
    }

@router.post("/add_table/")
def add_table_to_db(request: TableRequest, db: Session = Depends(get_db)):
    """
    Endpoint para agregar un DataFrame a la base de datos como una nueva tabla con columnas adicionales de control.
    """
    data = request.data
    table_name = request.table_name
    # Validar nombre de tabla
    if not table_name.isidentifier():
        raise HTTPException(
            status_code=400,
            detail="Invalid table name. The table name must be a valid Python identifier."
        )

    # Convertir el diccionario a DataFrame
    try:
        df = pd.DataFrame(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid data format: {e}")

    if df.empty:
        raise HTTPException(status_code=400, detail="The DataFrame is empty.")

    metadata = MetaData()

    columns = [
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("status", String, default="unprocessed"),
        Column("assigned_to", String, nullable=True),
        Column("assigned_at", String, nullable=True),
        Column("processed_at", String, nullable=True),
    ]

    # Agregar dinámicamente columnas basadas en las claves del diccionario
    for col in df.columns:
        columns.append(Column(col, String))

    table = Table(table_name, metadata, *columns)
    try:
        metadata.create_all(db.get_bind())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating table: {e}")

    try:
        records = df.to_dict(orient="records")
        for record in records:
            record["status"] = "unprocessed"  # Configurar estado inicial
        db.execute(table.insert(), records)
        db.commit()
        info = DatasetCreate(
            dataset_name=table_name,
            n_rows=df.shape[0],
            n_columns=df.shape[1],
            selected= False
        )
        create_dataset(db,info)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error inserting data: {e}")

    return {"message": f"Table '{table_name}' created successfully with {len(df)} records."}


@router.get("/resumen_production/")
def get_resumen_production(dataset:str,db:Session= Depends(get_db)):
    query = text(f"""
                SELECT u.full_name, u.username, count(*) as registros_procesados
                FROM {dataset} d
                LEFT JOIN users u ON u.id = d.assigned_to
                WHERE d.status = 'processed' AND d.assigned_to IS NOT NULL
                GROUP BY u.full_name, u.username
                 """)
    existing_record = db.execute(query).mappings().fetchall()
    return {
        "results": existing_record
    }

@router.get("/get_columns/")
def columns(dataset: str, db: Session = Depends(get_db)):
    # Obtener las columnas de la tabla
    tabla = dataset
    try:
        # Ejecutar la consulta PRAGMA para obtener la información de las columnas
        records = db.execute(text(f"PRAGMA table_info({tabla})")).mappings().fetchall()
        # Extraer solo los nombres de las columnas
        columnas = [fila["name"] for fila in records]
        return {"results": columnas}
    except Exception as e:
        return {"error": str(e)}

@router.get("/buscar_registro/")
def get_buscar_registro(dataset:str,id_name:str,id_busqueda:str,db:Session= Depends(get_db)):
    query = text(f"""
                SELECT *
                FROM {dataset} d
                WHERE {id_name} = "{id_busqueda}"
                 """)
    existing_record = db.execute(query).mappings().fetchall()
    return {
        "results": existing_record
    }

@router.get("/select_dataset/")
def get_selected_dataset(dataset:str,db:Session= Depends(get_db)):
    query = text(f"""
                    UPDATE datasets
                    SET selected = 0
                    WHERE selected = 1
                 """)
    db.execute(query)
    db.commit()
        
    query = text(f"""
                    UPDATE datasets
                    SET selected = 1
                    WHERE dataset_name = "{dataset}"
                 """)
    db.execute(query)
    db.commit()
    
    return {"message": f"Dataset'{dataset}' selected."}

@router.get("/dataset_status_information/")
def get_dataset_status_information(dataset:str,db:Session= Depends(get_db)):
    query = text(f"""
                SELECT full_name,username,d.*
                FROM {dataset} d
                LEFT JOIN users u ON u.id = d.assigned_to
                 """)
    existing_record = db.execute(query).mappings().fetchall()
    return {
        "results": existing_record
    }
    
@router.get("/current_dataset/")
def get_current_dataset(db:Session= Depends(get_db)):
    existing_query = text(f"""
        SELECT dataset_name
        FROM datasets
        WHERE selected = 1
    """)
    existing_record = db.execute(existing_query).mappings().fetchone()
    if existing_record:
        query = text(f"""
                    SELECT *
                    FROM {existing_record['dataset_name']}
                    """)
        dataset_data = db.execute(query).mappings().fetchall()
        return {
            "results": dataset_data,
            "dataset_name":existing_record['dataset_name']
        }
    else:
        return None

@router.get("/datasets_names/")
def get_datasets_names(db:Session= Depends(get_db)):
    query = text(f"""
                SELECT dataset_name
                FROM datasets
                 """)
    existing_record = db.execute(query).mappings().fetchall()
    return {
        "results": existing_record
    }

@router.get("/get_record/")
def get_record(user_id: str, db: Session = Depends(get_db)):
    """
    Endpoint para obtener un registro no procesado y asignarlo a un usuario.
    Si el usuario tiene un registro en 'in_progress', se le asigna ese mismo registro nuevamente.
    """
    # Verificar si el usuario ya tiene un registro en estado "in_progress"
    table_selected = text("""
                          SELECT dataset_name
                          FROM datasets
                          WHERE selected = 1
                          """)
    table_name = db.execute(table_selected).mappings().fetchone()
    if table_name:
        table_name = table_name['dataset_name']
        existing_query = text(f"""
            SELECT * 
            FROM {table_name}
            WHERE status = 'in_progress' AND assigned_to = :user_id
            LIMIT 1
        """)
        existing_record = db.execute(existing_query, {"user_id": user_id}).mappings().fetchone()

        if existing_record:
            # Actualizar la hora de asignación del registro existente
            update_existing_query = text(f"""
                UPDATE {table_name}
                SET assigned_at = :assigned_at
                WHERE id = :record_id
            """)
            
            # Convertir el tiempo actual en UTC a UTC-5
            utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
            utc_minus_5 = pytz.timezone('America/Lima')  # Ejemplo para una región en UTC-5
            assigned_at = utc_now.astimezone(utc_minus_5)        
            db.execute(
                update_existing_query,
                {
                    "assigned_at": assigned_at,
                    "record_id": existing_record["id"],
                }
            )
            db.commit()

            # Retornar el registro existente
            return {
                "record_id": existing_record["id"],
                "data": {col: existing_record[col] for col in existing_record.keys() if col not in ["id", "status", "assigned_to", "assigned_at", "processed_at"]},
                "assigned_to": user_id,
                "assigned_at": assigned_at.isoformat(),
            }

        # Si no tiene un registro en progreso, buscar un nuevo registro no procesado
        new_query = text(f"""
            SELECT * 
            FROM {table_name}
            WHERE status = 'unprocessed'
            LIMIT 1
        """)
        new_record = db.execute(new_query).mappings().fetchone()

        if not new_record:
            raise HTTPException(status_code=404, detail="No unprocessed records available.")

        # Asignar el nuevo registro al usuario
        assign_query = text(f"""
            UPDATE {table_name}
            SET status = 'in_progress', assigned_to = :user_id, assigned_at = :assigned_at
            WHERE id = :record_id
        """)
        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
        utc_minus_5 = pytz.timezone('America/Lima')  # Ejemplo para una región en UTC-5
        assigned_at = utc_now.astimezone(utc_minus_5)   
        
        db.execute(
            assign_query,
            {
                "user_id": user_id,
                "assigned_at": assigned_at,
                "record_id": new_record["id"],
            }
        )
        db.commit()

        # Retornar el nuevo registro asignado
        return {
            "record_id": new_record["id"],
            "data": {col: new_record[col] for col in new_record.keys() if col not in ["id", "status", "assigned_to", "assigned_at", "processed_at"]},
            "assigned_to": user_id,
            "assigned_at": assigned_at.isoformat(),
        }
    else:
        return None


class MarkAsProcessedRequest(BaseModel):
    record_id: int
    user_id: str

@router.post("/mark_as_processed/")
def mark_as_processed(request: MarkAsProcessedRequest, db: Session = Depends(get_db)):
    """
    Endpoint para marcar un registro como 'processed'.

    Args:
        record_id (int): ID del registro que se procesará.
        user_id (str): ID del usuario que marca el registro como procesado.
        db (Session): Sesión de la base de datos.

    Returns:
        dict: Confirmación de la operación.
    """
    table_selected = text("""
                          SELECT dataset_name
                          FROM datasets
                          WHERE selected = 1
                          """)
    table_name = db.execute(table_selected).mappings().fetchone()['dataset_name']
    record_id = request.record_id
    user_id = request.user_id
    # Verificar si el registro existe y está en progreso
    query = text(f"""
        SELECT * 
        FROM {table_name}
        WHERE id = :record_id AND status = 'in_progress' AND assigned_to = :user_id
    """)
    record = db.execute(query, {"record_id": record_id, "user_id": user_id}).mappings().fetchone()

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Record not found or not in progress."
        )

    # Marcar el registro como procesado
    update_query = text(f"""
        UPDATE {table_name}
        SET status = 'processed', processed_at = :processed_at
        WHERE id = :record_id
    """)
    utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
    utc_minus_5 = pytz.timezone('America/Lima')  # Ejemplo para una región en UTC-5
    processed_at = utc_now.astimezone(utc_minus_5)   
    db.execute(
        update_query,
        {
            "processed_at": processed_at,
            "record_id": record_id,
        }
    )
    db.commit()

    return {"message": f"Record {record_id} marked as processed successfully by user {user_id}."}


@router.delete("/delete_table/")
def delete_table_from_db(table_name: str, db: Session = Depends(get_db)):
    """
    Endpoint para eliminar una tabla de la base de datos.

    Args:
        table_name (str): Nombre de la tabla que se desea eliminar.
        db (Session): Sesión de la base de datos.

    Returns:
        dict: Confirmación de la operación.
    """
    # Validar que el nombre de la tabla sea válido
    if not table_name.isidentifier():
        raise HTTPException(
            status_code=400,
            detail="Invalid table name. The table name must be a valid Python identifier."
        )

    # Verificar si la tabla existe
    inspector = inspect(db.get_bind())
    if table_name not in inspector.get_table_names():
        raise HTTPException(
            status_code=404,
            detail=f"Table '{table_name}' does not exist in the database."
        )

    # Eliminar la tabla
    try:
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=db.get_bind())
        table.drop(db.get_bind())
        delete_dataset_by_name(db, table_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting table: {e}")

    return {"message": f"Table '{table_name}' has been successfully deleted."}
