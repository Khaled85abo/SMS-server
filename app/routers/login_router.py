from app.database.schemas import UserLoginSchema, UserSchema
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, insert, delete, update, func
from sqlalchemy.orm import Session, selectinload
from app.db_setup import get_db
from fastapi import Depends, APIRouter, HTTPException, status
from app.database.models import User
from app.auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
router = APIRouter()



@router.delete("/{login_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(login_id: int, db: Session = Depends(get_db)):
    """
    Hard delete of an users login
    """
    query = delete(User).where(User.id == login_id)
    result = db.execute(query)
    db.commit()
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")

@router.put("/deactivate/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    """
    Soft delete of a users profile by setting is_active to False.
    """
    query = (
        update(User).where(User.id == user_id).values(is_active=False)
    )
    result = db.execute(query)
    db.commit()

    if result is None:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deactivated successfully"}


@router.post("")
async def login_for_access_token(
    credentials: UserLoginSchema, db: Session = Depends(get_db)
) -> dict:
    db_user =   db.scalars(
        select(User).where(func.lower(User.email)  == func.lower(credentials.email) )
    ).first()
    user = authenticate_user(db_user, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        user={"email": user.email, "id": user.id}, expires_delta=access_token_expires
    )
    return {"token": access_token, "type": "bearer"}

