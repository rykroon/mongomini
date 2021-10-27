from collections.abc import Iterable
from contextlib import suppress
from datetime import date, datetime
from decimal import Decimal
import attr


document = attr.s


def type_validator(obj, attr, value):
    if isinstance(value, attr.type):
        return

    raise TypeError


### Converters ###

def bool_converter(value):
    with suppress(Exception):
        if isinstance(value, str):
            value = value.lower()

        truthy = {True, 1, '1', 'true', 't', 'yes', 'y', 'on'}
        falsey = {False, 0, '0', 'false', 'f', 'no', 'n', 'off'}
        
        if value in truthy:
            return True

        if value in falsey:
            return False

    return value


def datetime_converter(value):
    with suppress(Exception):
        if isinstance(value, str):
            return datetime.fromisoformat(value)

        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value)

        if isinstance(value, date):
            return datetime(
                year=value.year, 
                month=value.month, 
                day=value.day
            )

    return value


def decimal_converter(value):
    with suppress(Exception):
        if isinstance(value, float):
            return Decimal.from_float(value)
        return Decimal(value)
    return value


def float_converter(value):
    with suppress(Exception):
        return float(value)
    return value


def int_converter(value):
    with suppress(Exception):
        return int(value)
    return value


def str_converter(value):
    with suppress(Exception):
        return str(value)
    return value


### Fields ###

def field(**kwargs):
    return attr.ib(
        validator=type_validator,
        **kwargs
    )


def bool_field(**kwargs):
    return field(
        type=bool,
        converter=bool_converter,
        **kwargs
    )


def datetime_field(**kwargs):
    return field(
        type=datetime,
        converter=datetime_converter,
        **kwargs
    )


def decimal_field(**kwargs):
    return field(
        type=Decimal,
        converter=decimal_converter,
        **kwargs
    )


def float_field(**kwargs):
    return field(
        type=float,
        converter=float_converter,
        **kwargs
    )


def int_field(**kwargs):
    return field(
        type=int,
        converter=int_converter,
        **kwargs
    )


def str_field(**kwargs):
    return field(
        type=str,
        converter=str_converter,
        **kwargs
    )

