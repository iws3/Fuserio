import numpy as np
import pytest

from localchat.math_analysis import analyse_function, analyse_xy_data, evaluate_expression, parse_xy_data


def test_function_sampling_and_summary_are_deterministic():
    result = analyse_function("2*x + 1", 0, 4, 25)

    assert result.x_values.shape == (25,)
    assert np.allclose(result.y_values, 2 * result.x_values + 1)
    assert result.metrics["BEST-FIT LINE"] == "y = 2x + 1"
    assert result.metrics["R SQUARED"] == "1.0000"
    assert result.plot_png.startswith(b"\x89PNG")


def test_math_functions_and_constants_are_supported():
    x_values = np.array([0.0, np.pi / 2, np.pi])

    assert np.allclose(evaluate_expression("sin(x) + 2", x_values), [2, 3, 2])
    assert np.allclose(evaluate_expression("sqrt(x**2)", x_values), np.abs(x_values))


def test_expression_evaluator_rejects_python_execution():
    with pytest.raises(ValueError, match="supported math functions"):
        evaluate_expression("__import__('os').system('echo unsafe')", np.array([1.0, 2.0]))


def test_xy_data_parsing_and_regression_report():
    result = analyse_xy_data("x,y\n1,3\n2,5\n3,7\n4,9")

    assert result.metrics["POINTS"] == "4"
    assert result.metrics["BEST-FIT LINE"] == "y = 2x + 1"
    assert result.metrics["CORRELATION r"] == "1.0000"
    assert "increases" in result.summary


def test_xy_parser_reports_invalid_rows():
    with pytest.raises(ValueError, match="Line 2"):
        parse_xy_data("x,y\n1,2,3\n")


def test_constant_y_series_has_finite_correlation_and_fit_statistics():
    result = analyse_xy_data("1,4\n2,4\n3,4")

    assert result.metrics["CORRELATION r"] == "0.0000"
    assert result.metrics["R SQUARED"] == "1.0000"
    assert "does not change" in result.summary
