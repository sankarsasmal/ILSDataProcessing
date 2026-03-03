import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import csv
from plotly.colors import n_colors
import re
import streamlit.components.v1 as components

# =====================================================================
# 1. Page Configuration & Custom Theme (60-30-10 Rule)
# =====================================================================
st.set_page_config(page_title="ILS - Data Analysis", layout="wide", page_icon="⚡")

# Custom CSS for the Dark Theme (Black, White, Neon Green)
st.markdown(
    """
<style>
/* =========================================
    60-30-10 MASTER THEME
    ========================================= */
/* 60% Primary (Background) */
.stApp, .main { background-color: #0A0A0A; color: #FFFFFF; }
/* 30% Secondary (Text/Cards/Containers) */
h1, h2, h3, h4, h5, h6, p, span, label { color: #FFFFFF !important; }
/* Box Borders - Updated to #32322f */
[data-testid="stExpander"] {
    background-color: #121212;
    border: 1px solid #32322f !important;
    border-radius: 8px;
}
[data-testid="stHeader"] { background-color: rgba(10, 10, 10, 0.8); }
/* 10% Accent (Neon Green: #BFFF00) */
.stButton > button {
    background-color: #BFFF00 !important;
    color: #000000 !important;
    border: none !important;
    font-weight: bold !important;
    border-radius: 6px !important;
    transition: all 0.2s ease;
}
.stButton > button:hover { background-color: #99CC00 !important; transform: translateY(-2px); }
.stTabs [data-baseweb="tab-highlight"] { background-color: #BFFF00 !important; }

/* =========================================
    COMPONENT OVERRIDES
    ========================================= */
/* --- Slider Sliding Line and Thumb Color Fix --- */
.stSlider div[data-baseweb="slider"] div[role="slider"] {
    background-color: #f20014 !important;
    border-color: #f20014 !important;
}
.stSlider div[data-baseweb="slider"] div[style*="background-color: rgb(255, 75, 75)"] {
    background-color: #f20014 !important;
}
.stSlider div[data-baseweb="slider"] div > div > div > div[style*="background-color"] {
    background-color: #99CC00 !important;
}
/* --- Checkbox Fix: Remove highlight, keep bold white text --- */
.stCheckbox label span {
    background-color: transparent !important;
    color: #FFFFFF !important;
    font-weight: bold !important;
}
/* --- Input/Number Boxes Border Fix --- */
div[data-baseweb="input"] > div {
    border: 1px solid #32322f !important;
}
/* --- File Uploader Fix: Black text, #121212 background, Custom border --- */
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] small,
[data-testid="stFileUploadDropzone"] button,
[data-testid="stFileUploadDropzone"] span {
    color: #000000 !important;
}
[data-testid="stFileUploadDropzone"] {
    background-color: #121212 !important;
    border: 1px dashed #32322f !important;
}
/* --- Dropdown (Select/Multiselect) Background, Text, Placeholder & Border Update --- */
div[data-baseweb="select"] > div {
    background-color: #121212 !important;
    border: 1px solid #32322f !important;
}
div[data-baseweb="select"] * {
    color: #FFFFFF !important;
}
div[data-baseweb="select"] input::placeholder {
    color: #FFFFFF !important;
    opacity: 1 !important;
    -webkit-text-fill-color: #FFFFFF !important;
}
ul[role="listbox"] {
    background-color: #121212 !important;
    border: 1px solid #32322f !important;
}
ul[role="listbox"] li {
    color: #FFFFFF !important;
}
/* --- Multiselect Dropdown & Tag Highlight Color Update --- */
span[data-baseweb="tag"] {
    background-color: #f20014 !important;
    color: #000000 !important;
}
ul[role="listbox"] li:hover,
ul[role="listbox"] li[aria-selected="true"],
ul[role="listbox"] li[aria-selected="false"]:hover {
    background-color: #f20014 !important;
    color: #000000 !important;
}
/* --- Metric Color Fix: Ensure metric labels and values are white --- */
[data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
    color: #FFFFFF !important;
}
/* =========================================
    CUSTOM DEMARCATION HEADERS
    ========================================= */
.section-header {
    color: #BFFF00 !important;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-size: 16px;
    font-weight: bold;
    border-bottom: 2px solid #32322f !important; /* Changed from #222 */
    padding-bottom: 8px;
    margin-top: 40px;
    margin-bottom: 20px;
}
</style>
""",
    unsafe_allow_html=True,
)


# Header
t1, t2 = st.columns((0.05, 0.95))
t1.markdown(
    "<h1 style='color:#BFFF00; font-size: 40px;'>⚡</h1>", unsafe_allow_html=True
)
t2.markdown(
    '<h1 style="color:#FFFFFF; margin-top: 5px;">ILS Data Analysis Dashboard</h1>',
    unsafe_allow_html=True,
)

# =====================================================================
# 2. Main File Upload & Data Cleaning
# =====================================================================
fl = st.file_uploader(
    "📂 Upload main analysis file", type=["csv", "txt", "xlsx", "xls"]
)

if fl is None:
    st.info("👈 Please upload a dataset to begin analysis.")
    st.stop()

# Efficient Data Loading
file_extension = fl.name.split(".")[-1].lower()
if file_extension in ["csv", "txt"]:
    df_raw = pd.read_csv(fl, delimiter="\t", encoding="cp1252")
elif file_extension in ["xlsx", "xls"]:
    df_raw = pd.read_excel(fl)
else:
    st.error("Unsupported file type")
    st.stop()

# =====================================================================
# 2.1 Calibration Correction for H2
# =====================================================================

# ---- Calibration table for H2 (from your data) ----
calib_h2 = pd.DataFrame(
    {
        "H2 Conc[Vol%]": [19.77, 39.87, 59.76, 79.57],
        "Area": [4556250, 9023977, 13285364, 17515766],  # not used in calc
        "RF": [4.34e-06, 4.42e-06, 4.50e-06, 4.54e-06],
    }
)

H2_CONC_COL = "Conc_H2"  # H2 concentration column in df_raw (Vol%)
H2_AREA_COL = "Area_H2"  # Area column for H2 in df_raw


# Validate presence
missing_cols = [col for col in [H2_CONC_COL, H2_AREA_COL] if col not in df_raw.columns]
if missing_cols:
    st.error(
        f"Missing required column(s): {missing_cols}. "
        f"Please ensure your file contains '{H2_CONC_COL}' and '{H2_AREA_COL}'."
    )
    st.stop()

# Ensure numeric
df_raw[H2_CONC_COL] = pd.to_numeric(df_raw[H2_CONC_COL], errors="coerce")
df_raw[H2_AREA_COL] = pd.to_numeric(df_raw[H2_AREA_COL], errors="coerce")

# ===========================
# Extrapolate RF to 10 and 100
# ===========================
x = calib_h2["H2 Conc[Vol%]"].to_numpy()
y = calib_h2["RF"].to_numpy()

use_quadratic = False  # set True if you want to try deg=2; linear is default/safest

if use_quadratic and len(x) >= 3:
    # Quadratic fit (more flexible but risky with extrapolation)
    coeffs = np.polyfit(x, y, deg=2)  # y = a*x^2 + b*x + c
    poly = np.poly1d(coeffs)
    deg_used = 2
else:
    # Linear fit (robust for small datasets and safer extrapolation)
    coeffs = np.polyfit(x, y, deg=1)  # y = m*x + c
    poly = np.poly1d(coeffs)
    deg_used = 1

# Predict RF at endpoints 10 and 100
rf_at_10 = float(poly(10.0))
rf_at_100 = float(poly(100.0))

# Guard against negative RF due to odd fits (rare with your data)
rf_at_10 = max(rf_at_10, 0.0)
rf_at_100 = max(rf_at_100, 0.0)

# Build extended calibration grid using the original points and the extrapolated endpoints
extended_calib = (
    pd.DataFrame(
        {
            "H2 Conc[Vol%]": [10.0, 19.77, 39.87, 59.76, 79.57, 100.0],
            "RF": [rf_at_10, *y, rf_at_100],
        }
    )
    .sort_values("H2 Conc[Vol%]")
    .reset_index(drop=True)
)

with st.expander("↕ Expand to see H2 calibration table", expanded=False):
    st.dataframe(
        extended_calib,
        use_container_width=True,
        column_config={
            "RF": st.column_config.NumberColumn(format="%.6e"),
            "H2 Conc[Vol%]": st.column_config.NumberColumn(format="%.2f"),
        },
        hide_index=True,
    )


# Compute simple R^2 on original points for transparency
y_pred_on_train = poly(x)
ss_res = np.sum((y - y_pred_on_train) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2) if len(y) > 1 else 0.0
r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 1.0
st.info(
    f"RF fit degree = {deg_used}, R² on original points = {r2:.5f}. "
    f"Extrapolated RF(10%)={rf_at_10:.6g}, RF(100%)={rf_at_100:.6g}"
)

# ===========================
# Assign RF to each row
# ===========================
# We will use interpolation within [10, 100] and *clip* to endpoints outside that range.
# This avoids noisy nearest-neighbor jumps and ensures smooth mapping.
x_ext = extended_calib["H2 Conc[Vol%]"].to_numpy()
y_ext = extended_calib["RF"].to_numpy()

# Clip H2 conc into [10, 100] to avoid wild extrapolation beyond the fit
conc_vals = df_raw[H2_CONC_COL].to_numpy()
conc_clipped = np.clip(conc_vals, x_ext.min(), x_ext.max())

# Interpolate RF for each row
rf_interp = np.interp(conc_clipped, x_ext, y_ext)

# Add RF and corrected concentration
df_raw["RF_H2"] = rf_interp
df_raw["H2_corrected_conc"] = df_raw[H2_AREA_COL] * df_raw["RF_H2"]


# =====================================================================


# Optimized Cleaning Operations
df = df_raw.replace({"ÿ": 0}, regex=True)
df.dropna(subset=["Date/Time"], inplace=True)

# Keep these despite the regex drop
keep_cols = {H2_CONC_COL, H2_AREA_COL, "RF_H2", "H2_corrected_conc"}
cols_to_drop = [
    c
    for c in df.columns
    if re.search(r"(Conc|Name|RT|Area|GC)", c) and c not in keep_cols
]
if cols_to_drop:
    df.drop(columns=cols_to_drop, inplace=True)

df.columns = df.columns.str.replace("ESTD_", "")
df.columns = df.columns.str.replace("Sampled_", "")
# Datetime & TOS Processing
df["Date/Time"] = pd.to_datetime(df["Date/Time"], format="%d.%m.%Y %H:%M:%S")
df.insert(1, "Time", df["Date/Time"].dt.time)
df.insert(1, "Date", df["Date/Time"].dt.date)

start_date = df["Date/Time"].iloc[0]
df["TOS"] = df["Date/Time"] - start_date
df.insert(2, "TOS_h", (df["TOS"] / pd.Timedelta(hours=1)).astype(int))

if "C6 Above" in df.columns:
    df["C6 Above"] = pd.to_numeric(df["C6 Above"], errors="coerce")

if "reactor" in df.columns:
    df.insert(3, "Reactor", df.pop("reactor").astype(int))

df.insert(0, "ID", range(len(df)))

# --- RF Correction Toggle ---
rf_correction = st.toggle("RF Correction ON", value=False)

with st.expander("📰 View Cleaned Raw Dataset", expanded=False):
    st.dataframe(df.head(500), use_container_width=True)

# Ensure the required columns exist
if {"Area_H2", "RF_H2"}.issubset(df.columns):
    if rf_correction:
        df["H2"] = df["H2_corrected_conc"].astype(float)
    else:
        df["H2"] = df["H2"]  # keep original values
else:
    st.warning("Area_H2 or RF column missing — cannot apply RF correction.")

# =====================================================================
# 3. Flow Data Processing (Moving Average & Summary)
# =====================================================================

st.markdown(
    "<div class='section-header'>Flow Data Moving Average Processing</div>",
    unsafe_allow_html=True,
)

with st.expander("⚙️ Optional: 14400-point (2 Hrs) Moving Average", expanded=False):
    flow_uploaded = st.file_uploader(
        "Upload Flow Data CSV", type=["csv"], key="flow_uploader"
    )

    if flow_uploaded:
        try:
            # --- Read CSV ---
            df1_raw = pd.read_csv(
                flow_uploaded,
                encoding="utf-16le",
                sep=";",
                engine="python",
                quoting=csv.QUOTE_NONE,
                header=0,
                on_bad_lines="skip",
            )

            # --- Clean column names: remove surrounding quotes + trailing \PV or /PV ---
            def clean_col(col_name: str) -> str:
                s = str(col_name).strip()
                if (s.startswith('"') and s.endswith('"')) or (
                    s.startswith("'") and s.endswith("'")
                ):
                    s = s[1:-1]
                s = re.sub(r"\\PV$", "", s)  # remove ending \PV
                s = re.sub(r"/PV$", "", s)  # just in case /PV appears
                return s.strip()

            df1_raw.columns = [clean_col(c) for c in df1_raw.columns]

            # --- Exclude id-like columns ---
            exclude_cols = [
                c
                for c in df1_raw.columns
                if str(c).lower() in ["id", "index"] or str(c).lower().endswith("_id")
            ]

            # --- Keep numeric columns only ---
            numeric_df = (
                df1_raw.drop(columns=exclude_cols, errors="ignore")
                .apply(pd.to_numeric, errors="coerce")
                .dropna(axis=1, how="all")
            )

            if numeric_df.empty:
                st.error("No numeric columns found.")
            else:
                # --- Build 2-hour moving average via chunked mean (14400 rows per chunk) ---
                chunk_size = 14400
                num_chunks = len(numeric_df) // chunk_size

                if num_chunks == 0:
                    st.warning("Not enough rows to form a chunk. Upload a larger file.")
                else:
                    indexed = numeric_df.iloc[: num_chunks * chunk_size]
                    group_keys = indexed.index // chunk_size

                    # --- Preserve Time column (last value of each chunk) ---
                    if "Time" not in df1_raw.columns:
                        st.info("No 'Time' column found. Filters will be disabled.")
                        time_grouped = pd.Series([None] * (num_chunks))
                    else:
                        time_col = df1_raw["Time"].iloc[: num_chunks * chunk_size]
                        time_grouped = time_col.groupby(group_keys).last()

                    # --- Compute mean for numeric data
                    averaged_df = indexed.groupby(group_keys).mean()

                    # --- Attach Time column back (as-is, text)
                    averaged_df["Time"] = time_grouped.values

                    # --- Move Time to front
                    averaged_df = averaged_df[
                        ["Time"] + [c for c in averaged_df.columns if c != "Time"]
                    ]

                    # --- Round to 2 decimals for both display & CSV ---
                    averaged_df_rounded = averaged_df.round(2)

                    # =========================================================
                    # =========== Time text-based dropdown filters ============
                    # =========================================================
                    # Build dropdowns BEFORE the final checkbox
                    filtering_supported = "Time" in averaged_df_rounded.columns
                    if not filtering_supported:
                        st.info(
                            "Showing full table (no 'Time' available for filtering)."
                        )
                        df_to_display = averaged_df_rounded.copy()
                    else:
                        # Convert to string and preserve order of first appearance
                        time_str_series = averaged_df_rounded["Time"].astype(str)
                        unique_times_in_order = (
                            time_str_series.drop_duplicates().tolist()
                        )

                        options = ["All"] + unique_times_in_order
                        c1, c2 = st.columns(2)
                        sel_from = c1.selectbox(
                            "From Time", options=options, index=0, key="from_time_sel"
                        )
                        sel_to = c2.selectbox(
                            "To Time", options=options, index=0, key="to_time_sel"
                        )

                        # Precompute filtered frame now (but only display after checkbox)
                        start_idx = (
                            0
                            if sel_from == "All"
                            else unique_times_in_order.index(sel_from)
                        )
                        end_idx = (
                            len(unique_times_in_order) - 1
                            if sel_to == "All"
                            else unique_times_in_order.index(sel_to)
                        )

                        if start_idx > end_idx:
                            st.warning(
                                "From Time is after To Time. Swapping the range."
                            )
                            start_idx, end_idx = end_idx, start_idx

                        allowed_times = set(
                            unique_times_in_order[start_idx : end_idx + 1]
                        )
                        mask = time_str_series.isin(allowed_times)
                        df_to_display = averaged_df_rounded.loc[mask].copy()

                        # (Optional) keep Time first
                        front_cols = ["Time"] + [
                            c for c in df_to_display.columns if c != "Time"
                        ]
                        df_to_display = df_to_display[front_cols]

                    # =========================================================
                    # ============== LAST CONTROL: Enable processing ===========
                    # =========================================================
                    run_processing = st.checkbox("Enable processing", value=False)

                    if run_processing:
                        # --- Format only numeric columns ---
                        numeric_cols = df_to_display.select_dtypes(
                            include=[np.number]
                        ).columns

                        styled = (
                            df_to_display.style.format("{:.2f}", subset=numeric_cols)
                            .set_table_styles(
                                [
                                    {
                                        "selector": "th",
                                        "props": [
                                            ("color", "white"),
                                            ("text-align", "center"),
                                            ("padding", "4px 8px"),
                                            ("background-color", "transparent"),
                                            ("font-weight", "600"),
                                            ("vertical-align", "middle"),
                                        ],
                                    },
                                    {
                                        "selector": "td",
                                        "props": [
                                            ("color", "white"),
                                            ("text-align", "center"),
                                            ("padding", "4px 8px"),
                                            ("vertical-align", "middle"),
                                        ],
                                    },
                                ]
                            )
                            .set_properties(**{"text-align": "center"})
                        )

                        # --- SHOW TABLE ---
                        st.write(styled)  # Use st.write for pandas Styler

        except Exception as e:
            st.error(f"Error processing flow data: {e}")
    else:
        st.info("Upload a CSV to configure filters and enable processing.")

# =====================================================================
# 4. Data Range & Reactor Selection
# =====================================================================
st.markdown("<div class='section-header'>Data Filtering</div>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

# 1) Exact-match range selection over existing TOS_h values
# parent layout
col1, col2 = st.columns([1, 1])

# --- Inside parent col1 ---

with col1:
    # Gather exact options from df
    pt_vals = sorted(df["TOS_h"].unique().tolist())

    # Define the slider and keep the SAME variable name everywhere: pt_Selection
    if pt_vals:
        pt_Selection = st.select_slider(
            "Select Data Range (TOS_h):",
            options=pt_vals,
            value=(pt_vals[0], pt_vals[-1]),
        )
        start_val, end_val = pt_Selection
        df_slider = df[(df["TOS_h"] >= start_val) & (df["TOS_h"] <= end_val)]

        # Direct Date/Time lookup (no parsing, just first matching row)
        def dt_for(tos):
            s = df.loc[df["TOS_h"] == tos, "Date/Time"]
            return str(s.iloc[0]) if not s.empty else "—"

        start_dt = dt_for(start_val)
        end_dt = dt_for(end_val)

        # Two inner columns INSIDE parent col1 to show Date/Time side-by-side
        col1a, spacer, col1b = st.columns([1, 1.72, 1])

        with col1a:
            st.markdown(
                f"""
                <div><b>Start Date:&nbsp;&nbsp;</b> {start_dt}</div>
                </div>

                """,
                unsafe_allow_html=True,
            )

        with col1b:
            st.markdown(
                f"""
                <div><b>End Date:&nbsp;&nbsp;</b> {end_dt}</div>
                </div>

                """,
                unsafe_allow_html=True,
            )

    else:
        # Graceful fallback if df has no TOS_h values
        st.info("No TOS_h values available.")


# --- Reactor multiselect (inside col2), sourced from the same TOS_h window ---
with col2:
    if "Reactor" in df.columns:
        r_options = (
            df.loc[df["TOS_h"].between(start_val, end_val), "Reactor"]
            .dropna()
            .unique()
            .tolist()
        )
        r_options = sorted(r_options)
        reactor_selection = st.multiselect(
            "Select Reactors:", r_options, default=r_options
        )
    else:
        reactor_selection = []

# --- Apply filters once ---
mask = df["TOS_h"].between(start_val, end_val)
if reactor_selection:
    mask &= df["Reactor"].isin(reactor_selection)

r_df = df.loc[mask].copy()


# Cast plotting columns to float
exclude_cols = [
    "ID",
    "CH4",
    "Reactor",
    "Date",
    "Time",
    "TOS_h",
    "10i1TIC02",
    "10i2TIC02",
    "10i1PIC01",
    "10i2PIC01",
    "TOS",
    "Date/Time",
]
num_cols = [c for c in r_df.columns if c not in exclude_cols]
r_df[num_cols] = r_df[num_cols].apply(pd.to_numeric, errors="coerce")


# =====================================================================
# 5. Multi-Component Plot
# =====================================================================
st.markdown(
    "<div class='section-header'>Custom Plot Builder</div>", unsafe_allow_html=True
)

tab_vars, tab_limits = st.tabs(["Variables & Plotting", "Axis Limits"])

with tab_vars:
    c1, c2, c3, c4 = st.columns(4)
    sel_x = c1.selectbox(
        "Select X variable",
        df.columns,
        index=df.columns.get_loc("TOS_h") if "TOS_h" in df.columns else 0,
    )
    sel_y1 = c2.selectbox("Select Y1 variable", df.columns)
    sel_y2 = c3.selectbox("Select Y2 variable", df.columns)
    sel_y3 = c4.selectbox("Select Y3 variable", df.columns)

    c1, c2, c3, c4 = st.columns(4)
    plot_y1 = c2.checkbox("Plot Y1", value=True)
    plot_y2 = c3.checkbox("Plot Y2", value=False)
    plot_y3 = c4.checkbox("Plot Y3", value=False)
    plot_y3_sec = c4.checkbox("Plot Y3 on Secondary Axis")

with tab_limits:
    c1, c2 = st.columns(2)
    y_min = c1.number_input("Primary Y-axis min", value=-1)
    y_max = c2.number_input("Primary Y-axis max", value=100)
    y_sec_min = c1.number_input("Secondary Y-axis min", value=-1)
    y_sec_max = c2.number_input("Secondary Y-axis max", value=100)

# Build Multicomponent Plot
fig1 = make_subplots(specs=[[{"secondary_y": True}]])
x_data = r_df[sel_x]

colors = ["#BFFF00", "#00E5FF", "#FF3366"]  # Theme-compliant chart colors

if plot_y1:
    fig1.add_trace(
        go.Scatter(
            x=x_data,
            y=r_df[sel_y1],
            mode="lines+markers",
            name=sel_y1,
            line=dict(color=colors[0]),
        ),
        secondary_y=False,
    )
if plot_y2:
    fig1.add_trace(
        go.Scatter(
            x=x_data,
            y=r_df[sel_y2],
            mode="lines+markers",
            name=sel_y2,
            line=dict(color=colors[1]),
        ),
        secondary_y=False,
    )
if plot_y3:
    fig1.add_trace(
        go.Scatter(
            x=x_data,
            y=r_df[sel_y3],
            mode="lines+markers",
            name=sel_y3,
            line=dict(color=colors[2]),
        ),
        secondary_y=plot_y3_sec,
    )

# Dynamic Y-Axis Titling
titles = [t for t, p in zip([sel_y1, sel_y2, sel_y3], [plot_y1, plot_y2, plot_y3]) if p]
primary_title = " and ".join(titles[:2]) + (
    "" if plot_y3_sec else (", " + titles[2] if plot_y3 else "")
)

fig1.update_layout(
    template="plotly_dark",
    title="TOS Products Concentration",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    paper_bgcolor="#0A0A0A",
    plot_bgcolor="#121212",
    yaxis=dict(
        title_text=f"{primary_title} %Conc" if primary_title else "",
        range=[y_min, y_max],
        gridcolor="#333",
    ),
    xaxis=dict(title_text=sel_x, gridcolor="#333"),
)

if plot_y3_sec:
    fig1.update_yaxes(
        title_text=f"{sel_y3} %Conc", secondary_y=True, range=[y_sec_min, y_sec_max]
    )

st.plotly_chart(fig1, use_container_width=True)


# =====================================================================
# 6. Export / Download Center
# =====================================================================
st.markdown(
    "<div class='section-header'>Cleaned Data Export</div>", unsafe_allow_html=True
)
with st.expander("↕ Expand to view and xport", expanded=False):
    st.dataframe(r_df.head(500), use_container_width=True)

all_cols = list(r_df.columns)
select_all = st.checkbox("⇦ Select All", value=False)
chosen_cols = st.multiselect(
    "☰", options=all_cols, default=all_cols if select_all else []
)

if chosen_cols:
    df_to_download = r_df[chosen_cols]
    csv_bytes = df_to_download.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Selected Data (CSV)",
        data=csv_bytes,
        file_name="FilteredData.csv",
        mime="text/csv",
    )


# =====================================================================
# 7. Reactor Statistics & Calculation Tables
# =====================================================================
st.markdown(
    "<div class='section-header'>Reactor Statistics</div>", unsafe_allow_html=True
)


# STD Calculations for specific reactors
# def safe_std(df_ref, reactor_val, col_name):
#     series = df_ref.loc[
#         df_ref["Reactor"].astype(str).str.strip() == str(reactor_val), col_name
#     ]
#     return pd.to_numeric(
#         series.astype(str).str.strip().str.replace(",", "", regex=False),
#         errors="coerce",
#     ).std()


def safe_rsd(df_ref, reactor_val, col_name, ddof=1):
    """
    Compute RSD (%) for rows where Reactor == reactor_val on column col_name.
    - Cleans numbers (strip, remove commas), coerces to numeric.
    - Uses sample std by default (ddof=1), same as pandas default.
    - Returns NaN if not enough data, mean==0, or all NaN.
    """
    # Filter by reactor (string-safe comparison)
    series = df_ref.loc[
        df_ref["Reactor"].astype(str).str.strip() == str(reactor_val), col_name
    ]

    # Clean & numeric
    x = pd.to_numeric(
        series.astype(str).str.strip().str.replace(",", "", regex=False),
        errors="coerce",
    )

    # Drop NaNs for stats
    x = x.dropna()

    # Need at least 2 points for std with ddof=1; mean cannot be 0 for RSD
    if x.size < (ddof + 1):
        return np.nan

    mean = x.mean()
    if mean == 0:
        return np.nan

    std = x.std(ddof=ddof)
    rsd = (std / mean) * 100.0
    return rsd


c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)
if "H2" in r_df.columns and "Reactor" in r_df.columns:
    val = safe_rsd(r_df, 1, "H2")
    c1.metric("RSD(%) of H2 (R1)", "Inactive" if pd.isna(val) else round(val, 3))
    val = safe_rsd(r_df, 2, "H2")
    c2.metric("RSD(%) of H2 (R2)", "Inactive" if pd.isna(val) else round(val, 3))
    val = safe_rsd(r_df, 3, "H2")
    c3.metric("RSD(%) of H2 (R3)", "Inactive" if pd.isna(val) else round(val, 3))
    val = safe_rsd(r_df, 4, "H2")
    c4.metric("RSD(%) of H2 (R4)", "Inactive" if pd.isna(val) else round(val, 3))
    val = safe_rsd(r_df, 5, "H2")
    c5.metric("RSD(%) of H2 (R5)", "Inactive" if pd.isna(val) else round(val, 3))
    val = safe_rsd(r_df, 6, "H2")
    c6.metric("RSD(%) of H2 (R6)", "Inactive" if pd.isna(val) else round(val, 3))
    val = safe_rsd(r_df, 7, "H2")
    c7.metric("RSD(%) of H2 (R7)", "Inactive" if pd.isna(val) else round(val, 3))
    val = safe_rsd(r_df, 8, "H2")
    c8.metric("RSD(%) of H2 (R8)", "Inactive" if pd.isna(val) else round(val, 3))


# =====================================================================
# 8. Stacked Distributions & Comparison
# =====================================================================
st.markdown(
    "<div class='section-header'>Distributions & Comparison</div>",
    unsafe_allow_html=True,
)

# Stacked prep
dfstacked = r_df.loc[
    :,
    ~r_df.columns.isin(
        [
            "ID",
            "Date",
            "Time",
            "TOS_h",
            "10i1TIC02",
            "10i2TIC02",
            "10i1PIC01",
            "10i2PIC01",
            "TOS",
            "Date/Time",
        ]
    ),
]
dfstacked_col = dfstacked.drop(columns=["CH4", "Reactor"], errors="ignore")
dfmean = dfstacked.groupby(["Reactor"]).mean(numeric_only=True).reset_index()
df_melted = dfmean.melt(id_vars=["Reactor"], value_vars=dfmean.columns[1:])

col1, col2 = st.columns(2)

with col1:
    st.write("### Stacked Bar Chart")
    selectedcol_stac = st.multiselect(
        "Select columns to stack:",
        dfstacked_col.columns,
        default=dfstacked_col.columns[:3].tolist() if not dfstacked_col.empty else [],
    )

    if selectedcol_stac:
        filtered_df_stac = df_melted[df_melted["variable"].isin(selectedcol_stac)]

    # Guard: ensure we have something to plot
    if filtered_df_stac is None or filtered_df_stac.empty:
        st.warning(
            "No data available for the selected variables to plot the stacked bar chart."
        )
    else:
        # Extract variables present in the filtered dataset
        vars_in_plot = filtered_df_stac["variable"].astype(str).unique().tolist()

        if len(vars_in_plot) == 0:
            st.warning(
                "No variables found to plot. Please select at least one variable."
            )
        else:
            # Build palette
            if len(vars_in_plot) == 1:
                # Single variable → use the brand color
                palette = ["#99CC00"]
                color_map = {vars_in_plot[0]: palette[0]}
            else:
                # Multiple variables → generate shades around #99CC00
                base_rgb = (153, 204, 0)  # #99CC00

                # Create a lighter and darker bound
                light_rgb = [
                    min(255, int(c + (255 - c) * 0.65)) for c in base_rgb
                ]  # lighter
                dark_rgb = [max(0, int(c * 0.55)) for c in base_rgb]  # darker

                # Generate N shades between light and dark
                palette = n_colors(
                    f"rgb({light_rgb[0]},{light_rgb[1]},{light_rgb[2]})",
                    f"rgb({dark_rgb[0]},{dark_rgb[1]},{dark_rgb[2]})",
                    len(vars_in_plot),
                    colortype="rgb",
                )

                color_map = {var: palette[i] for i, var in enumerate(vars_in_plot)}

            # Optional: lock legend order to current variables
            category_orders = {"variable": vars_in_plot}

            # Build the figure
            fig3 = px.bar(
                filtered_df_stac,
                x="Reactor",
                y="value",
                color="variable",
                template="plotly_dark",
                color_discrete_map=color_map,
                category_orders=category_orders,
            )

            fig3.update_layout(
                title={
                    "text": "TOS Products concentration by reactor",
                    "font": {"color": "white"},
                },
                paper_bgcolor="#0A0A0A",
                plot_bgcolor="#121212",
                yaxis_range=[0, 100],
            )

            fig3.update_yaxes(gridcolor="#32322f")

            # Finally render
            st.plotly_chart(fig3, use_container_width=True)


with col2:
    st.write("### Reactor-to-Reactor Comparison")
    # =====================================================================
    # 8.1. use this for multi color lines
    # =====================================================================
    # # Select column for comparison
    # selectedcol_RCom = st.selectbox("Select column to compare:", dfstacked_col.columns)

    # # Always show outlet concentration (checkbox removed)
    # temp_r_df = r_df.reset_index(drop=True)

    # fig2 = px.line(
    #     temp_r_df,
    #     x="TOS_h",
    #     y=selectedcol_RCom,
    #     color="Reactor",
    #     markers=True,
    #     template="plotly_dark",
    # )

    # fig2.update_layout(
    #     title="TOS Products concentration by reactor",
    #     paper_bgcolor="#0A0A0A",
    #     plot_bgcolor="#121212",
    #     yaxis_range=[y_min, y_max],
    # )

    # # Set y-grid color
    # fig2.update_yaxes(gridcolor="#32322f")

    # st.plotly_chart(fig2, use_container_width=True)
    # -------------------------------------------------------------------
    # -------------------------------------------------------------------

    # Select column for comparison
    selectedcol_RCom = st.selectbox("Select column to compare:", dfstacked_col.columns)

    # Always show outlet concentration (checkbox removed)
    temp_r_df = r_df.reset_index(drop=True)

    # Determine reactors present in current data slice (keep original dtype to avoid key mismatch)
    reactors_in_plot = temp_r_df["Reactor"].dropna().unique().tolist()

    # Build color palette/map
    if len(reactors_in_plot) == 0:
        st.warning("No reactors found to plot.")
    else:
        if len(reactors_in_plot) == 1:
            # Single reactor → just the brand color
            palette = ["#99CC00"]
        else:
            # Multiple reactors → shades around #99CC00
            base_rgb = (153, 204, 0)  # #99CC00
            light_rgb = [
                min(255, int(c + (255 - c) * 0.65)) for c in base_rgb
            ]  # lighter bound
            dark_rgb = [max(0, int(c * 0.55)) for c in base_rgb]  # darker bound

            palette = n_colors(
                f"rgb({light_rgb[0]},{light_rgb[1]},{light_rgb[2]})",
                f"rgb({dark_rgb[0]},{dark_rgb[1]},{dark_rgb[2]})",
                len(reactors_in_plot),
                colortype="rgb",
            )

        # Stable mapping {reactor_value: color}
        color_map_line = {
            reactors_in_plot[i]: palette[i] for i in range(len(reactors_in_plot))
        }

        # Optional: lock legend/order
        category_orders_line = {"Reactor": reactors_in_plot}

        # Build the figure
        fig2 = px.line(
            temp_r_df,
            x="TOS_h",
            y=selectedcol_RCom,
            color="Reactor",
            markers=True,
            template="plotly_dark",
            color_discrete_map=color_map_line,
            category_orders=category_orders_line,
        )

        # Styling
        fig2.update_traces(line=dict(width=2), marker=dict(size=6))
        fig2.update_layout(
            title={
                "text": "TOS Products concentration by reactor",
                "font": {"color": "white"},
            },
            paper_bgcolor="#0A0A0A",
            plot_bgcolor="#121212",
            yaxis_range=[y_min, y_max],
        )
        fig2.update_yaxes(gridcolor="#32322f")

        st.plotly_chart(fig2, use_container_width=True)

# =====================================================================
# 9. Nap/H2 Mass Ratio Plot
# =====================================================================

st.markdown(
    "<div class='section-header'>Nap/H2 Mass Ratio (Supplied vs Measured)</div>",
    unsafe_allow_html=True,
)

try:
    # -----------------------------
    # Column names (NO "\PV")
    # -----------------------------
    fic_cols = [f"01i14FIC{i:02d}" for i in range(1, 9)]
    fi01_col = "01i14FI01"
    fic2_cols = [f"02i2FIC{i:02d}" for i in range(1, 9)]

    # -----------------------------
    # Basic validation on df
    # -----------------------------
    required_df_cols = ["Reactor", fi01_col] + fic_cols
    missing = [c for c in required_df_cols if c not in df.columns]
    if missing:
        st.warning(
            f"Skipping Ratio plot. Dataset is missing ILS columns: {missing[0]}..."
        )
    else:
        # =========================================
        # UI: Choose Calculation Mode
        # =========================================
        calc_mode = st.radio(
            "Choose The Mode of Calculation",
            options=["FIC Point Data", "FIC Time-Averaged Data"],
            index=0,
            horizontal=True,
        )

        # =======================================================
        # If user selects Time-Averaged Data but df_to_display NOT FOUND
        # → Show message + force fallback to FIC Point Data
        # =======================================================
        if calc_mode == "FIC Time-Averaged Data":
            if "df_to_display" not in globals() or not isinstance(
                df_to_display, pd.DataFrame
            ):
                st.error("Please Upload The Flow Data and Enable Processing")
                calc_mode = "FIC Point Data"  # Auto-switch

        # =======================================================
        # MODE 1: OLD CALCULATION (FIC Point Data)
        # =======================================================
        if calc_mode == "FIC Point Data":
            idx = pd.to_numeric(df["Reactor"], errors="coerce").to_numpy() - 1
            valid = (idx >= 0) & (idx < 8)
            col_idx = np.where(valid, idx, 0).astype(int)
            rows = np.arange(len(df))

            # Treat negatives as zero
            fic_df_num = (
                df[fic_cols].apply(pd.to_numeric, errors="coerce").clip(lower=0)
            )
            fic_mat = fic_df_num.to_numpy()

            chosen_fic = np.where(valid, fic_mat[rows, col_idx], np.nan)
            # Ignore zero FIC values
            chosen_fic = np.where(chosen_fic == 0, np.nan, chosen_fic)

            # Denominator: sum of FICs ignoring zeros
            den = fic_df_num.replace(0, np.nan).sum(axis=1).replace(0, np.nan)

            fi01_series = pd.to_numeric(df[fi01_col], errors="coerce").clip(lower=0)
            df["H2_massFlow"] = (fi01_series * chosen_fic) / den

        # =======================================================
        # MODE 2: NEW CALCULATION (FIC Time-Averaged Data)
        # Per-reactor constant computed from df_to_display averages
        # =======================================================
        else:
            # Ensure required columns exist in df_to_display
            for c in [fi01_col] + fic_cols:
                if c not in df_to_display.columns:
                    df_to_display[c] = np.nan  # will be ignored appropriately

            # Helper: FIC avg = mean over positive values only (negatives→0, zeros ignored)
            def fic_positive_mean(s: pd.Series) -> float:
                s_num = pd.to_numeric(s, errors="coerce").clip(lower=0)
                s_pos = s_num.replace(0, np.nan)
                return float(s_pos.mean()) if s_pos.notna().any() else 0.0

            # Helper: FI01 avg = mean with negatives→0 (zeros allowed)
            def fi01_nonneg_mean(s: pd.Series) -> float:
                s_num = pd.to_numeric(s, errors="coerce").clip(lower=0)
                return float(s_num.fillna(0).mean())

            fi01_avg_val = fi01_nonneg_mean(df_to_display[fi01_col])

            fic_avgs = np.array(
                [fic_positive_mean(df_to_display[c]) for c in fic_cols], dtype=float
            )

            # Denominator: sum of positive FIC averages (ignore zeros)
            den_avg = fic_avgs[fic_avgs > 0].sum()
            den_avg = np.nan if den_avg == 0 else den_avg

            # Per-reactor H2_massFlow (constant per reactor)
            h2mf_by_reactor = {}
            for r in range(1, 9):
                fic_r_avg = fic_avgs[r - 1]
                if not np.isfinite(den_avg):
                    h2mf_by_reactor[r] = np.nan
                else:
                    h2mf_by_reactor[r] = (fi01_avg_val * fic_r_avg) / den_avg

            # Map constant back into df by reactor
            reactor_num = pd.to_numeric(df["Reactor"], errors="coerce")
            df["H2_massFlow"] = reactor_num.map(pd.Series(h2mf_by_reactor))

        # =======================================================
        # Supplied H2 (02i2FICxx): MUST come from df_to_display
        # Treat negatives as zero and ignore zero FIC value
        # =======================================================
        # Ensure fic2 columns exist in df_to_display (or create NaNs)
        for c in fic2_cols:
            if c not in df_to_display.columns:
                df_to_display[c] = np.nan

        def pick_chosen_h2_from(source_df: pd.DataFrame) -> np.ndarray:
            fic2_df_num = (
                source_df[fic2_cols].apply(pd.to_numeric, errors="coerce").clip(lower=0)
            )
            fic2_mat = fic2_df_num.replace(0, np.nan).to_numpy()  # zeros ignored

            idx_local = pd.to_numeric(df["Reactor"], errors="coerce").to_numpy() - 1
            valid_local = (idx_local >= 0) & (idx_local < 8)
            col_idx_local = np.where(valid_local, idx_local, 0).astype(int)
            rows_local = np.arange(len(df))
            # Safe column index (if some fic2 cols were missing)
            col_idx_local = np.clip(col_idx_local, 0, fic2_mat.shape[1] - 1)
            return np.where(valid_local, fic2_mat[rows_local, col_idx_local], np.nan)

        chosen_h2 = None

        # Try index-aligned
        if (len(df_to_display) == len(df)) and df_to_display.index.equals(df.index):
            chosen_h2 = pick_chosen_h2_from(df_to_display)

        # Else try to merge on TOS_h
        elif ("TOS_h" in df.columns) and ("TOS_h" in df_to_display.columns):
            merged = df.merge(
                df_to_display[["TOS_h"] + fic2_cols],
                on="TOS_h",
                how="left",
                suffixes=("", "_src"),
            )
            fic2_df_num = (
                merged[fic2_cols].apply(pd.to_numeric, errors="coerce").clip(lower=0)
            )
            fic2_mat = fic2_df_num.replace(0, np.nan).to_numpy()

            idx_m = pd.to_numeric(merged["Reactor"], errors="coerce").to_numpy() - 1
            valid_m = (idx_m >= 0) & (idx_m < 8)
            col_idx_m = np.clip(
                np.where(valid_m, idx_m, 0).astype(int), 0, fic2_mat.shape[1] - 1
            )
            rows_m = np.arange(len(merged))
            tmp = np.where(valid_m, fic2_mat[rows_m, col_idx_m], np.nan)

            # Put back in original df's order
            df["__tmp_h2__"] = np.nan
            df.loc[merged.index, "__tmp_h2__"] = tmp
            chosen_h2 = df["__tmp_h2__"].to_numpy()
            df.drop(columns=["__tmp_h2__"], inplace=True)

        # Else try to merge on Time
        elif ("Time" in df.columns) and ("Time" in df_to_display.columns):
            merged = df.merge(
                df_to_display[["Time"] + fic2_cols],
                on="Time",
                how="left",
                suffixes=("", "_src"),
            )
            fic2_df_num = (
                merged[fic2_cols].apply(pd.to_numeric, errors="coerce").clip(lower=0)
            )
            fic2_mat = fic2_df_num.replace(0, np.nan).to_numpy()

            idx_m = pd.to_numeric(merged["Reactor"], errors="coerce").to_numpy() - 1
            valid_m = (idx_m >= 0) & (idx_m < 8)
            col_idx_m = np.clip(
                np.where(valid_m, idx_m, 0).astype(int), 0, fic2_mat.shape[1] - 1
            )
            rows_m = np.arange(len(merged))
            tmp = np.where(valid_m, fic2_mat[rows_m, col_idx_m], np.nan)

            df["__tmp_h2__"] = np.nan
            df.loc[merged.index, "__tmp_h2__"] = tmp
            chosen_h2 = df["__tmp_h2__"].to_numpy()
            df.drop(columns=["__tmp_h2__"], inplace=True)

        # Absolute fallback (should rarely trigger)
        if chosen_h2 is None:
            chosen_h2 = np.full(len(df), np.nan)

        # Compute Nap/H2_mass ratio (safe division)
        h2mf = pd.to_numeric(df["H2_massFlow"], errors="coerce").to_numpy()
        h2mf_safe = np.where((h2mf <= 0) | (~np.isfinite(h2mf)), np.nan, h2mf)
        df["Nap/H2_mass ratio"] = chosen_h2 / h2mf_safe

        # GC calculation
        if "H2" in df.columns and "N2" in df.columns:
            h2_arr = pd.to_numeric(df["H2"], errors="coerce")
            n2_arr = pd.to_numeric(df["N2"], errors="coerce")
            df["Nap/H2_GC"] = ((100 - (h2_arr + n2_arr)) * 100) / (h2_arr * 2)
        else:
            df["Nap/H2_GC"] = np.nan

        # Prepare for plotting
        df1 = df[
            ["TOS_h", "Reactor", "H2_massFlow", "Nap/H2_mass ratio", "Nap/H2_GC"]
        ].copy()
        df1 = df1.dropna(subset=["TOS_h", "Reactor"]).sort_values(["Reactor", "TOS_h"])
        df1["Reactor_num"] = pd.to_numeric(df1["Reactor"], errors="coerce")

        # Plot UI
        plot_ph = st.empty()
        with st.container():
            reactors_num = sorted(
                df1["Reactor_num"].dropna().unique().astype(int).tolist()
            )
            sel_all = st.checkbox("Select all reactors for ratio plot", value=True)
            sel_r_ratio = st.multiselect(
                "Filter Reactors",
                options=reactors_num,
                default=reactors_num if sel_all else reactors_num[:1],
            )
            df1_filtered = df1[df1["Reactor_num"].isin(sel_r_ratio)].copy()

        if df1_filtered.empty:
            plot_ph.info("No data matches selected reactors.")
        else:
            std_by_r = (
                df1_filtered.dropna(subset=["Nap/H2_GC"])
                .groupby("Reactor_num")["Nap/H2_GC"]
                .std(ddof=1)
            )

            fig_ratio = go.Figure()
            from plotly.colors import n_colors

            reactors_in_plot = sel_r_ratio
            if len(reactors_in_plot) == 1:
                palette = ["#99CC00"]
            else:
                base_rgb = (153, 204, 0)  # #99CC00
                light_rgb = [min(255, int(c + (255 - c) * 0.65)) for c in base_rgb]
                dark_rgb = [max(0, int(c * 0.55)) for c in base_rgb]
                palette = n_colors(
                    f"rgb({light_rgb[0]},{light_rgb[1]},{light_rgb[2]})",
                    f"rgb({dark_rgb[0]},{dark_rgb[1]},{dark_rgb[2]})",
                    len(reactors_in_plot),
                    colortype="rgb",
                )
            color_map_ratio = {
                reactors_in_plot[i]: palette[i] for i in range(len(reactors_in_plot))
            }

            for r in sel_r_ratio:
                d = df1_filtered[df1_filtered["Reactor_num"] == r]
                color = color_map_ratio[r]
                sigma = std_by_r.get(r, np.nan)
                lbl = (
                    f"(Supplied)Reactor {r} (σ={sigma:.3g})"
                    if np.isfinite(sigma)
                    else f"Reactor {r} (σ=NA)"
                )

                fig_ratio.add_trace(
                    go.Scatter(
                        x=d["TOS_h"],
                        y=d["Nap/H2_mass ratio"],
                        mode="lines",
                        name=lbl,
                        line=dict(color=color, width=2, dash="dash"),
                        marker=dict(size=6),
                    )
                )
                fig_ratio.add_trace(
                    go.Scatter(
                        x=d["TOS_h"],
                        y=d["Nap/H2_GC"],
                        mode="lines+markers",
                        name=f"Measured R{r}",
                        line=dict(color=color, width=2),
                        showlegend=False,
                    )
                )

            fig_ratio.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0A0A0A",
                plot_bgcolor="#121212",
                xaxis_title="TOS (hours)",
                yaxis_title="Ratio Value",
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    font=dict(color="white"),
                ),
            )
            fig_ratio.update_yaxes(gridcolor="#32322f")
            plot_ph.plotly_chart(fig_ratio, use_container_width=True)

except Exception as e:
    st.error(f"Error calculating Nap/H2 Ratio: {repr(e)}")
