from app.database.schemas import UserSchema, UserOutSchema, ResetPasswordSchema, ResetPasswordRequestScheam
from sqlalchemy import select, insert, delete, update, exc
from sqlalchemy.orm import Session, selectinload
from app.db_setup import get_db
from fastapi import Request, Depends, APIRouter, HTTPException, status, BackgroundTasks
from app.database.models import User
from app.auth import get_password_hash, get_user_id, create_access_token,  SECRET_KEY, ALGORITHM, oauth2_scheme, credentials_exception, ACCESS_TOKEN_EXPIRE_MINUTES
from app.logging.logger import logger
from typing import Annotated
from app.send_email import  send_verification_email, send_email_background
from app.config import backend_base_url, frontend_base_url
from datetime import timedelta
from app.send_email import env
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from jose import JWTError, jwt

router = APIRouter()

templates = Jinja2Templates(directory="./app/templates")

@router.post("/", status_code=201)
async def create_user( new_user: UserSchema,background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> UserOutSchema:
    try:
        hashed_password= get_password_hash(new_user.password)
        new_user.password = hashed_password  
        if not new_user.username:      
            new_user.username = new_user.first_name + " " + new_user.last_name
        created_user = User(**new_user.model_dump())
        db.add(created_user)
        db.commit()
        token_expiration_time = timedelta(minutes=5)
        validation_token = create_access_token(user={"id": created_user.id}, expires_delta=token_expiration_time)
        validation_url = f"{backend_base_url}/v1/users/verification/{validation_token}"
        # await send_verification_email(subject="Verify your account", email_to=new_user.email ,body={'title': 'Verification', 'name': f"{new_user.first_name} {new_user.last_name}", "link":validation_url })
        # send_email_background(background_tasks, subject="Verify your account", email_to=new_user.email ,body={'title': 'Verification', 'name': f"{new_user.first_name} {new_user.last_name}", "link":validation_url })
        return created_user

    except exc.IntegrityError as e:
        logger.error(e)
        db.rollback()  # Rollback the session to avoid transaction stuck
        # raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account with this email already exists.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", status_code=200)
def list_users(db: Session = Depends(get_db)):
    """
    Fetches all users
    """
    result = db.scalars(select(User).options(selectinload(User.profile))).all()
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users login credentials found")
    return result


@router.get("/me")
async def get_user(user_id: Annotated[int, Depends(get_user_id)], db: Session=Depends(get_db)) -> UserOutSchema:
    user = db.scalars(select(User).where(User.id == user_id).options(selectinload(User.profile))).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return user


@router.get("/validation")
def get_email_validation_status(user_id: Annotated[int, Depends(get_user_id)], db: Session = Depends(get_db)):
    query  = select(User).where(User.id == user_id)
    db_user = db.scalars(query).first()
    return {"verified": db_user.email_verified}


# Resend verification email
@router.post("/verification")
async def send_validation_email(user_id: Annotated[int, Depends(get_user_id)], db: Session=Depends(get_db)):
    db_user = db.scalars(select(User).where(User.id == user_id)).first()
    token_expiration_time = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    validation_token = create_access_token(user={"id": user_id}, expires_delta=token_expiration_time)
    validation_url = f"{backend_base_url}/v1/users/verification/{validation_token}"
    # await send_verification_email(subject="Verify your account", email_to=db_user.email ,body={'title': 'Verification', 'name': f"{db_user.first_name} {db_user.last_name}", "link":validation_url })
    return {"message": "Verification email sent"}



@router.get("/verification/{token}", response_class=HTMLResponse)
def validate_user(token: str,request: Request, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("id")
        query = select(User).where(User.id == user_id)
        db_user = db.scalars(query).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        db_user.email_verified = True
        db.commit()
        return templates.TemplateResponse(
            request=request, name="account_verified.html" , context={"message": "Your account has been verified."}
        )
    except JWTError:
        return templates.TemplateResponse(
            request=request, name="account_verified.html" , context={"message": "Token is not valid."}
        )
    except Exception:
        return templates.TemplateResponse(
            request=request, name="account_verified.html" , context={"message": "Sorry, Something went wrong!"}
        )

# User request to get reset password email
@router.post("/reset-password-request")
async def reset_password_request(data: ResetPasswordRequestScheam, db: Session= Depends(get_db)):
    db_user = db.scalars(select(User).where(User.email == data.email)).first()
    if db_user:
        token_expiration_time = timedelta(minutes=5)
        validation_token = create_access_token(user={"id": db_user.id, "email":db_user.email}, expires_delta=token_expiration_time)
        # The url of frontend reset password page
        pwd_reset_url = f"{frontend_base_url}/reset-password/{validation_token}"
        # await send_verification_email(subject="Reset password", email_to=db_user.email ,body={'title': 'Reset your passwrod', 'name': f"{db_user.first_name} {db_user.last_name}", "link":pwd_reset_url })
        return {"message": "email sent"}
    else:
        raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= "Email is not registered")

@router.post("/reset-password")
def reset_password(data: ResetPasswordSchema, token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("id")
        db_user = db.scalars(select(User).where(User.id == user_id)).first()
        if not db_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= "User does not exist")
        hashed_password= get_password_hash(data.password)
        db_user.password = hashed_password
        db.add(db_user)
        db.commit()
        return {"message": "user password updated"}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Your session has expired, please send another request to reset your password.")


@router.get("/refresh-token")
def refresh_token(user_id: Annotated[int, Depends(get_user_id)]):
    token_expiration_time = timedelta(minutes=5)
    token = create_access_token(user={"id": user_id}, expires_delta=token_expiration_time)
    return {"token": token}

@router.get("/{user_id}", status_code=200)
def list_users(user_id: int, db: Session = Depends(get_db)):
    """
    Fetches one user based on user_id
    """
    result = db.scalars(select(User).where(User.id == user_id).options(selectinload(User.profile))).first()
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users login credentials found")
    return result # Returns the password for now. Passwords needs to be hashed.

@router.delete("/{users_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_users(users_id: int, db: Session = Depends(get_db)):
    """
    Deletes a user based on an id
    """
    query = delete(User).where(User.id == users_id)
    db.execute(query)
    db.commit()
    if query is None:
        raise HTTPException(status_code=404, detail="User not found")