import { Pool, PoolClient } from "pg";
import * as dotenv from "dotenv";
import { logger } from "./file";

// Load environment variables
dotenv.config();

// Database configuration
const dbConfig = {
  host: process.env.PG_HOST || "localhost",
  port: parseInt(process.env.PG_PORT || "5432", 10),
  user: process.env.PG_USER || "postgres",
  password: process.env.PG_PASSWORD || "postgres",
  database: process.env.PG_DATABASE || "reportdb",
};

// Create a connection pool
const pool = new Pool(dbConfig);

// Interface for simple column-value pairs
interface ColumnValuePair {
  column: string;
  value: any;
}

/**
 * Format a value for SQL insertion based on its type
 */
export const formatSqlValue = (value: any): string => {
  if (value === null || value === undefined) {
    return "NULL";
  } else if (typeof value === "number") {
    return value.toString();
  } else if (typeof value === "boolean") {
    return value ? "TRUE" : "FALSE";
  } else if (value instanceof Date) {
    return `'${value.toISOString()}'`;
  } else {
    // Escape single quotes in strings
    const escaped = String(value).replace(/'/g, "''");
    return `'${escaped}'`;
  }
};

/**
 * Generate an INSERT statement for a single row
 */
export const generateInsertStatement = (
  tableName: string,
  columnValues: ColumnValuePair[]
): string => {
  const columns = columnValues.map((cv) => cv.column).join(", ");
  const values = columnValues.map((cv) => formatSqlValue(cv.value)).join(", ");

  return `INSERT INTO ${tableName} (${columns}) VALUES (${values});`;
};

/**
 * Generate a multi-row INSERT statement
 */
export const generateBulkInsertStatement = (
  tableName: string,
  rows: ColumnValuePair[][]
): string => {
  if (rows.length === 0) return "";

  // Assuming all rows have the same columns in the same order
  const columns = rows[0].map((cv) => cv.column).join(", ");

  const valueStrings = rows
    .map((row) => {
      const values = row.map((cv) => formatSqlValue(cv.value)).join(", ");
      return `(${values})`;
    })
    .join(",\n  ");

  return `INSERT INTO ${tableName} (${columns}) VALUES\n  ${valueStrings};`;
};

/**
 * Create a basic table creation SQL statement
 */
export const generateCreateTableStatement = (
  tableName: string,
  columns: {
    name: string;
    type: string;
    nullable?: boolean;
    defaultValue?: string;
  }[]
): string => {
  const columnDefs = columns
    .map((col) => {
      let def = `${col.name} ${col.type}`;
      if (col.nullable === false) def += " NOT NULL";
      if (col.defaultValue) def += ` DEFAULT ${col.defaultValue}`;
      return def;
    })
    .join(",\n  ");

  return `CREATE TABLE IF NOT EXISTS ${tableName} (\n  ${columnDefs}\n);`;
};

/**
 * Execute SQL directly in the database
 */
export const executeSql = async (sql: string): Promise<any> => {
  let client: PoolClient | null = null;
  try {
    client = await pool.connect();
    logger.info("Executing SQL...");
    const result = await client.query(sql);
    logger.success(
      `SQL executed successfully. Affected rows: ${result.rowCount}`
    );
    return result;
  } catch (error) {
    logger.error("Failed to execute SQL", error as Error);
    throw error;
  } finally {
    if (client) client.release();
  }
};

/**
 * Clean up database connections
 */
export const closeDbConnections = async (): Promise<void> => {
  try {
    await pool.end();
    logger.info("Database connections closed");
  } catch (error) {
    logger.error("Error closing database connections", error as Error);
  }
};
