# BirdCLEF Prediction Response Schema

## Overview

The `/predict` endpoint returns a comprehensive JSON response containing:
- Real duration tracking and padding markers
- Per-window predictions with padding flags
- Heatmap for visualization (species × valid windows)
- Branch scores from individual model components
- Ranked species with detection metrics
- Waveform peaks for audio visualization

## Complete Response Structure

```json
{
  "real_duration_sec": float,
  "n_windows": int,
  "n_classes": int,
  "valid_windows": int,
  "windows": [...],
  "heatmap": {...},
  "branch_scores": {...},
  "top_species": [...],
  "waveform_peaks": [...]
}
```

---

## Field Definitions

### 1. Basic Metadata

#### `real_duration_sec`
- **Type**: `float`
- **Description**: Actual duration of the uploaded audio file in seconds (before padding)
- **Example**: `28.5`
- **Note**: May be less than 60 seconds for short clips

#### `n_windows`
- **Type**: `int`
- **Description**: Total number of 5-second windows (always 12)
- **Example**: `12`

#### `n_classes`
- **Type**: `int`
- **Description**: Total number of bird/animal classes (always 234)
- **Example**: `234`

#### `valid_windows`
- **Type**: `int`
- **Description**: Number of windows containing real audio (0-12)
- **Calculation**: `ceil(real_duration_sec / 5)`
- **Example**: `6` for a 28-second clip

---

## 2. Windows

#### `windows`
- **Type**: `list[dict]`
- **Length**: 12
- **Description**: Per-window predictions with padding flags

### Window Object

```json
{
  "index": int,
  "start_sec": int,
  "end_sec": int,
  "is_padding": bool,
  "top_k": [...]
}
```

#### Fields

##### `index`
- **Type**: `int`
- **Description**: Window index (0-11)
- **Example**: `0`

##### `start_sec`
- **Type**: `int`
- **Description**: Start time of this window in seconds
- **Example**: `0` for window 0, `5` for window 1, etc.

##### `end_sec`
- **Type**: `int`
- **Description**: End time of this window in seconds
- **Example**: `5` for window 0, `10` for window 1, etc.

##### `is_padding`
- **Type**: `bool`
- **Description**: `true` if this window is beyond `real_duration_sec` (padding only)
- **Note**: Padding windows have `top_k: []` (no predictions)
- **Example**: `false` for first 6 windows of a 28s clip, `true` for windows 6-11

##### `top_k`
- **Type**: `list[dict]`
- **Description**: Top 5 predictions for this window (empty if padding)
- **Example**: See "Prediction Object" below

### Prediction Object (within `top_k`)

```json
{
  "code": "string",
  "common_name": "string",
  "scientific_name": "string",
  "taxon": "string",
  "score": float
}
```

#### Fields

##### `code`
- **Type**: `string`
- **Description**: Class code (iNaturalist taxon ID)
- **Example**: `"whtdov"` or `"116570"`

##### `common_name`
- **Type**: `string`
- **Description**: Common species name
- **Example**: `"White Dove"`

##### `scientific_name`
- **Type**: `string`
- **Description**: Latin scientific name
- **Example**: `"Columba palumbus"`

##### `taxon`
- **Type**: `string`
- **Description**: High-level taxonomic classification
- **Values**: `"Aves"`, `"Insecta"`, `"Mammalia"`, `"Amphibia"`, `"Reptilia"`, or `"Unknown"`
- **Example**: `"Aves"`

##### `score`
- **Type**: `float`
- **Range**: `[0.0, 1.0]`
- **Description**: Confidence score after post-processing and blending
- **Example**: `0.87`

---

## 3. Heatmap

#### `heatmap`
- **Type**: `dict`
- **Description**: Visualization data for species detected across valid windows

### Heatmap Object

```json
{
  "species": [...],
  "matrix": [[...], [...], ...]
}
```

#### `heatmap.species`
- **Type**: `list[dict]`
- **Description**: List of species detected at least once in valid windows
- **Note**: Empty if no species above threshold

### Species Object (within `heatmap.species`)

```json
{
  "code": "string",
  "common_name": "string",
  "scientific_name": "string",
  "taxon": "string"
}
```

Fields same as Prediction Object above (without `score`).

#### `heatmap.matrix`
- **Type**: `list[list[float]]`
- **Description**: 2D array of prediction scores
- **Shape**: `[n_detected, valid_windows]`
  - Rows = detected species (same order as `heatmap.species`)
  - Columns = valid windows (indices 0 to `valid_windows-1`)
- **Note**: Only includes valid windows (padding windows excluded)
- **Example**: `[[0.95, 0.87, 0.0, 0.12, 0.0, 0.0], ...]`

---

## 4. Branch Scores

#### `branch_scores`
- **Type**: `dict`
- **Description**: Raw scores from individual model branches for debugging/visualization

### Branch Scores Object

```json
{
  "proto": [...],
  "sed": [...],
  "final": [...],
  "species_indices": [...]
}
```

#### `branch_scores.proto`
- **Type**: `list[list[float]]`
- **Shape**: `[valid_windows, 234]`
- **Description**: ProtoSSM branch probabilities (before final blend)
- **Note**: Only includes valid windows

#### `branch_scores.sed`
- **Type**: `list[list[float]]`
- **Shape**: `[valid_windows, 234]`
- **Description**: SED (Sound Event Detection) branch probabilities (before final blend)
- **Note**: Only includes valid windows

#### `branch_scores.final`
- **Type**: `list[list[float]]`
- **Shape**: `[valid_windows, 234]`
- **Description**: Final blended probabilities (60% Proto + 40% SED)
- **Note**: Only includes valid windows

#### `branch_scores.species_indices`
- **Type**: `list[int]`
- **Description**: Indices of top 15 species across all branches (for frontend filtering)
- **Example**: `[45, 102, 23, 189, ...]`

---

## 5. Top Species

#### `top_species`
- **Type**: `list[dict]`
- **Length**: Up to 10
- **Description**: Ranked species based on detection metrics
- **Ranking**: By `windows_detected` (desc), then `mean_score` (desc), then `max_score` (desc)
- **Note**: Ranking only considers valid windows; padding windows excluded

### Top Species Object

```json
{
  "rank": int,
  "code": "string",
  "common_name": "string",
  "scientific_name": "string",
  "taxon": "string",
  "max_score": float,
  "mean_score": float,
  "windows_detected": int,
  "seconds_present": float
}
```

#### Fields

##### `rank`
- **Type**: `int`
- **Description**: Rank (1-10)
- **Example**: `1`

##### `code`, `common_name`, `scientific_name`, `taxon`
- Same as defined in Prediction Object above

##### `max_score`
- **Type**: `float`
- **Range**: `[0.0, 1.0]`
- **Description**: Highest score across all windows for this species
- **Example**: `0.98`

##### `mean_score`
- **Type**: `float`
- **Range**: `[0.0, 1.0]`
- **Description**: Average score across valid windows where species appeared
- **Calculation**: Mean of non-zero scores in valid windows
- **Example**: `0.76`

##### `windows_detected`
- **Type**: `int`
- **Range**: `[0, valid_windows]`
- **Description**: Number of valid windows where score ≥ per-class threshold
- **Example**: `5`

##### `seconds_present`
- **Type**: `float`
- **Calculation**: `min(windows_detected * 5, real_duration_sec)`
- **Description**: Duration across all detected windows (capped by real audio length)
- **Example**: `25.0` (5 windows × 5 sec = 25 sec)
- **Note**: Never exceeds `real_duration_sec`

---

## 6. Waveform Peaks

#### `waveform_peaks`
- **Type**: `list[float]`
- **Length**: 1000
- **Range**: `[0.0, 1.0]`
- **Description**: Normalized max-abs amplitude per time bucket
- **Calculation**: 
  1. Divide real audio into 1000 equal buckets
  2. Compute max-abs amplitude in each bucket
  3. Normalize by global max (0.0-1.0)
- **Use**: Audio visualization (e.g., waveform display in frontend)
- **Example**: `[0.05, 0.12, 0.87, 0.95, 0.43, ...]`

---

## Example Response (28-second clip)

```json
{
  "real_duration_sec": 28.5,
  "n_windows": 12,
  "n_classes": 234,
  "valid_windows": 6,
  "windows": [
    {
      "index": 0,
      "start_sec": 0,
      "end_sec": 5,
      "is_padding": false,
      "top_k": [
        {
          "code": "whtdov",
          "common_name": "White Dove",
          "scientific_name": "Columba palumbus",
          "taxon": "Aves",
          "score": 0.92
        },
        {
          "code": "barswa",
          "common_name": "Barn Swallow",
          "scientific_name": "Hirundo rustica",
          "taxon": "Aves",
          "score": 0.43
        }
      ]
    },
    {
      "index": 1,
      "start_sec": 5,
      "end_sec": 10,
      "is_padding": false,
      "top_k": [...]
    },
    ...
    {
      "index": 6,
      "start_sec": 30,
      "end_sec": 35,
      "is_padding": true,
      "top_k": []
    },
    ...
    {
      "index": 11,
      "start_sec": 55,
      "end_sec": 60,
      "is_padding": true,
      "top_k": []
    }
  ],
  "heatmap": {
    "species": [
      {
        "code": "whtdov",
        "common_name": "White Dove",
        "scientific_name": "Columba palumbus",
        "taxon": "Aves"
      },
      {
        "code": "barswa",
        "common_name": "Barn Swallow",
        "scientific_name": "Hirundo rustica",
        "taxon": "Aves"
      }
    ],
    "matrix": [
      [0.92, 0.87, 0.0, 0.15, 0.0, 0.0],
      [0.43, 0.38, 0.12, 0.0, 0.0, 0.0]
    ]
  },
  "branch_scores": {
    "proto": [...],
    "sed": [...],
    "final": [...],
    "species_indices": [45, 102, ...]
  },
  "top_species": [
    {
      "rank": 1,
      "code": "whtdov",
      "common_name": "White Dove",
      "scientific_name": "Columba palumbus",
      "taxon": "Aves",
      "max_score": 0.92,
      "mean_score": 0.49,
      "windows_detected": 2,
      "seconds_present": 10.0
    },
    {
      "rank": 2,
      "code": "barswa",
      "common_name": "Barn Swallow",
      "scientific_name": "Hirundo rustica",
      "taxon": "Aves",
      "max_score": 0.43,
      "mean_score": 0.31,
      "windows_detected": 3,
      "seconds_present": 15.0
    }
  ],
  "waveform_peaks": [0.05, 0.12, 0.87, 0.95, ...]
}
```

---

## Frontend Integration Notes

### Padding Detection
- **Use `is_padding` flag** to visually distinguish real audio from padding in the UI
- **Exclude padding windows** from any aggregate statistics
- **Show "No data" or fade** padding windows in timeline visualizations

### Top Species Ranking
- **Sort frontend by `windows_detected`** (descending), then by `mean_score`
- **Display all three metrics**: max_score, mean_score, windows_detected
- **Use `seconds_present`** to show "Detected in X seconds of audio"

### Heatmap Visualization
- **X-axis**: Valid windows (0 to `valid_windows-1`)
- **Y-axis**: Detected species (rows in `heatmap.matrix`)
- **Color**: Score value (0.0 = white, 1.0 = dark)
- **Click to expand**: Show full species name on hover

### Waveform
- **Use `waveform_peaks`** to draw a simplified waveform
- **Draw only up to `real_duration_sec`** or use `valid_windows * 5` seconds on the x-axis
- **Overlay** with detections (e.g., rectangles at detected windows)

### Branch Scores
- **Optional "Advanced" tab** showing `branch_scores` side-by-side
- **Highlight species** in `species_indices` for quick comparison
- **Useful for debugging** model outputs

---

## Backward Compatibility

Old fields (if referenced elsewhere):
- ❌ `top_predictions` → ✅ Use `top_species` instead
- ❌ `window_predictions` → ✅ Use `windows[].top_k` instead
- ❌ `file_scores` → ✅ Use `branch_scores.final` or compute max per species

---

## Status Codes

- **200 OK**: Successful prediction
- **400 Bad Request**: Invalid `site_id` or `hour_id`
- **422 Unprocessable Entity**: Invalid audio file format
- **500 Internal Server Error**: Model inference failure

---

## Performance Notes

- Response size: ~500 KB - 2 MB (depending on number of detected species)
- Branch scores can be large; consider lazy-loading in frontend if needed
- Waveform peaks are pre-computed (efficient)
- Heatmap matrix only includes detected species (smaller than 234 × 12)

