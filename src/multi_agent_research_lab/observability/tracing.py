# ruff: noqa: SIM105
"""Tracing hooks.

This file integrates LangSmith and Langfuse to provide a robust hierarchical
tracing system (Parent: Multi-Agent-Run, Children: Supervisor, Researcher, Analyst, Writer).
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from time import perf_counter
from typing import Any

from dotenv import load_dotenv

# Load .env variables into os.environ
load_dotenv()

# Global context variables to track hierarchical traces/spans across async/sync boundaries safely.
_langfuse_active: ContextVar[Any] = ContextVar("langfuse_active", default=None)
_langsmith_active: ContextVar[Any] = ContextVar("langsmith_active", default=None)

# Lazy import helpers to avoid startup overhead or hard crashes if packages are missing
_langfuse_client: Any = None
_langsmith_client: Any = None


def _get_langfuse() -> Any:
    global _langfuse_client
    if _langfuse_client is not None:
        return _langfuse_client
    try:
        from langfuse import Langfuse
        # Ensure credentials exist
        if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
            _langfuse_client = Langfuse()
            return _langfuse_client
    except ImportError:
        pass
    return None


def _get_langsmith() -> Any:
    global _langsmith_client
    if _langsmith_client is not None:
        return _langsmith_client
    try:
        from langsmith import Client
        if os.getenv("LANGSMITH_API_KEY"):
            _langsmith_client = Client()
            return _langsmith_client
    except ImportError:
        pass
    return None


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Context manager for hierarchical tracing supporting LangSmith and Langfuse.

    Creates a parent trace or a child span depending on the current context.
    Ensures absolute safety by failing gracefully (non-blocking) on network or library errors.
    """
    started = perf_counter()
    span: dict[str, Any] = {"name": name, "attributes": attributes or {}, "duration_seconds": None}

    # 1. Initialize Langfuse span
    lf_client = _get_langfuse()
    lf_span = None
    lf_token = None
    if lf_client:
        try:
            parent_lf = _langfuse_active.get()
            if parent_lf is None:
                # Top-level Trace
                lf_span = lf_client.trace(name=name, metadata=attributes)
            else:
                # Child Span
                lf_span = parent_lf.span(name=name, metadata=attributes)
            lf_token = _langfuse_active.set(lf_span)
        except Exception:
            # Non-blocking graceful fallback
            pass

    # 2. Initialize Langsmith span
    ls_client = _get_langsmith()
    ls_span = None
    ls_token = None
    if ls_client:
        try:
            from langsmith.run_trees import RunTree
            parent_ls = _langsmith_active.get()
            if parent_ls is None:
                ls_span = RunTree(
                    name=name,
                    inputs=attributes or {},
                    project_name=os.getenv("LANGSMITH_PROJECT", "multi-agent-research-lab")
                )
                ls_span.post()
            else:
                ls_span = parent_ls.create_child(
                    name=name,
                    inputs=attributes or {}
                )
                ls_span.post()
            ls_token = _langsmith_active.set(ls_span)
        except Exception:
            # Non-blocking graceful fallback
            pass

    try:
        yield span
    except Exception as e:
        # Record error state in tracing
        if lf_span:
            try:
                lf_span.update(metadata={**(attributes or {}), "error": str(e)})
            except Exception:
                pass
        if ls_span:
            try:
                ls_span.end(outputs={"error": str(e)})
                ls_span.patch()
            except Exception:
                pass
        raise e
    finally:
        duration = perf_counter() - started
        span["duration_seconds"] = duration

        # End Langfuse tracing safely
        if lf_span:
            try:
                lf_span.update(metadata={**(attributes or {}), "duration_seconds": duration})
                # If it's a child span, we call end()
                if hasattr(lf_span, "end"):
                    lf_span.end()
            except Exception:
                pass
            if lf_token is not None:
                _langfuse_active.reset(lf_token)

        # End Langsmith tracing safely
        if ls_span:
            try:
                ls_span.end(outputs={"duration_seconds": duration})
                ls_span.patch()
            except Exception:
                pass
            if ls_token is not None:
                _langsmith_active.reset(ls_token)
