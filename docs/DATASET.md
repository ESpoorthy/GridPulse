# GridPulse — Dataset Selection and Validation

## 1. Selected primary dataset

**Name:** Individual Household Electric Power Consumption  
**Publisher:** UCI Machine Learning Repository  
**Official page:** https://archive.ics.uci.edu/dataset/235/individualhouseholdelectricpowerconsumption  
**DOI:** https://doi.org/10.24432/C58K54  
**License:** Creative Commons Attribution 4.0 International (CC BY 4.0)  
**Primary file:** `household_power_consumption.txt`

UCI documents 2,075,259 one-minute measurements collected from one household in Sceaux, France, between December 2006 and November 2010. The data has nine attributes, including date, time, global active/reactive power, voltage, current intensity and three sub-metering values. UCI notes that some measurement values are missing (approximately 1.25% of rows). Source: the official UCI dataset page linked above.

### Why this dataset fits GridPulse

- Nearly four years of minute-level historical readings provide useful daily and weekly patterns.
- The `Global_active_power` signal supports a clearly defined regression target.
- The sub-metering and electrical measurements enable data exploration even if they are not all used as forecasting inputs.
- The dataset supports regression and clustering experiments relevant to the course syllabus.

### Important limitations

- It represents **one historical household**, not multiple buildings or the utility grid.
- Its observations are from 2006–2010; it is not live or contemporary consumption.
- The primary dataset does not include weather features, so the MVP cannot claim weather-aware forecasting.
- Measurements have missing values and require explicit validation and preprocessing.
- A detected anomaly indicates unusual consumption relative to the defined baseline, not proof of waste or equipment malfunction.

## 2. Download and local placement

The training command downloads the archive from UCI's official static dataset URL and checks its SHA-256 before reading it. The current pinned digest is recorded in `ml/data_loader.py`; updating it requires verifying a fresh official download and the archive contents. Place a manually downloaded source file at:

```text
data/
└── raw/
    └── household_power_consumption.txt
```

Do not commit the raw data file. It is large, does not belong in source control, and is reproducible from the official source. Keep local raw and processed datasets ignored by Git.

An alternative access route is the Python `ucimlrepo` package documented by UCI, but the project should standardise on one ingestion method before implementation.

## 3. Expected fields

The source uses a semicolon-delimited text file. The relevant columns are:

| Column | Meaning | Units / handling |
|---|---|---|
| `Date` | Measurement date | Parse as day/month/year |
| `Time` | Measurement time | Parse as hour:minute:second |
| `Global_active_power` | Average active power | kW; primary target |
| `Global_reactive_power` | Reactive power | kW as described by source |
| `Voltage` | Average voltage | V |
| `Global_intensity` | Average current intensity | A |
| `Sub_metering_1` | First sub-metering channel | Wh per minute |
| `Sub_metering_2` | Second sub-metering channel | Wh per minute |
| `Sub_metering_3` | Third sub-metering channel | Wh per minute |

The actual file schema must be checked when loading it; code should not silently assume a different delimiter, decimal convention or missing-value format.

## 4. Data validation checklist

The validator produces a summary before training:
- file exists, is readable and has the expected columns;
- row count is reported and compared with UCI's published 2,075,259 records (a difference should produce a warning, not an unexamined silent pass);
- timestamps parse successfully, sort chronologically and are checked for duplicates;
- missing expected minute timestamps, non-minute gaps, and missing hour bins are counted;
- all numeric columns are parsed, with `?` and empty values represented as missing;
- missing counts and percentages are reported for each measurement column;
- negative active-power/sub-metering readings and implausible electrical values are flagged for inspection;
- hourly aggregation reports valid minute counts and missing/excluded hours;
- target values are never forward/backward-filled from future observations;
- the output records covered date range, valid hourly count and validation warnings.

For hourly means, begin with a configurable coverage threshold of at least 45 valid minute-level target observations per hour. Document the threshold and test its effect; do not silently treat an hour with only a few measurements as complete.

## Local validation tooling

The repository includes a chunked validator at `scripts/validate_data.py`. It checks the expected schema, source row count, timestamp parsing/order, duplicate timestamps, missing minute/hour timestamps, numeric missingness and parse failures, suspicious active-power readings, and hourly coverage. It deterministically retains the first source record for a timestamp and excludes later duplicates from hourly aggregation, so duplicate records cannot increase an hour's reading count. It writes:

- `reports/generated/dataset_validation.json` — local data-quality report.
- `data/processed/hourly_power.csv` — hourly means with at least 45 valid target readings by default.

Run it from the repository root after installing dependencies and downloading the file:

```bash
python -m pip install -r requirements.txt
python scripts/validate_data.py
pytest -q tests/test_validate_data.py
```

The published row count is used as a warning/check, not as silent proof of integrity. Missing measurements are expected in this dataset and are reported, not imputed. Generated data and reports are ignored by Git. Run `python scripts/train_models.py` to validate the full raw file and create the experiment/model artifacts.

## 5. License and attribution

The UCI dataset is licensed under CC BY 4.0. Preserve attribution in the README and final report:

> Hebrail, G. & Berard, A. (2006). *Individual Household Electric Power Consumption* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C58K54.

This project is an academic/educational analysis of the dataset and should not imply that the original data was collected by the GridPulse team.

## 6. Considered alternative

UCI's *Appliances Energy Prediction* dataset contains 19,735 ten-minute observations over about 4.5 months, with appliance energy readings and indoor/outdoor temperature and humidity. It may be useful for a future weather/environmental-feature experiment, but it has a shorter period and a different target. To keep the MVP reproducible and focused, it is **not** part of the primary training pipeline unless a later, explicit experiment adds it.

Alternative source: https://archive.ics.uci.edu/dataset/374/appliancesenergyprediction
