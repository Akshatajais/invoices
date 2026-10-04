# Invoice bills

A small web app for generating bills from Excel templates. UltraTech, Dalmia Lalan, Dalmia Shila, ACC Lalan, and ACC Shila are active.

The PDF is not drawn in HTML. The app copies `ultratech.xlsx`, writes three cells, and asks LibreOffice to print that workbook to PDF. The original template file is never modified.

## What you need

- Python 3.12 or newer
- LibreOffice (free). It is the Excel-to-PDF engine.

No paid PDF API, Excel API, database, or hosting account is required to run this on your own computer.

## Install and run locally

From this project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Install LibreOffice:

```bash
# macOS
brew install --cask libreoffice

# Debian or Ubuntu
sudo apt update
sudo apt install -y libreoffice-calc fonts-liberation fonts-crosextra-carlito fonts-crosextra-caladea fonts-texgyre fontconfig
```

Start the app so a phone on the same Wi‑Fi can open it:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

On this computer, open [http://localhost:8000](http://localhost:8000).

On an Android phone, open `http://<this-computer-lan-ip>:8000`.

## Try UltraTech

1. Open the home screen. UltraTech, Dalmia Lalan, Dalmia Shila, ACC Lalan, and ACC Shila are active.
2. Open UltraTech Bill.
3. Choose an invoice date from 1 May 2026 through 30 April 2027.
4. Check the billing month, invoice number, and bill period. You do not type those.
5. Click **Generate PDF**, wait for “PDF generated successfully.”, then **Download PDF**.

Examples:

| Invoice date | Invoice number | Bill period |
| --- | --- | --- |
| 15 May 2026 | 2026-27/Q1 | 09 May 2026 – 08 June 2026 |
| 15 June 2026 | 2026-27/Q2 | 09 June 2026 – 08 July 2026 |
| 15 July 2026 | 2026-27/Q3 | 09 July 2026 – 08 August 2026 |

The downloaded file is named `UltraTech_Invoice_2026-27-Q1.pdf` (and Q2, Q3, and so on).

May 2026 is Q1 and April 2027 is Q12. Dates outside 1 May 2026–30 April 2027 are rejected. Later financial years are not guessed.

The billing month is the calendar month of the invoice date. The period runs from the 9th of that month through the 8th of the next month. A date on the 1st–8th still uses that calendar month. That choice lives only in `app/bill_modules/ultratech/billing_period.py`.

## Check the Excel-to-PDF result

With the app running in development (the default):

- Open [http://localhost:8000/dev/compare](http://localhost:8000/dev/compare)
- Or run:

```bash
python scripts/render_proof.py
pytest
```

The proof script writes:

- `artifacts/reference-ultratech.pdf` — the original template, unchanged, printed to PDF
- `artifacts/test-ultratech.pdf` — 15 May 2026
- `artifacts/UltraTech_Invoice_2026-27-Q1.pdf` (and Q2, Q3)

`POST /api/test-ultratech-render` does the same 15 May 2026 render and saves `artifacts/test-ultratech.pdf`. These routes answer only when `APP_ENV` is not `production`.

## Where the template lives

```text
app/bill_modules/ultratech/template/ultratech.xlsx
```

That file is the master. The app only reads it. Each request copies it to a unique temporary file, edits the copy, converts the copy, then deletes the temporary files.

The template is not available as a public download.

## How Excel processing works

UltraTech settings are only in `app/bill_modules/ultratech/`.

Cell mapping, from the real workbook (sheet `Godwon rent (2)`):

| Field | Cell | Notes |
| --- | --- | --- |
| Invoice number | L8 | Label `Invoice No-` stays in I8 |
| Invoice date | L9 | Label `Invoice Date -` stays in I9. L9 was empty. |
| Bill period | L16 | Label `Bill for the period :` stays in I16. The value is split onto two lines in L16:M17 so it stays the same size as that label. |

The signature is a grouped picture inside the workbook. Saving with a spreadsheet library would drop that drawing, so the copy is updated inside the xlsx zip. Labels, images, and the drawing stay as they are.

A full billing period is wider than column L at the label’s 14pt size. The temporary copy merges L16:M17 and prints the two dates on separate lines, so the text stays that size and inside the invoice border. The master template is not given that merge.

## How PDF conversion works

LibreOffice (`soffice --headless`) prints the temporary workbook to PDF. Nothing is sent to a commercial conversion service.

The template’s table lines are black in Excel, stored as palette index 8. LibreOffice imports that index as white, so the Sl No / Particulars / No of Month / Rate / Amount grid would not print. Before conversion, the temporary copy’s border colors are rewritten to explicit black. The master template is not changed.

The workbook is set to fit on one portrait page. The converter asks LibreOffice for that single-page sheet export.

Fonts in the template include Calibri and Century Schoolbook, which are not free to ship. The app uses Carlito (metric match for Calibri) and TeX Gyre Schola (metric match for Century Schoolbook). On a Mac, Times New Roman and Helvetica Neue are used when the system already has them. Licenses for the bundled fonts are in `deploy/fonts/`.

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_ENV` | `development` | Set to `production` before a shared deployment. That hides the render-test routes. |
| `PORT` | `8000` locally, `8080` in Docker | HTTP port |
| `LIBREOFFICE_PATH` | discovered automatically | Full path to `soffice` if it is not on `PATH` |
| `ARTIFACTS_DIR` | `./artifacts` | Where the development proof PDFs are saved |

There is no database and no API key.

## Deploy without a paid plan

Cloudflare Workers, Cloudflare Pages, and Vercel’s normal serverless runtime cannot run LibreOffice. The program is a native desktop app, and those hosts do not allow this kind of conversion. A static site would also be unable to print the Excel file.

Use a free container or a free virtual machine instead. The same `Dockerfile` runs in either place. It installs LibreOffice Calc and the open fonts, then serves the website and the API together.

Build and run it on any machine that has Docker:

```bash
docker build -t invoice-bills .
docker run --rm -p 8000:8080 -e APP_ENV=production invoice-bills
```

Open [http://localhost:8000](http://localhost:8000).

### Google Cloud Run free tier

Cloud Run’s free tier can host this container. Google asks for a billing account, but a personal volume of bills stays inside the free quota (scale to zero, 1 GiB memory). The first request after idle time is slow because LibreOffice starts cold.

```bash
gcloud run deploy invoice-bills \
  --source . \
  --region asia-south1 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --min-instances 0 \
  --allow-unauthenticated \
  --set-env-vars APP_ENV=production
```

Use 1 GiB. LibreOffice fails in a smaller instance.

### Render

Docker is required. Render’s plain Python runtime cannot install LibreOffice, and that program is what prints each Excel workbook to PDF. The site and the API are the same service. The browser calls `/api/...` on the same host, so no separate frontend URL and no CORS setting are required.

In the Render dashboard, create a **Web Service** from this repository:

- Environment: **Docker**
- Build Command: leave empty. Render runs `docker build`.
- Start Command: leave empty. The image runs `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Health Check Path: `/health`

`APP_ENV=production` is set in the image and in `render.yaml`. It hides the development PDF routes. No API key or database is used.

The free instance has 512 MB of RAM. LibreOffice often fails in less than 1 GB, so if a generated PDF returns an error, move the service to an instance with at least 1 GB. The first bill after the service wakes up is slower because LibreOffice starts cold. Temporary workbooks are created per request under `/tmp` and deleted when the PDF is returned.

### A free virtual machine

Oracle Cloud’s Always Free Ampere VM can run the same image and stay on, so the first bill is not delayed by a cold start. Install Docker on the VM, copy this project up, then run the `docker build` and `docker run` commands above. Open the VM’s port 8000 only to the people who should generate bills.

This phase has no login. Keep the server on a private network, or put it behind access control, before anyone on the internet can reach it.

## ACC Lalan and ACC Shila

These two bills do not use UltraTech’s May = Q1 numbering or the 9th-to-8th period.

The only input is the invoice date, and only dates in 2026 are accepted. January is month 1.

| Bill | Invoice number | Time period | Cells |
| --- | --- | --- | --- |
| ACC Lalan | `LPJ/26-27/5` for May | `May 2026` | E6 number, E7 date, E10 period. Template: `app/bill_modules/acc_lalan/template/acc_lalan.xlsx` |
| ACC Shila | `SHJ/26-27/5` for May | `May 2026` | E6 number, E7 date, E10 period. Template: `app/bill_modules/acc_shila/template/acc_sheela.xlsx` |

The date cell already has Excel’s built-in date format, so the working copy writes a date value there and leaves that format in place. The downloaded files are named `ACC_Lalan_Invoice_LPJ_26-27_5.pdf` and `ACC_Shila_Invoice_SHJ_26-27_5.pdf`.

## Dalmia Lalan and Dalmia Shila

These two bills do not use UltraTech’s May = Q1 numbering or the 9th-to-8th period, and they do not use the ACC invoice prefixes.

The only input is the invoice date. Dates from 1 January 2026 through 31 January 2027 are accepted. January is month 1. The `26-27` token stays the same for January 2027.

| Bill | Invoice number | Time period | Cells |
| --- | --- | --- | --- |
| Dalmia Lalan | `LPJ/26-27/D-5` for May | `May 2026` | E6 number, E7 date, E10 period. Template: `app/bill_modules/dalmia_lalan/template/dalmia_lalan.xlsx` |
| Dalmia Shila | `SHJ/26-27/D-5` for May | `May 2026` | E6 number, E7 date, E10 period. Template: `app/bill_modules/dalmia_shila/template/dalmia_shila.xlsx` |

Lalan’s date cell already has Excel’s built-in date format, so the working copy writes a date value there. Shila’s date cell is General, so the working copy writes `15/05/2026` as text. Lalan’s sheet does not store a blank E10, so the working copy adds that cell and the master file is left unchanged. The downloaded files are named `Dalmia_Lalan_Invoice_LPJ_26-27_D-5.pdf` and `Dalmia_Shila_Invoice_SHJ_26-27_D-5.pdf`.

## Add another bill later

Do not extend the UltraTech rules. Each bill gets its own folder:

```text
app/bill_modules/dalmia_lalan/
app/bill_modules/dalmia_shila/
app/bill_modules/acc_lalan/
app/bill_modules/acc_shila/
```

For a new bill:

1. Put its Excel file in that folder’s `template/` directory.
2. Add its own fields, cell map, date rules, numbering, and validation in that folder.
3. Mark it `available: True` in `app/bill_modules/registry.py`.
4. Add its own page. The home screen already lists the five names.

The 9th-to-8th period and `2026-27/Q1` numbering belong to UltraTech only.

## Replace the UltraTech template safely

1. Stop the app.
2. Replace `app/bill_modules/ultratech/template/ultratech.xlsx` with the new master file. Do not generate a bill by editing that file and saving over it.
3. If the invoice number, date, or period moved, change only `app/bill_modules/ultratech/configuration.py`.
4. Start the app and run `python scripts/render_proof.py`.
5. Compare `artifacts/reference-ultratech.pdf` with `artifacts/test-ultratech.pdf`.

## Tests

```bash
pytest
python scripts/render_proof.py
```

`pytest` always checks the date rules and that the master workbook’s hash does not change. The PDF test runs when LibreOffice is installed.
