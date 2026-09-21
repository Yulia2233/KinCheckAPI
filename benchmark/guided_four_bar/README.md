# Guided four-bar benchmark

`prompt.md` and `verify.py` are the paired benchmark inputs. `verify.py` is a
byte-for-byte copy of the authoritative
`examples/guided_four_bar_actuator/verification/verify.py`; the original example
script has not been edited.
The reference checks the exported motion, closure residuals, limits, sampled
and continuous geometry, all physical pair expansion, assembly integrity, and
a real-mesh negative control.

The evaluator deliberately reports `benchmark_ready=false`: the historical
example does not independently measure every drawing feature named by the
prompt (hole, flange, web, and lightening-hole dimensions). Its motion and
collision result is retained as `reference_passed`; it is not promoted to a
full prompt hard pass without those geometry checks.

Run through the common adapter:

```bash
python benchmark/adapter.py \
  /path/to/guided_four_bar_actuator.scadpkg \
  benchmark/guided_four_bar/verification/verify.py \
  --work-dir /tmp/benchmark-guided-four-bar
```
