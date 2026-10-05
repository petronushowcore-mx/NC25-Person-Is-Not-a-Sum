"""Finite structural examples accompanying The Person Is Not a Sum.

Exact rational costs; fixed capacity; charges at discrete window ends.
No ethical verdict, physical duration law, or identity-collapse detector.
"""
from enum import Enum
from fractions import Fraction as F
from itertools import product
import json
import sys
from typing import NamedTuple


class Refusal(ValueError):
    pass


class Window(NamedTuple):
    cost: F
    span: int


class Verdict(Enum):
    ADMIT = "admit"
    REJECT = "reject"
    INSUFFICIENT = "insufficient"


def validate(trace):
    if type(trace) is not tuple or not trace:
        raise Refusal("trace must be a nonempty tuple")
    for window in trace:
        if type(window) is not Window:
            raise Refusal("trace entries must be Window")
        if type(window.cost) is not F or window.cost < 0:
            raise Refusal("cost must be an exact nonnegative rational")
        if type(window.span) is not int or window.span <= 0:
            raise Refusal("span must be a positive integer")


def capacity_guard(capacity):
    if type(capacity) is not F or capacity <= 0:
        raise Refusal("capacity must be an exact positive rational")


def prefix_budgets(trace, capacity):
    validate(trace)
    capacity_guard(capacity)
    zero_cost = 0
    zero_tick = 0
    spent = F(zero_cost)
    tick = zero_tick
    result = []
    for window in trace:
        spent += window.cost
        tick += window.span
        result.append((capacity - spent, tick))
    return tuple(result)


def total_observation(trace):
    validate(trace)
    cost = sum((window.cost for window in trace), F(0))
    span = sum(window.span for window in trace)
    return cost, span


def first_crossing(trace, capacity):
    """First nonpositive budget: (1-based window, declared end coordinate)."""
    for index, (budget, tick) in enumerate(prefix_budgets(trace, capacity), 1):
        if budget <= 0:
            return index, tick
    return None


def final_survival(trace, capacity):
    return prefix_budgets(trace, capacity)[-1][0] > 0


def whole_survival(trace, capacity):
    return all(budget > 0 for budget, _ in prefix_budgets(trace, capacity))


def level_guard(levels, floor):
    if (type(levels) is not tuple or not levels
            or any(type(level) is not F for level in levels)
            or type(floor) is not F):
        raise Refusal("levels and floor must be exact rationals")


def held_line(levels, floor):
    level_guard(levels, floor)
    return all(level >= floor for level in levels)


def peak(levels):
    level_guard(levels, F(0))
    return max(levels)


def observer_invariant(answers):
    """Constancy of supplied Boolean answers, including a constant false line."""
    if type(answers) is not tuple or not answers or any(type(a) is not bool for a in answers):
        raise Refusal("answers must be a nonempty Boolean tuple")
    return len(set(answers)) == 1


def fibre_verdict(universe, observe, predicate, visible):
    """Classify an attained observation over the declared finite catalogue."""
    if type(universe) is not tuple or not universe:
        raise Refusal("universe must be a nonempty tuple")
    answers = []
    for trace in universe:
        validate(trace)
        if observe(trace) == visible:
            answer = predicate(trace)
            if type(answer) is not bool:
                raise Refusal("predicate must return a Boolean")
            answers.append(answer)
    if not answers:
        raise Refusal("observation is not attained in the declared universe")
    if all(answers):
        return Verdict.ADMIT
    if not any(answers):
        return Verdict.REJECT
    return Verdict.INSUFFICIENT


def loss_status(before, after, capacity):
    if not final_survival(before, capacity):
        raise Refusal("loss requires an admissible baseline")
    return "preserved" if final_survival(after, capacity) else "lost"


def refused(operation):
    try:
        operation()
    except Refusal:
        return True
    return False


def run_checks():
    rows = []

    def check(name, operation):
        try:
            passed = operation() is True
            detail = "" if passed else "predicate was not true"
        except Exception as error:
            passed, detail = False, type(error).__name__ + ": " + str(error)
        rows.append({"name": name, "ok": passed, "detail": detail})

    unit = (Window(F(1, 3), 1),)
    capacity = F(1, 2)
    late = (Window(F(1, 3), 1), Window(F(2, 3), 1))
    early = tuple(reversed(late))
    universe = (late, early)
    visible = (F(1), 2)
    at_start = lambda trace: first_crossing(trace, capacity)[0] == 1
    sample = (Window(F(1, 6), 2), Window(F(2, 3), 3), Window(F(1, 3), 5))
    alphabet = tuple(Window(cost, span) for cost in (F(0), F(1, 3), F(2, 3)) for span in (1, 2))
    traces = tuple(word for size in range(1, 5) for word in product(alphabet, repeat=size))

    check("INPUT_TRACE", lambda:
          all(refused(lambda bad=bad: validate(bad)) for bad in ((), [], (1,)))
          and validate(unit) is None)
    check("INPUT_COST", lambda:
          all(refused(lambda bad=bad: validate((Window(bad, 1),)))
              for bad in (F(-1), 0.5, True))
          and validate((Window(F(0), 1),)) is None)
    check("INPUT_SPAN", lambda:
          all(refused(lambda bad=bad: validate((Window(F(0), bad),)))
              for bad in (0, -1, 0.5, True))
          and validate((Window(F(0), 2),)) is None)
    check("INPUT_CAPACITY", lambda:
          all(refused(lambda bad=bad: capacity_guard(bad)) for bad in (F(0), F(-1), 0.5, True))
          and capacity_guard(F(1, 2)) is None)
    check("INPUT_LEVELS", lambda:
          all(refused(lambda bad=bad: level_guard(bad, F(0))) for bad in ((), [F(0)], (0.5,)))
          and refused(lambda: level_guard((F(0),), 0.5))
          and level_guard((F(-1), F(0)), F(0)) is None)
    check("INPUT_OBSERVER", lambda:
          all(refused(lambda bad=bad: observer_invariant(bad)) for bad in ((), [], (1,)))
          and type(observer_invariant((False, False))) is bool)
    check("INPUT_FIBRE", lambda:
          refused(lambda: fibre_verdict((unit,), lambda t: t, lambda t: 1, unit))
          and refused(lambda: fibre_verdict((unit,), lambda t: t, lambda t: True, ()))
          and refused(lambda: fibre_verdict((), lambda t: t, lambda t: True, unit))
          and refused(lambda: fibre_verdict([unit], lambda t: t, lambda t: True, unit))
          and type(fibre_verdict((unit,), lambda t: t, lambda t: True, unit)) is Verdict)
    check("INPUT_BASELINE", lambda:
          refused(lambda: loss_status(late, unit, capacity))
          and not refused(lambda: loss_status(unit, unit, capacity)))
    check("EXACT_PREFIX", lambda:
          prefix_budgets(sample, F(1)) == ((F(5, 6), 2), (F(1, 6), 5), (F(-1, 6), 10))
          and all(type(b) is F for b, _ in prefix_budgets(sample, F(1))))
    check("TOTAL_PAIR", lambda:
          total_observation(sample) == (F(7, 6), 10)
          and total_observation(late) == total_observation(early) == visible)
    check("FIRST_CROSSING", lambda:
          first_crossing(sample, F(5, 6)) == (2, 5)
          and first_crossing(unit, capacity) is None
          and first_crossing(late, capacity) == (2, 2)
          and first_crossing(early, capacity) == (1, 1))
    check("FINAL_SURVIVAL", lambda:
          all(final_survival(trace, capacity) is
              (sum((w.cost for w in trace), F(0)) < capacity) for trace in traces)
          and final_survival((Window(F(1, 2), 1),), capacity) is False)
    check("WHOLE_SURVIVAL", lambda:
          all(whole_survival(trace, capacity) is
              (sum((w.cost for w in trace), F(0)) < capacity) for trace in traces)
          and whole_survival((Window(F(1, 2), 1),), capacity) is False)
    check("HELD_LINE", lambda:
          held_line((F(1), F(0), F(0)), F(1, 4)) is False
          and held_line((F(1, 3),) * 3, F(1, 4)) is True
          and held_line((F(1, 4),), F(1, 4)) is True
          and held_line((F(1, 3), F(0), F(1, 3)), F(1, 4)) is False)
    check("PEAK", lambda:
          peak((F(1), F(0), F(0))) == F(1)
          and peak((F(1, 3),) * 3) == F(1, 3)
          and peak((F(0), F(1))) == F(1))
    check("OBSERVER_INVARIANCE", lambda:
          observer_invariant((True, True)) is True
          and observer_invariant((False, False)) is True
          and observer_invariant((True, False)) is False
          and observer_invariant((True, False, True)) is False)
    check("FIBRE_TRIAD", lambda:
          fibre_verdict(universe, total_observation, at_start, visible) is Verdict.INSUFFICIENT
          and fibre_verdict(universe, total_observation, lambda t: final_survival(t, capacity),
                            visible) is Verdict.REJECT
          and fibre_verdict(universe, total_observation, lambda t: not final_survival(t, capacity),
                            visible) is Verdict.ADMIT)
    check("LOSS_STATUS", lambda:
          loss_status(unit, early, capacity) == "lost"
          and loss_status(unit, unit, capacity) == "preserved")
    return rows, len(traces)


def main():
    if len(sys.argv) > 1 and sys.argv[1:] not in (["--teeth"], ["--json"]):
        raise SystemExit("usage: person_harness.py [--teeth|--json]")
    rows, cases = run_checks()
    summary = "Checks: %d/%d; finite rational cases=%d" % (
        sum(r["ok"] for r in rows), len(rows), cases)
    result = {"checks": rows, "finite_cases": cases, "ok": all(r["ok"] for r in rows),
              "summary": summary}
    if "--json" in sys.argv:
        print(json.dumps(result, sort_keys=True))
    else:
        for row in rows:
            print(("PASS " if row["ok"] else "FAIL ") + row["name"]
                  + (": " + row["detail"] if row["detail"] else ""))
        print(summary)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())