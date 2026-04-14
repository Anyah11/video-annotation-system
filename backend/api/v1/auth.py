from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database import get_db
from models import User
from auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    get_current_admin_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register")
async def register_user(
    username: str,
    email: str,
    password: str,
    is_admin: bool = False,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """
    Register a new user (admin only)
    Only admins can create new users
    """
    # Check if username exists
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Check if email exists
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(password)
    new_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_admin=1 if is_admin else 0
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "success": True,
        "message": f"User {username} created successfully",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "is_admin": new_user.is_admin
        }
    }


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with username and password
    Returns JWT access token
    """
    # Find user by username
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        }
    }


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current logged-in user information"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at.isoformat(),
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }


@router.get("/users")
async def list_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """List all users (admin only)"""
    users = db.query(User).all()
    
    return {
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
            for user in users
        ]
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Delete a user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deleting themselves
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    db.delete(user)
    db.commit()
    
    return {
        "success": True,
        "message": f"User {user.username} deleted successfully"
    }


@router.post("/create-first-admin")
async def create_first_admin(
    username: str,
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    """
    Create the first admin user
    Only works if no users exist in the database
    """
    # Check if any users exist
    if db.query(User).count() > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users already exist. Use /register endpoint instead."
        )
    
    # Create first admin
    hashed_password = get_password_hash(password)
    admin = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        is_admin=1
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    return {
        "success": True,
        "message": "First admin created successfully",
        "user": {
            "id": admin.id,
            "username": admin.username,
            "email": admin.email,
            "is_admin": admin.is_admin
        }
    }