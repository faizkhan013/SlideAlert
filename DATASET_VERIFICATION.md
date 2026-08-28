# Landslide4Sense Dataset Extraction and Verification Report

This document records the verification of the extracted **Landslide4Sense** dataset archives in the workspace.

---

## 1. Dataset Archive Verification

Before extraction, the download archive integrity was checked:
- **`TrainData.zip`** exists, size: `2,484,071,934` bytes (~2.31 GB).
- **`ValidData.zip`** exists, size: `143,423,314` bytes (~136.77 MB).
- Both ZIP archives were extracted successfully without error using native Windows `tar` utility.
- The original ZIP archives are still kept in the directory.

---

## 2. Extracted Directory Structure

The directory structure inside the `D:\slideland\dataset\Landslide4Sense\` workspace is as follows:

```text
D:\slideland\dataset\Landslide4Sense\
├── TrainData.zip                       # Original training zip archive
├── ValidData.zip                       # Original validation zip archive
├── TrainData/                          # Extracted training dataset
│   ├── img/                            # 14-band remote sensing image files (.h5)
│   └── mask/                           # Binary landslide ground truth masks (.h5)
└── ValidData/                          # Extracted validation dataset
    ├── img/                            # 14-band remote sensing validation image files (.h5)
    └── mask/                           # Binary landslide validation masks (.h5)
```

*Note: The validation archive `ValidData.zip` did contain a `mask/` directory with 245 corresponding `.h5` files, making it a labeled validation set.*

---

## 3. Dataset Counts and Extensions

- **Training Image Count** (`TrainData/img/`): `3,799` files
- **Training Mask Count** (`TrainData/mask/`): `3,799` files
- **Validation Image Count** (`ValidData/img/`): `245` files
- **Validation Mask Count** (`ValidData/mask/`): `245` files
- **File Extensions**: All files in the folders have the `.h5` extension.

---

## 4. Image-Mask Pairing Verification

A Python script was executed to verify the pairing of image and mask files based on their index naming convention.
- **Naming Pattern**: `image_x.h5` in `img/` maps to `mask_x.h5` in `mask/`.
- **Results**:
  - `Train mismatched`: `set()` (0 mismatches - every image has its corresponding mask file).
  - `Valid mismatched`: `set()` (0 mismatches - every image has its corresponding mask file).

---

## 5. Example Filenames

### TrainData/img/
1. `image_1.h5`
2. `image_10.h5`
3. `image_100.h5`
4. `image_1000.h5`
5. `image_1001.h5`

### TrainData/mask/
1. `mask_1.h5`
2. `mask_10.h5`
3. `mask_100.h5`
4. `mask_1000.h5`
5. `mask_1001.h5`

### ValidData/img/
1. `image_1.h5`
2. `image_10.h5`
3. `image_100.h5`
4. `image_101.h5`
5. `image_102.h5`

### ValidData/mask/
1. `mask_1.h5`
2. `mask_10.h5`
3. `mask_100.h5`
4. `mask_101.h5`
5. `mask_102.h5`

---

## 6. Extraction Errors & Problems Found

- No extraction errors were encountered.
- No naming discrepancies or corrupt files were found.

---

## Status

DATASET VERIFIED — READY FOR PREPROCESSING
