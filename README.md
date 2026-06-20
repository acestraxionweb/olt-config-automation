# OLT Configuration Automation

A Python toolkit for bulk-generating and verifying GPON OLT device configurations from Excel site data. Designed for field fibre engineers deploying ZTE (GVGH-16 port, GVGO-8 port) and VSOL OLTs.

## Problem Statement

Rolling out FTTH at scale means provisioning dozens of OLTs per district. Manual configuration is:
- **Error-prone** — one mistyped IP or VLAN breaks an entire PON port
- **Slow** — each device takes 20-30 minutes of CLI typing
- **Unverifiable** — no easy way to audit that deployed configs match the planning spreadsheet

This tool automates the entire cycle: template-based generation + post-deployment verification.

## How It Works

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Site Excel      │────▶│  config_generator│────▶│  Per-site .txt files│
│  (sites + VLANs) │     │  + vendor template│     │  (ready to deploy)  │
└─────────────────┘     └──────────────────┘     └─────────────────────┘
                                                           │
                                                           ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Report .xlsx    │◀────│  config_verifier │◀────│  Deployed configs   │
│  (pass/fail)     │     │  (compare step)  │     │  (from OLT or file) │
└─────────────────┘     └──────────────────┘     └─────────────────────┘
```

## Repository Structure

```
olt-config-automation/
├── src/
│   ├── config_generator.py   # Template → per-site config files
│   └── config_verifier.py    # Compare generated configs vs Excel source
├── templates/
│   ├── zte_gvgh_16_port.txt  # ZTE GVGH-16 port skeleton
│   ├── zte_gvgo_8_port.txt   # ZTE GVGO-8 port skeleton
│   └── vsol.txt              # VSOL OLT skeleton
├── sample_data/
│   └── sample_site_data.xlsx # Example Excel with expected columns
├── requirements.txt
├── .gitignore
└── README.md
```

## Excel Input Format

The spreadsheet must contain these columns (case-sensitive):

| Column Name  | Example        | Description                       |
|-------------|----------------|-----------------------------------|
| District    | Selangor       | Geographical grouping             |
| Site Name   | OLT-BKT-INDONG | Unique OLT identifier             |
| Private IP  | 10.100.32.1/22 | OLT management IP + prefix        |
| TMVLAN      | 800            | Primary ISP (TM) customer VLAN    |
| MVLAN       | 801            | Secondary ISP (Maxis) customer VLAN |

The `District` value is used as a subfolder name when generating configs.

## Template Placeholder System

Templates use four placeholders that get substituted at generation time:

| Placeholder | Replaced With         |
|-------------|-----------------------|
| `**L`       | Site Name (hostname)  |
| `**PIP`     | Private IP + netmask  |
| `**TMV`     | TM VLAN ID            |
| `**MV`      | Maxis VLAN ID         |

Example template snippet:
```text
hostname **L
interface vlan15
  ip address **PIP 255.255.252.0
```

### Adding a New Vendor Template

1. Copy an existing `.txt` from `templates/`
2. Replace device-specific config while keeping the `**L`, `**PIP`, `**TMV`, `**MV` placeholders
3. Pass the new template to `config_generator.py` via the second positional argument

## Usage

### Installation

```bash
pip install -r requirements.txt
```

### Generate Configs

```bash
python src/config_generator.py sample_data/sample_site_data.xlsx templates/zte_gvgo_8_port.txt ./output
```

Configs are saved as `./output/<District>/<Site Name>.txt`.

Add `--flat` to omit district subfolders:
```bash
python src/config_generator.py sample_data/sample_site_data.xlsx templates/vsol.txt ./output --flat
```

### Verify Configs

```bash
python src/config_verifier.py sample_data/sample_site_data.xlsx ./output ./verification_report.xlsx
```

Produces an Excel report with columns: `Site Name`, `District`, `Private IP`, `TMVLAN`, `MVLAN`, `Status`.

Status values:
- **Correct** — all values match, no placeholders remain
- **Discrepancy** — one or more values differ or placeholders still present
- **Config File Missing** — file not found for this site

## Vendor Support

| Vendor | Template File             | PON Ports | Notes                        |
|--------|---------------------------|-----------|------------------------------|
| ZTE    | `zte_gvgh_16_port.txt`    | 16 GPON   | C300 / C600 series           |
| ZTE    | `zte_gvgo_8_port.txt`     | 8 GPON    | C300 / C600 series           |
| VSOL   | `vsol.txt`                | 8 GPON    | VSOL OLT (V-Series)          |

## Development & Contributing

1. Fork the repo and create a feature branch
2. Add or update templates in `templates/`
3. Test with `sample_data/sample_site_data.xlsx`
4. Run both scripts and verify the output
5. Submit a pull request

## License

MIT — see LICENSE file.
