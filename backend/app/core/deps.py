"""
Authentication dependencies for FastAPI.
Provides current user injection and role-based access control.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core import database
from app.core.security import decode_token, TokenData
from app.models.user import User, UserRole

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(database.get_db)
) -> Optional[User]:
    """
    Get the current authenticated user from the JWT token.
    Returns None if no valid token is provided.
    """
    if not token:
        return None
    
    token_data = decode_token(token)
    if not token_data:
        return None
    
    user = db.query(User).filter(User.id == token_data.user_id).first()
    
    if user and not user.is_active:
        return None
    
    return user


async def get_current_user_required(
    user: Optional[User] = Depends(get_current_user)
) -> User:
    """
    Get the current user, raising an error if not authenticated.
    Use this for endpoints that require authentication.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_roles(allowed_roles: List[UserRole]):
    """
    Dependency factory for role-based access control.
    Usage: Depends(require_roles([UserRole.ADMIN, UserRole.MANAGER]))
    """
    async def role_checker(
        user: User = Depends(get_current_user_required)
    ) -> User:
        if user.is_superuser:
            return user
        
        if user.role not in [r.value for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[r.value for r in allowed_roles]}"
            )
        return user
    
    return role_checker


# Pre-built role dependencies
require_admin = require_roles([UserRole.ADMIN])
require_manager = require_roles([UserRole.ADMIN, UserRole.MANAGER])
require_agent = require_roles([UserRole.ADMIN, UserRole.MANAGER, UserRole.AGENT])
