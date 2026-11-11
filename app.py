"""econlab web app.  Run:  streamlit run app.py"""
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from econlab import core, cross_section as cs, time_series as ts, panel as pn, ml, llm
from econlab.auto import Analysis, _fmt

st.set_page_config(page_title="econlab", layout="wide")
st.title("econlab — secondary data analysis")
st.caption("Cross-section · Time series · Panel · Machine learning · Offline assistant")

# ------------------------------------------------------------------ sidebar: data
with st.sidebar:
    st.header("1 · Data")
    up = st.file_uploader("Upload csv / xlsx / dta / parquet / json",
                          type=["csv", "tsv", "xlsx", "xls", "dta", "parquet", "json"])
    demo = st.selectbox("…or use a demo dataset", ["—", "cross_section_wages", "time_series_macro", "panel_firms"])
    if up is not None:
        import tempfile, os
        suffix = os.path.splitext(up.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            f.write(up.getbuffer()); path = f.name
        raw = core.load_data(path)
    elif demo != "—":
        raw = core.load_data(f"examples/{demo}.csv")
    else:
        st.info("Upload a file or pick a demo."); st.stop()

    prof0 = core.detect_structure(raw)
    st.header("2 · Structure")
    cols = ["(none)"] + list(raw.columns)
    ent = st.selectbox("Entity column", cols, index=cols.index(prof0.entity_col) if prof0.entity_col in cols else 0)
    tim = st.selectbox("Time column", cols, index=cols.index(prof0.time_col) if prof0.time_col in cols else 0)
    ent = None if ent == "(none)" else ent
    tim = None if tim == "(none)" else tim
    prof = core.detect_structure(raw, ent, tim)

    st.header("3 · Variables")
    num = prof.numeric_cols
    y = st.selectbox("Dependent (y)", num)
    x = st.multiselect("Regressors (x)", [c for c in num if c != y], default=[c for c in num if c != y][:3])

st.success(f"Detected: **{prof.kind.replace('_', ' ')}**  ·  {prof.n_obs} obs  ·  {prof.n_vars} variables"
           + (f"  ·  {prof.n_entities} entities × {prof.n_periods} periods" if prof.kind == "panel" else ""))

tabs = st.tabs(["Explore", "Cross-section", "Time series", "Panel", "ML", "Assistant / Text", "Auto report"])

# ------------------------------------------------------------------ explore
with tabs[0]:
    st.dataframe(raw.head(50), width='stretch')
    st.subheader("Descriptive statistics"); st.dataframe(core.describe(raw), width='stretch')
    st.subheader("Correlation")
    c = core.correlation(raw[[y] + x]) if x else None
    if c is not None:
        fig, ax = plt.subplots(figsize=(5, 4)); im = ax.imshow(c, cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set_xticks(range(len(c))); ax.set_xticklabels(c.columns, rotation=45, ha="right")
        ax.set_yticks(range(len(c))); ax.set_yticklabels(c.index); fig.colorbar(im); st.pyplot(fig)

# ------------------------------------------------------------------ cross-section
with tabs[1]:
    st.caption("Works on any dataset (pooled treatment of rows).")
    model = st.selectbox("Model", ["OLS", "Logit", "Probit", "Poisson", "Quantile", "2SLS (IV)", "Diff-in-diff"])
    if x and st.button("Run", key="cs"):
        f = f"{y} ~ " + " + ".join(x)
        try:
            if model == "OLS":
                cov = st.session_state.get("cov", "HC3")
                r = cs.ols(raw, f, cov); st.code(str(r.summary())); st.json({k: v for k, v in cs.diagnostics(r).items()}, expanded=False)
            elif model == "Logit":
                r = cs.logit(raw, f); st.code(str(r.summary())); st.dataframe(cs.marginal_effects(r))
            elif model == "Probit":
                r = cs.probit(raw, f); st.code(str(r.summary())); st.dataframe(cs.marginal_effects(r))
            elif model == "Poisson":
                st.code(str(cs.poisson(raw, f).summary()))
            elif model == "Quantile":
                for q, r in cs.quantile_reg(raw, f).items():
                    st.write(f"τ = {q}"); st.dataframe(r.params.to_frame("coef"))
            elif model == "2SLS (IV)":
                endog = st.multiselect("Endogenous", x); inst = st.multiselect("Instruments", [c for c in num if c not in x + [y]])
                if endog and inst:
                    st.code(str(cs.iv2sls(raw, y, [c for c in x if c not in endog], endog, inst)))
            elif model == "Diff-in-diff":
                st.info("Pick treat, post as the first two regressors; interaction is added automatically.")
                st.code(str(cs.diff_in_diff(raw, y, x[0], x[1]).summary()))
        except Exception as e:
            st.error(str(e))

# ------------------------------------------------------------------ time series
with tabs[2]:
    if prof.time_col is None:
        st.info("Select a time column in the sidebar to enable time-series tools.")
    elif x or y:
        d = ts.prepare(raw.drop_duplicates(prof.time_col) if prof.kind == "panel" else raw, prof.time_col)
        var = st.selectbox("Series", num, index=num.index(y)); st.line_chart(d[var])
        t = st.selectbox("Tool", ["Unit-root tests", "ARIMA + forecast", "VAR + Granger", "Cointegration (Johansen)",
                                  "GARCH", "HP filter", "Local projections"])
        if st.button("Run", key="ts"):
            try:
                if t == "Unit-root tests":
                    st.dataframe(ts.unit_root_tests(d[var])); st.write("Order of integration I(d), d =", ts.integration_order(d[var]))
                elif t == "ARIMA + forecast":
                    order, res = ts.auto_arima(d[var], 3, 3); st.write("Selected", order); st.code(str(res.summary()))
                    f = ts.forecast(res, 12); st.line_chart(pd.concat([d[var].tail(60), f["mean"]]))
                elif t == "VAR + Granger" and x:
                    v = d[[var] + x[:3]].diff().dropna(); res, sel = ts.var_model(v, 8); st.code(str(res.summary()))
                    st.dataframe(ts.granger(v, var, x[0], 4))
                elif t == "Cointegration (Johansen)" and x:
                    st.dataframe(ts.johansen(d[[var] + x[:3]]))
                elif t == "GARCH":
                    st.code(str(ts.garch(d[var].pct_change().dropna() if (d[var] > 0).all() else d[var]).summary()))
                elif t == "HP filter":
                    st.line_chart(ts.hp_filter(d[var]))
                elif t == "Local projections" and x:
                    lp = ts.local_projections(d[var].diff(), d[x[0]].diff(), 12); st.line_chart(lp.set_index("h")[["beta", "lo", "hi"]])
            except Exception as e:
                st.error(str(e))

# ------------------------------------------------------------------ panel
with tabs[3]:
    if prof.kind != "panel":
        st.info("Needs entity + time columns (set them in the sidebar).")
    elif x:
        p_ = pn.to_panel(raw, prof.entity_col, prof.time_col)
        cov = st.selectbox("Standard errors", ["clustered", "robust", "unadjusted", "driscoll-kraay"])
        if st.button("Run all estimators", key="pn"):
            try:
                pool = pn.pooled(p_, y, x, cov if cov != "driscoll-kraay" else "clustered")
                fe = pn.fixed_effects(p_, y, x, True, False, cov); re = pn.random_effects(p_, y, x, cov if cov != "driscoll-kraay" else "clustered")
                tw = pn.fixed_effects(p_, y, x, True, True, cov)
                st.code(str(pn.compare_models(Pooled=pool, FE=fe, RE=re, TwoWayFE=tw)))
                st.subheader("Specification tests")
                st.write("Entity-effects F-test", pn.f_test_effects(fe)); st.write("Hausman", pn.hausman_test(p_, y, x))
                st.write("Serial corr / heterosk. / cross-sectional dependence", pn.panel_diagnostics(p_, y, x, fe))
                st.write("Panel unit root", pn.panel_unit_root(p_, y))
            except Exception as e:
                st.error(str(e))

# ------------------------------------------------------------------ ML
with tabs[4]:
    if x:
        m = st.selectbox("Method", ["LASSO selection", "Random-forest importance", "Double ML (effect of 1st regressor)"])
        if st.button("Run", key="ml"):
            try:
                if m == "LASSO selection":
                    st.dataframe(ml.lasso_select(raw, y, x)[0].to_frame("coef"))
                elif m == "Random-forest importance":
                    imp, r2, _ = ml.forest_importance(raw, y, x); st.write(f"CV R² = {r2:.3f}"); st.bar_chart(imp)
                else:
                    st.json(ml.double_ml(raw, y, x[0], x[1:]) if len(x) > 1 else {"error": "need ≥2 regressors"})
            except Exception as e:
                st.error(str(e))

# ------------------------------------------------------------------ LLM / text
with tabs[5]:
    st.write("Assistant mode:", "🟢 " + llm.mode(), "— works with no internet and no API key.")
    q = st.text_area("Research question / context (or a question about your data, e.g. 'average of wage')")
    c1, c2, c3 = st.columns(3)
    if c1.button("Suggest specification"):
        st.markdown(llm.suggest_specification(prof.summary(), raw.columns, q))
    if c2.button("Ask about the data"):
        st.text(llm.natural_language_query(raw, q))
    if c3.button("Critique my design"):
        st.markdown(llm.critique_design(q or prof.summary()))
    if x and st.button("Run a model and explain it in plain language"):
        try:
            if prof.kind == "panel":
                res = pn.fixed_effects(pn.to_panel(raw, prof.entity_col, prof.time_col), y, x)
            else:
                res = cs.ols(raw, f"{y} ~ " + " + ".join(x), "HC3")
            st.markdown(llm.interpret_results(res, q))
        except Exception as e:
            st.error(str(e))
    if prof.text_cols:
        st.subheader("Text columns")
        tc = st.selectbox("Column", prof.text_cols)
        if st.button("Sentiment score"):
            st.write(ml.lexicon_sentiment(raw[tc]).describe())
        lab = st.text_input("Classify into labels (comma-separated)", "positive,negative,neutral")
        if st.button("Classify text"):
            st.dataframe(llm.classify_texts(raw[tc].head(100), [l.strip() for l in lab.split(",")]).value_counts())
        if st.button("Topic model"):
            tp, _ = ml.topic_model(raw[tc]); st.json(tp)

# ------------------------------------------------------------------ auto report
with tabs[6]:
    use_llm = st.checkbox("Include plain-language interpretation and strategy advice", value=True)
    if st.button("Generate full report"):
        a = Analysis(raw, y, x, ent, tim).run(with_llm=use_llm, research_question=q if 'q' in dir() else "")
        md = a.report(); st.markdown(md)
        st.download_button("Download report (.md)", md, "econlab_report.md")
