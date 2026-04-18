from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class DemoResult:
    user_id: int
    health_score: float
    pred_label: int
    pred_name: str
    prob_non_clinical: float
    prob_clinical: float
    post_count: int = 0


# 演示开关：仅用于展示场景，不影响默认推理流程。
SHOW_MODE_ENABLED = True

SHOW_DEMO_RESULTS: Dict[int, DemoResult] = {
    4: DemoResult(
        user_id=4,
        health_score=0.69,
        pred_label=0,
        pred_name="Non-Clinical",
        prob_non_clinical=0.69,
        prob_clinical=0.31,
        post_count=0,
    )
}


def get_demo_result(user_id: int) -> Optional[DemoResult]:
    if not SHOW_MODE_ENABLED:
        return None
    return SHOW_DEMO_RESULTS.get(int(user_id))
