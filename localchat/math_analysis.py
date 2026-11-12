"""Safe expression evaluation and numeric analysis for the student Math Data Lab."""

from __future__ import annotations

import ast
import io
import operator
import re
from dataclasses import dataclass
from typing import Callable

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure


_BINARY_OPERATORS: dict[type[ast.operator], Callable] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_UNARY_OPERATORS: dict[type[ast.unaryop], Callable] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}
_FUNCTIONS: dict[str, Callable] = {
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "sqrt": np.sqrt,
    "log": np.log10,
    "ln": np.log,
    "exp": np.exp,
    "abs": np.abs,
}
_CONSTANTS = {"pi": np.pi, "e": np.e}


@dataclass(frozen=True)
class AnalysisResult:
    x_values: np.ndarray
    y_values: np.ndarray
    metrics: dict[str, str]
    summary: str
    plot_png: bytes
    source: str


def _evaluate_node(node: ast.AST, x_values: np.ndarray):
    if isinstance(node, ast.Name):
        if node.id == "x":
            return x_values
        if node.id in _CONSTANTS:
            return _CONSTANTS[node.id]
        raise ValueError(f"Unknown symbol: {node.id}")
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate_node(node.left, x_values)
        right = _evaluate_node(node.right, x_values)
        return _BINARY_OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_evaluate_node(node.operand, x_values))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        function = _FUNCTIONS.get(node.func.id)
        if function is None or node.keywords or len(node.args) != 1:
            raise ValueError("Use one supported function argument: sin, cos, tan, sqrt, log, ln, exp, or abs.")
        return function(_evaluate_node(node.args[0], x_values))
    raise ValueError("Use x, numbers, + - * / ** %, parentheses, and supported math functions only.")


def evaluate_expression(expression: str, x_values: np.ndarray) -> np.ndarray:
    """Evaluate a restricted arithmetic expression without executing arbitrary Python."""
    try:
        syntax = ast.parse(expression.strip(), mode="eval")
        with np.errstate(all="ignore"):
            values = np.asarray(_evaluate_node(syntax.body, x_values), dtype=float)
        if values.ndim == 0:
            values = np.full(x_values.shape, float(values))
        values = np.broadcast_to(values, x_values.shape).astype(float, copy=True)
    except (SyntaxError, TypeError, ZeroDivisionError, OverflowError, FloatingPointError) as error:
        raise ValueError(f"Could not evaluate that function: {error}") from error
    if not np.all(np.isfinite(values)):
        raise ValueError("The function is undefined for part of this x range. Try a different range.")
    return values


def parse_xy_data(text: str) -> tuple[np.ndarray, np.ndarray]:
    """Parse two-column student data separated by commas, semicolons, tabs, or spaces."""
    x_values: list[float] = []
    y_values: list[float] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        columns = re.split(r"[,;\t ]+", stripped)
        try:
            if len(columns) != 2:
                raise ValueError
            x_value, y_value = (float(value) for value in columns)
        except ValueError:
            if not x_values and line_number == 1 and any(character.isalpha() for character in stripped):
                continue
            raise ValueError(f"Line {line_number}: enter exactly two numbers, x and y.")
        if not np.isfinite(x_value) or not np.isfinite(y_value):
            raise ValueError(f"Line {line_number}: values must be finite numbers.")
        x_values.append(x_value)
        y_values.append(y_value)
    if len(x_values) < 2:
        raise ValueError("Enter at least two rows of x,y data.")
    return np.asarray(x_values, dtype=float), np.asarray(y_values, dtype=float)


def _analyse_values(x_values: np.ndarray, y_values: np.ndarray, source: str) -> AnalysisResult:
    if x_values.size != y_values.size or x_values.size < 2:
        raise ValueError("Analysis needs at least two matching x and y values.")
    if not np.all(np.isfinite(x_values)) or not np.all(np.isfinite(y_values)):
        raise ValueError("Data must contain finite numeric values only.")
    if np.ptp(x_values) == 0:
        raise ValueError("The x values must not all be identical to calculate a trend line.")

    slope, intercept = np.polyfit(x_values, y_values, 1)
    predicted = slope * x_values + intercept
    residual_sum = float(np.sum((y_values - predicted) ** 2))
    total_sum = float(np.sum((y_values - np.mean(y_values)) ** 2))
    tol = 1e-12
    if total_sum <= tol and residual_sum <= tol:
        r_squared = 1.0
    elif total_sum <= tol:
        r_squared = 0.0
    else:
        r_squared = 1 - residual_sum / total_sum
    correlation = (
        float(np.corrcoef(x_values, y_values)[0, 1])
        if np.std(x_values) > 0 and np.std(y_values) > 0
        else 0.0
    )
    metrics = {
        "POINTS": str(int(y_values.size)),
        "MEAN Y": f"{np.mean(y_values):.4g}",
        "MEDIAN Y": f"{np.median(y_values):.4g}",
        "SAMPLE SD": f"{np.std(y_values, ddof=1):.4g}",
        "BEST-FIT LINE": f"y = {slope:.4g}x {'+' if intercept >= 0 else '-'} {abs(intercept):.4g}",
        "CORRELATION r": f"{correlation:.4f}",
        "R SQUARED": f"{r_squared:.4f}",
    }
    if abs(slope) <= 1e-12:
        direction = "does not change"
        slope_text = "0"
    elif slope > 0:
        direction = "increases"
        slope_text = f"{abs(slope):.4g}"
    else:
        direction = "decreases"
        slope_text = f"{abs(slope):.4g}"
    summary = (
        f"The fitted trend has slope {slope:.4g}, so y {direction} by about "
        f"{slope_text} for each one-unit increase in x. "
        f"The line accounts for {max(0.0, min(1.0, r_squared)):.1%} of the variation in y."
    )
    return AnalysisResult(
        x_values=np.asarray(x_values, dtype=float),
        y_values=np.asarray(y_values, dtype=float),
        metrics=metrics,
        summary=summary,
        plot_png=_make_plot(x_values, y_values, source),
        source=source,
    )


def analyse_function(
    expression: str,
    x_min: float,
    x_max: float,
    sample_count: int = 160,
) -> AnalysisResult:
    """Sample a safe function of x and calculate summary statistics and a linear fit."""
    if not expression.strip():
        raise ValueError("Enter a function such as x**2 or sin(x).")
    if not np.isfinite(x_min) or not np.isfinite(x_max) or x_min >= x_max:
        raise ValueError("The x minimum must be smaller than the x maximum.")
    if not 10 <= sample_count <= 1000:
        raise ValueError("Choose between 10 and 1000 graph samples.")
    x_values = np.linspace(x_min, x_max, sample_count)
    y_values = evaluate_expression(expression, x_values)
    return _analyse_values(x_values, y_values, expression.strip())


def analyse_xy_data(text: str) -> AnalysisResult:
    """Calculate descriptive statistics, correlation, regression, and a plot for entered data."""
    x_values, y_values = parse_xy_data(text)
    return _analyse_values(x_values, y_values, "Measured data")


def _make_plot(x_values: np.ndarray, y_values: np.ndarray, source: str) -> bytes:
    figure = Figure(figsize=(7.2, 4.5), dpi=120, facecolor="#071512", tight_layout=True)
    canvas = FigureCanvasAgg(figure)
    axes = figure.add_subplot(111)
    axes.set_facecolor("#0b201a")
    axes.tick_params(colors="#b3d4c5", labelsize=9)
    for spine in axes.spines.values():
        spine.set_color("#416456")
    axes.grid(color="#25483b", linewidth=0.7, alpha=0.8)
    axes.set_xlabel("x", color="#d9f3e5")
    axes.set_ylabel("y", color="#d9f3e5")
    axes.set_title(source[:64], color="#8ef0c2", loc="left", fontsize=12, pad=12)
    order = np.argsort(x_values)
    sorted_x = x_values[order]
    sorted_y = y_values[order]
    axes.plot(sorted_x, sorted_y, color="#55d9bd", linewidth=2.2, label="Data / function")
    axes.scatter(x_values, y_values, color="#ffc478", edgecolors="#fff0c8", linewidths=0.5, s=22, zorder=3)
    if source == "Measured data":
        slope, intercept = np.polyfit(x_values, y_values, 1)
        axes.plot(sorted_x, slope * sorted_x + intercept, color="#ff8294", linewidth=1.6, linestyle="--", label="Linear fit")
        axes.legend(facecolor="#10251f", edgecolor="#355d4d", labelcolor="#d8eee2", fontsize=8)
    output = io.BytesIO()
    canvas.print_png(output)
    return output.getvalue()
