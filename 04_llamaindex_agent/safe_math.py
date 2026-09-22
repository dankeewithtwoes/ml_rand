"""Bounded arithmetic tool for agents; deliberately excludes code execution."""
import ast
import operator

OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
       ast.UAdd: operator.pos, ast.USub: operator.neg}


def evaluate(expression: str) -> float | int:
    if len(expression) > 256:
        raise ValueError("expression is too long")
    def walk(node):
        if isinstance(node, ast.Expression): return walk(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float): return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPS: return OPS[type(node.op)](walk(node.left), walk(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPS: return OPS[type(node.op)](walk(node.operand))
        raise ValueError(f"unsupported expression: {type(node).__name__}")
    return walk(ast.parse(expression, mode="eval"))
