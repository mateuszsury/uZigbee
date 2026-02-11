"""Security helpers for install-code and network-key operations."""


def _normalize_hex_bytes(value, expected_len, label):
    if isinstance(value, str):
        compact = value.replace(":", "").replace("-", "").replace(" ", "")
        if len(compact) != expected_len * 2:
            raise ValueError("%s must be %d bytes (%d hex chars)" % (label, expected_len, expected_len * 2))
        try:
            raw = bytes.fromhex(compact)
        except ValueError:
            raise ValueError("%s must be valid hex" % label)
    else:
        try:
            raw = bytes(value)
        except Exception:
            raise ValueError("%s must be bytes-like or hex string" % label)
    if len(raw) != expected_len:
        raise ValueError("%s must be %d bytes" % (label, expected_len))
    return raw


def normalize_network_key(key):
    """Normalize network key from bytes-like or hex string."""
    return _normalize_hex_bytes(key, 16, "network key")


def set_network_key(stack, key):
    """Set network key and return normalized key bytes."""
    normalized = normalize_network_key(key)
    stack.set_network_key(normalized)
    return normalized


def switch_network_key(stack, key, key_seq_num):
    """Switch local key to `key_seq_num` and return `(key, key_seq_num)`."""
    normalized = normalize_network_key(key)
    seq = int(key_seq_num) & 0xFF
    stack.switch_network_key(normalized, seq)
    return normalized, seq


def broadcast_network_key(stack, key, key_seq_num, activate=False):
    """Broadcast key (and optionally activate it) and return `(key, key_seq_num)`."""
    normalized = normalize_network_key(key)
    seq = int(key_seq_num) & 0xFF
    stack.broadcast_network_key(normalized, seq)
    if activate:
        stack.broadcast_network_key_switch(seq)
    return normalized, seq


def add_install_code(stack, ieee_addr, ic_str):
    """Add remote install code and return normalized IEEE address bytes."""
    ieee = bytes(ieee_addr)
    if len(ieee) != 8:
        raise ValueError("ieee address must be 8 bytes")
    stack.add_install_code(ieee, str(ic_str))
    return ieee


def set_local_install_code(stack, ic_str):
    """Set local install code string."""
    stack.set_local_install_code(str(ic_str))
    return True


def remove_install_code(stack, ieee_addr):
    """Remove remote install code and return normalized IEEE address bytes."""
    ieee = bytes(ieee_addr)
    if len(ieee) != 8:
        raise ValueError("ieee address must be 8 bytes")
    stack.remove_install_code(ieee)
    return ieee


def remove_all_install_codes(stack):
    """Remove all remote install codes."""
    stack.remove_all_install_codes()
    return True


def configure_security(stack, install_code_policy=None, network_security_enabled=None, network_key=None):
    """Apply selected security settings and return a small status dict."""
    out = {}
    if install_code_policy is not None:
        enabled = bool(install_code_policy)
        stack.set_install_code_policy(enabled)
        out["install_code_policy"] = enabled
    if network_security_enabled is not None:
        enabled = bool(network_security_enabled)
        stack.set_network_security_enabled(enabled)
        out["network_security_enabled"] = enabled
    if network_key is not None:
        normalized = normalize_network_key(network_key)
        stack.set_network_key(normalized)
        out["network_key"] = normalized
    return out
