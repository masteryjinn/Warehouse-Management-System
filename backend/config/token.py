from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, Depends
import jwt
import datetime

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = "my_secret_key"
ALGORITHM = "HS256"

# Функція для створення JWT-токена
def create_jwt_token(user_id: int, role: str):
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": expiration,
        "iss": "my_server"  # Додаємо issuer для додаткової безпеки
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# Функція для перевірки токена
def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        # Декодуємо токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], issuer="my_server")
        return payload  # повертаємо payload, який містить user_id і role
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен прострочений")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Недійсний токен")
