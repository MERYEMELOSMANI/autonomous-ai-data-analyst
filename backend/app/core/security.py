import re
from pathlib import Path
from typing import List, Optional, Tuple, Set
import sqlglot
from sqlglot import exp
from app.core.config import settings

FORBIDDEN_SQL_STATEMENTS = (
    exp.Drop,
    exp.Delete,
    exp.Insert,
    exp.Update,
    exp.Alter,
    exp.Command,
    exp.Create,
    exp.Pragma,
)

FORBIDDEN_FUNCTIONS = {
    "read_csv",
    "read_parquet",
    "read_json",
    "scan_csv",
    "scan_parquet",
    "write_csv",
    "copy",
    "attach",
    "detach",
    "load",
    "install",
    "query",
}

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"system\s*prompt\s*reveal",
    r"disregard\s+(all\s+)?guidelines",
    r"jailbreak",
]

def sanitize_filename(filename: str) -> str:
    """Sanitize uploaded filename to prevent directory traversal and special chars."""
    basename = Path(filename).name
    clean = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', basename)
    return clean

def validate_file_extension(filename: str) -> bool:
    """Check if file extension is among allowed list."""
    suffix = Path(filename).suffix.lower()
    return suffix in settings.ALLOWED_EXTENSIONS

def validate_sql_query(query: str, allowed_table: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate that a SQL query is strictly read-only SELECT and does not execute
    dangerous operations or touch unauthorized tables/files.
    """
    if not query or not query.strip():
        return False, "Query cannot be empty"

    # Quick regex checks for forbidden keywords
    normalized = query.strip().upper()
    if any(keyword in normalized for keyword in ["DROP ", "DELETE ", "INSERT ", "UPDATE ", "ALTER ", "ATTACH ", "DETACH ", "COPY ", "EXPORT ", "IMPORT "]):
        return False, "Dangerous SQL mutation keywords detected"

    try:
        parsed = sqlglot.parse(query, read="duckdb")
    except Exception as e:
        return False, f"SQL syntax error: {str(e)}"

    if not parsed or len(parsed) > 1:
        # Multiple queries not allowed to prevent query chaining injection
        return False, "Only a single SELECT statement is permitted"

    statement = parsed[0]
    if statement is None:
        return False, "Empty parsed statement"

    # Check if the statement is a Select statement
    if not isinstance(statement, exp.Select):
        return False, f"Statement must be a SELECT query, received: {type(statement).__name__}"

    # Check for forbidden statement types anywhere in the tree
    for node in statement.walk():
        if isinstance(node, FORBIDDEN_SQL_STATEMENTS):
            return False, f"Forbidden statement type detected: {type(node).__name__}"
        
        # Check forbidden functions
        if isinstance(node, exp.Anonymous):
            func_name = node.name.lower()
            if func_name in FORBIDDEN_FUNCTIONS:
                return False, f"Access to function '{func_name}' is forbidden for security"

    # Enforce allowed table name if specified
    if allowed_table:
        table_references: Set[str] = set()
        ctes: Set[str] = set()
        
        # Collect CTE aliases
        for with_clause in statement.find_all(exp.With):
            for cte in with_clause.expressions:
                if cte.alias:
                    ctes.add(cte.alias.lower())

        for tbl in statement.find_all(exp.Table):
            tbl_name = tbl.name.lower()
            table_references.add(tbl_name)

        # Remove CTEs from required allowed tables
        external_tables = table_references - ctes
        for t in external_tables:
            if t != allowed_table.lower():
                return False, f"Unauthorized table access: '{t}'. Only '{allowed_table}' is accessible."

    return True, None

def check_prompt_injection(user_input: str) -> Tuple[bool, Optional[str]]:
    """Check user text for known jailbreak or prompt injection attacks."""
    lowered = user_input.lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            return True, "Potential prompt injection or jailbreak attempt detected."
    return False, None
