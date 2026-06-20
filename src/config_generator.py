"""
OLT Configuration Generator
---------------------------
Reads site data from an Excel spreadsheet and generates per-device OLT
configuration files by substituting placeholders in a vendor-specific template.

Supported vendors: ZTE (GVGH-16port, GVGO-8port), VSOL
"""

import argparse
import os
import sys

import pandas as pd


def load_template(template_path: str) -> str:
    with open(template_path, "r") as f:
        return f.read()


def generate_configs(
    excel_path: str,
    template_path: str,
    output_dir: str,
    group_by_district: bool = True,
) -> None:
    df = pd.read_excel(excel_path)
    template = load_template(template_path)

    required_cols = {"Site Name", "District", "Private IP", "TMVLAN", "MVLAN"}
    missing = required_cols - set(df.columns)
    if missing:
        sys.exit(f"Excel missing required columns: {missing}")

    for _, row in df.iterrows():
        district = str(row["District"])
        site_name = str(row["Site Name"])
        private_ip = str(row["Private IP"])
        tm_vlan = str(row["TMVLAN"])
        mv_vlan = str(row["MVLAN"])

        config = template.replace("**L", site_name)
        config = config.replace("**PIP", private_ip)
        config = config.replace("**TMV", tm_vlan)
        config = config.replace("**MV", mv_vlan)

        if group_by_district:
            target = os.path.join(output_dir, district)
        else:
            target = output_dir
        os.makedirs(target, exist_ok=True)

        out_path = os.path.join(target, f"{site_name}.txt")
        with open(out_path, "w") as f:
            f.write(config)

        print(f"  [OK] {site_name}.txt -> {target}")

    print(f"\nDone. All configs saved under: {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate OLT configuration files from Excel site data."
    )
    parser.add_argument("excel", help="Path to the Excel file with site data")
    parser.add_argument("template", help="Path to the OLT vendor template file")
    parser.add_argument("output", help="Output directory for generated configs")
    parser.add_argument(
        "--flat",
        action="store_true",
        help="Do not group output files by District subfolder",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.excel):
        sys.exit(f"Excel file not found: {args.excel}")
    if not os.path.isfile(args.template):
        sys.exit(f"Template file not found: {args.template}")

    generate_configs(args.excel, args.template, args.output, group_by_district=not args.flat)


if __name__ == "__main__":
    main()
