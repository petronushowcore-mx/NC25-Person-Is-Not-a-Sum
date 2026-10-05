"""Run mutations against disposable copies; the original model is never edited."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory


BREAKS = (
    ("INPUT_TRACE", "if type(trace) is not tuple or not trace:",
     "if False:", "accept empty or mutable trace"),
    ("INPUT_COST", "if type(window.cost) is not F or window.cost < 0:",
     "if False:", "accept signed or inexact costs"),
    ("INPUT_SPAN", "if type(window.span) is not int or window.span <= 0:",
     "if False:", "accept invalid declared span"),
    ("INPUT_CAPACITY", "if type(capacity) is not F or capacity <= 0:",
     "if False:", "accept nonpositive or inexact capacity"),
    ("INPUT_LEVELS", "or type(floor) is not F):",
     "or type(floor) is not F) and False:", "accept empty or inexact levels"),
    ("INPUT_OBSERVER", "if type(answers) is not tuple or not answers or any(type(a) is not bool for a in answers):",
     "if False:", "accept empty or nonboolean answers"),
    ("INPUT_FIBRE", "if type(answer) is not bool:",
     "if False:", "silently coerce a nonboolean predicate"),
    ("INPUT_FIBRE", "if not answers:",
     "if False:", "admit an unattained observation by empty all"),
    ("INPUT_FIBRE", "if type(universe) is not tuple or not universe:",
     "if False:", "accept a mutable declared catalogue"),
    ("INPUT_BASELINE", "if not final_survival(before, capacity):",
     "if False:", "declare loss without a positive baseline"),
    ("EXACT_PREFIX", "spent += window.cost",
     "spent = window.cost", "reset the cumulative burden each window"),
    ("EXACT_PREFIX", "result.append((capacity - spent, tick))",
     "result.append((float(capacity - spent), tick))", "discard exact rational arithmetic"),
    ("TOTAL_PAIR", "span = sum(window.span for window in trace)",
     "span = len(trace)", "replace declared span by number of windows"),
    ("TOTAL_PAIR", "cost = sum((window.cost for window in trace), F(0))",
     "cost = trace[-1].cost", "forget earlier burden in the aggregate"),
    ("FIRST_CROSSING", "if budget <= 0:",
     "if budget < 0:", "miss an exact boundary crossing"),
    ("FIRST_CROSSING", "enumerate(prefix_budgets(trace, capacity), 1)",
     "enumerate(reversed(prefix_budgets(trace, capacity)), 1)", "scan backwards for the first crossing"),
    ("FINAL_SURVIVAL", "return prefix_budgets(trace, capacity)[-1][0] > 0",
     "return prefix_budgets(trace, capacity)[-1][0] >= 0", "allow an exhausted final budget"),
    ("WHOLE_SURVIVAL", "return all(budget > 0 for budget, _ in prefix_budgets(trace, capacity))",
     "return any(budget > 0 for budget, _ in prefix_budgets(trace, capacity))", "replace every prefix by one surviving prefix"),
    ("WHOLE_SURVIVAL", "return all(budget > 0 for budget, _ in prefix_budgets(trace, capacity))",
     "return all(budget >= 0 for budget, _ in prefix_budgets(trace, capacity))", "allow an exhausted prefix budget"),
    ("HELD_LINE", "return all(level >= floor for level in levels)",
     "return any(level >= floor for level in levels)", "replace a held line by one peak"),
    ("HELD_LINE", "return all(level >= floor for level in levels)",
     "return all(level > floor for level in levels)", "reject the declared closed floor"),
    ("HELD_LINE", "return all(level >= floor for level in levels)",
     "return levels[0] >= floor and levels[-1] >= floor", "ignore an internal level dip"),
    ("PEAK", "return max(levels)",
     "return sum(levels)", "replace peak by sum"),
    ("PEAK", "return max(levels)",
     "return levels[0]", "replace maximum by first level"),
    ("OBSERVER_INVARIANCE", "return len(set(answers)) == 1",
     "return all(answers)", "confuse an invariant answer with a true answer"),
    ("OBSERVER_INVARIANCE", "return len(set(answers)) == 1",
     "return True", "ignore an observer-dependent answer"),
    ("OBSERVER_INVARIANCE", "return len(set(answers)) == 1",
     "return answers[0] == answers[-1]", "ignore an internal observer change"),
    ("FIBRE_TRIAD", "return Verdict.INSUFFICIENT",
     "return Verdict.ADMIT", "admit a mixed fibre"),
    ("FIBRE_TRIAD", "if not any(answers):\n        return Verdict.REJECT",
     "if not any(answers):\n        return Verdict.ADMIT", "admit a uniformly false fibre"),
    ("FIBRE_TRIAD", "if all(answers):\n        return Verdict.ADMIT",
     "if all(answers):\n        return Verdict.REJECT", "reject a uniformly true fibre"),
    ("LOSS_STATUS", 'return "preserved" if final_survival(after, capacity) else "lost"',
     'return "preserved"', "hide a loss after a normal baseline"),
    ("LOSS_STATUS", 'return "preserved" if final_survival(after, capacity) else "lost"',
     'return "lost"', "report loss despite a preserved budget"),
    ("SURVIVE", "    zero_cost = 0\n    zero_tick = 0",
     "    zero_tick = 0\n    zero_cost = 0", "reorder-independent"),
    ("REACH", "    zero_cost = 0\n    zero_tick = 0",
     "    zero_cost = 0\n    zero_tick = 1", "changed origin"),
)



def changed(source, anchor, replacement):
    if source.count(anchor) != 1:
        raise ValueError("mutation anchor must occur exactly once")
    return source.replace(anchor, replacement, 1)


EXPECTED_NAMES = (
    "INPUT_TRACE", "INPUT_COST", "INPUT_SPAN", "INPUT_CAPACITY",
    "INPUT_LEVELS", "INPUT_OBSERVER", "INPUT_FIBRE", "INPUT_BASELINE",
    "EXACT_PREFIX", "TOTAL_PAIR", "FIRST_CROSSING", "FINAL_SURVIVAL",
    "WHOLE_SURVIVAL", "HELD_LINE", "PEAK", "OBSERVER_INVARIANCE",
    "FIBRE_TRIAD", "LOSS_STATUS",
)


def read_report(stdout, returncode):
    report = json.loads(stdout)
    if type(report) is not dict or type(report.get("checks")) is not list:
        raise ValueError("missing named result")
    rows = report["checks"]
    if any(type(row) is not dict or type(row.get("ok")) is not bool for row in rows):
        raise ValueError("invalid named result")
    names = [row.get("name") for row in rows]
    if tuple(names) != EXPECTED_NAMES:
        raise ValueError("incomplete or reordered named result")
    if type(report.get("finite_cases")) is not int or report["finite_cases"] != 1554:
        raise ValueError("unexpected finite case count")
    reds = [row["name"] for row in rows if not row["ok"]]
    if returncode != (1 if reds else 0) or report.get("ok") is not (not reds):
        raise ValueError("exit status or overall verdict disagrees with named verdicts")
    wanted_summary = "Checks: %d/%d; finite rational cases=%d" % (
        len(names) - len(reds), len(names), report["finite_cases"])
    if report.get("summary") != wanted_summary:
        raise ValueError("printed summary differs from named results")
    return names, reds, report["finite_cases"], report["summary"]


def parser_controls():
    good = {"checks": [{"name": name, "ok": True} for name in EXPECTED_NAMES],
            "finite_cases": 1554, "ok": True,
            "summary": "Checks: 18/18; finite rational cases=1554"}
    red = json.loads(json.dumps(good))
    red["checks"][10]["ok"] = False
    red["ok"] = False
    red["summary"] = "Checks: 17/18; finite rational cases=1554"
    read_report(json.dumps(good), 0)
    if read_report(json.dumps(red), 1)[1] != ["FIRST_CROSSING"]:
        raise ValueError("valid named failure returned unexpected red names")
    invalid = []
    cut = json.loads(json.dumps(red))
    cut["checks"] = cut["checks"][10:11]
    invalid.append(("truncated", cut, 1))
    wrong_count = json.loads(json.dumps(red))
    wrong_count["finite_cases"] = 0
    invalid.append(("case-count", wrong_count, 1))
    fractional_count = json.loads(json.dumps(good))
    fractional_count["finite_cases"] = 1554.0
    invalid.append(("inexact-count", fractional_count, 0))
    duplicate = json.loads(json.dumps(red))
    duplicate["checks"][-1] = duplicate["checks"][0]
    invalid.append(("duplicate-name", duplicate, 1))
    reordered = json.loads(json.dumps(red))
    reordered["checks"].reverse()
    invalid.append(("reordered-name", reordered, 1))
    nonboolean = json.loads(json.dumps(red))
    nonboolean["checks"][0]["ok"] = 1
    invalid.append(("nonboolean-result", nonboolean, 1))
    empty = json.loads(json.dumps(good))
    empty["checks"] = []
    invalid.append(("empty-result", empty, 0))
    invalid.append(("wrong-exit", red, 0))
    wrong_summary = json.loads(json.dumps(good))
    wrong_summary["ok"] = False
    invalid.append(("wrong-overall-verdict", wrong_summary, 0))
    inconsistent_summary = json.loads(json.dumps(good))
    inconsistent_summary["summary"] = "Checks: 0/18; finite rational cases=1554"
    invalid.append(("inconsistent-summary", inconsistent_summary, 0))
    controls = [{"control": "complete-green", "ok": True},
                {"control": "complete-red", "ok": True}]
    for name, report, exitcode in invalid:
        try:
            read_report(json.dumps(report), exitcode)
        except ValueError:
            controls.append({"control": name, "ok": True})
        else:
            raise ValueError("invalid report accepted: " + name)
    return controls


def run_copy(source, optimized):
    with TemporaryDirectory(prefix="person-model-") as folder:
        model = Path(folder) / "person_harness.py"
        model.write_text(source, encoding="utf-8", newline="\n")
        command = [sys.executable] + (["-O"] if optimized else []) + [str(model), "--json"]
        completed = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True,
                                   text=True, encoding="utf-8", timeout=15)
        return read_report(completed.stdout, completed.returncode)


def main():
    model = Path(__file__).with_name("person_harness.py")
    original = model.read_bytes()
    source = original.decode("utf-8")
    results = []
    controls = parser_controls()
    for optimized in (False, True):
        names, reds, cases, summary = run_copy(source, optimized)
        coverage = set(marker for marker, _, _, _ in BREAKS if marker not in ("SURVIVE", "REACH"))
        if reds or set(names) != coverage or cases != 1554:
            raise ValueError("baseline or bidirectional named coverage failed")
        number = 0
        for marker, anchor, replacement, description in BREAKS:
            number += 1
            names, reds, cases, summary = run_copy(changed(source, anchor, replacement), optimized)
            first = reds[0] if reds else None
            kind = marker if marker in ("SURVIVE", "REACH") else "RED"
            expected = None if kind == "SURVIVE" else "EXACT_PREFIX" if kind == "REACH" else marker
            passed = not reds if kind == "SURVIVE" else first == expected
            results.append({"mutation": number, "optimized": optimized, "expected": expected,
                            "first": first, "ok": passed, "kind": kind, "description": description,
                            "alive": names == list(EXPECTED_NAMES) and cases == 1554, "summary": summary})

    if model.read_bytes() != original:
        raise ValueError("original model was changed")
    result = {"model_sha256": hashlib.sha256(original).hexdigest(), "results": results,
              "parser_controls": controls, "ok": all(row["ok"] for row in results)}
    if "--json" in sys.argv:
        print(json.dumps(result, sort_keys=True))
    else:
        for row in results:
            print(("PASS " if row["ok"] else "FAIL ") + str(row["mutation"])
                  + (" -O" if row["optimized"] else "")
                  + " expected=" + str(row["expected"]) + " first=" + str(row["first"]))
        print("PARSER_CONTROLS %d/%d" % (sum(row["ok"] for row in controls), len(controls)))
        print("MUTATIONS %d/%d" % (sum(row["ok"] for row in results), len(results)))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())