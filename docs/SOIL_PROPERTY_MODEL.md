# Soil Property Approach

**CRITICAL: The current dataset has NO paired image→property labels.**

## What is Supported
- Soil type classification from RGB images (7 classes).

## What is NOT Supported
- Direct image-based prediction of pH, Nitrogen (N), Phosphorus (P), Potassium (K), moisture, organic carbon, and Electrical Conductivity (EC).

## Current Approach
- Literature-based reference ranges from ICAR, NBSS&LUP, and state agriculture universities.

## Source of Data
- `soil_property_ranges.json` with documented citations.

## Clear Labeling
- Every value is marked as `REFERENCE_RANGE` and never presented as a prediction.

## Property Status
For each property, the status is:
- **pH**: REFERENCE_RANGE (typical ranges per soil type from ICAR)
- **Nitrogen**: REFERENCE_RANGE
- **Phosphorus**: REFERENCE_RANGE
- **Potassium**: REFERENCE_RANGE
- **Moisture**: REFERENCE_RANGE
- **Organic Carbon**: REFERENCE_RANGE
- **Electrical Conductivity**: REFERENCE_RANGE

## Future Path
- If paired image-property datasets become available, the architecture supports regression heads for true prediction.

## Scientific Honesty
- The application distinguishes between image classification, reference ranges, and user-provided measurements.
