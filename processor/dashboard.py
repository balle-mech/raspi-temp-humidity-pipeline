import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import altair as alt
import pandas as pd
import streamlit as st

from processor.data import (
    compute_hum_domain,
    compute_temp_domain,
    load_data as _load_data,
    resample_for_display,
    rolling_median,
    x_format,
)

st.set_page_config(page_title="温湿度ダッシュボード", page_icon="🌡", layout="wide")


@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    return _load_data()


def _make_chart(
    data: pd.DataFrame,
    column: str,
    y_title: str,
    y_domain: list,
    fmt: str,
    raw: pd.DataFrame | None = None,
) -> alt.Chart:
    color = "#e05c5c" if column == "temperature_c" else "#5c8ae0"
    line = (
        alt.Chart(data.reset_index())
        .mark_line(color=color, strokeWidth=2)
        .encode(
            x=alt.X("timestamp:T", axis=alt.Axis(format=fmt, title=None, labelAngle=-30)),
            y=alt.Y(
                f"{column}:Q",
                scale=alt.Scale(domain=y_domain, clamp=True),
                axis=alt.Axis(title=y_title),
            ),
            tooltip=[
                alt.Tooltip("timestamp:T", title="日時", format="%Y/%m/%d %H:%M"),
                alt.Tooltip(f"{column}:Q", title=y_title, format=".1f"),
            ],
        )
        .properties(height=280)
    )
    if raw is None:
        return line
    raw_line = (
        alt.Chart(raw.reset_index())
        .mark_line(color=color, strokeWidth=1, opacity=0.3)
        .encode(
            x=alt.X("timestamp:T"),
            y=alt.Y(f"{column}:Q", scale=alt.Scale(domain=y_domain, clamp=True)),
        )
    )
    return raw_line + line


st.markdown("""
<style>
[data-testid="stHeader"]::before {
    content: "🌡 温湿度ダッシュボード";
    position: absolute;
    left: 1rem;
    top: 50%;
    transform: translateY(-50%);
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-color);
}
</style>
""", unsafe_allow_html=True)

df = load_data()

if df.empty:
    st.warning("データが見つかりません。")
    st.stop()

latest_ts = df["timestamp"].max()
latest = df[df["timestamp"] == latest_ts].iloc[0]
c1, c2, c3 = st.columns(3)
c1.metric("最新 温度", f"{latest['temperature_c']:.1f} ℃")
c2.metric("最新 湿度", f"{latest['humidity_pct']:.1f} %")
c3.metric("最終更新", latest_ts.strftime("%m/%d %H:%M"))

st.divider()

_PERIODS = {"直近1日": 1, "直近3日": 3, "直近1週間": 7, "直近1ヶ月": 30, "直近1年": 365, "カスタム": None}
period_label = st.radio("表示期間", list(_PERIODS.keys()), horizontal=True)

if _PERIODS[period_label] is not None:
    mask = df["timestamp"] >= latest_ts - pd.Timedelta(days=_PERIODS[period_label])
else:
    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input("開始日", value=df["timestamp"].dt.date.min())
    with col2:
        end = st.date_input("終了日", value=df["timestamp"].dt.date.max())
    mask = (df["timestamp"].dt.date >= start) & (df["timestamp"].dt.date <= end)
filtered = df[mask].set_index("timestamp")

if filtered.empty:
    st.warning("選択した期間にデータがありません。")
    st.stop()

smooth_on = st.checkbox(
    "平滑化（1時間ローリング中央値）",
    value=True,
    help="DHT-11 の読み取りノイズを抑えるため、直近1時間の中央値を表示します。薄い線が生データです。",
)

display = resample_for_display(filtered)
days_shown = (display.index[-1] - display.index[0]).total_seconds() / 86400
fmt = x_format(days_shown)

if smooth_on:
    main_line = resample_for_display(rolling_median(filtered)).dropna(how="all")
    raw_line = display
else:
    main_line = display
    raw_line = None

st.subheader("温度 (℃)")
st.altair_chart(
    _make_chart(main_line, "temperature_c", "℃", compute_temp_domain(display), fmt, raw=raw_line),
    use_container_width=True,
)

st.subheader("湿度 (%)")
st.altair_chart(
    _make_chart(main_line, "humidity_pct", "%", compute_hum_domain(display), fmt, raw=raw_line),
    use_container_width=True,
)
