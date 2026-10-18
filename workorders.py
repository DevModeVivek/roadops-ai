
import pandas as pd
from pathlib import Path

FILE = Path(__file__).parent / "data" / "workorders.csv"


def load_workorders():
    return pd.read_csv(FILE, dtype={"Title": str})


def get_total():
    df = load_workorders()
    return len(df)


def get_high_priority():
    df = load_workorders()

    high = df[
        df["Priority"].str.strip().str.lower() == "high"
    ]

    return len(high)


def get_status(work_order):
    df = load_workorders()

    found = df[
        df["Title"].str.strip().str.upper()
        == work_order.strip().upper()
    ]

    if found.empty:
        return "Work order not found."

    row = found.iloc[0]

    return (
        f"Work order: {row['Title']}\n"
        f"Status: {row['Status']}\n"
        f"Priority: {row['Priority']}\n"
        f"Site: {row['Site']}\n"
        f"Issue: {row['IssueType']}"
    )


def get_top_site():
    df = load_workorders()

    counts = df["Site"].value_counts()

    if counts.empty:
        return "No work orders available."

    return (
        f"{counts.index[0]}: "
        f"{counts.iloc[0]} work orders"
    )


if __name__ == "__main__":
    print("Total work orders:", get_total())
    print("High priority:", get_high_priority())
    print("\nWO-1001:")
    print(get_status("WO-1001"))
    print("\nSite with most requests:", get_top_site())
