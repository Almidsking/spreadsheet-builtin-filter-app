import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="Universal Spreadsheet Filter",
    layout="wide"
)

st.title("📊 Universal Spreadsheet Filter")
st.caption("Click on any column header to filter or sort (Excel-style). Use multiple filters with AND/OR below.")

# --------------------------------------------------
# Load data (hardcoded for simplicity)
# --------------------------------------------------
DATA_FILE = "data.xlsx"

try:
    df = pd.read_excel(DATA_FILE)
except Exception as e:
    st.error(f"Failed to load data file: {e}")
    st.stop()

# --------------------------------------------------
# Clean datetime columns for display
# --------------------------------------------------
for col in df.select_dtypes(include=["datetime64[ns]"]).columns:
    df[col] = df[col].dt.date

# --------------------------------------------------
# Optional: AND/OR filter controls
# --------------------------------------------------
st.subheader("Multiple Filter Logic (Optional)")
logic = st.radio("Combine multiple criteria using:", ["AND", "OR"])

# Store filters in session state for multiple criteria
if "filters" not in st.session_state:
    st.session_state.filters = []

# Add new filter button
if st.button("➕ Add Filter"):
    st.session_state.filters.append({
        "column": df.columns[0],
        "operator": "==",
        "value": ""
    })

# Render existing filters
for i, f in enumerate(st.session_state.filters):
    c1, c2, c3, c4 = st.columns([3, 2, 3, 1])
    with c1:
        f["column"] = st.selectbox(
            "Column",
            df.columns,
            key=f"col_{i}"
        )
    with c2:
        f["operator"] = st.selectbox(
            "Operator",
            ['==', '!=', '>', '<', '>=', '<=', 'contains'],
            key=f"op_{i}"
        )
    with c3:
        series = df[f["column"]]
        if pd.api.types.is_bool_dtype(series):
            f["value"] = st.selectbox(
                "Value",
                sorted(series.dropna().unique()),
                key=f"val_{i}"
            )
        else:
            f["value"] = st.text_input(
                "Value",
                f["value"],
                key=f"val_{i}"
            )
    with c4:
        if st.button("❌", key=f"del_{i}"):
            st.session_state.filters.pop(i)
            st.experimental_rerun()

# --------------------------------------------------
# Build Excel-like grid
# --------------------------------------------------
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(
    filter=True,
    sortable=True,
    resizable=True
)
gb.configure_grid_options(
    enableRangeSelection=True,
    domLayout="normal"
)
grid_options = gb.build()

# --------------------------------------------------
# Apply AND/OR filters if any
# --------------------------------------------------
filtered_df = df.copy()
if st.session_state.filters:
    masks = []
    for f in st.session_state.filters:
        col = f["column"]
        op = f["operator"]
        val = f["value"]
        series = df[col]
        try:
            if pd.api.types.is_numeric_dtype(series):
                val = float(val)
        except:
            pass

        if op == '==':
            mask = series == val
        elif op == '!=':
            mask = series != val
        elif op == '>':
            mask = series > val
        elif op == '<':
            mask = series < val
        elif op == '>=':
            mask = series >= val
        elif op == '<=':
            mask = series <= val
        elif op == 'contains':
            mask = series.astype(str).str.contains(str(val), case=False)
        else:
            continue
        masks.append(mask)

    # Combine masks
    if masks:
        final_mask = masks[0]
        for m in masks[1:]:
            final_mask = final_mask & m if logic == "AND" else final_mask | m
        filtered_df = df[final_mask]

# --------------------------------------------------
# Display grid
# --------------------------------------------------
grid_response = AgGrid(
    filtered_df,
    gridOptions=grid_options,
    height=550,
    fit_columns_on_grid_load=True,
    allow_unsafe_jscode=True,
    update_mode=GridUpdateMode.MODEL_CHANGED
)

st.success(f"Rows displayed: {len(filtered_df)}")

# --------------------------------------------------
# Download button
# --------------------------------------------------
st.download_button(
    "⬇️ Download Current View",
    data=filtered_df.to_excel(index=False),
    file_name="filtered_output.xlsx"
)
