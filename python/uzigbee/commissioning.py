"""Commissioning/network profile helpers for high-level API."""

NETWORK_MODE_AUTO = "auto"
NETWORK_MODE_FIXED = "fixed"
NETWORK_MODE_GUIDED = "guided"

_VALID_MODES = (
    NETWORK_MODE_AUTO,
    NETWORK_MODE_FIXED,
    NETWORK_MODE_GUIDED,
)

PROFILE_SOURCE_AUTO = "auto"
PROFILE_SOURCE_FIXED = "fixed"
PROFILE_SOURCE_GUIDED = "guided"
PROFILE_SOURCE_RESTORED = "restored"

_VALID_SOURCES = (
    PROFILE_SOURCE_AUTO,
    PROFILE_SOURCE_FIXED,
    PROFILE_SOURCE_GUIDED,
    PROFILE_SOURCE_RESTORED,
)


def _ieee_to_hex(ieee_addr):
    if ieee_addr is None:
        return None
    return "".join("{:02x}".format(int(b)) for b in bytes(ieee_addr))


def _normalize_ieee_addr(value):
    if value is None:
        return None
    if isinstance(value, str):
        compact = value.strip().lower().replace(":", "").replace("-", "").replace(" ", "")
        if len(compact) != 16:
            raise ValueError("ieee address hex string must have 16 hex chars")
        try:
            return bytes.fromhex(compact)
        except Exception:
            raise ValueError("invalid ieee address hex string")
    try:
        out = bytes(value)
    except Exception:
        raise ValueError("ieee address must be bytes-like or hex string")
    if len(out) != 8:
        raise ValueError("ieee address must be 8 bytes")
    return out


def normalize_mode(value, label="mode"):
    mode = str(value or NETWORK_MODE_AUTO).strip().lower()
    if mode not in _VALID_MODES:
        raise ValueError("invalid {}: {}".format(label, value))
    return mode


def infer_mode(mode, channel_mask=None, pan_id=None, extended_pan_id=None, label="mode"):
    mode = normalize_mode(mode, label=label)
    if mode == NETWORK_MODE_AUTO:
        if channel_mask is not None or pan_id is not None or extended_pan_id is not None:
            # Backward-compatible behavior for existing code paths that passed
            # explicit network params before introducing mode selectors.
            return NETWORK_MODE_FIXED
    return mode


def mode_profile_source(mode):
    mode = normalize_mode(mode)
    if mode == NETWORK_MODE_FIXED:
        return PROFILE_SOURCE_FIXED
    if mode == NETWORK_MODE_GUIDED:
        return PROFILE_SOURCE_GUIDED
    return PROFILE_SOURCE_AUTO


def channel_mask_to_single_channel(channel_mask):
    if channel_mask is None:
        return None
    mask = int(channel_mask)
    if mask <= 0:
        return None
    if mask & (mask - 1):
        return None
    channel = 0
    while mask > 1:
        mask >>= 1
        channel += 1
    if channel < 11 or channel > 26:
        return None
    return int(channel)


class NetworkProfile:
    """Serializable high-level network profile snapshot."""

    __slots__ = (
        "channel_mask",
        "pan_id",
        "extended_pan_id",
        "source",
        "formed_at_ms",
    )

    def __init__(
        self,
        channel_mask=None,
        pan_id=None,
        extended_pan_id=None,
        source=PROFILE_SOURCE_AUTO,
        formed_at_ms=None,
    ):
        self.channel_mask = None if channel_mask is None else int(channel_mask)
        self.pan_id = None if pan_id is None else int(pan_id)
        self.extended_pan_id = _normalize_ieee_addr(extended_pan_id)
        self.source = str(source or PROFILE_SOURCE_AUTO).strip().lower()
        if self.source not in _VALID_SOURCES:
            self.source = PROFILE_SOURCE_AUTO
        self.formed_at_ms = None if formed_at_ms is None else int(formed_at_ms)

    def update(
        self,
        channel_mask=None,
        pan_id=None,
        extended_pan_id=None,
        source=None,
        formed_at_ms=None,
    ):
        if channel_mask is not None:
            self.channel_mask = int(channel_mask)
        if pan_id is not None:
            self.pan_id = int(pan_id)
        if extended_pan_id is not None:
            self.extended_pan_id = _normalize_ieee_addr(extended_pan_id)
        if source is not None:
            source = str(source).strip().lower()
            if source in _VALID_SOURCES:
                self.source = source
        if formed_at_ms is not None:
            self.formed_at_ms = int(formed_at_ms)
        return self

    def to_dict(self):
        return {
            "channel_mask": None if self.channel_mask is None else int(self.channel_mask),
            "channel": channel_mask_to_single_channel(self.channel_mask),
            "pan_id": None if self.pan_id is None else int(self.pan_id),
            "extended_pan_id": _ieee_to_hex(self.extended_pan_id),
            "source": str(self.source),
            "formed_at_ms": None if self.formed_at_ms is None else int(self.formed_at_ms),
        }

    @classmethod
    def from_dict(cls, payload):
        payload = dict(payload or {})
        return cls(
            channel_mask=payload.get("channel_mask", None),
            pan_id=payload.get("pan_id", None),
            extended_pan_id=payload.get("extended_pan_id", None),
            source=payload.get("source", PROFILE_SOURCE_RESTORED),
            formed_at_ms=payload.get("formed_at_ms", None),
        )
