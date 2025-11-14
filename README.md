# Data Quality Monitoring System

A comprehensive, production-ready data quality monitoring system with automated quality checks, real-time alerting, and interactive dashboards. Built with enterprise-grade deduplication algorithms and quality metrics based on Private Banking best practices.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![React](https://img.shields.io/badge/react-18.2-blue.svg)

## Features

### Core Data Quality Dimensions

- **Completeness**: Missing value detection, null rate analysis, empty string checks
- **Accuracy**: Data type validation, range checks, format validation (email, phone, dates)
- **Consistency**: Cross-field validation, case consistency, date format standardization
- **Uniqueness**: Exact and fuzzy duplicate detection with configurable matching
- **Validity**: Business rule validation, domain constraint checks

### Advanced Deduplication

Based on industry best practices from financial data management:

- **Exact Matching**: Hash-based duplicate detection
- **Fuzzy Matching**: String similarity algorithms (Levenshtein, token sort ratio)
- **Phonetic Matching**: Sound-alike name detection (useful for customer records)
- **Blocking**: Efficient comparison grouping for large datasets
- **Merge Strategies**: First, last, or best (most complete) record retention

### Monitoring & Alerting

- **Real-time Quality Scoring**: Overall and dimension-specific scores
- **Trend Analysis**: Historical quality tracking with 30-day history
- **Configurable Alerts**: Custom thresholds with severity levels (Info, Warning, Critical)
- **Alert Management**: Acknowledgment and trend tracking
- **Recommendations**: Automated actionable insights based on quality issues

### Interactive Dashboard

- **Quality Score Visualization**: Real-time scoring with trend indicators
- **Dimension Breakdown**: Individual quality dimension analysis
- **Historical Trends**: Time-series charts for quality metrics
- **Data Profiling**: Comprehensive statistical analysis
- **Alert Management**: View and acknowledge quality alerts

## Architecture

```
data-quality-monitoring-system/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── core/              # Core quality engine & deduplication
│   │   ├── models/            # Pydantic data models
│   │   ├── services/          # Business logic services
│   │   └── main.py            # FastAPI application
│   └── requirements.txt
├── frontend/                   # React TypeScript dashboard
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Application pages
│   │   ├── services/          # API client
│   │   └── types/             # TypeScript types
│   └── package.json
├── data/                       # Data storage
│   ├── sample/                # Sample datasets
│   └── quality_metrics.db     # SQLite metrics database
└── docs/                       # Documentation

```

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd data-quality-monitoring-system
```

2. **Install uv (Recommended - Fast Python Package Manager)**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or use pip
pip install uv
```

3. **Backend Setup**
```bash
cd backend

# Using uv (recommended - much faster!)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt

# Or using traditional pip
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. **Frontend Setup**
```bash
cd frontend
npm install
```

### Running the Application

1. **Start the Backend** (from backend directory)
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

2. **Start the Frontend** (from frontend directory)
```bash
npm run dev
```

The dashboard will be available at `http://localhost:3000`

### Quick Test with Sample Data

1. Navigate to `http://localhost:3000`
2. Click "Upload" in the navigation
3. Upload one of the sample datasets from `data/sample/`:
   - `customer_accounts.csv` - Banking customer accounts with duplicates
   - `transactions.csv` - Transaction data with quality issues
4. View the automatically generated quality assessment

## API Endpoints

### Datasets
- `POST /api/datasets/upload` - Upload a dataset
- `GET /api/datasets` - List all datasets
- `GET /api/datasets/{dataset_id}` - Get dataset details

### Quality Assessment
- `POST /api/assess/{dataset_id}` - Run quality assessment
- `GET /api/assess/{dataset_id}/history` - Get quality history
- `GET /api/assess/{dataset_id}/trends` - Get trend analysis

### Data Profiling
- `GET /api/profile/{dataset_id}` - Generate dataset profile

### Deduplication
- `POST /api/deduplication/{dataset_id}` - Find duplicates
- `POST /api/deduplication/{dataset_id}/merge` - Merge duplicates

### Alerts
- `GET /api/alerts` - Get alerts with filtering
- `POST /api/alerts/{alert_id}/acknowledge` - Acknowledge alert
- `GET /api/alerts/summary` - Get alert summary
- `GET /api/alerts/trends` - Get alert trends

### Reports
- `GET /api/reports/{dataset_id}` - Generate comprehensive report

## Data Quality Metrics

### Completeness (25% weight)
- Overall completeness rate
- Per-column completeness
- Empty string detection

### Accuracy (25% weight)
- Data type consistency
- Numeric range validation (outlier detection)
- Format validation (email, phone, dates)

### Consistency (20% weight)
- Case consistency
- Date format consistency
- Cross-field validation (e.g., start_date < end_date)

### Uniqueness (15% weight)
- Row-level duplicate detection
- Column-level uniqueness analysis

### Validity (15% weight)
- Business rule compliance
- Domain constraint validation
- Negative value checks for amount fields

## Use Cases

### Financial Services
- Customer data deduplication
- Account data quality monitoring
- Transaction data validation
- Regulatory compliance reporting

### Healthcare
- Patient record quality
- Duplicate patient identification
- Data integrity monitoring

### E-commerce
- Product data quality
- Customer database cleanup
- Order data validation

### General
- Data migration quality checks
- ETL pipeline monitoring
- Master data management

## Configuration

### Quality Rules

Create custom quality rules programmatically:

```python
from app.models.data_quality import QualityRule, QualityDimension, AlertSeverity

rule = QualityRule(
    rule_id="rule_001",
    name="Email Completeness",
    dimension=QualityDimension.COMPLETENESS,
    description="Email field must be 95% complete",
    column="email",
    threshold=95.0,
    severity=AlertSeverity.WARNING,
    enabled=True
)
```

### Deduplication Settings

```python
from app.core.deduplication import DeduplicationEngine

# Configure fuzzy matching threshold (0-100)
dedup_engine = DeduplicationEngine(fuzzy_threshold=85)

# Find duplicates with multiple methods
duplicates = dedup_engine.find_duplicates(
    df,
    key_columns=['customer_name', 'email'],
    fuzzy_columns=['customer_name'],
    methods=['exact', 'fuzzy', 'phonetic']
)
```

## Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework
- **uv**: Ultra-fast Python package installer (10-100x faster than pip)
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computations
- **FuzzyWuzzy**: Fuzzy string matching
- **SQLite**: Metrics storage
- **Pydantic**: Data validation

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool
- **Axios**: HTTP client
- **Custom CSS**: Responsive styling

## Performance Considerations

### Data Quality Engine
- **Blocking**: Reduces O(n²) comparisons in fuzzy matching
- **Efficient Algorithms**: Optimized similarity calculations
- **Incremental Processing**: Suitable for large datasets
- **Caching**: Metrics stored for historical analysis

### Package Management with uv
- **10-100x faster** than pip for dependency installation
- **Disk space efficient**: Shared package cache across environments
- **Reliable**: Written in Rust with better dependency resolution
- **Drop-in replacement**: Works with existing requirements.txt and pyproject.toml
- **Fast virtual environments**: Creates venvs in milliseconds

## Best Practices

1. **Start with Exact Matching**: Run exact duplicate detection before fuzzy matching
2. **Adjust Fuzzy Threshold**: Lower values (70-80) for more matches, higher (85-95) for precision
3. **Use Blocking**: For datasets >10,000 records, blocking significantly improves performance
4. **Regular Monitoring**: Schedule daily quality assessments for critical datasets
5. **Set Appropriate Thresholds**: Align alert thresholds with business requirements

## Troubleshooting

### Common Issues

**Backend won't start**
- Ensure Python 3.9+ is installed
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check port 8000 is available

**Frontend won't start**
- Ensure Node.js 18+ is installed
- Delete `node_modules` and run `npm install` again
- Check port 3000 is available

**File upload fails**
- Verify file format (CSV, Excel, JSON supported)
- Check file size (large files may need increased limits)
- Ensure proper encoding (UTF-8 recommended)

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License.

## Acknowledgments

Built with industry best practices from:
- Private Banking data quality management
- Financial services deduplication techniques
- Enterprise data governance standards

## Support

For questions or issues, please open an issue on GitHub.

---

**Built with focus on data quality excellence**
