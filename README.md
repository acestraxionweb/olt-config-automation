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
┌──────────────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Single Excel             │────▶│  config_generator│────▶│  Per-site .txt files│
│  (50+ sites, mixed vendor)│     │  + templates/    │     │  (ready to deploy)  │
│  ZTE, VSOL in one sheet   │     │  auto-picks per  │     │  one per site       │
└──────────────────────────┘     │  row by OLT Type │     └─────────────────────┘
                                 └──────────────────┘              │
                                                                    ▼
┌──────────────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Report .xlsx             │◀────│  config_verifier │◀────│  Deployed configs   │
│  (pass/fail per site)     │     │  compare step    │     │  (from OLT or file) │
└──────────────────────────┘     └──────────────────┘     └─────────────────────┘
```

**Workflow summary:**
1. List all 50+ sites in **one Excel** with their OLT vendor type
2. Run `config_generator.py` once — it picks the right template (ZTE / VSOL) per site
3. Deploy the output `.txt` files to each OLT
4. Run `config_verifier.py` to audit everything matches

## Repository Structure

```
olt-config-automation/
├── src/
│   ├── config_generator.py   # Excel → per-site configs (auto-selects vendor template)
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

| Column Name  | Example            | Description                                |
|-------------|--------------------|--------------------------------------------|
| District    | Selangor           | Geographical grouping (becomes subfolder)  |
| Site Name   | OLT-BKT-INDONG     | Unique OLT identifier (becomes filename)   |
| OLT Type    | ZTE GVGO           | Vendor model — mapped to template file     |
| Private IP  | 10.100.32.1/22     | OLT management IP + prefix                 |
| TMVLAN      | 800                | Primary ISP (TM) customer VLAN             |
| MVLAN       | 801                | Secondary ISP (Maxis) customer VLAN        |

The `OLT Type` column tells the generator which template to use. Supported values:

| OLT Type | Template Used              | PON Ports |
|----------|----------------------------|-----------|
| ZTE GVGH | `templates/zte_gvgh_16_port.txt` | 16 GPON |
| ZTE GVGO | `templates/zte_gvgo_8_port.txt`  | 8 GPON  |
| VSOL     | `templates/vsol.txt`             | 8 GPON  |

This means a site that says VSOL will get a VSOL config, while a site in the same Excel that says ZTE GVGO will get a ZTE config — all in a single run.

### Example Row

| District | Site Name        | OLT Type | Private IP       | TMVLAN | MVLAN |
|----------|------------------|----------|------------------|--------|-------|
| Selangor | OLT-SEL-BDR-BARU | ZTE GVGO | 10.100.1.1/22    | 800    | 900   |
| Selangor | OLT-SEL-KLANG    | VSOL     | 10.100.3.1/22    | 801    | 901   |

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

1. Create a new `.txt` in `templates/`
2. Use the `**L`, `**PIP`, `**TMV`, `**MV` placeholders in the config skeleton
3. Add an entry in `VENDOR_TEMPLATE_MAP` in `src/config_generator.py`
4. Put matching `OLT Type` values in your Excel

## Usage

### Installation

```bash
pip install -r requirements.txt
```

### Generate Configs (Single Run — All Vendors)

```bash
python src/config_generator.py sample_data/sample_site_data.xlsx ./templates ./output
```

`config_generator.py` reads the `OLT Type` column, looks up the matching template in the `./templates` directory, and writes per-site config files.

Output structure:
```
./output/
├── Selangor/
│   ├── OLT-SEL-BDR-BARU.txt   # ZTE GVGO config
│   ├── OLT-SEL-KLANG.txt      # VSOL config
│   └── ...
├── Perak/
│   └── ...
└── Johor/
    └── ...
```

Add `--flat` to omit district subfolders:
```bash
python src/config_generator.py sample_data/sample_site_data.xlsx ./templates ./output --flat
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

### Running in Thonny / IDLE

If you prefer a GUI editor over the command line, open `src/config_generator.py` in Thonny and edit the `main()` call at the bottom, or run it from a terminal with:

```python
# Inside Thonny shell
import sys
sys.argv = ["config_generator.py", "sample_data/sample_site_data.xlsx", "templates", "output"]
exec(open("src/config_generator.py").read())
```

## Vendor Support

| Vendor | Template File             | PON Ports | Notes                        |
|--------|---------------------------|-----------|------------------------------|
| ZTE    | `zte_gvgh_16_port.txt`    | 16 GPON   | C300 / C600 series           |
| ZTE    | `zte_gvgo_8_port.txt`     | 8 GPON    | C300 / C600 series           |
| VSOL   | `vsol.txt`                | 8 GPON    | VSOL OLT (V-Series)          |

## Development & Contributing

1. Fork the repo and create a feature branch
2. Add or update templates in `templates/`
3. Add a new entry in `VENDOR_TEMPLATE_MAP` in `config_generator.py`
4. Test with `sample_data/sample_site_data.xlsx`
5. Run both scripts and verify the output
6. Submit a pull request

## License

MIT — see LICENSE file.
