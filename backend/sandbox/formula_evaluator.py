"""
FinMAN AST Formula Sandbox.
Secure, isolated mathematical formula evaluator for financial indicators,
quantitative factor weights, and user-defined scoring rules.

Uses Python's abstract syntax tree (ast) to parse and evaluate mathematical expressions
without allowing arbitrary code execution, dunder access, attribute lookups, or file/OS primitives.
"""

import ast
import math
from typing import Dict, Any, Union, Set


class FormulaSecurityError(ValueError):
    """Raised when an expression attempts forbidden AST operations or unauthorized functions."""
    pass


class FormulaEvaluationError(Exception):
    """Raised when evaluation fails due to arithmetic errors, missing variables, or math bounds."""
    pass


class SafeFormulaEvaluator:
    """
    Evaluates mathematical expressions safely using an AST visitor pattern.
    Only whitelisted operators, numeric literals, declared context variables,
    and safe math functions are permitted.
    """

    MAX_FORMULA_LENGTH = 500
    MAX_EXPONENT = 10.0
    MAX_MAGNITUDE = 1e12

    SAFE_MATH_FUNCS = {
        "min": min,
        "max": max,
        "abs": abs,
        "round": round,
        "sqrt": math.sqrt,
        "log": math.log,
        "exp": math.exp,
    }

    SAFE_CONSTANTS = {
        "pi": math.pi,
        "e": math.e,
    }

    ALLOWED_BINARY_OPS = {
        ast.Add: lambda a, b: a + b,
        ast.Sub: lambda a, b: a - b,
        ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: SafeFormulaEvaluator._safe_div(a, b),
        ast.FloorDiv: lambda a, b: SafeFormulaEvaluator._safe_floordiv(a, b),
        ast.Mod: lambda a, b: SafeFormulaEvaluator._safe_mod(a, b),
        ast.Pow: lambda a, b: SafeFormulaEvaluator._safe_pow(a, b),
    }

    ALLOWED_UNARY_OPS = {
        ast.UAdd: lambda a: +a,
        ast.USub: lambda a: -a,
    }

    ALLOWED_COMPARE_OPS = {
        ast.Eq: lambda a, b: float(a == b),
        ast.NotEq: lambda a, b: float(a != b),
        ast.Lt: lambda a, b: float(a < b),
        ast.LtE: lambda a, b: float(a <= b),
        ast.Gt: lambda a, b: float(a > b),
        ast.GtE: lambda a, b: float(a >= b),
    }

    @staticmethod
    def _safe_div(a: float, b: float) -> float:
        if abs(b) < 1e-15:
            raise FormulaEvaluationError("Division by zero in formula evaluation")
        return a / b

    @staticmethod
    def _safe_floordiv(a: float, b: float) -> float:
        if abs(b) < 1e-15:
            raise FormulaEvaluationError("Floor division by zero in formula evaluation")
        return a // b

    @staticmethod
    def _safe_mod(a: float, b: float) -> float:
        if abs(b) < 1e-15:
            raise FormulaEvaluationError("Modulo by zero in formula evaluation")
        return a % b

    @staticmethod
    def _safe_pow(base: float, exp: float) -> float:
        if abs(exp) > SafeFormulaEvaluator.MAX_EXPONENT:
            raise FormulaSecurityError(
                f"Exponent {exp} exceeds safe sandbox limit ({SafeFormulaEvaluator.MAX_EXPONENT})"
            )
        if abs(base) > SafeFormulaEvaluator.MAX_MAGNITUDE:
            raise FormulaEvaluationError(
                f"Base magnitude {base} exceeds maximum allowed value ({SafeFormulaEvaluator.MAX_MAGNITUDE})"
            )
        try:
            res = base ** exp
            if isinstance(res, complex):
                raise FormulaEvaluationError("Formula evaluation resulted in complex numbers")
            if math.isinf(res) or math.isnan(res):
                raise FormulaEvaluationError("Formula calculation overflowed to infinity or NaN")
            return float(res)
        except OverflowError:
            raise FormulaEvaluationError("Arithmetic overflow during power calculation")

    def __init__(self, formula: str):
        if not isinstance(formula, str):
            raise FormulaEvaluationError("Formula must be a non-empty string")
        formula_str = formula.strip()
        if not formula_str:
            raise FormulaEvaluationError("Formula cannot be empty or blank")
        if len(formula_str) > self.MAX_FORMULA_LENGTH:
            raise FormulaSecurityError(
                f"Formula length ({len(formula_str)}) exceeds maximum allowed ({self.MAX_FORMULA_LENGTH})"
            )

        self.formula = formula_str
        try:
            self.parsed_ast = ast.parse(self.formula, mode="eval")
        except SyntaxError as e:
            raise FormulaEvaluationError(f"Syntax error in formula: {str(e)}")

        self._validate_ast(self.parsed_ast.body)

    def _validate_ast(self, node: ast.AST):
        """Recursively validates the AST tree ensuring only safe nodes are present."""
        forbidden_types = (
            ast.Import, ast.ImportFrom, ast.Attribute, ast.Subscript,
            ast.Lambda, ast.Assign, ast.AugAssign, ast.ListComp,
            ast.DictComp, ast.SetComp, ast.GeneratorExp, ast.Yield,
            ast.YieldFrom, ast.Await, ast.AsyncFor, ast.AsyncWith
        )
        if isinstance(node, forbidden_types):
            raise FormulaSecurityError(f"Forbidden AST node type: {type(node).__name__}")

        if isinstance(node, ast.Name):
            if node.id.startswith("__"):
                raise FormulaSecurityError(f"Dunder access forbidden: {node.id}")
            return

        elif isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float, bool)):
                raise FormulaSecurityError(f"Unsupported constant type: {type(node.value).__name__}")
            return

        elif isinstance(node, ast.BinOp):
            if type(node.op) not in self.ALLOWED_BINARY_OPS:
                raise FormulaSecurityError(f"Unsupported binary operator: {type(node.op).__name__}")
            self._validate_ast(node.left)
            self._validate_ast(node.right)
            return

        elif isinstance(node, ast.UnaryOp):
            if type(node.op) not in self.ALLOWED_UNARY_OPS:
                raise FormulaSecurityError(f"Unsupported unary operator: {type(node.op).__name__}")
            self._validate_ast(node.operand)
            return

        elif isinstance(node, ast.Compare):
            for op in node.ops:
                if type(op) not in self.ALLOWED_COMPARE_OPS:
                    raise FormulaSecurityError(f"Unsupported comparison operator: {type(op).__name__}")
            self._validate_ast(node.left)
            for comparator in node.comparators:
                self._validate_ast(comparator)
            return

        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise FormulaSecurityError("Dynamic function dispatch is strictly forbidden")
            func_name = node.func.id
            if func_name not in self.SAFE_MATH_FUNCS:
                raise FormulaSecurityError(f"Function '{func_name}' is not in the approved safe list")
            if node.keywords:
                raise FormulaSecurityError("Keyword arguments are not supported in formula calls")
            for arg in node.args:
                self._validate_ast(arg)
            return

        else:
            raise FormulaSecurityError(f"Disallowed expression node: {type(node).__name__}")

    def evaluate(self, context: Dict[str, Union[int, float]] = None) -> float:
        """Evaluates the validated AST against provided variable dictionary."""
        ctx = context or {}
        # Verify context variable names are safe
        for k in ctx.keys():
            if k.startswith("__"):
                raise FormulaSecurityError(f"Forbidden context variable: {k}")

        result = self._eval_node(self.parsed_ast.body, ctx)
        if isinstance(result, bool):
            return 1.0 if result else 0.0
        return float(result)

    def _eval_node(self, node: ast.AST, context: Dict[str, Any]) -> Any:
        if isinstance(node, ast.Constant):
            return node.value

        elif isinstance(node, ast.Name):
            var_name = node.id
            if var_name in context:
                val = context[var_name]
                if not isinstance(val, (int, float, bool)):
                    raise FormulaEvaluationError(f"Variable '{var_name}' must be numeric, got {type(val).__name__}")
                return float(val)
            elif var_name in self.SAFE_CONSTANTS:
                return float(self.SAFE_CONSTANTS[var_name])
            else:
                raise FormulaEvaluationError(f"Undefined variable in formula: '{var_name}'")

        elif isinstance(node, ast.BinOp):
            left_val = self._eval_node(node.left, context)
            right_val = self._eval_node(node.right, context)
            op_fn = self.ALLOWED_BINARY_OPS[type(node.op)]
            return op_fn(left_val, right_val)

        elif isinstance(node, ast.UnaryOp):
            operand_val = self._eval_node(node.operand, context)
            op_fn = self.ALLOWED_UNARY_OPS[type(node.op)]
            return op_fn(operand_val)

        elif isinstance(node, ast.Compare):
            left_val = self._eval_node(node.left, context)
            for op, comparator in zip(node.ops, node.comparators):
                right_val = self._eval_node(comparator, context)
                cmp_fn = self.ALLOWED_COMPARE_OPS[type(op)]
                if not cmp_fn(left_val, right_val):
                    return 0.0
                left_val = right_val
            return 1.0

        elif isinstance(node, ast.Call):
            func_name = node.func.id
            args = [self._eval_node(arg, context) for arg in node.args]
            func = self.SAFE_MATH_FUNCS[func_name]
            try:
                return func(*args)
            except Exception as e:
                raise FormulaEvaluationError(f"Error executing '{func_name}': {str(e)}")

        raise FormulaEvaluationError(f"Unhandled evaluation node: {type(node).__name__}")


def evaluate_formula(formula: str, context: Dict[str, Union[int, float]] = None) -> float:
    """Convenience helper to evaluate a mathematical formula safely in one call."""
    evaluator = SafeFormulaEvaluator(formula)
    return evaluator.evaluate(context)
