"""
DevAd - Hindsight Cloud Integration

Handles:
- Hindsight Cloud health checks
- Campaign experience recall
- Campaign experience retention
- Campaign outcome retention
- Observation retention

Hindsight Cloud:
https://api.hindsight.vectorize.io
"""

import logging
from typing import Any, Dict, List, Optional

import httpx

from ..config import settings


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT = 30.0
RETAIN_TIMEOUT = 60.0

RETAINED_SENTINEL = "__HINDSIGHT_RETAINED__"


# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def _get_base_url() -> str:
    """
    Return the configured Hindsight API base URL without a trailing slash.
    """
    return (settings.HINDSIGHT_API_URL or "").strip().rstrip("/")


def _get_bank_id(bank_id: Optional[str] = None) -> str:
    """
    Return the supplied bank ID or the default configured bank ID.
    """
    return (
        bank_id
        or (settings.HINDSIGHT_BANK_ID or "").strip()
    )


def _get_headers() -> Dict[str, str]:
    """
    Build HTTP headers for Hindsight Cloud.
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    api_key = (settings.HINDSIGHT_API_KEY or "").strip()

    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    return headers


def _validate_configuration() -> None:
    """
    Validate Hindsight configuration before making an API request.
    """
    base_url = _get_base_url()
    bank_id = _get_bank_id()
    api_key = (settings.HINDSIGHT_API_KEY or "").strip()

    if not base_url:
        raise RuntimeError(
            "HINDSIGHT_API_URL is not configured."
        )

    if not bank_id:
        raise RuntimeError(
            "HINDSIGHT_BANK_ID is not configured."
        )

    invalid_placeholders = {
        "",
        "your-hindsight-api-key-here",
        "your-api-key",
        "your_hindsight_api_key",
        "your-hindsight-api-key",
    }

    if api_key.lower() in invalid_placeholders:
        raise RuntimeError(
            "HINDSIGHT_API_KEY is missing or still contains "
            "a placeholder value."
        )


def _raise_hindsight_http_error(
    response: httpx.Response,
    operation: str,
    bank_id: str,
) -> None:
    """
    Convert an Hindsight HTTP error into a useful RuntimeError.
    """
    status_code = response.status_code

    try:
        body = response.json()
    except ValueError:
        body = response.text

    logger.error(
        "Hindsight %s failed: status=%s bank=%s body=%s",
        operation,
        status_code,
        bank_id,
        body,
    )

    if status_code == 401:
        raise RuntimeError(
            f"Hindsight {operation} failed with HTTP 401. "
            "Check HINDSIGHT_API_KEY."
        )

    if status_code == 403:
        raise RuntimeError(
            f"Hindsight {operation} failed with HTTP 403. "
            "Check API key permissions for the memory bank."
        )

    if status_code == 404:
        raise RuntimeError(
            f"Hindsight {operation} failed with HTTP 404. "
            f"Check HINDSIGHT_API_URL and "
            f"HINDSIGHT_BANK_ID='{bank_id}'."
        )

    if status_code == 402:
        raise RuntimeError(
            f"Hindsight {operation} failed with HTTP 402. "
            "The Hindsight account may have insufficient credits."
        )

    if status_code == 422:
        raise RuntimeError(
            f"Hindsight {operation} failed with HTTP 422. "
            f"Invalid request: {body}"
        )

    raise RuntimeError(
        f"Hindsight {operation} failed with HTTP {status_code}: {body}"
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

async def health_check() -> dict:
    """
    Check Hindsight Cloud readiness.

    Endpoint:
        GET /health/ready
    """
    try:
        _validate_configuration()

        url = f"{_get_base_url()}/health/ready"

        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:
            response = await client.get(
                url,
                headers=_get_headers(),
            )

        try:
            data = response.json()
        except ValueError:
            data = {
                "text": response.text,
            }

        return {
            "available": response.status_code == 200,
            "status_code": response.status_code,
            "status": data,
        }

    except httpx.TimeoutException:
        logger.warning(
            "Hindsight health check timed out."
        )

        return {
            "available": False,
            "error": "Hindsight health check timed out.",
        }

    except httpx.ConnectError:
        logger.warning(
            "Could not connect to Hindsight Cloud."
        )

        return {
            "available": False,
            "error": (
                "Could not connect to Hindsight Cloud. "
                "Check HINDSIGHT_API_URL and internet connectivity."
            ),
        }

    except Exception as exc:
        logger.warning(
            "Hindsight health check failed: %s",
            exc,
        )

        return {
            "available": False,
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# Recall
# ---------------------------------------------------------------------------

async def recall_campaign_experience(
    query: str,
    limit: int = 10,
    bank_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Recall campaign-related experience and observation memories.

    Hindsight endpoint:

        POST /v1/default/banks/{bank_id}/memories/recall
    """

    _validate_configuration()

    query = (query or "").strip()

    if not query:
        return []

    limit = max(0, limit)

    if limit == 0:
        return []

    bid = _get_bank_id(bank_id)

    payload = {
        "query": query,
        # DevAd cares about prior campaign experiences and consolidated
        # observations; world knowledge is not campaign performance history.
        "types": ["experience", "observation"],
        "prefer_observations": True,
        "budget": "high",
        "max_tokens": 4096,
    }

    url = (
        f"{_get_base_url()}"
        f"/v1/default/banks/{bid}/memories/recall"
    )

    try:
        async with httpx.AsyncClient(
            timeout=DEFAULT_TIMEOUT
        ) as client:
            response = await client.post(
                url,
                headers=_get_headers(),
                json=payload,
            )

        if response.status_code >= 400:
            _raise_hindsight_http_error(
                response=response,
                operation="recall",
                bank_id=bid,
            )

        data = response.json()

        if not isinstance(data, dict):
            logger.warning(
                "Unexpected Hindsight recall response type: %s",
                type(data).__name__,
            )
            return []

        results = data.get("results", [])

        if not isinstance(results, list):
            logger.warning(
                "Unexpected Hindsight recall results type: %s",
                type(results).__name__,
            )
            return []

        return results[:limit]

    except RuntimeError:
        raise

    except httpx.ConnectError as exc:
        logger.error(
            "Could not connect to Hindsight Cloud during recall: %s",
            exc,
        )

        raise RuntimeError(
            "Hindsight service unavailable during recall. "
            "Check HINDSIGHT_API_URL and internet connectivity."
        )

    except httpx.TimeoutException as exc:
        logger.error(
            "Hindsight recall timed out: %s",
            exc,
        )

        raise RuntimeError(
            "Hindsight recall timed out."
        )

    except Exception as exc:
        logger.exception(
            "Unexpected Hindsight recall error."
        )

        raise RuntimeError(
            f"Hindsight recall failed: {exc}"
        )


async def recall_observations(
    query: str,
    limit: int = 5,
    bank_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Recall only consolidated observations from Hindsight.
    """

    _validate_configuration()

    query = (query or "").strip()

    if not query:
        return []

    limit = max(0, limit)

    if limit == 0:
        return []

    bid = _get_bank_id(bank_id)

    payload = {
        "query": query,
        "types": [
            "observation",
        ],
    }

    url = (
        f"{_get_base_url()}"
        f"/v1/default/banks/{bid}/memories/recall"
    )

    try:
        async with httpx.AsyncClient(
            timeout=DEFAULT_TIMEOUT
        ) as client:
            response = await client.post(
                url,
                headers=_get_headers(),
                json=payload,
            )

        if response.status_code >= 400:
            _raise_hindsight_http_error(
                response=response,
                operation="observation recall",
                bank_id=bid,
            )

        data = response.json()

        if not isinstance(data, dict):
            return []

        results = data.get("results", [])

        if not isinstance(results, list):
            return []

        return results[:limit]

    except RuntimeError:
        raise

    except httpx.ConnectError as exc:
        logger.error(
            "Could not connect to Hindsight Cloud during observation recall: %s",
            exc,
        )

        raise RuntimeError(
            "Hindsight service unavailable during observation recall."
        )

    except httpx.TimeoutException:
        raise RuntimeError(
            "Hindsight observation recall timed out."
        )

    except Exception as exc:
        logger.exception(
            "Unexpected Hindsight observation recall error."
        )

        raise RuntimeError(
            f"Hindsight observation recall failed: {exc}"
        )


# ---------------------------------------------------------------------------
# Retain
# ---------------------------------------------------------------------------

async def retain_campaign_experience(
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    bank_id: Optional[str] = None,
) -> Optional[str]:
    """
    Store a campaign experience in Hindsight Cloud.

    IMPORTANT:
    Hindsight's synchronous Retain response does not necessarily contain
    an individual memory ID. A successful response can contain:

        {
            "success": true,
            "bank_id": "...",
            "items_count": 1,
            "async": false,
            "operation_id": null
        }

    Therefore this function returns:

    - actual ID if Hindsight provides one
    - operation ID if asynchronous processing provides one
    - RETAINED_SENTINEL when Retain succeeded but no ID was returned
    - None only when the operation did not succeed

    The sentinel prevents the application from incorrectly marking a
    successful Retain operation as "failed".
    """

    _validate_configuration()

    content = (content or "").strip()

    if not content:
        raise ValueError(
            "Cannot retain an empty campaign experience."
        )

    bid = _get_bank_id(bank_id)

    item: Dict[str, Any] = {
        "content": content,
    }

    # Hindsight supports `context` on each memory item.
    # Convert DevAd's metadata dictionary into readable context.
    if metadata:
        context_parts: List[str] = []

        for key, value in metadata.items():
            if value is None:
                continue

            context_parts.append(
                f"{key}: {value}"
            )

        if context_parts:
            item["context"] = (
                "DevAd campaign context. "
                + "; ".join(context_parts)
            )

    payload = {
        "items": [
            item,
        ],
        "async": False,
    }

    url = (
        f"{_get_base_url()}"
        f"/v1/default/banks/{bid}/memories"
    )

    try:
        logger.info(
            "Sending campaign experience to Hindsight: bank=%s",
            bid,
        )

        async with httpx.AsyncClient(
            timeout=RETAIN_TIMEOUT
        ) as client:
            response = await client.post(
                url,
                headers=_get_headers(),
                json=payload,
            )

        if response.status_code >= 400:
            _raise_hindsight_http_error(
                response=response,
                operation="retain",
                bank_id=bid,
            )

        data = response.json()

        if not isinstance(data, dict):
            raise RuntimeError(
                "Hindsight retain returned an unexpected response."
            )

        success = data.get("success")

        if success is not True:
            raise RuntimeError(
                f"Hindsight retain did not report success: {data}"
            )

        items_count = data.get("items_count", 0)
        is_async = bool(data.get("async", False))
        operation_id = data.get("operation_id")

        logger.info(
            "Hindsight retain succeeded: "
            "bank=%s items_count=%s async=%s operation_id=%s",
            bid,
            items_count,
            is_async,
            operation_id,
        )

        # If Hindsight explicitly gives us an ID, preserve it.
        memory_id = data.get("id")

        if memory_id:
            return str(memory_id)

        memory_id = data.get("memory_id")

        if memory_id:
            return str(memory_id)

        # Async operations provide an operation ID.
        if operation_id:
            return str(operation_id)

        # Synchronous success with no memory ID is still success.
        return RETAINED_SENTINEL

    except RuntimeError:
        raise

    except httpx.ConnectError as exc:
        logger.error(
            "Could not connect to Hindsight Cloud during retain: %s",
            exc,
        )

        raise RuntimeError(
            "Hindsight service unavailable during retain. "
            "Check HINDSIGHT_API_URL and internet connectivity."
        )

    except httpx.TimeoutException:
        logger.error(
            "Hindsight retain timed out: %s",
            exc,
        )

        raise RuntimeError(
            "Hindsight retain timed out."
        )

    except Exception as exc:
        logger.exception(
            "Unexpected Hindsight retain error."
        )

        raise RuntimeError(
            f"Hindsight retain failed: {exc}"
        )


# ---------------------------------------------------------------------------
# Specialized retain functions
# ---------------------------------------------------------------------------

async def retain_campaign_outcome(
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    bank_id: Optional[str] = None,
) -> Optional[str]:
    """
    Store a campaign outcome as an experiential memory.
    """

    return await retain_campaign_experience(
        content=content,
        metadata=metadata,
        bank_id=bank_id,
    )


async def retain_observation(
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    bank_id: Optional[str] = None,
) -> Optional[str]:
    """
    Store an explicit DevAd observation.

    Hindsight itself determines the resulting memory classification
    during the Retain pipeline.
    """

    return await retain_campaign_experience(
        content=content,
        metadata=metadata,
        bank_id=bank_id,
    )


# ---------------------------------------------------------------------------
# Memory listing - useful for DevAd debugging
# ---------------------------------------------------------------------------

async def list_memories(
    limit: int = 20,
    bank_id: Optional[str] = None,
    memory_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List memory units from Hindsight.

    This is useful for verifying that a newly retained campaign experience
    actually exists in the bank.

    Endpoint:

        GET /v1/default/banks/{bank_id}/memories/list
    """

    _validate_configuration()

    limit = max(1, min(limit, 100))

    bid = _get_bank_id(bank_id)

    params: Dict[str, Any] = {
        "limit": limit,
        "offset": 0,
    }

    if memory_type:
        params["type"] = memory_type

    url = (
        f"{_get_base_url()}"
        f"/v1/default/banks/{bid}/memories/list"
    )

    try:
        async with httpx.AsyncClient(
            timeout=DEFAULT_TIMEOUT
        ) as client:
            response = await client.get(
                url,
                headers=_get_headers(),
                params=params,
            )

        if response.status_code >= 400:
            _raise_hindsight_http_error(
                response=response,
                operation="list memories",
                bank_id=bid,
            )

        data = response.json()

        if not isinstance(data, dict):
            return []

        items = data.get("items", [])

        if not isinstance(items, list):
            return []

        return items[:limit]

    except RuntimeError:
        raise

    except httpx.ConnectError:
        raise RuntimeError(
            "Hindsight service unavailable while listing memories."
        )

    except httpx.TimeoutException:
        raise RuntimeError(
            "Hindsight memory listing timed out."
        )

    except Exception as exc:
        logger.exception(
            "Unexpected Hindsight memory listing error."
        )

        raise RuntimeError(
            f"Hindsight memory listing failed: {exc}"
        )

async def count_memories(
    memory_type: Optional[str] = None,
    bank_id: Optional[str] = None,
) -> int:
    """Return the server-reported Hindsight memory-unit count."""
    _validate_configuration()
    bid = _get_bank_id(bank_id)
    params: Dict[str, Any] = {"limit": 1, "offset": 0}
    if memory_type:
        params["type"] = memory_type
    url = f"{_get_base_url()}/v1/default/banks/{bid}/memories/list"
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(url, headers=_get_headers(), params=params)
        if response.status_code >= 400:
            _raise_hindsight_http_error(response, "count memories", bid)
        data = response.json()
        return int(data.get("total", len(data.get("items", []))))
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Hindsight memory count failed: {exc}") from exc

