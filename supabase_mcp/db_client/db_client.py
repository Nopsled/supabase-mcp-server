import urllib.parse
from dataclasses import dataclass
from typing import Any, Literal

import psycopg2
from psycopg2 import errors as psycopg2_errors
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from tenacity import retry, stop_after_attempt, wait_exponential

from supabase_mcp.db_client.db_safety_config import DbSafetyLevel
from supabase_mcp.exceptions import ConnectionError, PermissionError, QueryError
from supabase_mcp.logger import logger
from supabase_mcp.settings import Settings, settings
from supabase_mcp.validators import validate_transaction_control


@dataclass
class QueryResult:
    """Represents a query result with metadata."""

    rows: list[dict[str, Any]]
    count: int
    status: str


class SupabaseClient:
    """Connects to Supabase PostgreSQL database directly."""

    _instance = None  # Singleton instance

    def __init__(
        self,
        project_ref: str | None = None,
        db_password: str | None = None,
        settings_instance: Settings | None = None,
        _mode: Literal[DbSafetyLevel.RO, DbSafetyLevel.RW] = DbSafetyLevel.RO,  # Start
    ):
        """Initialize the PostgreSQL connection pool.

        Args:
            project_ref: Optional Supabase project reference. If not provided, will be taken from settings.
            db_password: Optional database password. If not provided, will be taken from settings.
            settings_instance: Optional Settings instance. If not provided, will use global settings.
        """
        self._pool = None
        self._settings = settings_instance or settings
        self.project_ref = project_ref or self._settings.supabase_project_ref
        self.db_password = db_password or self._settings.supabase_db_password
        self.db_url = self._get_db_url_from_supabase()
        self._mode = _mode

    def _get_db_url_from_supabase(self) -> str:
        """Create PostgreSQL connection string from settings."""
        encoded_password = urllib.parse.quote_plus(self.db_password)

        if self.project_ref.startswith("127.0.0.1"):
            # Local development
            return f"postgresql://postgres:{encoded_password}@{self.project_ref}/postgres"

        # Production Supabase
        return (
            f"postgresql://postgres.{self.project_ref}:{encoded_password}"
            f"@aws-0-{self._settings.supabase_region}.pooler.supabase.com:6543/postgres"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=15),
    )
    def _get_pool(self):
        """Get or create PostgreSQL connection pool with better error handling."""
        if self._pool is None:
            try:
                logger.debug(f"Creating connection pool for: {self.db_url.split('@')[1]}")
                self._pool = SimpleConnectionPool(
                    minconn=1,
                    maxconn=10,
                    cursor_factory=RealDictCursor,
                    dsn=self.db_url,
                )
                # Test the connection
                with self._pool.getconn() as conn:
                    self._pool.putconn(conn)
                logger.info("✓ Created PostgreSQL connection pool")
            except psycopg2.OperationalError as e:
                logger.error(f"Failed to connect to database: {e}")
                raise ConnectionError(f"Could not connect to database: {e}") from e
            except Exception as e:
                logger.exception("Unexpected error creating connection pool")
                raise ConnectionError(f"Unexpected connection error: {e}") from e
        return self._pool

    @classmethod
    def create(
        cls,
        project_ref: str | None = None,
        db_password: str | None = None,
        settings_instance: Settings | None = None,
    ) -> "SupabaseClient":
        """Create and return a configured SupabaseClient instance.

        Args:
            project_ref: Optional Supabase project reference
            db_password: Optional database password
            settings_instance: Optional Settings instance
        """
        if cls._instance is None:
            cls._instance = cls(
                project_ref=project_ref,
                db_password=db_password,
                settings_instance=settings_instance,
            )
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset the singleton instance cleanly"""
        if hasattr(cls, "_instance") and cls._instance is not None:
            # Close any connections if needed
            if hasattr(cls._instance, "close"):
                cls._instance.close()
            # Reset to None
            cls._instance = None

    def close(self):
        """Explicitly close the connection pool."""
        if self._pool is not None:
            try:
                self._pool.closeall()
                self._pool = None
                logger.info("Closed PostgreSQL connection pool")
            except Exception as e:
                logger.error(f"Error closing connection pool: {e}")

    @property
    def mode(self) -> DbSafetyLevel:
        """Current operation mode"""
        return self._mode

    def switch_mode(self, mode: Literal[DbSafetyLevel.RO, DbSafetyLevel.RW]) -> None:
        """Switch the database connection mode."""
        self._mode = mode
        logger.info(f"Switched to {self.mode.value} mode")

    def execute_query(self, query: str, params: tuple = None) -> QueryResult:
        """Execute a SQL query and return structured results.

        Args:
            query: SQL query to execute
            params: Optional query parameters to prevent SQL injection

        Returns:
            QueryResult containing rows and metadata

        Raises:
            ConnectionError: When database connection fails
            QueryError: When query execution fails (schema or general errors)
            PermissionError: When user lacks required privileges
        """
        if self._pool is None:
            self._pool = self._get_pool()

        pool = self._get_pool()
        conn = pool.getconn()
        try:
            # Check if we are in transaction mode
            in_transaction = conn.status == psycopg2.extensions.STATUS_IN_TRANSACTION
            logger.debug(f"Connection state before query: {conn.status}")

            has_transaction_control = validate_transaction_control(query)
            logger.debug(f"Has transaction control: {has_transaction_control}")

            # Define readonly once at the top so it's available throughout the function
            readonly = self.mode == DbSafetyLevel.RO

            # Set session only if not in transaction mode
            if not in_transaction:
                conn.set_session(readonly=readonly)

            with conn.cursor() as cur:
                try:
                    cur.execute(query, params)

                    # Fetch results if available
                    rows = []
                    if cur.description:  # If query returns data
                        rows = cur.fetchall() or []

                    # Only auto-commit if not in write mode AND query doesn't contain
                    if not readonly and not has_transaction_control:
                        conn.commit()

                    status = cur.statusmessage
                    logger.debug(f"Query status: {status}")
                    return QueryResult(rows=rows, count=len(rows), status=status)

                except psycopg2_errors.InsufficientPrivilege as e:
                    logger.error(f"Permission denied: {e}")
                    raise PermissionError(
                        f"Access denied: {str(e)}. Use live_dangerously('database', True) for write operations."
                    ) from e
                except (
                    psycopg2_errors.UndefinedTable,
                    psycopg2_errors.UndefinedColumn,
                ) as e:
                    logger.error(f"Schema error: {e}")
                    raise QueryError(str(e)) from e
                except psycopg2.Error as e:
                    if not readonly:
                        try:
                            conn.rollback()
                            logger.debug("Transaction rolled back due to error")
                        except Exception as rollback_error:
                            logger.warning(f"Failed to rollback transaction: {rollback_error}")
                    logger.error(f"Database error: {e.pgerror}")
                    raise QueryError(f"Query failed: {str(e)}") from e
        finally:
            if pool and conn:
                pool.putconn(conn)
