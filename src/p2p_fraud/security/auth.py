"""Authentification basique + rôles RBAC.

Conception minimaliste pour Sprint 7 :
- Hash bcrypt-like (PBKDF2-SHA256, 200 000 itérations) pour ne pas ajouter
  une dépendance bcrypt — cryptography fournit ce qu'il faut.
- Store JSON + sel par user, lecture seule en runtime (pas de création
  d'user via UI ; on génère le store hors ligne avec `auth_cli`).
- Rôles ordonnés : viewer < analyst < manager < admin.
- Décorateur `@requires_role` pour les services qui ont besoin d'un check
  programmatique. La page Streamlit garde un check explicite.
"""

from __future__ import annotations

import functools
import hashlib
import json
import logging
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Any

from ..config import get_settings

log = logging.getLogger(__name__)

DEFAULT_USERS_PATH = Path("data") / "security" / "users.json"
DEFAULT_PBKDF2_ITERATIONS = 200_000


class AuthError(RuntimeError):
    """Erreur d'authentification ou d'autorisation."""


class Role(IntEnum):
    """Rôles ordonnés du moins privilégié au plus privilégié."""

    VIEWER = 1  # lecture findings + cockpit
    ANALYST = 2  # création / clôture de cases
    MANAGER = 3  # whitelist, modification weights, escalade
    ADMIN = 4  # gestion users, accès clé crypto

    @classmethod
    def parse(cls, name: str | int | Role) -> Role:
        if isinstance(name, Role):
            return name
        if isinstance(name, int):
            return cls(name)
        return cls[name.upper()]


@dataclass(frozen=True)
class User:
    username: str
    role: Role
    salt_hex: str
    hash_hex: str
    iterations: int

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "role": self.role.name,
            "salt_hex": self.salt_hex,
            "hash_hex": self.hash_hex,
            "iterations": self.iterations,
        }

    @classmethod
    def from_dict(cls, d: dict) -> User:
        return cls(
            username=d["username"],
            role=Role.parse(d["role"]),
            salt_hex=d["salt_hex"],
            hash_hex=d["hash_hex"],
            iterations=int(d.get("iterations", DEFAULT_PBKDF2_ITERATIONS)),
        )


def _pbkdf2(password: str, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)


def hash_password(
    password: str, *, iterations: int = DEFAULT_PBKDF2_ITERATIONS
) -> tuple[str, str, int]:
    """Renvoie (salt_hex, hash_hex, iterations) pour un mot de passe en clair."""
    salt = secrets.token_bytes(16)
    h = _pbkdf2(password, salt, iterations)
    return salt.hex(), h.hex(), iterations


def verify_password(password: str, user: User) -> bool:
    salt = bytes.fromhex(user.salt_hex)
    h = _pbkdf2(password, salt, user.iterations)
    return secrets.compare_digest(h.hex(), user.hash_hex)


class AuthService:
    """Charge un store JSON read-only en mémoire et expose login + autorisation."""

    def __init__(self, users_path: Path | None = None, *, users: list[User] | None = None) -> None:
        self._users: dict[str, User] = {}
        if users is not None:
            self._users = {u.username: u for u in users}
            return
        path = users_path or Path(get_settings().p2p_fraud_users_path or str(DEFAULT_USERS_PATH))
        if path.exists():
            with path.open(encoding="utf-8") as f:
                raw = json.load(f)
            self._users = {d["username"]: User.from_dict(d) for d in raw.get("users", [])}
        else:
            log.info(
                "Aucun store users.json trouvé (%s). AuthService en mode 'no-auth' "
                "(à n'utiliser qu'en démo).",
                path,
            )

    @property
    def has_users(self) -> bool:
        return bool(self._users)

    def authenticate(self, username: str, password: str) -> User:
        u = self._users.get(username)
        if u is None or not verify_password(password, u):
            raise AuthError("Identifiants invalides.")
        return u

    def get_user(self, username: str) -> User | None:
        return self._users.get(username)

    def has_permission(self, user: User | None, required: Role) -> bool:
        if user is None:
            return not self.has_users  # démo : pas d'users → tout est permis
        return int(user.role) >= int(required)


def requires_role(required: Role) -> Callable:
    """Décorateur : exige un kwarg `current_user: User` >= `required`.

    Lève AuthError si manquant ou insuffisant. Conçu pour décorer les méthodes
    de services métier (case service, etc.) sans dépendre de Streamlit.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            user: User | None = kwargs.get("current_user")
            if user is None:
                # Tolère l'absence si pas d'auth configurée (legacy)
                if get_settings().p2p_fraud_auth_required:
                    raise AuthError(f"current_user requis pour {func.__name__}.")
                return func(*args, **kwargs)
            if int(user.role) < int(required):
                raise AuthError(
                    f"Rôle insuffisant pour {func.__name__} : {user.role.name} < {required.name}."
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator
