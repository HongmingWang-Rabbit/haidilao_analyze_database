import * as fs from "fs";
import * as path from "path";
import * as dotenv from "dotenv";

// Load environment variables
dotenv.config();

/**
 * Logger utility with different log levels
 */
export const logger = {
  info: (message: string): void => {
    console.log(`[INFO] ${message}`);
  },
  error: (message: string, error?: Error): void => {
    console.error(`[ERROR] ${message}`, error || "");
  },
  warn: (message: string): void => {
    console.warn(`[WARN] ${message}`);
  },
  success: (message: string): void => {
    console.log(`[SUCCESS] ${message}`);
  },
};

/**
 * Parse a filename to extract date information
 * Example: 营业日报-底表-2025.6.10.xlsx -> 2025-06-10
 */
export const extractDateFromFilename = (filename: string): string | null => {
  // Match patterns like 2025.6.10 or 2025-6-10 or 2025.06.10
  const datePattern = /(\d{4})[\.-](\d{1,2})[\.-](\d{1,2})/;
  const match = filename.match(datePattern);

  if (!match) return null;

  const year = match[1];
  const month = match[2].padStart(2, "0"); // Ensure 2-digit month
  const day = match[3].padStart(2, "0"); // Ensure 2-digit day

  return `${year}-${month}-${day}`;
};

/**
 * Ensure output directory exists
 */
export const ensureOutputDir = (): string => {
  const outputDir = process.env.OUTPUT_DIR || "./output";
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
    logger.info(`Created output directory: ${outputDir}`);
  }
  return outputDir;
};

/**
 * Generate output filename based on input file
 */
export const generateOutputFilename = (
  inputFile: string,
  suffix = "insert_data"
): string => {
  const date = extractDateFromFilename(inputFile) || "unknown-date";
  const outputDir = ensureOutputDir();
  return path.join(outputDir, `${suffix}_${date}.sql`);
};

/**
 * Save SQL to file
 */
export const saveSqlToFile = (sql: string, outputPath: string): void => {
  try {
    fs.writeFileSync(outputPath, sql);
    logger.success(`SQL saved to: ${outputPath}`);
  } catch (error) {
    logger.error("Failed to save SQL file", error as Error);
    throw error;
  }
};
