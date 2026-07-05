"""Tests guarding against a real production bug: HttpClient's session/connector
creation used to build the SSL context (blocking disk I/O via
ssl.create_default_context's load_verify_locations) directly on the event
loop, which Home Assistant's blocking-call detector caught live:

    Detected blocking call to load_verify_locations ... by custom
    integration 'centrometal_boiler' at .../HttpClient.py, line 112

Fixing that means _make_connector/_ensure_session/_require_session all
gained a real await point (the executor hop), which in turn opens a
concurrency hazard if not guarded: multiple coroutines calling
_ensure_session() before any session exists could each build and assign
their own ClientSession, leaking every one but the last. These tests cover
both, plus close_session() racing with concurrent session creation.
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
import ssl
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "custom_components" / "centrometal_boiler"))

# NOTE: plain `import centrometal_web_boiler.HttpClient as http_client_module`
# is NOT safe here. centrometal_web_boiler/__init__.py does
# `from .HttpClient import HttpClient`, and since the module is named
# HttpClient and the class inside it is *also* named HttpClient, that import
# overwrites the package's "HttpClient" attribute from "the module" to "the
# class" after it's imported. importlib.import_module() goes through
# sys.modules directly and isn't affected by that.
http_client_module = importlib.import_module("centrometal_web_boiler.HttpClient")
HttpClientBase = http_client_module.HttpClientBase


def test_make_connector_is_a_coroutine_function() -> None:
    # Guards against ever reverting to a plain sync function, which is
    # exactly what let the blocking SSL context build run on the event loop.
    assert inspect.iscoroutinefunction(http_client_module._make_connector)


def test_ensure_session_and_require_session_are_coroutine_functions() -> None:
    assert inspect.iscoroutinefunction(HttpClientBase._ensure_session)
    assert inspect.iscoroutinefunction(HttpClientBase._require_session)


def test_ssl_context_build_runs_off_the_event_loop_thread(monkeypatch) -> None:
    """Directly prove the blocking work happens on a different thread, not
    just that it was routed through run_in_executor."""

    async def runner() -> None:
        event_loop_thread = threading.get_ident()
        builder_threads: list[int] = []

        def fake_build_verified_ssl_context() -> ssl.SSLContext:
            builder_threads.append(threading.get_ident())
            return ssl.create_default_context()

        monkeypatch.setattr(http_client_module, "build_verified_ssl_context", fake_build_verified_ssl_context)

        connector = await http_client_module._make_connector()
        try:
            assert builder_threads
            assert builder_threads[0] != event_loop_thread
        finally:
            await connector.close()

    asyncio.run(runner())


def test_concurrent_first_callers_share_one_session(monkeypatch) -> None:
    """Regression test for the session-leak race, forced deterministically:
    every concurrent caller is made to reach the lock before any of them is
    allowed to finish creating a session, instead of hoping asyncio.gather's
    scheduling happens to interleave unfavorably on its own."""

    async def runner() -> None:
        connector_calls = 0
        connector_started = asyncio.Event()
        release_connector = asyncio.Event()

        async def delayed_make_connector():
            nonlocal connector_calls
            connector_calls += 1
            connector_started.set()
            await release_connector.wait()
            return http_client_module.aiohttp.TCPConnector()

        monkeypatch.setattr(http_client_module, "_make_connector", delayed_make_connector)

        client = HttpClientBase("user@example.com", "secret")
        tasks = [asyncio.create_task(client._ensure_session()) for _ in range(20)]

        await connector_started.wait()
        # Let every task get scheduled at least once. Without the lock, all
        # 20 would reach _make_connector before it's ever released.
        await asyncio.sleep(0)
        assert connector_calls == 1

        release_connector.set()
        sessions = await asyncio.gather(*tasks)
        try:
            assert connector_calls == 1
            assert all(s is sessions[0] for s in sessions)
            assert client.http_session is sessions[0]
        finally:
            await client.close_session()

    asyncio.run(runner())


def test_close_session_waits_for_the_same_lock_as_session_creation() -> None:
    """close_session() must be serialized against _ensure_session() via the
    same lock. Verified directly and deterministically: hold the lock
    ourselves and confirm close_session() can't proceed until it's released,
    rather than trying to engineer an emergent race through timing (which,
    checked directly, doesn't actually expose this: http_session stays None
    for the entire span of _ensure_session()'s await, so close_session()'s
    own `if self.http_session is not None` guard happens to no-op during
    that specific window regardless of locking -- the thing that actually
    needs guarding is close_session() landing between session creation
    finishing and the caller of _ensure_session() getting to use it)."""

    async def runner() -> None:
        client = HttpClientBase("user@example.com", "secret")
        await client._ensure_session()
        assert client.http_session is not None

        lock = client._session_lock
        release_holder = asyncio.Event()

        async def hold_the_lock():
            async with lock:
                await release_holder.wait()

        holder = asyncio.create_task(hold_the_lock())
        await asyncio.sleep(0)  # let holder acquire the lock first
        assert lock.locked()

        close_task = asyncio.create_task(client.close_session())
        try:
            await asyncio.wait_for(asyncio.shield(close_task), timeout=0.05)
            blocked_on_lock = False
        except asyncio.TimeoutError:
            blocked_on_lock = True
        assert blocked_on_lock, "close_session() completed while the lock was held -- it isn't actually using it"
        assert client.http_session is not None  # not yet cleared

        release_holder.set()
        await holder
        await close_task
        assert client.http_session is None

    asyncio.run(runner())
