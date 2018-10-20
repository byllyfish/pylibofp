"""Implements Match class."""


class Match(dict):
    """Match implementation."""

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__  # type: ignore

    def to_list(self):
        """Convert to list of fields."""
        return [_make_field(key, value) for key, value in self.items()]


def _make_field(name, value):
    assert not isinstance(value, list)

    fname = name.upper()
    value = _convert_slash_notation(fname, value)

    if isinstance(value, tuple):
        if len(value) != 2:
            raise ValueError('len(tuple) != 2')
        return dict(field=fname, value=value[0], mask=value[1])

    return dict(field=fname, value=value)


def _convert_slash_notation(fname, value):
    """Convert string value in slash notation into a tuple (addr, mask)."""
    assert fname.isupper()
    if not isinstance(value, str) or '/' not in value:
        return value

    if fname not in _IP_FIELDS:
        return tuple(value.split('/', 1))

    try:
        # ip_interface handles IP prefix notation "/nn"
        addr = ipaddress.ip_interface(value)
        return (addr.ip, addr.netmask)
    except ValueError:
        if not fname.startswith('IPV6_'):
            raise

    # Handle generic slash notation for IPv6 addresses.
    addr = value.split('/', 1)
    return (ipaddress.IPv6Address(addr[0]), ipaddress.IPv6Address(addr[1]))


_IP_FIELDS = {'IPV4_SRC', 'IPV4_DST', 'IPV6_SRC', 'IPV6_DST', 'IPV6_ND_TARGET'}