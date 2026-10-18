from pathlib import Path
from typing import Dict, Any, List, Optional
import polars as pl
import numpy as np
from app.schemas.dataset import ColumnSummary, DataQualitySummary, QualityWarning

class PolarsTool:
    @staticmethod
    def load_frame(file_path: Path, file_format: str) -> pl.DataFrame:
        """Load dataset into a Polars DataFrame safely."""
        if file_format == "csv":
            return pl.read_csv(file_path, infer_schema_length=10000, ignore_errors=True)
        elif file_format == "parquet":
            return pl.read_parquet(file_path)
        elif file_format in ["xlsx", "xls"]:
            import pandas as pd
            df_pd = pd.read_excel(file_path)
            return pl.from_pandas(df_pd)
        else:
            raise ValueError(f"Unsupported format: {file_format}")

    @classmethod
    def profile_dataset(cls, file_path: Path, file_format: str) -> tuple[List[ColumnSummary], DataQualitySummary, List[Dict[str, Any]]]:
        """Generate comprehensive column profiles, quality metrics, and sample rows."""
        df = cls.load_frame(file_path, file_format)
        total_rows = len(df)
        total_cols = len(df.columns)
        
        # Calculate duplicate rows
        duplicate_rows = total_rows - len(df.unique()) if total_rows > 0 else 0
        duplicate_pct = round((duplicate_rows / total_rows) * 100, 2) if total_rows > 0 else 0.0

        column_summaries: List[ColumnSummary] = []
        warnings: List[QualityWarning] = []
        total_null_cells = 0

        for col_name in df.columns:
            series = df[col_name]
            null_count = series.null_count()
            total_null_cells += null_count
            null_pct = round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
            unique_count = series.n_unique()
            
            # Non-null samples
            valid_series = series.drop_nulls()
            sample_vals = [cls._sanitize_val(v) for v in valid_series.head(5).to_list()]
            
            col_type = str(series.dtype)
            is_numeric = series.dtype.is_numeric()

            min_val, max_val, mean_val, std_val, median_val = None, None, None, None, None
            q25_val, q75_val, outlier_count = None, None, 0

            if is_numeric and len(valid_series) > 0:
                try:
                    min_val = float(valid_series.min()) if valid_series.min() is not None else None
                    max_val = float(valid_series.max()) if valid_series.max() is not None else None
                    mean_val = round(float(valid_series.mean()), 4) if valid_series.mean() is not None else None
                    std_val = round(float(valid_series.std()), 4) if valid_series.std() is not None else None
                    median_val = round(float(valid_series.median()), 4) if valid_series.median() is not None else None
                    q25_val = round(float(valid_series.quantile(0.25)), 4) if valid_series.quantile(0.25) is not None else None
                    q75_val = round(float(valid_series.quantile(0.75)), 4) if valid_series.quantile(0.75) is not None else None

                    # Outlier calculation via IQR rule
                    if q25_val is not None and q75_val is not None:
                        iqr = q75_val - q25_val
                        if iqr > 0:
                            lower_bound = q25_val - 1.5 * iqr
                            upper_bound = q75_val + 1.5 * iqr
                            outlier_filter = valid_series.filter((valid_series < lower_bound) | (valid_series > upper_bound))
                            outlier_count = len(outlier_filter)
                            if outlier_count > 0:
                                warnings.append(QualityWarning(
                                    severity="info",
                                    column=col_name,
                                    message=f"{outlier_count} potential outlier(s) detected via 1.5*IQR rule in '{col_name}'.",
                                    suggestion="Check if values reflect rare transactions or data entry anomalies."
                                ))
                except Exception:
                    pass
            elif not is_numeric:
                # String / Categorical column warnings
                if unique_count == total_rows and total_rows > 10:
                    warnings.append(QualityWarning(
                        severity="info",
                        column=col_name,
                        message=f"Column '{col_name}' has 100% unique values (possible unique ID/primary key).",
                        suggestion="Avoid using high-cardinality IDs as aggregation categories."
                    ))
                elif unique_count == 1 and total_rows > 1:
                    warnings.append(QualityWarning(
                        severity="warning",
                        column=col_name,
                        message=f"Column '{col_name}' contains only 1 constant value across all rows.",
                        suggestion="Consider dropping constant columns as they provide zero variance."
                    ))

            # Missing value warnings
            if null_pct > 30.0:
                warnings.append(QualityWarning(
                    severity="critical" if null_pct > 60.0 else "warning",
                    column=col_name,
                    message=f"High missingness in '{col_name}': {null_pct}% missing ({null_count}/{total_rows} rows).",
                    suggestion="Impute missing data or filter nulls before training or deep aggregations."
                ))

            col_summary = ColumnSummary(
                name=col_name,
                data_type=col_type,
                null_count=null_count,
                null_percentage=null_pct,
                unique_count=unique_count,
                sample_values=sample_vals,
                min_val=min_val,
                max_val=max_val,
                mean=mean_val,
                std_dev=std_val,
                median=median_val,
                q25=q25_val,
                q75=q75_val,
                outlier_count=outlier_count
            )
            column_summaries.append(col_summary)

        # Duplicate row warning
        if duplicate_pct > 0.0:
            warnings.append(QualityWarning(
                severity="warning" if duplicate_pct > 5.0 else "info",
                message=f"Found {duplicate_rows} duplicate row(s) ({duplicate_pct}% of dataset).",
                suggestion="Verify if identical records reflect multiple valid events or ingestion duplicates."
            ))

        # Overall Quality Score Calculation (0-100)
        total_cells = total_rows * total_cols if (total_rows * total_cols) > 0 else 1
        missing_cells_pct = round((total_null_cells / total_cells) * 100, 2)
        score = 100.0 - (missing_cells_pct * 0.6) - (duplicate_pct * 0.4)
        overall_score = max(0.0, min(100.0, round(score, 1)))

        quality_report = DataQualitySummary(
            overall_score=overall_score,
            total_rows=total_rows,
            total_columns=total_cols,
            duplicate_rows=duplicate_rows,
            duplicate_percentage=duplicate_pct,
            total_missing_cells=total_null_cells,
            missing_cells_percentage=missing_cells_pct,
            warnings=warnings
        )

        # Sample rows (first 100 rows formatted as dicts)
        sample_df = df.head(100)
        sample_rows = [
            {k: cls._sanitize_val(v) for k, v in row.items()}
            for row in sample_df.to_dicts()
        ]

        return column_summaries, quality_report, sample_rows

    @classmethod
    def compute_correlations(cls, file_path: Path, file_format: str) -> Dict[str, Any]:
        """Compute Pearson correlation matrix across all numeric columns."""
        df = cls.load_frame(file_path, file_format)
        numeric_cols = [c for c in df.columns if df[c].dtype.is_numeric()]
        if len(numeric_cols) < 2:
            return {"columns": numeric_cols, "matrix": []}

        corr_df = df.select(numeric_cols).corr()
        matrix = []
        for row in corr_df.to_dicts():
            cleaned_row = {k: round(v, 4) if v is not None and not np.isnan(v) else 0.0 for k, v in row.items()}
            matrix.append(cleaned_row)

        return {"columns": numeric_cols, "matrix": matrix}

    @staticmethod
    def _sanitize_val(val: Any) -> Any:
        """Sanitize non-serializable objects (NaT, NaN, dates)."""
        if val is None:
            return None
        if hasattr(val, "isoformat"):
            return val.isoformat()
        if isinstance(val, (float, np.floating)):
            if np.isnan(val) or np.isinf(val):
                return None
            return float(val)
        return val

polars_tool = PolarsTool()
