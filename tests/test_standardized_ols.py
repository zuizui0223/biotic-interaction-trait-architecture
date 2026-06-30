from trait_architecture.standardized_ols import fit_ols_hc3


def test_ols_recovers_exact_linear_relation_with_zero_hc3_error() -> None:
    design = [[1.0, float(index)] for index in range(1, 9)]
    y = [2.0 + 3.0 * row[1] for row in design]

    result = fit_ols_hc3(y, design, ["Intercept", "A_z"])
    by_term = {item.term: item for item in result.coefficients}

    assert result.n == 8
    assert result.residual_df == 6
    assert abs(by_term["Intercept"].estimate - 2.0) < 1e-10
    assert abs(by_term["A_z"].estimate - 3.0) < 1e-10
    assert result.r_squared > 0.999999


def test_ols_rejects_singular_design() -> None:
    try:
        fit_ols_hc3([1.0, 2.0, 3.0], [[1.0, 1.0]] * 3, ["Intercept", "constant"])
    except ValueError as error:
        assert "singular" in str(error)
    else:
        raise AssertionError("singular design should be rejected")
