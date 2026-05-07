"""Tests auth / RBAC — Sprint 7."""

from __future__ import annotations

import os

import pytest

from p2p_fraud.security.auth import (
    AuthError,
    AuthService,
    Role,
    User,
    hash_password,
    requires_role,
    verify_password,
)


def _make_user(username: str, password: str, role: Role) -> User:
    salt, h, it = hash_password(password)
    return User(username=username, role=role, salt_hex=salt, hash_hex=h, iterations=it)


def test_role_ordering():
    assert Role.VIEWER < Role.ANALYST < Role.MANAGER < Role.ADMIN


def test_role_parse_accepts_str_int_and_role():
    assert Role.parse("viewer") == Role.VIEWER
    assert Role.parse("ADMIN") == Role.ADMIN
    assert Role.parse(2) == Role.ANALYST
    assert Role.parse(Role.MANAGER) == Role.MANAGER


def test_hash_and_verify_round_trip():
    user = _make_user("alice", "p@ssw0rd!", Role.ANALYST)
    assert verify_password("p@ssw0rd!", user)
    assert not verify_password("wrong", user)


def test_authenticate_unknown_user():
    svc = AuthService(users=[])
    with pytest.raises(AuthError):
        svc.authenticate("ghost", "x")


def test_authenticate_valid_user():
    svc = AuthService(users=[_make_user("alice", "secret", Role.MANAGER)])
    assert svc.authenticate("alice", "secret").role == Role.MANAGER


def test_has_permission_with_user():
    svc = AuthService(users=[_make_user("alice", "x", Role.ANALYST)])
    user = svc.get_user("alice")
    assert svc.has_permission(user, Role.VIEWER)
    assert svc.has_permission(user, Role.ANALYST)
    assert not svc.has_permission(user, Role.MANAGER)


def test_has_permission_no_users_returns_true():
    """Mode démo : si pas d'users définis, tout est permis."""
    svc = AuthService(users=[])
    assert svc.has_permission(None, Role.ADMIN)


def test_has_permission_with_users_blocks_anonymous():
    svc = AuthService(users=[_make_user("alice", "x", Role.VIEWER)])
    assert not svc.has_permission(None, Role.VIEWER)


def test_requires_role_decorator_blocks_low_role():
    @requires_role(Role.MANAGER)
    def sensitive(*, current_user: User | None = None) -> str:
        return "ok"

    viewer = _make_user("v", "x", Role.VIEWER)
    with pytest.raises(AuthError, match="insuffisant"):
        sensitive(current_user=viewer)


def test_requires_role_decorator_allows_sufficient_role():
    @requires_role(Role.ANALYST)
    def sensitive(*, current_user: User | None = None) -> str:
        return "ok"

    analyst = _make_user("a", "x", Role.ANALYST)
    assert sensitive(current_user=analyst) == "ok"


def test_requires_role_no_user_when_not_required(monkeypatch):
    """Mode démo : pas de user → on tolère (legacy)."""
    monkeypatch.delenv("P2P_FRAUD_AUTH_REQUIRED", raising=False)

    @requires_role(Role.MANAGER)
    def sensitive(*, current_user: User | None = None) -> str:
        return "ok"

    assert sensitive() == "ok"


def test_requires_role_strict_mode(monkeypatch):
    """Mode strict : exige un current_user."""
    monkeypatch.setenv("P2P_FRAUD_AUTH_REQUIRED", "1")

    @requires_role(Role.MANAGER)
    def sensitive(*, current_user: User | None = None) -> str:
        return "ok"

    with pytest.raises(AuthError, match="requis"):
        sensitive()
    os.environ.pop("P2P_FRAUD_AUTH_REQUIRED", None)


def test_user_serialization_round_trip():
    u = _make_user("alice", "x", Role.ANALYST)
    d = u.to_dict()
    u2 = User.from_dict(d)
    assert u2.username == u.username
    assert u2.role == u.role
    assert u2.hash_hex == u.hash_hex
