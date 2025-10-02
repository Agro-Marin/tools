"""
CSV Manager for Field/Method Changes
====================================

Handles reading, writing, and deduplication of CSV files containing
field and method rename records.
"""

import csv
import logging
from pathlib import Path

from core.models import RenameCandidate
from config.settings import CSV_ENCODING, CSV_HEADERS, VALID_ITEM_TYPES

logger = logging.getLogger(__name__)


class CSVManager:
    """Manager for CSV operations with deduplication and validation"""

    def __init__(self, csv_file_path: str):
        """
        Initialize CSV manager.

        Args:
            csv_file_path: Path to the CSV file
        """
        self.csv_file_path = Path(csv_file_path)
        self.headers = CSV_HEADERS
        self.encoding = CSV_ENCODING
        self.existing_records = []
        self.existing_record_keys = set()

    def _clean_csv_row(self, row: dict[str, str]) -> dict[str, str]:
        """Clean CSV row data"""
        cleaned = {}
        for header in self.headers:
            value = row.get(header, "").strip()
            cleaned[header] = value
        return cleaned

    def _validate_csv_row(self, row: dict[str, str], row_num: int) -> bool:
        """Validate CSV row data"""
        # Check required fields
        required_fields = ["old_name", "new_name"]
        for field in required_fields:
            if not row.get(field):
                logger.warning(f"Row {row_num}: Missing required field '{field}'")
                return False

        # Check for obvious duplicates within the row
        if row["old_name"] == row["new_name"]:
            logger.warning(
                f"Row {row_num}: old_name and new_name are identical: {row['old_name']}"
            )
            return False

        # Validate item_type if present
        item_type = row.get("item_type", "").strip()
        if item_type and item_type not in VALID_ITEM_TYPES:
            logger.warning(
                f"Row {row_num}: Invalid item_type '{item_type}'. Valid types: {VALID_ITEM_TYPES}"
            )
            return False

        return True

    def _create_record_key(self, record: dict[str, str]) -> str:
        """Create unique key for record deduplication"""
        return f"{record['old_name']}→{record['new_name']}:{record.get('item_type', '')}:{record.get('module', '')}:{record.get('model', '')}"

    def filter_new_candidates(
        self, candidates: list[RenameCandidate]
    ) -> tuple[list[RenameCandidate], list[RenameCandidate]]:
        """
        Filter candidates to separate new ones from existing ones.

        Args:
            candidates: List of rename candidates

        Returns:
            Tuple of (new_candidates, duplicate_candidates)
        """
        new_candidates = []
        duplicate_candidates = []

        for candidate in candidates:
            record_key = self._create_record_key_from_candidate(candidate)

            if record_key in self.existing_record_keys:
                duplicate_candidates.append(candidate)
                logger.debug(
                    f"Duplicate candidate found: {candidate.old_name} → {candidate.new_name}"
                )
            else:
                new_candidates.append(candidate)

        logger.info(
            f"Filtered {len(new_candidates)} new candidates, skipped {len(duplicate_candidates)} duplicates"
        )

        return new_candidates, duplicate_candidates

    def _create_record_key_from_candidate(self, candidate: RenameCandidate) -> str:
        """Create record key from rename candidate"""
        return f"{candidate.old_name}→{candidate.new_name}:{candidate.item_type}:{candidate.module}:{candidate.model}"

    def _create_backup(self) -> Path | None:
        """Create backup of existing CSV file"""
        if not self.csv_file_path.exists():
            return None

        # Create backup filename with timestamp
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.csv_file_path.with_suffix(f".backup_{timestamp}.csv")

        try:
            import shutil

            shutil.copy2(self.csv_file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.warning(f"Could not create backup: {e}")
            return None

    def validate_csv_integrity(self) -> dict[str, any]:
        """
        Validate CSV file integrity and return statistics.

        Returns:
            Dictionary with validation results and statistics
        """
        if not self.csv_file_path.exists():
            return {"exists": False, "valid": False, "error": "File does not exist"}

        try:
            with open(
                self.csv_file_path, "r", encoding=self.encoding, newline=""
            ) as csvfile:
                reader = csv.DictReader(csvfile)

                # Check headers
                headers_valid = reader.fieldnames == self.headers

                # Count records and check for issues
                total_records = 0
                valid_records = 0
                duplicate_keys = set()
                duplicates_found = 0
                issues = []

                for row_num, row in enumerate(reader, start=2):
                    total_records += 1

                    # Clean row
                    cleaned_row = self._clean_csv_row(row)

                    # Validate row
                    if self._validate_csv_row(cleaned_row, row_num):
                        valid_records += 1

                        # Check for duplicates
                        record_key = self._create_record_key(cleaned_row)
                        if record_key in duplicate_keys:
                            duplicates_found += 1
                            issues.append(
                                f"Row {row_num}: Duplicate record - {record_key}"
                            )
                        else:
                            duplicate_keys.add(record_key)
                    else:
                        issues.append(f"Row {row_num}: Invalid record")

                return {
                    "exists": True,
                    "valid": headers_valid and valid_records == total_records,
                    "headers_valid": headers_valid,
                    "total_records": total_records,
                    "valid_records": valid_records,
                    "duplicate_records": duplicates_found,
                    "issues": issues,
                    "file_size": self.csv_file_path.stat().st_size,
                }

        except Exception as e:
            return {"exists": True, "valid": False, "error": str(e)}

    def export_candidates_report(
        self, candidates: list[RenameCandidate], report_file: str
    ) -> bool:
        """
        Export detailed candidates report to CSV.

        Args:
            candidates: List of rename candidates
            report_file: Path to report file

        Returns:
            True if successful
        """
        if not candidates:
            logger.warning("No candidates to export")
            return False

        # Extended headers for detailed report
        extended_headers = [
            "old_name",
            "new_name",
            "module",
            "model",
            "type",
            "confidence",
            "signature_match",
            "rule_applied",
            "file_path",
        ]

        try:
            report_path = Path(report_file)
            report_path.parent.mkdir(parents=True, exist_ok=True)

            with open(report_path, "w", encoding=self.encoding, newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=extended_headers)
                writer.writeheader()

                for candidate in candidates:
                    row = {
                        "old_name": candidate.old_name,
                        "new_name": candidate.new_name,
                        "module": candidate.module,
                        "model": candidate.model,
                        "type": candidate.item_type,
                        "confidence": f"{candidate.confidence:.3f}",
                        "signature_match": candidate.signature_match,
                        "rule_applied": candidate.rule_applied or "",
                        "file_path": candidate.file_path,
                    }
                    writer.writerow(row)

            logger.info(
                f"Exported detailed report with {len(candidates)} candidates to {report_path}"
            )
            return True

        except Exception as e:
            logger.error(f"Error exporting candidates report: {e}")
            return False

    def get_statistics(self) -> dict[str, any]:
        """Get statistics about current CSV data"""
        if not self.existing_records:
            return {
                "total_records": 0,
                "modules": {},
                "models": {},
                "field_changes": 0,
                "method_changes": 0,
            }

        modules = {}
        models = {}

        for record in self.existing_records:
            module = record.get("module", "unknown")
            model = record.get("model", "unknown")

            modules[module] = modules.get(module, 0) + 1
            models[model] = models.get(model, 0) + 1

        return {
            "total_records": len(self.existing_records),
            "unique_modules": len(modules),
            "unique_models": len(models),
            "modules": modules,
            "models": models,
            "file_path": str(self.csv_file_path),
            "file_exists": self.csv_file_path.exists(),
        }

    # CSV methods for cross-reference support

    CSV_HEADERS = [
        "change_id",
        "old_name",
        "new_name",
        "item_type",
        "module",
        "model",
        "change_scope",
        "impact_type",
        "context",
        "confidence",
        "parent_change_id",
        "validation_status",
    ]

    def write_csv(self, candidates: list[RenameCandidate], filename: str = None) -> int:
        """
        Write candidates with cross-reference structure.

        Args:
            candidates: List of RenameCandidate objects
            filename: Optional filename override

        Returns:
            Number of records written
        """
        if not candidates:
            logger.info("No candidates to write to enhanced CSV")
            return 0

        output_path = (
            Path(filename)
            if filename
            else self.csv_file_path.with_suffix(".enhanced.csv")
        )

        # Group candidates by primary declaration and their impacts
        grouped = self._group_by_declaration(candidates)

        rows = []
        for change_id, (primary_change, impacts) in grouped.items():
            # Primary declaration first
            rows.append(self._candidate_to_csv_row(primary_change))

            # Impact changes sorted by confidence (highest first)
            sorted_impacts = sorted(impacts, key=lambda x: x.confidence, reverse=True)
            for impact in sorted_impacts:
                rows.append(self._candidate_to_csv_row(impact))

        try:
            # Ensure directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write CSV
            with open(output_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=self.CSV_HEADERS)
                writer.writeheader()
                writer.writerows(rows)

            logger.info(
                f"CSV written: {len(rows)} total records ({len(grouped)} declarations, {len(rows) - len(grouped)} impacts)"
            )

            return len(rows)

        except Exception as e:
            logger.error(f"Error writing CSV to {output_path}: {e}")
            raise

    def _group_by_declaration(self, candidates: list[RenameCandidate]) -> dict:
        """Group impact candidates by their primary declaration"""
        grouped = {}

        # Separar declaraciones primarias de impactos
        primary_changes = [c for c in candidates if c.impact_type == "primary"]
        impact_changes = [c for c in candidates if c.impact_type != "primary"]

        # Crear grupos con declaraciones primarias
        for primary in primary_changes:
            impacts = [
                i for i in impact_changes if i.parent_change_id == primary.change_id
            ]
            grouped[primary.change_id] = (primary, impacts)

        # Manejar impactos huérfanos (sin declaración primaria)
        for impact in impact_changes:
            if impact.parent_change_id not in grouped:
                # Crear entrada para impacto huérfano
                grouped[impact.change_id] = (impact, [])

        return grouped

    def _candidate_to_csv_row(self, candidate: RenameCandidate) -> dict:
        """Convert RenameCandidate to CSV row"""
        return {
            "change_id": candidate.change_id,
            "old_name": candidate.old_name,
            "new_name": candidate.new_name,
            "item_type": candidate.item_type,
            "module": candidate.module,
            "model": candidate.model,
            "change_scope": candidate.change_scope,
            "impact_type": candidate.impact_type,
            "context": candidate.context,
            "confidence": f"{candidate.confidence:.3f}",
            "parent_change_id": candidate.parent_change_id,
            "validation_status": candidate.validation_status,
        }

    def _deduplicate_candidates(
        self, candidates: list[RenameCandidate]
    ) -> list[RenameCandidate]:
        """
        Remove duplicate candidates based on all fields except change_id.

        When multiple candidates have identical values for all fields except change_id,
        only keep the first one encountered.

        Args:
            candidates: List of RenameCandidate objects

        Returns:
            List of unique candidates
        """
        seen_keys = set()
        unique_candidates = []

        for candidate in candidates:
            # Create a key from all fields except change_id
            key = (
                candidate.old_name,
                candidate.new_name,
                candidate.item_type,
                candidate.module,
                candidate.model,
                candidate.change_scope,
                candidate.impact_type,
                candidate.context,
                f"{candidate.confidence:.3f}",  # Format to match CSV output
                candidate.parent_change_id,
                candidate.validation_status,
            )

            if key not in seen_keys:
                seen_keys.add(key)
                unique_candidates.append(candidate)
            else:
                logger.debug(
                    f"Skipping duplicate candidate: {candidate.module}.{candidate.model}.{candidate.old_name} -> {candidate.new_name}"
                )

        return unique_candidates

    def write_candidates(self, candidates: list[RenameCandidate]) -> int:
        """
        Write candidates in enhanced format to the main CSV file.
        This is now the primary method for writing CSV output.

        Args:
            candidates: List of RenameCandidate objects

        Returns:
            Number of records written
        """
        # Create backup of existing file if it exists
        if self.csv_file_path.exists():
            self._create_backup()

        # Deduplicate candidates before writing
        deduplicated = self._deduplicate_candidates(candidates)

        if len(deduplicated) < len(candidates):
            logger.info(
                f"Deduplicated {len(candidates) - len(deduplicated)} duplicate candidates "
                f"({len(deduplicated)} unique candidates remaining)"
            )

        # Write directly to the main CSV file
        count = self.write_csv(deduplicated, str(self.csv_file_path))

        logger.info(f"CSV written: {count} records to {self.csv_file_path}")

        return count

    def read_csv(self, filename: str = None) -> list[RenameCandidate]:
        """Read candidates from CSV format"""
        csv_path = Path(filename) if filename else self.csv_file_path

        if not csv_path.exists():
            logger.warning(f"CSV file {csv_path} does not exist")
            return []

        candidates = []

        try:
            with open(csv_path, "r", encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file)

                # Validate headers
                if not reader.fieldnames or not all(
                    header in reader.fieldnames for header in self.CSV_HEADERS
                ):
                    logger.warning(
                        f"CSV headers don't match expected format. Expected: {self.CSV_HEADERS}"
                    )
                    logger.warning(f"Found: {reader.fieldnames}")

                for row_num, row in enumerate(reader, start=2):
                    try:
                        candidate = self._csv_row_to_candidate(row)

                        # Validate required fields
                        if not candidate.old_name or not candidate.new_name:
                            logger.warning(
                                f"Row {row_num}: Missing required field (old_name or new_name), skipping"
                            )
                            continue

                        if candidate.old_name == candidate.new_name:
                            logger.warning(
                                f"Row {row_num}: old_name and new_name are identical ({candidate.old_name}), skipping"
                            )
                            continue

                        candidates.append(candidate)
                    except Exception as e:
                        logger.error(f"Error parsing row {row_num}: {e}")
                        continue

            logger.info(f"Read {len(candidates)} candidates from CSV {csv_path}")
            return candidates

        except Exception as e:
            logger.error(f"Error reading CSV {csv_path}: {e}")
            return []

    def _csv_row_to_candidate(self, row: dict) -> RenameCandidate:
        """Convert CSV row to RenameCandidate with robust type conversion"""
        try:
            # Safe confidence conversion
            confidence_str = row.get("confidence", "0.0")
            confidence = float(confidence_str) if confidence_str else 0.0

            # Ensure confidence is within valid range
            confidence = max(0.0, min(1.0, confidence))

        except (ValueError, TypeError) as e:
            logger.warning(
                f"Invalid confidence value '{confidence_str}' in CSV row, using 0.0: {e}"
            )
            confidence = 0.0

        return RenameCandidate(
            change_id=row.get("change_id", "").strip(),
            old_name=row.get("old_name", "").strip(),
            new_name=row.get("new_name", "").strip(),
            item_type=row.get("item_type", "").strip(),
            module=row.get("module", "").strip(),
            model=row.get("model", "").strip(),
            change_scope=row.get("change_scope", "declaration").strip(),
            impact_type=row.get("impact_type", "primary").strip(),
            context=row.get("context", "").strip(),
            confidence=confidence,
            parent_change_id=row.get("parent_change_id", "").strip(),
            validation_status=row.get("validation_status", "pending").strip(),
        )
