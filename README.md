# The Person Is Not a Sum

![The Person Is Not a Sum — same total, different histories](assets/person-cover.gif)

**The Thousand-Year Warrior II, or The Person Is Not a Sum**  
by MxBv · Navigational Cybernetics 2.5

The original essay was published on **29 June 2026**: [DOI 10.17605/OSF.IO/MJPDX](https://doi.org/10.17605/OSF.IO/MJPDX). This repository preserves that edition and adds finite, executable structural examples written on **30 September 2026**.

## Scope and limits

The code illustrates selected distinctions from the essay. It does not verify every argument in the essay, determine moral character, detect a clinical change, identify a person, or establish preservation of a whole system.

The preserved essay is a structural illustration in moral language. These executable examples do not establish its moral classifications or its broad claims about aggregates for arbitrary systems. An aggregate can be sufficient for one predicate while losing information needed for another.

Budget examples use a fixed positive rational capacity and exact nonnegative rational charges. Charges occur at the ends of a finite ordered sequence of windows. Each window has a positive integer span: a declared coordinate, with no physical clock or within-window dynamics supplied by this model. Complete proposed routes may contain rejected prefixes; they are not thereby wholly executed admissible histories.

Level examples use supplied rational values and a declared floor. Observer examples compare supplied Boolean answers; constancy alone does not establish their truth. Observation classes are restricted to an explicitly supplied finite catalogue and deterministic functions defined on the relevant inputs. The code does not establish that the catalogue describes an actual system or exhausts all possible states.

## What the examples distinguish

**An aggregate and the first crossing.** At capacity `1/2`, the proposed charge sequences `(1/3, 2/3)` and `(2/3, 1/3)`, each with unit spans, have equal total charge `1` and total span `2`. Their first nonpositive budget occurs at window `2` and window `1`, respectively. The ordered trace retains that difference; the aggregate loses it.

**Where the aggregate is sufficient.** Under the stated fixed-capacity, nonnegative-charge assumptions, a positive final budget is equivalent to positive budgets at every prefix. Total charge therefore determines this particular verdict. The example does not imply that every aggregate is insufficient.

**A peak and a held line.** The supplied sequences `(1, 0, 0)` and `(1/3, 1/3, 1/3)` both sum to `1`. Only the second stays at or above a floor of `1/4` at every supplied position. A closed level floor (`>=`) is distinct from the strictly positive budget rule (`> 0`).

**Constancy and truth.** Both `(True, True)` and `(False, False)` are constant. Neither the word “constant” nor a constant monitor output makes a state admissible.

**What a finite observation permits.** For an attained observation, an all-true class admits the supplied predicate, an all-false class rejects it, and a mixed class is insufficient to decide. These are verdicts about the supplied predicate on that finite class. An unattained observation is refused; it is not treated as an empty successful class.

**Loss of the checked budget condition.** A positive initial condition is required before the budget comparison reports loss. This checks one declared condition and does not establish loss or preservation of identity.

## Run

Python 3.10 or later; standard library only.

```sh
python person_harness.py
python -O person_harness.py
python break_person_harness.py
```

The harness prints 18 named checks, including 1,554 enumerated rational traces and additional explicit boundary examples. `--json` produces machine-readable results.

The mutation runner changes disposable copies. For every copy, it validates the ordered named Boolean verdicts, finite case count, exit status, overall verdict and summary. It requires the expected first failure for each of 32 broken implementations and runs an equivalent-change control and a changed-origin control. Model runs include both ordinary Python and `-O`. Report-parser controls check acceptance of consistent named-verdict reports and refusal of reports that omit or contradict required verdict fields. Diagnostic `detail` is outside this admission check. These checks concern the published examples and listed mutations.

## Original publication

The essay and its existing signatures and timestamps are copied without editing into `paper/`. The PDF and its detached signature match the original [OSF deposit](https://osf.io/mjpdx/).

The publication date is independently visible in the [OSF event journal](https://api.osf.io/v2/nodes/mjpdx/logs/?page%5Bsize%5D=100): the work became public on 29 June 2026 and its DOI was registered that day. It is also recorded on the [author's publication page](https://petronus.eu/blog/thousand-year-warrior-ii/).

The June publication date belongs to the essay. It does not backdate the September code or the creation of this repository.

## License

[Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International](https://creativecommons.org/licenses/by-nc-nd/4.0/) — MxBv.

[Part I](https://doi.org/10.17605/OSF.IO/ZY3PW) · [NC2.5 v2.1](https://doi.org/10.17605/OSF.IO/NHTC5)

The essay offers a structural interpretation of moral evaluation; it does not establish a moral code or issue judgments about particular people.
