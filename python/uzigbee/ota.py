"""OTA helpers (client + server control plane with safe fallbacks)."""

try:
    from .core import ZigbeeError
except Exception:
    class ZigbeeError(Exception):
        pass


OTA_STATE_IDLE = "idle"
OTA_STATE_CLIENT_ACTIVE = "client_active"
OTA_STATE_SERVER_ACTIVE = "server_active"


def _try_call(method, *args, **kwargs):
    try:
        return True, method(*args, **kwargs)
    except TypeError:
        return False, None


def _call_method_variants(obj, method_names, variants):
    for name in method_names:
        method = getattr(obj, name, None)
        if method is None:
            continue
        for args, kwargs in variants:
            ok, result = _try_call(method, *args, **kwargs)
            if ok:
                return result
    raise ZigbeeError("OTA method not available in firmware")


def _has_method(obj, method_names):
    for name in method_names:
        if callable(getattr(obj, name, None)):
            return True
    return False


def is_control_supported(stack):
    """Return whether OTA client control plane is enabled in current firmware."""
    method = getattr(stack, "ota_client_control_supported", None)
    if method is None:
        return False
    return bool(method())


def is_server_supported(stack):
    """Return whether OTA server control API is exposed by current firmware."""
    return _has_method(stack, ("ota_server_start", "ota_start_server"))


def capabilities(stack):
    """Return OTA capability flags for current firmware."""
    return {
        "client_control": bool(is_control_supported(stack)),
        "server_control": bool(is_server_supported(stack)),
    }


def set_query_interval_if_supported(stack, endpoint_id=1, interval_min=5):
    """Set query interval only when OTA client control plane is available."""
    if not is_control_supported(stack):
        return False
    set_query_interval(stack, endpoint_id=endpoint_id, interval_min=interval_min)
    return True


def query_image_if_supported(stack, server_ep=1, server_addr=0x00):
    """Trigger image query only when OTA client control plane is available."""
    if not is_control_supported(stack):
        return False
    query_image(stack, server_ep=server_ep, server_addr=server_addr)
    return True


def stop_query_if_supported(stack):
    """Stop OTA query only when OTA client control plane is available."""
    if not is_control_supported(stack):
        return False
    stop_query(stack)
    return True


def set_query_interval(stack, endpoint_id=1, interval_min=5):
    """Configure OTA client periodic query interval in minutes."""
    stack.ota_client_query_interval_set(endpoint_id=int(endpoint_id), interval_min=int(interval_min))
    return (int(endpoint_id), int(interval_min))


def query_image(stack, server_ep=1, server_addr=0x00):
    """Trigger OTA client query to a server endpoint/address."""
    stack.ota_client_query_image_req(server_ep=int(server_ep), server_addr=int(server_addr))
    return (int(server_ep), int(server_addr))


def stop_query(stack):
    """Stop ongoing periodic OTA client image query."""
    stack.ota_client_query_image_stop()
    return True


def start_client(stack, callback=None, endpoint_id=1, strict=False):
    """Start OTA client service if firmware exposes explicit start API.

    When API is absent:
    - strict=False: return a structured unsupported response.
    - strict=True: raise ZigbeeError.
    """
    variants = (
        ((), {"callback": callback, "endpoint_id": int(endpoint_id)}),
        ((), {"callback": callback}),
        ((), {"endpoint_id": int(endpoint_id)}),
        ((callback,), {}),
        ((int(endpoint_id),), {}),
        ((), {}),
    )
    try:
        result = _call_method_variants(stack, ("ota_client_start", "ota_start_client"), variants)
        return {
            "started": True,
            "endpoint_id": int(endpoint_id),
            "result": result,
        }
    except ZigbeeError:
        if strict:
            raise
        return {
            "started": False,
            "reason": "unsupported",
        }


def stop_client(stack, strict=False):
    """Stop OTA client service if firmware exposes explicit stop API."""
    variants = (
        ((), {}),
    )
    try:
        result = _call_method_variants(stack, ("ota_client_stop", "ota_stop_client"), variants)
        return {
            "stopped": True,
            "result": result,
        }
    except ZigbeeError:
        if strict:
            raise
        return {
            "stopped": False,
            "reason": "unsupported",
        }


def start_server(
    stack,
    image_path,
    file_version,
    hw_version,
    endpoint_id=1,
    manufacturer_code=None,
    image_type=None,
    min_hw_version=None,
    max_hw_version=None,
    strict=False,
):
    """Start OTA server if firmware exposes server control API."""
    variants = (
        (
            (),
            {
                "image_path": str(image_path),
                "file_version": int(file_version),
                "hw_version": int(hw_version),
                "endpoint_id": int(endpoint_id),
                "manufacturer_code": None if manufacturer_code is None else int(manufacturer_code),
                "image_type": None if image_type is None else int(image_type),
                "min_hw_version": None if min_hw_version is None else int(min_hw_version),
                "max_hw_version": None if max_hw_version is None else int(max_hw_version),
            },
        ),
        (
            (),
            {
                "image_path": str(image_path),
                "file_version": int(file_version),
                "hw_version": int(hw_version),
            },
        ),
        (
            (str(image_path), int(file_version), int(hw_version)),
            {},
        ),
    )
    try:
        result = _call_method_variants(stack, ("ota_server_start", "ota_start_server"), variants)
        return {
            "started": True,
            "image_path": str(image_path),
            "file_version": int(file_version),
            "hw_version": int(hw_version),
            "endpoint_id": int(endpoint_id),
            "result": result,
        }
    except ZigbeeError:
        if strict:
            raise
        return {
            "started": False,
            "reason": "unsupported",
            "image_path": str(image_path),
            "file_version": int(file_version),
            "hw_version": int(hw_version),
        }


def stop_server(stack, strict=False):
    """Stop OTA server if firmware exposes server stop API."""
    variants = (
        ((), {}),
    )
    try:
        result = _call_method_variants(stack, ("ota_server_stop", "ota_stop_server"), variants)
        return {
            "stopped": True,
            "result": result,
        }
    except ZigbeeError:
        if strict:
            raise
        return {
            "stopped": False,
            "reason": "unsupported",
        }


class OtaManager:
    """Stateful OTA manager around stack-level helper calls."""

    __slots__ = (
        "stack",
        "_state",
        "_client_started",
        "_server_started",
        "_last_error",
        "_last_result",
    )

    def __init__(self, stack):
        self.stack = stack
        self._state = OTA_STATE_IDLE
        self._client_started = False
        self._server_started = False
        self._last_error = None
        self._last_result = None

    def status(self):
        return {
            "state": str(self._state),
            "client_started": bool(self._client_started),
            "server_started": bool(self._server_started),
            "capabilities": capabilities(self.stack),
            "last_error": self._last_error,
            "last_result": self._last_result,
        }

    def start_client(self, callback=None, endpoint_id=1, strict=False):
        result = start_client(
            self.stack,
            callback=callback,
            endpoint_id=endpoint_id,
            strict=strict,
        )
        self._last_result = result
        if result.get("started"):
            self._client_started = True
            self._state = OTA_STATE_CLIENT_ACTIVE
            self._last_error = None
        else:
            self._last_error = result.get("reason")
        return result

    def stop_client(self, strict=False):
        result = stop_client(self.stack, strict=strict)
        self._last_result = result
        if result.get("stopped"):
            self._client_started = False
            if not self._server_started:
                self._state = OTA_STATE_IDLE
            self._last_error = None
        else:
            self._last_error = result.get("reason")
        return result

    def start_server(
        self,
        image_path,
        file_version,
        hw_version,
        endpoint_id=1,
        manufacturer_code=None,
        image_type=None,
        min_hw_version=None,
        max_hw_version=None,
        strict=False,
    ):
        result = start_server(
            self.stack,
            image_path=image_path,
            file_version=file_version,
            hw_version=hw_version,
            endpoint_id=endpoint_id,
            manufacturer_code=manufacturer_code,
            image_type=image_type,
            min_hw_version=min_hw_version,
            max_hw_version=max_hw_version,
            strict=strict,
        )
        self._last_result = result
        if result.get("started"):
            self._server_started = True
            self._state = OTA_STATE_SERVER_ACTIVE
            self._last_error = None
        else:
            self._last_error = result.get("reason")
        return result

    def stop_server(self, strict=False):
        result = stop_server(self.stack, strict=strict)
        self._last_result = result
        if result.get("stopped"):
            self._server_started = False
            if not self._client_started:
                self._state = OTA_STATE_IDLE
            self._last_error = None
        else:
            self._last_error = result.get("reason")
        return result

    def set_query_interval(self, endpoint_id=1, interval_min=5):
        value = set_query_interval(self.stack, endpoint_id=endpoint_id, interval_min=interval_min)
        self._last_result = {
            "set_query_interval": value,
        }
        self._last_error = None
        return value

    def query_image(self, server_ep=1, server_addr=0x00):
        value = query_image(self.stack, server_ep=server_ep, server_addr=server_addr)
        self._last_result = {
            "query_image": value,
        }
        self._last_error = None
        return value

    def stop_query(self):
        value = stop_query(self.stack)
        self._last_result = {
            "stop_query": bool(value),
        }
        self._last_error = None
        return bool(value)
