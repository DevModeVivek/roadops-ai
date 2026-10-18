
import re
from pathlib import Path

import pandas as pd
import streamlit as st
from ollama import chat

from retriever import retrieve
from workorders import (
    get_total,
    get_high_priority,
    get_status,
    get_top_site
)


# ---------------------------------
# PAGE SETTINGS
# ---------------------------------

st.set_page_config(
    page_title="RoadOps AI | Operations Center",
    page_icon="🚧",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ---------------------------------
# DESIGN
# ---------------------------------

st.markdown("""
<style>
    .stApp {
        background: #0B1220;
        color: #E5EDF8;
    }

    [data-testid="stSidebar"] {
        background: #111C30;
        border-right: 1px solid #27364C;
    }

    h1, h2, h3 {
        color: #F4F7FC !important;
        letter-spacing: -0.5px;
    }

    div[data-testid="stMetric"] {
        background: #17243A;
        border: 1px solid #2B3D58;
        padding: 18px;
        border-radius: 14px;
    }

    div[data-testid="stMetricLabel"] {
        color: #AABBD2;
    }

    div[data-testid="stMetricValue"] {
        color: #F4F7FC;
    }

    .roadops-header {
        background: linear-gradient(
            115deg,
            #152B4B 0%,
            #101B2D 100%
        );
        padding: 26px;
        border: 1px solid #314C70;
        border-radius: 16px;
        margin-bottom: 20px;
    }

    .roadops-title {
        font-size: 30px;
        font-weight: 750;
        color: #FFFFFF;
        margin-bottom: 6px;
    }

    .roadops-subtitle {
        color: #B1C4DF;
        font-size: 14px;
    }

    .section-label {
        color: #8CA5C5;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1.5px;
        margin-bottom: 10px;
    }

    .roadops-note {
        background: #14253D;
        border-left: 3px solid #60A5FA;
        border-radius: 8px;
        padding: 12px 16px;
        color: #BED0E6;
        margin: 14px 0;
    }

    div[data-testid="stChatMessage"] {
        background: #142238;
        border: 1px solid #263B57;
        border-radius: 12px;
    }

    .stButton > button {
        border-radius: 9px;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #293E59;
        border-radius: 10px;
    }

    [data-testid="stTabs"] button {
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------
# DATA FUNCTIONS
# ---------------------------------

DATA_FILE = (
    Path(__file__).parent
    / "data"
    / "workorders.csv"
)


@st.cache_data
def load_data():
    df = pd.read_csv(
        DATA_FILE,
        dtype=str,
        keep_default_na=False
    )

    # Remove accidental spaces from column names
    df.columns = df.columns.str.strip()

    required_columns = [
        "Title",
        "Site",
        "AssetType",
        "IssueType",
        "Priority",
        "Status",
        "EstimatedCostCAD"
    ]

    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing CSV columns: "
            + ", ".join(missing)
        )

    # Clean text fields
    for column in [
        "Title",
        "Site",
        "AssetType",
        "IssueType",
        "Priority",
        "Status"
    ]:
        df[column] = df[column].str.strip()

    # SharePoint CSV costs can contain commas
    cost_text = (
        df["EstimatedCostCAD"]
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.strip()
    )

    df["CostNumeric"] = pd.to_numeric(
        cost_text,
        errors="coerce"
    )

    return df


def answer_from_data(question):
    q = question.lower().strip()

    # Look up individual work orders
    match = re.search(r"\bwo[- ]?\d+\b", q)

    if match:
        number = match.group().upper().replace(" ", "-")

        if "-" not in number:
            number = number.replace("WO", "WO-")

        return get_status(number)

    # Count High-priority requests
    if "high" in q and "priority" in q:
        return (
            f"There are {get_high_priority()} "
            "High-priority work orders "
            "in the exported SharePoint data."
        )

    # Identify busiest site
    if (
        ("site" in q or "yard" in q)
        and any(
            word in q
            for word in ["most", "highest", "busiest"]
        )
    ):
        return (
            "The site with the most work orders is "
            f"{get_top_site()}."
        )

    # Count all work orders
    if "work order" in q or "workorder" in q:
        if any(
            phrase in q
            for phrase in [
                "how many",
                "total",
                "number of",
                "count"
            ]
        ):
            return (
                f"There are {get_total()} work orders "
                "in the exported SharePoint data."
            )

    return None


# ---------------------------------
# OLLAMA + RAG
# ---------------------------------

SYSTEM_PROMPT = """
You are RoadOps AI Assistant for a fictional
road maintenance operations company.

RoadOps uses Power Apps for maintenance requests,
SharePoint for record storage, Power Automate for
High-priority alerts, and Power BI for dashboards.

Answer RoadOps procedure questions using only the
retrieved documentation provided with the question.

Never invent work-order records, application fields,
maintenance policies, or completed actions.

If documentation is insufficient or unrelated,
say you cannot verify the information.

Live SharePoint lookup is not connected.
Work-order data is from a local CSV snapshot.

Keep answers clear, professional, and concise.

For immediate safety hazards, advise people to
stop unsafe work and contact their supervisor.

All RoadOps information is fictional demonstration data.
"""


def get_ai_response(question):
    q = question.lower().strip()

    # Greetings
    if q in [
        "hi",
        "hello",
        "hey",
        "good morning",
        "good evening"
    ]:
        return (
            "Hello! I'm RoadOps AI. I can help you "
            "check work orders, understand maintenance "
            "procedures, and explore operational data."
        ), [], "General"

    # Data questions
    data_answer = answer_from_data(question)

    if data_answer is not None:
        return data_answer, [], "CSV Data"

    # Knowledge base retrieval
    sections = retrieve(question)

    if not sections:
        return (
            "I couldn't find enough verified information "
            "in the RoadOps knowledge base."
        ), [], "Knowledge Base"

    context = "\n\n".join(sections)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": (
                "Retrieved documentation:\n\n"
                + context
                + "\n\nQuestion:\n"
                + question
                + "\n\nUse only relevant documentation. "
                "Do not guess missing details."
            )
        }
    ]

    response = chat(
        model="qwen2.5:3b",
        messages=messages,
        options={"temperature": 0.1}
    )

    return (
        response.message.content,
        sections,
        "Ollama + RAG"
    )


# ---------------------------------
# SIDEBAR
# ---------------------------------

with st.sidebar:
    st.markdown("## 🚧 RoadOps AI")
    st.caption("OPERATIONS INTELLIGENCE")

    st.divider()

    st.markdown("### System Components")

    st.write("✅ Power Apps")
    st.write("✅ SharePoint")
    st.write("✅ Power Automate")
    st.write("✅ Power BI")
    st.write("✅ Ollama + Qwen")

    st.divider()

    st.markdown("### AI Configuration")

    st.caption("Model: Qwen 2.5 3B")
    st.caption("Knowledge: Local RAG")
    st.caption("Retrieval: Keyword matching")
    st.caption("Records: CSV export")

    st.divider()

    if st.button(
        "🔄 Reload Dashboard Data",
        use_container_width=True
    ):
        load_data.clear()
        st.rerun()

    st.caption("Independent educational demo")
    st.caption("Not an official company system")


# ---------------------------------
# LOAD WORK ORDERS
# ---------------------------------

try:
    df = load_data()

except Exception as e:
    st.error("Unable to load RoadOps work-order data.")
    st.code(str(e))
    st.stop()


total_orders = len(df)

high_orders = len(
    df[
        df["Priority"].str.lower() == "high"
    ]
)

resolved_orders = len(
    df[
        df["Status"].str.lower() == "resolved"
    ]
)

active_orders = total_orders - resolved_orders

estimated_cost = df["CostNumeric"].sum()

site_counts = df["Site"].value_counts()

top_site = (
    site_counts.index[0]
    if not site_counts.empty
    else "N/A"
)


# ---------------------------------
# MAIN HEADER
# ---------------------------------

st.markdown("""
<div class="roadops-header">
    <div class="roadops-title">
        🚧 RoadOps AI
    </div>
    <div class="roadops-subtitle">
        Maintenance Operations Intelligence Platform
        <br>
        Asset Monitoring · Work Orders · AI Assistance
    </div>
</div>
""", unsafe_allow_html=True)

st.caption(
    "DEMO ENVIRONMENT · Data source: exported SharePoint CSV "
    "· Not a live connection"
)


# ---------------------------------
# NAVIGATION TABS
# ---------------------------------

overview_tab, ai_tab, orders_tab = st.tabs([
    "📊 Overview",
    "🤖 AI Assistant",
    "📋 Work Orders"
])


# ---------------------------------
# TAB 1: OVERVIEW
# ---------------------------------

with overview_tab:

    st.markdown("### Operations Overview")

    st.write(
        "Monitor work-order volumes, priorities, "
        "equipment issues and estimated maintenance costs."
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Work Orders",
            total_orders
        )

    with col2:
        st.metric(
            "High Priority",
            high_orders
        )

    with col3:
        st.metric(
            "Active Work Orders",
            active_orders
        )

    with col4:
        st.metric(
            "Estimated Cost",
            f"${estimated_cost:,.2f}"
        )

    st.caption(
        "Active = every status other than Resolved. "
        "Estimated cost is the sum of available CSV values."
    )

    st.divider()

    left, right = st.columns(2)

    with left:
        st.markdown("#### Work Orders by Status")

        status_counts = (
            df["Status"]
            .value_counts()
            .rename_axis("Status")
            .reset_index(name="Count")
        )

        st.bar_chart(
            status_counts,
            x="Status",
            y="Count",
            color="#60A5FA"
        )

    with right:
        st.markdown("#### Work Orders by Priority")

        priority_counts = (
            df["Priority"]
            .value_counts()
            .rename_axis("Priority")
            .reset_index(name="Count")
        )

        st.bar_chart(
            priority_counts,
            x="Priority",
            y="Count",
            color="#38BDF8"
        )

    st.divider()

    left, right = st.columns(2)

    with left:
        st.markdown("#### Maintenance Requests by Site")

        site_chart = (
            df["Site"]
            .value_counts()
            .rename_axis("Site")
            .reset_index(name="Count")
        )

        st.bar_chart(
            site_chart,
            x="Site",
            y="Count",
            color="#818CF8"
        )

    with right:
        st.markdown("#### Asset Types")

        asset_chart = (
            df["AssetType"]
            .value_counts()
            .rename_axis("Asset Type")
            .reset_index(name="Count")
        )

        st.bar_chart(
            asset_chart,
            x="Asset Type",
            y="Count",
            color="#34D399"
        )

    st.divider()

    st.markdown("#### Operational Snapshot")

    a, b, c = st.columns(3)

    with a:
        st.metric(
            "Resolved Orders",
            resolved_orders
        )

    with b:
        st.metric(
            "Maintenance Sites",
            df["Site"].nunique()
        )

    with c:
        st.metric(
            "Busiest Site",
            top_site
        )

    st.markdown(
        '<div class="roadops-note">'
        'These metrics are calculated from a local CSV export. '
        'New SharePoint records will not appear until the CSV '
        'is replaced and the dashboard is reloaded.'
        '</div>',
        unsafe_allow_html=True
    )


# ---------------------------------
# TAB 2: AI ASSISTANT
# ---------------------------------

with ai_tab:

    st.markdown("### AI Maintenance Assistant")

    st.write(
        "Ask questions about maintenance procedures, "
        "work-order statuses, operational counts, "
        "and equipment issues."
    )

    st.caption(
        "Powered by local Qwen 2.5 3B, "
        "keyword retrieval and CSV data lookup."
    )

    st.markdown("#### Suggested Questions")

    q1, q2, q3 = st.columns(3)

    with q1:
        suggested_total = st.button(
            "Total work orders",
            use_container_width=True
        )

    with q2:
        suggested_high = st.button(
            "High-priority orders",
            use_container_width=True
        )

    with q3:
        suggested_procedure = st.button(
            "Create a work order",
            use_container_width=True
        )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

            if message.get("source_type"):
                st.caption(
                    "Source: " + message["source_type"]
                )

            if message.get("sources"):
                with st.expander("View Knowledge Sources"):
                    for section in message["sources"]:
                        st.write(section.splitlines()[0])

    typed_question = st.chat_input(
        "Ask RoadOps AI...",
        key="roadops_chat"
    )

    question = typed_question

    if suggested_total:
        question = "How many work orders are there?"

    elif suggested_high:
        question = "How many high priority work orders?"

    elif suggested_procedure:
        question = "How do I create a work order?"

    if question:

        st.session_state.messages.append({
            "role": "user",
            "content": question
        })

        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Processing your request..."):
                try:
                    answer, sources, source_type = (
                        get_ai_response(question)
                    )

                    st.write(answer)
                    st.caption("Source: " + source_type)

                    if sources:
                        with st.expander("View Knowledge Sources"):
                            for section in sources:
                                st.write(section.splitlines()[0])

                except Exception as e:
                    answer = (
                        "Sorry, I couldn't process that request."
                    )
                    sources = []
                    source_type = "Error"
                    st.error(str(e))

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "source_type": source_type
        })


# ---------------------------------
# TAB 3: WORK ORDERS
# ---------------------------------

with orders_tab:

    st.markdown("### Work Order Explorer")

    st.write(
        "Search and filter maintenance records "
        "from the exported SharePoint dataset."
    )

    # Search and filter controls
    search_col, priority_col, status_col = st.columns(
        [2, 1, 1]
    )

    with search_col:
        search_text = st.text_input(
            "Search work orders",
            placeholder="WO-1001, equipment, site, issue..."
        )

    with priority_col:
        priorities = [
            "All",
            *sorted(df["Priority"].unique())
        ]

        selected_priority = st.selectbox(
            "Priority",
            priorities
        )

    with status_col:
        statuses = [
            "All",
            *sorted(df["Status"].unique())
        ]

        selected_status = st.selectbox(
            "Status",
            statuses
        )

    filtered = df.copy()

    if selected_priority != "All":
        filtered = filtered[
            filtered["Priority"] == selected_priority
        ]

    if selected_status != "All":
        filtered = filtered[
            filtered["Status"] == selected_status
        ]

    if search_text.strip():
        search_columns = [
            "Title",
            "Site",
            "AssetType",
            "IssueType",
            "Description"
        ]

        available_search_columns = [
            col for col in search_columns
            if col in filtered.columns
        ]

        matches = filtered[
            available_search_columns
        ].astype(str).apply(
            lambda column: column.str.contains(
                search_text,
                case=False,
                regex=False,
                na=False
            )
        ).any(axis=1)

        filtered = filtered[matches]

    st.divider()

    st.metric(
        "Matching Work Orders",
        len(filtered)
    )

    display_columns = [
        "Title",
        "Site",
        "AssetType",
        "IssueType",
        "Priority",
        "Status",
        "EstimatedCostCAD"
    ]

    st.dataframe(
        filtered[display_columns],
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇️ Download Filtered CSV",
        data=filtered[display_columns].to_csv(
            index=False
        ),
        file_name="roadops_filtered_workorders.csv",
        mime="text/csv"
    )

    st.divider()

    st.markdown("#### Work Order Details")

    if not filtered.empty:

        selected_order = st.selectbox(
            "Select a work order",
            filtered["Title"].tolist()
        )

        selected_row = filtered[
            filtered["Title"] == selected_order
        ].iloc[0]

        left, right = st.columns(2)

        with left:
            st.write(
                "**Work Order:**",
                selected_row["Title"]
            )
            st.write(
                "**Site:**",
                selected_row["Site"]
            )
            st.write(
                "**Asset:**",
                selected_row["AssetType"]
            )
            st.write(
                "**Issue:**",
                selected_row["IssueType"]
            )

        with right:
            st.write(
                "**Priority:**",
                selected_row["Priority"]
            )
            st.write(
                "**Status:**",
                selected_row["Status"]
            )
            st.write(
                "**Estimated Cost:**",
                selected_row["EstimatedCostCAD"]
            )

        if "Description" in selected_row.index:
            st.markdown("**Issue Description**")
            st.write(
                selected_row["Description"] or "Not provided"
            )

        if "ResolutionNotes" in selected_row.index:
            st.markdown("**Resolution Notes**")
            st.write(
                selected_row["ResolutionNotes"] or "Not provided"
            )

    else:
        st.info(
            "No work orders match the selected filters."
        )


# ---------------------------------
# FOOTER
# ---------------------------------

st.divider()

st.caption(
    "RoadOps AI | Independent Portfolio Demonstration | "
    "Streamlit + Python + Ollama + RAG + SharePoint CSV"
)
