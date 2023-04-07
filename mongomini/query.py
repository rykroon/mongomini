from dataclasses import dataclass
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


class Operator(StrEnum):

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


# Logical operators
AND = '$and'
OR = '$or'
NOT = '$not'


@dataclass(frozen=True, eq=False)
class Field:
    name: str
    
    def __eq__(self, value):
        ...
    
    def __ne__(self, value):
        ...
    
    def __gt__(self, value):
        ...
    
    def __gte__(self, value):
        ...
    
    def __lt__(self, value):
        ...
    
    def __lte__(self, value):
        ...


@dataclass(frozen=True, slots=True)
class Expression:
    field: str
    op: Operator
    value: Any
    neg: bool = False

    def __and__(self, other):
        if not isinstance(other, Expression):
            return NotImplemented
        return LogicalExpression(op=AND, expressions=[self, other])

    def __or__(self, other):
        if not isinstance(other, Expression):
            return NotImplemented
        return LogicalExpression(op=OR, expressions=[self, other])

    def __neg__(self):
        return Expression(field=self.field, op=self.op, value=self.value, neg=(not self.neg))

    def to_dict(self):
        if not self.neg:
            return {self.field: {self.op, self.value}}
        return {self.field: {NOT: {self.op: self.value}}}


@dataclass(frozen=True, slots=True)
class LogicalExpression:
    op: Literal['$and', '$or']
    expressions: list[Expression | "LogicalExpression"]

    def __post_init__(self):
        self.expressions = list(set(self.expressions))

    def __and__(self, other):
        if not isinstance(other, (Expression, LogicalExpression)):
            return NotImplemented

        if isinstance(other, Expression):
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
        if not isinstance(other, (Expression, LogicalExpression)):
            return NotImplemented
        
        if isinstance(other, Expression):
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

    def to_dict(self):
        return {self.op: [expr.to_dict() for expr in self.expressions]}
