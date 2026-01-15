# ACLED Aggregated Data Collector

Automated collector for ACLED public aggregated datasets with versioning and metadata tracking.

## Features

- ✅ **Authentication**: Automatic login to ACLED
- ✅ **12 Datasets**: Covers all official aggregated data sources
- ✅ **Versioning**: SHA256 hash-based deduplication
- ✅ **Retry Logic**: Exponential backoff for failed downloads
- ✅ **Metadata**: JSON tracking for each dataset
- ✅ **Logging**: Structured logs to file and console
- ✅ **Resilient**: Failures in one dataset don't stop the pipeline

## Installation

```bash
cd c:\Users\augusto.moreira\Documents\sofia-pulse
pip install requests beautifulsoup4 pandas
```

## Configuration

Edit credentials in `scripts/collect-acled-aggregated.py`:

```python
EMAIL = "your_email@example.com"
PASSWORD = "your_password"
```

## Usage

### Run Once

```bash
python scripts/collect-acled-aggregated.py
```

### Schedule with Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Weekly (e.g., every Monday at 3 AM)
4. Action: Start a program
   - Program: `python`
   - Arguments: `scripts\collect-acled-aggregated.py`
   - Start in: `c:\Users\augusto.moreira\Documents\sofia-pulse`

### Schedule with Cron (Linux/Mac)

```cron
0 3 * * 1 cd /path/to/sofia-pulse && python scripts/collect-acled-aggregated.py
```

## Directory Structure

After first run:

```
data/
  acled/
    raw/
      political-violence-country-year/
        2026-01-15/
          number_of_political_violence_events_by_country-year_as-of-09Jan2026.xlsx
      aggregated-africa/
        2026-01-15/
          Africa_aggregated_data_up_to-2026-01-03.xlsx
      ...
    metadata/
      political-violence-country-year.json
      aggregated-africa.json
      ...
```

## Metadata Example

```json
{
  "dataset_slug": "political-violence-country-year",
  "source_url": "https://acleddata.com/aggregated/...",
  "download_url": "https://acleddata.com/system/files/...",
  "file_name": "number_of_political_violence_events_by_country-year_as-of-09Jan2026.xlsx",
  "file_path": "data/acled/raw/political-violence-country-year/2026-01-15/...",
  "file_hash": "a3f5...",
  "file_size_bytes": 44943,
  "collected_at": "2026-01-15T16:54:00.000Z",
  "region": "Global",
  "aggregation_level": "country-year",
  "version_date": "2026-01-15"
}
```

## Adding New Datasets

Edit the `DATASETS` list in `collect-acled-aggregated.py`:

```python
{
    "slug": "my-new-dataset",
    "url": "https://acleddata.com/aggregated/...",
    "aggregation_level": "country-week",
    "region": "Custom Region"
}
```

## Logs

Logs are written to:
- **File**: `acled_collector.log`
- **Console**: Real-time output

## Optional: Convert to Parquet

Run the conversion utility:

```bash
python scripts/acled-convert-to-parquet.py
```

This will create `.parquet` files alongside the original `.xlsx` files with:
- Faster read times
- Smaller file sizes
- Column names in snake_case

## Troubleshooting

### Authentication Fails

- Verify credentials in the script
- Check if ACLED changed their login form
- Ensure account is active

### No Download Links Found

- ACLED may have changed page structure
- Check logs for HTTP errors
- Manually verify the URL is accessible when logged in

### Hash Always Different

- ACLED may be modifying files (timestamps, formatting)
- This is expected if they update data frequently
- The collector will save each version with a date stamp

## Dataset Coverage

| Slug | Aggregation | Region |
|------|-------------|--------|
| `political-violence-country-year` | country-year | Global |
| `political-violence-country-month-year` | country-month-year | Global |
| `demonstrations-country-year` | country-year | Global |
| `civilian-targeting-country-year` | country-year | Global |
| `fatalities-country-year` | country-year | Global |
| `civilian-fatalities-country-year` | country-year | Global |
| `aggregated-europe-central-asia` | regional | Europe/Central Asia |
| `aggregated-us-canada` | regional | US/Canada |
| `aggregated-latin-america-caribbean` | regional | Latin America |
| `aggregated-middle-east` | regional | Middle East |
| `aggregated-asia-pacific` | regional | Asia Pacific |
| `aggregated-africa` | regional | Africa |

## License

Part of the Sofia Pulse project.
