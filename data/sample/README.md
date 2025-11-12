# Sample Datasets

This directory contains sample datasets designed to demonstrate the Data Quality Monitoring System's capabilities.

## Available Datasets

### 1. customer_accounts.csv

**Description**: Banking customer account information with intentional quality issues

**Size**: 30 records, 10 columns

**Data Quality Issues**:
- **Duplicates**: Contains exact duplicates (ACC001/ACC004, ACC003/ACC015)
- **Missing Values**: Some phone numbers and balances are missing
- **Invalid Data**: One account (ACC024) has a negative balance
- **Inconsistent Status**: Mix of Active/Inactive/Closed statuses

**Columns**:
- `account_id`: Unique account identifier
- `customer_name`: Customer full name
- `email`: Customer email address
- `phone`: Phone number (some missing)
- `account_type`: Savings, Checking, or Investment
- `balance`: Account balance (some missing, one negative)
- `open_date`: Account opening date
- `status`: Account status
- `branch_code`: Branch identifier
- `customer_id`: Customer identifier

**Expected Quality Score**: ~85-90%

**Key Findings**:
- Completeness: ~95% (missing phones and balances)
- Accuracy: ~90% (negative balance issue)
- Uniqueness: ~93% (2 duplicate pairs)
- Consistency: ~95%
- Validity: ~96%

### 2. transactions.csv

**Description**: Financial transaction data with various quality issues

**Size**: 40 records, 9 columns

**Data Quality Issues**:
- **Missing Values**: Some amounts and merchant names are missing
- **Inconsistent Dates**: One transaction (TXN034) has inconsistent dates (transaction_date vs processed_date)
- **Invalid Amounts**: One transaction (TXN024) has a negative amount
- **Missing Processed Dates**: Some transactions lack processed_date
- **Empty Categories**: One transaction (TXN015) has empty merchant_name

**Columns**:
- `transaction_id`: Unique transaction identifier
- `account_id`: Reference to customer account
- `transaction_date`: Date of transaction
- `amount`: Transaction amount
- `transaction_type`: Debit, Credit, or Transfer
- `merchant_name`: Merchant or source/destination
- `category`: Transaction category
- `status`: Completed, Pending, or Failed
- `processed_date`: Date transaction was processed

**Expected Quality Score**: ~80-85%

**Key Findings**:
- Completeness: ~88% (missing amounts, dates, merchant names)
- Accuracy: ~85% (date inconsistencies, negative amount)
- Consistency: ~90% (date format issues)
- Uniqueness: ~100% (no duplicates)
- Validity: ~92%

## Using the Sample Data

### Quick Start

1. **Start the Application**
   ```bash
   ./start.sh
   ```

2. **Upload a Dataset**
   - Navigate to http://localhost:3000
   - Click "Upload" in the navigation
   - Select `customer_accounts.csv` or `transactions.csv`
   - Click "Upload and Assess"

3. **View Results**
   - Review the quality score dashboard
   - Explore dimension-specific metrics
   - Check for alerts
   - View duplicate records (for customer_accounts.csv)

### Expected Alerts

#### customer_accounts.csv
- Warning: Duplicate records detected
- Warning: Missing phone numbers in several records
- Critical: Negative balance in account ACC024

#### transactions.csv
- Warning: Missing transaction amounts
- Warning: Missing processed dates
- Critical: Invalid negative amount in TXN024
- Warning: Date inconsistency in TXN034

## Deduplication Examples

### Exact Duplicates (customer_accounts.csv)

Use the API or UI to find exact duplicates:

```bash
curl -X POST "http://localhost:8000/api/deduplication/DATASET_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "DATASET_ID",
    "methods": ["exact"]
  }'
```

Expected: 2 duplicate groups (4 total duplicate records)

### Fuzzy Duplicates (customer_accounts.csv)

Test fuzzy matching on customer names:

```bash
curl -X POST "http://localhost:8000/api/deduplication/DATASET_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "DATASET_ID",
    "fuzzy_columns": ["customer_name"],
    "methods": ["fuzzy"]
  }'
```

This will detect near-matches like "John Smith" and "John Smith " (with trailing space).

## Creating Custom Sample Data

To create your own sample datasets for testing:

1. Include intentional quality issues:
   - Missing values (nulls, empty strings)
   - Duplicates (exact and near-matches)
   - Invalid values (negative amounts, future dates)
   - Format inconsistencies (date formats, case)
   - Data type mismatches

2. Supported formats:
   - CSV (recommended)
   - Excel (.xlsx, .xls)
   - JSON

3. Best practices:
   - Include 20-100 records for testing
   - Mix of good and bad data
   - Multiple quality dimensions affected
   - Real-world scenarios (banking, retail, healthcare)

## Understanding the Quality Scores

### Score Ranges

- **90-100%**: Excellent - Production-ready data quality
- **70-89%**: Good - Minor issues, suitable for most use cases
- **50-69%**: Fair - Moderate issues, requires attention
- **0-49%**: Poor - Significant issues, remediation needed

### Dimension Weights

- Completeness: 25%
- Accuracy: 25%
- Consistency: 20%
- Uniqueness: 15%
- Validity: 15%

The overall score is a weighted average of all dimensions.

## Advanced Testing

### Test Different Scenarios

1. **Clean Data**: Create a perfect dataset with no issues
2. **Extremely Poor Quality**: Dataset with 50%+ missing values
3. **Large Dataset**: Test performance with 10,000+ records
4. **Complex Duplicates**: Test fuzzy matching with similar names
5. **Multi-column Validation**: Cross-field consistency checks

### Performance Testing

```bash
# Generate large dataset
python -c "
import pandas as pd
import numpy as np

df = pd.DataFrame({
    'id': range(10000),
    'name': ['Customer ' + str(i) for i in range(10000)],
    'value': np.random.randn(10000) * 100
})
df.to_csv('large_dataset.csv', index=False)
"

# Upload and assess
curl -X POST -F "file=@large_dataset.csv" http://localhost:8000/api/datasets/upload
```

## Troubleshooting

**Dataset won't upload**
- Check file format (CSV, Excel, JSON only)
- Verify file size (default max: 10MB)
- Ensure UTF-8 encoding for CSV files

**Unexpected quality scores**
- Review the metrics breakdown
- Check the details in each metric
- Consider the weighted scoring system

**No duplicates found**
- Verify exact match criteria
- Try fuzzy matching with lower threshold (70-80)
- Check that key columns are specified correctly
