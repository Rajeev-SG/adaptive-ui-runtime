from adaptive_ui_runtime.contracts import Budget, RouteKind, Subtask, SuccessCriterion


def test_default_budget_is_bounded() -> None:
    budget = Budget()
    assert budget.max_actions > 0
    assert budget.max_unchanged_state_actions <= budget.max_actions


def test_subtask_has_explicit_success_criteria() -> None:
    task = Subtask(
        id="demo",
        goal="Set country to UK",
        success_criteria=[
            SuccessCriterion(
                kind="dom_value",
                description="Country field equals UK",
                expected="UK",
            )
        ],
    )
    assert task.success_criteria[0].expected == "UK"
    assert RouteKind.JEV in task.allowed_routes
