# econlab

Secondary-data analysis for **cross-section, time-series and panel** data. Two ways to use it:

| | Python toolkit + Streamlit app | Browser Workbench |
|---|---|---|
| What | `econlab` package, CLI and a Streamlit web app built on statsmodels, linearmodels, arch and scikit-learn | One self-contained HTML page, plain JavaScript, no install |
| Where | `econlab/`, `app.py` | `web/` (built page: `docs/index.html`) |
| Best for | Scripted, reproducible analysis; automatic reports | Beginners, teaching, quick looks, data cleaning, charts |
| Offline | Yes (no API key, no network) | Yes (your data never leaves the page) |

Both work without any API key. An optional Claude integration exists in the Python toolkit only.

## Browser Workbench

Open `docs/index.html` in any browser, or publish the repo with **GitHub Pages** (Settings → Pages → *Deploy from a branch* → `main` → `/docs`).

- **Data tab:** sort, filter, drop or fill missing values, trim or winsorize outliers, lags / leads / differences, rolling statistics, within- and between-entity transforms, dummies, formulas, resampling. Every step is listed, removable, and replayable; copy or download the result.
- **Explore tab:** summary statistics, correlations, distributions, scatter plots, group comparisons, panel and time plots.
- **Cross-section:** OLS with diagnostics, logit, probit, Poisson, negative binomial, Tobit, quantile regression, IV/2SLS, Heckman, LASSO / ridge / elastic net, post-double-selection LASSO, matching / IPW, RDD, DiD, Oaxaca-Blinder, bootstrap, non-linear curves.
- **Time series:** unit-root suite, structural breaks, Hodrick-Prescott / Baxter-King / Christiano-Fitzgerald / Hamilton filters, seasonal adjustment, Kalman smoother, ARIMA, VAR with impulse responses, Johansen, ARDL bounds, GARCH, local projections, forecasting.
- **Panel:** pooled / fixed / random effects with the tests to choose, many standard-error options, first-difference, Fama-MacBeth, mean-group / CCE, Arellano-Bond, event study, Callaway-Sant'Anna, diagnostics and panel pictures.

Every result has a plain-English explanation and charts with hover tooltips. The full list of 63 analyses is in [`docs/METHODS.md`](docs/METHODS.md).

**Accuracy.** During development the numerics were compared with statsmodels, linearmodels, arch and scikit-learn on the example data; most match to four or more digits. Known differences: ARIMA and GARCH with Student-t use their own optimiser and can differ in the third digit; clustered standard errors in some panel methods differ by a few percent from packages that use other small-sample corrections; the Arellano-Bond tool is one-step only (its AR tests are a simplified regression version); Levin-Lin-Chu and Im-Pesaran-Shin panel unit-root tests and the Goodman-Bacon decomposition are not included. The comparison scripts are not part of this repository. For work you will publish, confirm key results in a statistics package.

**Developing.**
```bash
python web/build.py                      # src/ -> web/index.html and docs/index.html
pip install playwright && playwright install chromium
python web/tests/smoke_test.py           # renders every analysis, desktop and phone width
```
See [CONTRIBUTING.md](CONTRIBUTING.md).

## Python toolkit

```bash
pip install -r requirements.txt
streamlit run app.py                                                       # web app (csv/xlsx/dta/parquet/json)
python -m econlab.cli data.csv --y profit --x invest,size --report out.md  # command line
pytest -q                                                                  # known-truth simulations
```
```python
import econlab as el
a = el.Analysis("examples/panel_firms.csv", y="profit", x=["invest", "size"]).run()
print(a.report("report.md"))
```

It detects the data structure and runs the matching methods:

| Data type | Methods |
|---|---|
| Cross-section | OLS (HC0-3 / clustered), WLS, Logit/Probit + marginal effects, Poisson, NegBin, MNLogit, ordered logit, Tobit, quantile regression, 2SLS/IV, Heckman, propensity score & matching, RDD, diff-in-diff, BP/White/RESET/JB tests, influence, VIF |
| Time series | ADF, KPSS, Phillips-Perron, DF-GLS, Zivot-Andrews, auto-ARIMA/SARIMA, Holt-Winters, STL, HP filter, Ljung-Box/ARCH-LM, Chow & CUSUM, VAR, Granger, IRF/FEVD, Engle-Granger, Johansen, VECM, ARDL bounds, GARCH/GJR/EGARCH, Markov switching, local projections |
| Panel | Pooled, FE (entity/time/two-way), RE, between, first-difference, clustered / Driscoll-Kraay SE, Hausman (+ robust Mundlak), Wooldridge serial correlation, groupwise heteroskedasticity, Pesaran CD, panel unit root, panel IV, Anderson-Hsiao, TWFE event study |
| ML / text | LASSO / Ridge / Elastic Net, post-LASSO, random-forest importance, Double ML, TF-IDF, LDA, lexicon sentiment |
| Assistant | Rule-based plain-language interpretation, specification advice, design critique, data Q&A, text classification. Fully offline in `econlab/local_ai.py`; optional Claude upgrade (`pip install anthropic`, set `ANTHROPIC_API_KEY`) falls back to the offline engine on any error |

**Limits.** The dynamic-panel estimator here is Anderson-Hsiao; use the Workbench's Arellano-Bond or Stata `xtabond2` / R `pgmm` for GMM. Staggered-adoption DiD (Callaway-Sant'Anna) is in the Workbench, not the Python package; `twfe_event_study` is plain TWFE and can be biased under heterogeneous effects. The offline assistant applies fixed econometric rules to coefficients and test outputs; it is not a language model, and numbers always come from the econometric code.

### Run it offline / host it
- **Windows:** double-click `run.bat`. **Linux/macOS:** `./run.sh` (creates a virtual environment on first run).
- **Docker:** `docker build -t econlab . && docker run -p 8501:8501 econlab`
- **Streamlit Community Cloud / Hugging Face Spaces / Render:** point at `app.py` (start command `streamlit run app.py`).

## Repository layout
```
econlab/        Python package (core, cross_section, time_series, panel, ml, llm, local_ai, auto, cli)
app.py          Streamlit app
tests/          Python tests (known-truth simulations)
examples/       Sample CSVs and the generator script
web/            Browser Workbench: src/ (head, body, js modules), build.py, tests/
docs/           Built Workbench (index.html) for GitHub Pages + METHODS.md
.github/        CI: Python tests, stale-build check, Workbench smoke test
```

## License
MIT — see [LICENSE](LICENSE).
