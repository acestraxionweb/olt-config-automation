"""
OLT Configuration Verifier
--------------------------
Compares every generated OLT config file against the original Excel site
data and produces a discrepancy report (.xlsx) showing which configs are
correct, have mismatches, or are missing.
"""

import argparse
import os
import sys

import pandas as pd

PLACEHOLDERS = {"**L", "**PIP", "**TMV", "**MV"}


def verify_configs(
    excel_path: str,
    config_root: str,
    report_path: str,
    group_by_district: bool = True,
) -> None:
    df = pd.read_excel(excel_path)

    required_cols = {"Site Name", "District", "Private IP", "TMVLAN", "MVLAN"}
    missing = required_cols - set(df.columns)
    if missing:
        sys.exit(f"Excel missing required columns: {missing}")

    records = []

    for _, row in df.iterrows():
        district = str(row["District"])
        site_name = str(row["Site Name"])
        private_ip = str(row["Private IP"])
        tm_vlan = str(row["TMVLAN"])
        mv_vlan = str(row["MVLAN"])

        if group_by_district:
            config_path = os.path.join(config_root, district, f"{site_name}.txt")
        else:
            config_path = os.path.join(config_root, f"{site_name}.txt")

        if not os.path.isfile(config_path):
            records.append(
                {
                    "Site Name": site_name,
                    "District": district,
                    "Private IP": private_ip,
                    "TMVLAN": tm_vlan,
                    "MVLAN": mv_vlan,
                    "Status": "Config File Missing",
                }
            )
            continue

        with open(config_path, "r") as f:
            text = f.read()

        has_placeholder = any(p in text for p in PLACEHOLDERS)

        site_ok = site_name in text
        ip_ok = private_ip in text
        tm_ok = str(tm_vlan) in text
        mv_ok = str(mv_vlan) in text

        all_ok = site_ok and ip_ok and tm_ok and mv_ok and not has_placeholder

        records.append(
            {
                "Site Name": site_name,
                "District": district,
                "Private IP": private_ip,
                "TMVLAN": tm_vlan,
                "MVLAN": mv_vlan,
                "Status": "Correct" if all_ok else "Discrepancy",
            }
        )

    report_df = pd.DataFrame(records)
    report_df.to_excel(report_path, index=False)
    print(f"Verification report saved: {report_path}")
    print(f"  Total sites : {len(report_df)}")
    print(f"  Correct     : {len(report_df[report_df['Status'] == 'Correct'])}")
    print(f"  Discrepancy : {len(report_df[report_df['Status'] == 'Discrepancy'])}")
    print(f"  Missing     : {len(report_df[report_df['Status'] == 'Config File Missing'])}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify generated OLT configs against the source Excel data."
    )
    parser.add_argument("excel", help="Path to the original Excel file with site data")
    parser.add_argument("config_dir", help="Directory containing generated config files")
    parser.add_argument("report", help="Output path for the verification report (.xlsx)")
    parser.add_argument(
        "--flat",
        action="store_true",
        help="Configs are NOT organized in District subfolders",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.excel):
        sys.exit(f"Excel file not found: {args.excel}")
    if not os.path.isdir(args.config_dir):
        sys.exit(f"Config directory not found: {args.config_dir}")

    verify_configs(
        args.excel,
        args.config_dir,
        args.report,
        group_by_district=not args.flat,
    )


if __name__ == "__main__":
    main()
