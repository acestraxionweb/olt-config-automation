"""
OLT Configuration Generator
---------------------------
Reads a single Excel with mixed-vendor sites (ZTE / VSOL) and generates
per-device configuration files by picking the correct vendor template for
each row and substituting placeholders.
"""

import argparse
import os
import sys

import pandas as pd

# Maps the "OLT Type" column value → template filename in the templates directory
VENDOR_TEMPLATE_MAP = {
    "ZTE GVGH": "zte_gvgh_16_port.txt",
    "ZTE GVGO": "zte_gvgo_8_port.txt",
    "VSOL": "vsol.txt",
}


def load_template(template_dir: str, vendor_key: str) -> str:
    filename = VENDOR_TEMPLATE_MAP.get(vendor_key)
    if not filename:
        valid = ", ".join(VENDOR_TEMPLATE_MAP)
        sys.exit(f"Unknown OLT Type '{vendor_key}'. Valid values: {valid}")
    path = os.path.join(template_dir, filename)
    if not os.path.isfile(path):
        sys.exit(f"Template file not found: {path}")
    with open(path, "r") as f:
        return f.read()


def generate_configs(
    excel_path: str,
    template_dir: str,
    output_dir: str,
    group_by_district: bool = True,
) -> None:
    df = pd.read_excel(excel_path)

    required_cols = {"Site Name", "District", "Private IP", "TMVLAN", "MVLAN", "OLT Type"}
    missing = required_cols - set(df.columns)
    if missing:
        sys.exit(f"Excel missing required columns: {missing}")

    for _, row in df.iterrows():
        vendor = str(row["OLT Type"]).strip()
        district = str(row["District"])
        site_name = str(row["Site Name"])
        private_ip = str(row["Private IP"])
        tm_vlan = str(row["TMVLAN"])
        mv_vlan = str(row["MVLAN"])

        template = load_template(template_dir, vendor)

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

        print(f"  [{vendor}] {site_name}.txt -> {target}")

    print(f"\nDone. All configs saved under: {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate OLT configuration files from Excel site data."
    )
    parser.add_argument("excel", help="Path to the Excel file with site data")
    parser.add_argument("templates_dir", help="Directory containing vendor template files")
    parser.add_argument("output", help="Output directory for generated configs")
    parser.add_argument(
        "--flat",
        action="store_true",
        help="Do not group output files by District subfolder",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.excel):
        sys.exit(f"Excel file not found: {args.excel}")
    if not os.path.isdir(args.templates_dir):
        sys.exit(f"Templates directory not found: {args.templates_dir}")

    generate_configs(args.excel, args.templates_dir, args.output, group_by_district=not args.flat)


if __name__ == "__main__":
    main()
