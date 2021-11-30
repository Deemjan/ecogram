from fastapi.exceptions import HTTPException
from typing import List
import logging
from db.sql_models import User

from fastapi import Depends

from src.views.auth_views import get_current_user

logger = logging.getLogger(__name__)


class RoleChecker:
    def __init__(self, allowed_roles: List):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            logger.debug(f"User with role {user.role} not in {self.allowed_roles}")
            raise HTTPException(status_code=403, detail="Operation not permitted")


basic_access = RoleChecker(["base_user", "courier"])
