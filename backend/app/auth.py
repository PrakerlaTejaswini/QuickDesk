from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from jose import jwt
from passlib.context import CryptContext

from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/token"
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:

    return pwd_context.verify(
        plain_password,
        hashed_password
    )


def create_access_token(user: User):

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user.id),
        "role": user.role,
        "exp": expire
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials"
    )

    try:

        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        user_id = payload.get("sub")

        if not user_id:
            raise credentials_exception

    except Exception:
        raise credentials_exception

    user = db.query(User).filter(
        User.id == int(user_id)
    ).first()

    if not user:
        raise credentials_exception

    return user


def require_role(role: str):

    def role_checker(
        user: User = Depends(get_current_user)
    ):

        if user.role != role:

            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions"
            )

        return user

    return role_checker