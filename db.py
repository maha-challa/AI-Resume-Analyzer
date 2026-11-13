import os
import json
from urllib.parse import urlparse
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

# Load environment variables on startup
load_dotenv(override=True)


def get_db_config():
    """
    Dynamically loads configuration from environment variables on each connection.
    Supports either individual variables (DB_HOST, etc.) or a single DATABASE_URL / MYSQL_URL.
    """
    load_dotenv(override=True)
    db_url = os.getenv("DATABASE_URL") or os.getenv("MYSQL_URL")
    if db_url:
        parsed = urlparse(db_url)
        ssl_enabled = os.getenv("DB_SSL", "false").lower() in ("true", "1") or "ssl" in (parsed.query or "").lower()
        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 3306,
            "user": parsed.username or "root",
            "password": parsed.password or "",
            "database": parsed.path.lstrip("/") if parsed.path else "ai_resume_analyzer",
            "ssl": ssl_enabled
        }

    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "user": os.getenv("DB_USER", "resume_user"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "ai_resume_analyzer"),
        "ssl": os.getenv("DB_SSL", "false").lower() in ("true", "1")
    }


def get_raw_connection(include_database=True):
    """
    Creates and returns a connection to MySQL using current environment values.
    Enforces strict TLS certificate and hostname identity verification when SSL is enabled.
    """
    cfg = get_db_config()
    connect_kwargs = {
        "host": cfg["host"],
        "port": cfg["port"],
        "user": cfg["user"],
        "password": cfg["password"],
        "database": cfg["database"] if include_database else None,
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
        "connect_timeout": 5,
        "autocommit": True
    }
    if cfg["ssl"]:
        # Enable secure TLS verification for cloud databases (e.g. TiDB Cloud)
        connect_kwargs["ssl_verify_cert"] = True
        connect_kwargs["ssl_verify_identity"] = True
        ssl_ca = os.getenv("DB_SSL_CA")
        if ssl_ca:
            connect_kwargs["ssl_ca"] = ssl_ca

    return pymysql.connect(**connect_kwargs)


def test_connection():
    """
    Tests if MySQL server is reachable with the current credentials.
    Tries connecting to the configured database directly first, then server-wide.
    """
    try:
        conn = get_raw_connection(include_database=True)
        conn.close()
        return True, "Successfully connected to MySQL database."
    except Exception as db_err:
        try:
            conn = get_raw_connection(include_database=False)
            conn.close()
            return True, f"Connected to MySQL server (database pending creation): {db_err}"
        except Exception as server_err:
            return False, str(server_err)


def init_db():
    """
    Initializes the database and creates the required 'analyses' table if it does not exist.
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS `analyses` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `resume_filename` VARCHAR(255) NOT NULL,
        `job_description` TEXT NOT NULL,
        `skill_match_percentage` FLOAT NOT NULL,
        `matched_skills` TEXT NOT NULL,
        `missing_skills` TEXT NOT NULL,
        `improvement_suggestions` TEXT NOT NULL,
        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """

    try:
        # Attempt 1: Connect directly to the database (works if database already exists)
        conn = get_raw_connection(include_database=True)
        with conn.cursor() as cursor:
            cursor.execute(create_table_query)
        conn.close()
        return True, "Table 'analyses' verified successfully in database."
    except Exception as direct_err:
        # Attempt 2: If database doesn't exist, try creating it first
        try:
            cfg = get_db_config()
            conn = get_raw_connection(include_database=False)
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{cfg['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn.close()

            conn = get_raw_connection(include_database=True)
            with conn.cursor() as cursor:
                cursor.execute(create_table_query)
            conn.close()
            return True, "Database and table created successfully."
        except Exception as e:
            return False, f"Database initialization failed: {str(e)}"


def save_analysis(filename: str, job_description: str, match_percentage: float,
                  matched_skills: list, missing_skills: list, suggestions: list) -> int:
    """
    Saves an analysis record into the MySQL database.
    Returns the newly inserted row ID.
    """
    conn = get_raw_connection(include_database=True)
    try:
        with conn.cursor() as cursor:
            insert_query = """
            INSERT INTO `analyses` (
                `resume_filename`,
                `job_description`,
                `skill_match_percentage`,
                `matched_skills`,
                `missing_skills`,
                `improvement_suggestions`
            ) VALUES (%s, %s, %s, %s, %s, %s);
            """
            cursor.execute(insert_query, (
                filename,
                job_description,
                float(match_percentage),
                json.dumps(matched_skills),
                json.dumps(missing_skills),
                json.dumps(suggestions)
            ))
            new_id = cursor.lastrowid
        return new_id
    finally:
        conn.close()


def get_all_analyses() -> list:
    """
    Retrieves all past analysis records, ordered from most recent to oldest.
    Parses JSON-encoded fields into Python lists.
    """
    conn = get_raw_connection(include_database=True)
    try:
        with conn.cursor() as cursor:
            select_query = """
            SELECT `id`, `resume_filename`, `job_description`, `skill_match_percentage`,
                   `matched_skills`, `missing_skills`, `improvement_suggestions`, `created_at`
            FROM `analyses`
            ORDER BY `created_at` DESC;
            """
            cursor.execute(select_query)
            rows = cursor.fetchall()

        for row in rows:
            try:
                row["matched_skills"] = json.loads(row["matched_skills"])
            except Exception:
                row["matched_skills"] = []

            try:
                row["missing_skills"] = json.loads(row["missing_skills"])
            except Exception:
                row["missing_skills"] = []

            try:
                row["improvement_suggestions"] = json.loads(row["improvement_suggestions"])
            except Exception:
                row["improvement_suggestions"] = []

            if row.get("created_at"):
                row["formatted_date"] = row["created_at"].strftime("%b %d, %Y - %I:%M %p")
            else:
                row["formatted_date"] = "N/A"

        return rows
    finally:
        conn.close()


def get_analysis_by_id(analysis_id: int):
    """
    Retrieves a single analysis record by its primary key ID.
    """
    conn = get_raw_connection(include_database=True)
    try:
        with conn.cursor() as cursor:
            select_query = """
            SELECT `id`, `resume_filename`, `job_description`, `skill_match_percentage`,
                   `matched_skills`, `missing_skills`, `improvement_suggestions`, `created_at`
            FROM `analyses`
            WHERE `id` = %s;
            """
            cursor.execute(select_query, (analysis_id,))
            row = cursor.fetchone()

        if row:
            try:
                row["matched_skills"] = json.loads(row["matched_skills"])
            except Exception:
                row["matched_skills"] = []

            try:
                row["missing_skills"] = json.loads(row["missing_skills"])
            except Exception:
                row["missing_skills"] = []

            try:
                row["improvement_suggestions"] = json.loads(row["improvement_suggestions"])
            except Exception:
                row["improvement_suggestions"] = []

            if row.get("created_at"):
                row["formatted_date"] = row["created_at"].strftime("%b %d, %Y - %I:%M %p")

        return row
    finally:
        conn.close()
