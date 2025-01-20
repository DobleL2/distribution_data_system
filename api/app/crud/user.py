# Manejo de las operaciones de base de datos relacionados con usuario

from sqlalchemy.orm import Session
from app.models.user import User,Datasets
from app.schemas.user import UserCreate,DatasetCreate

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate, hashed_password: str):
    db_user = User(username=user.username, full_name=user.full_name,role=user.role, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_dataset(db: Session, dataset: DatasetCreate):
    db_dataset = Datasets(dataset_name=dataset.dataset_name, n_rows=dataset.n_rows,n_columns=dataset.n_columns, selected=False)
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    return db_dataset

def delete_dataset_by_name(db: Session, dataset_name: str):
    datasets_to_delete = db.query(Datasets).filter(Datasets.dataset_name == dataset_name).all()
    if datasets_to_delete:
        for dataset in datasets_to_delete:
            db.delete(dataset)
        db.commit()
        return True
    return False