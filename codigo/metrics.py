import numpy as np, pandas as pd
from itertools import combinations
from scipy.stats import norm, skew, kurtosis


def stats(res, rf=0.0):
    r = res["ret"]
    nav = res["nav"]
    yrs = (nav.index[-1] - nav.index[0]).days / 365.25
    cagr = (nav.iloc[-1] / (nav.iloc[0] / (1 + r.iloc[0]))) ** (1 / max(yrs, 1e-9)) - 1
    vol = r.std() * np.sqrt(365)
    sh = r.mean() / r.std() * np.sqrt(365) if r.std() > 0 else 0
    dn = r[r < 0].std() * np.sqrt(365)
    dd = (nav / nav.cummax() - 1).min()
    act = r[r.abs() > 1e-7]
    wk = nav.resample("W").last().pct_change().dropna()
    mo = nav.resample("ME").last().pct_change().dropna()
    return dict(CAGR=cagr, Vol=vol, Sharpe=sh, Sortino=(r.mean() * 365 / dn if dn > 0 else 0), MaxDD=dd,
                Calmar=(cagr / -dd if dd < 0 else np.nan), DiasPos=(act > 0).mean(), MediaDia=act.mean(),
                SemanasPos=(wk > 0).mean(), MesesPos=(mo > 0).mean(),
                CostesAnualPct=res["cost"].sum() / nav.mean() / max(yrs, 1e-9),
                Turnover=res["turnover"].mean() * 365, Gross=res["gross"].mean(), Net=res["net"].mean())


def deflated_sharpe(r, n_trials, sr_trials_var=None):
    """Bailey & López de Prado (2014). r: retornos por periodo. Devuelve prob. de que SR>0 tras corregir nº de pruebas."""
    r = pd.Series(r).dropna()
    r = r[r != 0]
    T = len(r)
    sr = r.mean() / r.std()
    g3, g4 = skew(r), kurtosis(r, fisher=False)
    if sr_trials_var is None:
        sr_trials_var = 1.0 / T  # varianza de SR bajo la nula
    emc = 0.5772156649
    sr0 = np.sqrt(sr_trials_var) * ((1 - emc) * norm.ppf(1 - 1 / n_trials) + emc * norm.ppf(1 - 1 / (n_trials * np.e))) if n_trials > 1 else 0
    z = (sr - sr0) * np.sqrt(T - 1) / np.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr ** 2)
    return norm.cdf(z)


def pbo_cscv(M, S=16):
    """Probabilidad de sobreajuste del backtest (CSCV). M: DataFrame T x estrategias de retornos OOS."""
    M = M.dropna()
    blocks = np.array_split(np.arange(len(M)), S)
    X = M.values
    logits = []
    for comb in combinations(range(S), S // 2):
        tr = np.concatenate([blocks[k] for k in comb])
        te = np.concatenate([blocks[k] for k in range(S) if k not in comb])
        sr_tr = X[tr].mean(0) / X[tr].std(0)
        sr_te = X[te].mean(0) / X[te].std(0)
        best = np.argmax(sr_tr)
        rank = (sr_te < sr_te[best]).sum() + 0.5
        w = rank / (X.shape[1] + 0)
        w = min(max(w, 1e-6), 1 - 1e-6)
        logits.append(np.log(w / (1 - w)))
    logits = np.array(logits)
    return (logits <= 0).mean()
