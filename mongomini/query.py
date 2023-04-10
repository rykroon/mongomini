from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal


class Query:

    def __init__(self, *args, **kwargs):
        ...

    def __and__(self, other):
        ...

    def __or__(self, other):
        ...

    def __neg__(self):
        ...


def kwargs_to_exprs(**kwargs):
    expressions = None
    for k, v in kwargs.items():
        field, op = k.split('__') if '__' in k else (k, FieldOperator.EQUAL.value)
        expr = Expression(field=field, op=op, value=v)
        if expressions is None:
            expressions = expr
        else:
            expressions = expressions & expr
    return expressions


class FieldOperator(StrEnum):

    # Comparison
    EQUAL = '$eq'
    GREATER_THAN = '$gt'
    GREATER_THAN_OR_EQUAL_TO = '$gte'
    IN = '$in'
    LESS_THAN = '$lt'
    LESS_THAN_OR_EQUAL_TO = '$lte'
    NOT_EQUAL = '$ne'
    NOT_IN = '$nin'

    # Element
    EXISTS = '$exists'
    TYPE = '$type'

    # Evaluation
    MOD = '$mod'
    REGEX = '$regex'

    # Array
    ALL = '$all'
    ELEM_MATCH = '$elemMatch'
    SIZE = '$size'


# Logical operators
AND = '$and'
OR = '$or'
NOT = '$not'


@dataclass(init=False, repr=False, eq=False)
class Expression(dict):
    lhs: str = field(init=False, repr=False, compare=False)
    rhs: Any = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        self[self.lhs] = self.rhs


@dataclass(repr=False)
class FieldExpression(Expression):
    field: str
    op: FieldOperator
    value: Any
    neg: bool = False

    @property
    def lhs(self):
        return self.field

    @property
    def rhs(self):
        rhs = {self.op: self.value}
        if not self.neg:
            return rhs
        return {NOT: rhs}

    def __and__(self, other):
        if not isinstance(other, FieldExpression):
            return NotImplemented
        return LogicalExpression(op=AND, expressions=[self, other])

    def __or__(self, other):
        if not isinstance(other, FieldExpression):
            return NotImplemented
        return LogicalExpression(op=OR, expressions=[self, other])

    def __neg__(self):
        return FieldExpression(field=self.field, op=self.op, value=self.value, neg=(not self.neg))


@dataclass(repr=False)
class LogicalExpression(dict):
    op: Literal['$and', '$or']
    expressions: list[dict[str, Any]]

    def __post_init__(self):
        self[self.op] = self.expressions
    
    @property
    def lhs(self):
        return self.op

    @property
    def rhs(self):
        return self.expressions

    def __and__(self, other):
        if not isinstance(other, Expression):
            return NotImplemented

        if isinstance(other, FieldExpression):
            if self.op == AND:
                return LogicalExpression(
                    op=AND, expressions=[*self.expressions, other]
                )
            if self.op == OR:
                return LogicalExpression(op=AND, expressions=[self, other])

        if self.op == AND and other.op == AND:
            return LogicalExpression(
                op=AND, expressions=[*self.expressions, *other.expressions]
            )
        
        return LogicalExpression(op=AND, expressions=[self, other])

    def __or__(self, other):
        if not isinstance(other, Expression):
            return NotImplemented
        
        if isinstance(other, FieldExpression):
            if self.op == OR:
                return LogicalExpression(
                    op=OR, expressions=[*self.expressions, other]
                )
            if self.op == AND:
                return LogicalExpression(op=OR, expressions=[self, other])

        if self.op == OR and other.op == OR:
            return LogicalExpression(
                op=OR, expressions=[*self.expressions, *other.expressions]
            )

        return LogicalExpression(op=OR, expressions=[self, other])

    def __neg__(self):
        op = {AND: OR, OR: AND}[self.op]
        expressions = [-expr for expr in self.expressions]
        return LogicalExpression(op=op, expressions=expressions)
