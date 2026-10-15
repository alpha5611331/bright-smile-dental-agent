from httpx import AsyncClient

from bright_smile.core.security import SESSION_COOKIE
from tests.factories import STAFF_PASSWORD


async def test_login_sets_a_hardened_session_cookie(client: AsyncClient) -> None:
    response = await client.post("/api/auth/login", json={"password": STAFF_PASSWORD})

    assert response.status_code == 204
    cookie = response.headers["set-cookie"].lower()
    assert cookie.startswith(f"{SESSION_COOKIE}=")
    for attribute in ("httponly", "samesite=lax", "path=/", "max-age=43200"):
        assert attribute in cookie
    assert "secure" not in cookie  # development; production adds Secure


async def test_wrong_password_is_rejected(client: AsyncClient) -> None:
    response = await client.post("/api/auth/login", json={"password": "wrong password"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
    assert "set-cookie" not in response.headers


async def test_me_reflects_the_session(client: AsyncClient, staff_client: AsyncClient) -> None:
    assert (await client.get("/api/auth/me")).status_code == 401
    assert (await staff_client.get("/api/auth/me")).status_code == 204


async def test_tampered_cookie_is_rejected(client: AsyncClient) -> None:
    client.cookies.set(SESSION_COOKIE, "forged.token.value")

    assert (await client.get("/api/auth/me")).status_code == 401


async def test_logout_clears_the_cookie(staff_client: AsyncClient) -> None:
    response = await staff_client.post("/api/auth/logout")

    assert response.status_code == 204
    assert f'{SESSION_COOKIE}=""' in response.headers["set-cookie"]
    assert (await staff_client.get("/api/auth/me")).status_code == 401


async def test_login_is_rate_limited(client: AsyncClient) -> None:
    for _ in range(5):
        await client.post("/api/auth/login", json={"password": "guess"})

    response = await client.post("/api/auth/login", json={"password": STAFF_PASSWORD})

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "rate_limited"
    assert int(response.headers["retry-after"]) > 0
