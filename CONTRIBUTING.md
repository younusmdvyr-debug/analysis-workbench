# Contributing

## Python package (`econlab/`)
```bash
pip install -r requirements.txt pytest
pytest -q
```
Add a method to the matching module (`cross_section.py`, `time_series.py`, `panel.py`, `ml.py`), expose it in `auto.py` if it should run in the automatic pipeline, and add a known-truth simulation to `tests/test_econlab.py`.

## Browser Workbench (`web/`)
The page is plain JavaScript with no dependencies and no bundler. Sources live in `web/src/`; `python web/build.py` concatenates them into `web/index.html` (copied to `docs/index.html` for GitHub Pages). **Commit the rebuilt files** — CI fails if they are stale.

- `src/js/` files load in file-name order inside one strict-mode function, so a new module needs its own `(function(){ ... })();` wrapper and a numeric prefix that places it after the helpers it uses.
- Register an analysis with `method({id, area, group, label, blurb, needs, opts, run(ctx)})` (see `40_ui_core.js` and any `*_base.js` file for examples) and give it a `test:{demo, y, xs, opts}` entry so the smoke test can exercise it.
- Every result should carry a plain-English explanation (`plain([...])`) and, where possible, be checked against statsmodels / linearmodels / arch on the bundled example data.
- `python web/tests/smoke_test.py` renders every analysis at desktop and phone width.
- `01_tables.js` (MacKinnon p-value tables) and the Johansen table inside `65_ts_more.js` are copied from statsmodels; regenerate rather than edit by hand.
