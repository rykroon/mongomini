from contextlib import suppress
from datetime import date, datetime
from decimal import Decimal
import attr


document = attr.s


def type_validator(obj, attr, value):
    if isinstance(value, attr.type):
        return
    
    if value is None and attr.metadata['optional']:
        return

    raise TypeError


def choice_validator(obj, attr, value):
    if not attr.metadata['choices']:
        return

    if value in attr.metadata['choices']:
        return

    if value is None and attr.metadata['optional']:
        return

    raise ValueError


def max_length_validator(obj, attr, value):
    if not attr.metadata['max_length']:
        return

    if value is None and attr.metadata['optional']:
        return

    if len(value) <= attr.metadata['max_length']:
        return

    raise ValueError



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

def field(choices=None, optional=False, metadata=None, **kwargs):
    metadata = dict() if metadata is None else metadata
    metadata['choices'] = choices
    metadata['optional'] = optional

    return attr.ib(
        validator=type_validator,
        metadata=metadata,
        **kwargs
    )


def bool_field(**kwargs):
    return field(
        type=bool,
        converter=bool_converter,
        **kwargs
    )


def datetime_field(auto_now=False, **kwargs):
    factory = datetime.utcnow if auto_now else None
    
    return field(
        type=datetime,
        factory=factory,
        converter=datetime_converter,
        **kwargs
    )


def decimal_field(max_digits=None, decimal_places=None, **kwargs):
    return field(
        type=Decimal,
        converter=decimal_converter,
        metadata={
            'max_digits': max_digits,
            'decimal_places': decimal_places
        }
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


def str_field(max_length=None, **kwargs):
    return field(
        type=str,
        converter=str_converter,
        validator=max_length_validator,
        metedata={
            'max_length': max_length
        }
        **kwargs
    )

