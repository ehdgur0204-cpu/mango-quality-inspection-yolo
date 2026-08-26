# 품질 판정 정책 (Inspection Policy) — 초안

> 이 문서는 초안이며, Confidence 기준값 등 세부 수치는 아직 확정되지 않았다.

## 1. 기본 판정 규칙(초안)

```text
Healthy + 기준 이상의 Confidence      → PASS
병해 클래스 + 기준 이상의 Confidence   → REJECT
기준 미만의 Confidence                → HOLD
객체 미검출                           → HOLD 및 재촬영
판정이 불명확한 경우                   → 작업자 재검사
```

- 병해 클래스: Alternaria, Anthracnose, Scab
- 정상 클래스: Healthy

## 2. Confidence 기준값 결정 방식

Confidence 기준값(threshold)은 임의로 정하지 않는다. Validation 데이터에서
얻은 **Precision-Recall 곡선 결과와 오통과(병해를 정상으로 잘못 판정하는
경우) 위험을 함께 고려하여 결정**할 예정이다. 특히 오통과는 REJECT되어야
할 병해 망고가 PASS로 유통되는 상황으로, 이를 최소화하는 방향을 우선
고려한다.

기준값이 확정되기 전까지는 이 문서의 규칙을 초안으로 간주하며, Validation
결과가 나오는 대로 구체적인 수치를 업데이트한다.

## 3. 제한사항

YOLO가 출력하는 Confidence 값은 모델이 내부적으로 계산한 점수일 뿐,
**보정(calibration)된 실제 확률과 완전히 동일하지 않다.** 즉, Confidence가
0.9라고 해서 실제로 90%의 확률로 맞다는 의미는 아닐 수 있다.

따라서 Confidence 숫자만 보고 다음과 같은 결정을 자동으로 내려서는 안 된다.

- 단순히 Confidence 값만으로 최종 폐기(REJECT) 여부를 전적으로 자동 결정하는 것
- 사람의 재검토 없이 Confidence 하나만으로 모든 예외 상황을 처리하는 것

불명확하거나 경계값에 가까운 판정은 반드시 작업자의 재검사 절차를 거치도록
한다.
