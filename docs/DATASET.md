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

Download the dataset from the official UCI page and extract the source file locally. Place it at:

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

The validation script should produce a summary before training:
- file exists, is readable and has the expected columns;
- row count is reported and compared with UCI's published 2,075,259 records (a difference should produce a warning, not an unexamined silent pass);
- timestamps parse successfully, sort chronologically and are checked for duplicates;
- timestamp gaps and non-minute intervals are counted;
- all numeric columns are parsed, with `?` and empty values represented as missing;
- missing counts and percentages are reported for each measurement column;
- negative active-power/sub-metering readings and implausible electrical values are flagged for inspection;
- hourly aggregation reports valid minute counts and missing/excluded hours;
- target values are never forward/backward-filled from future observations;
- the output records covered date range, valid hourly count and validation warnings.

For hourly means, begin with a configurable coverage threshold of at least 45 valid minute-level target observations per hour. Document the threshold and test its effect; do not silently treat an hour with only a few measurements as complete.

## 5. License and attribution

The UCI dataset is licensed under CC BY 4.0. Preserve attribution in the README and final report:

> Hebrail, G. & Berard, A. (2006). *Individual Household Electric Power Consumption* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C58K54.

This project is an academic/educational analysis of the dataset and should not imply that the original data was collected by the GridPulse team.

## 6. Considered alternative

UCI's *Appliances Energy Prediction* dataset contains 19,735 ten-minute observations over about 4.5 months, with appliance energy readings and indoor/outdoor temperature and humidity. It may be useful for a future weather/environmental-feature experiment, but it has a shorter period and a different target. To keep the MVP reproducible and focused, it is **not** part of the primary training pipeline unless a later, explicit experiment adds it.

Alternative source: https://archive.ics.uci.edu/dataset/374/appliancesenergyprediction
