#!/usr/bin/env ts-node

import { Command } from "commander";
import * as fs from "fs";
import * as path from "path";
import * as xlsx from "xlsx";
import * as dotenv from "dotenv";
import { logger, generateOutputFilename, saveSqlToFile } from "../utils/file";
import {
  generateBulkInsertStatement,
  executeSql,
  closeDbConnections,
} from "../utils/sql";
import { spawn } from "child_process";

// Load environment variables
dotenv.config();

interface ColumnValuePair {
  column: string;
  value: any;
}

interface ExcelProcessingOptions {
  inputFile: string;
  outputFile?: string;
  directDbInsert?: boolean;
  table?: string;
  sheetName?: string;
  dateColumn?: string;
}

/**
 * Process an Excel file and extract data
 * Note: seats_total is now a fixed property of each store in the store table,
 * not part of the daily_report data.
 */
async function processExcelFile(
  options: ExcelProcessingOptions
): Promise<void> {
  const {
    inputFile,
    outputFile = generateOutputFilename(inputFile),
    directDbInsert = process.env.DIRECT_DB_INSERT === "true",
    table = "daily_report",
    sheetName,
    dateColumn,
  } = options;

  try {
    logger.info(`Processing Excel file: ${inputFile}`);

    // Read the Excel file
    if (!fs.existsSync(inputFile)) {
      throw new Error(`File not found: ${inputFile}`);
    }

    const workbook = xlsx.readFile(inputFile);
    const sheets = workbook.SheetNames;

    // Use the first sheet if not specified
    const targetSheetName = sheetName || sheets[0];
    if (!sheets.includes(targetSheetName)) {
      throw new Error(`Sheet "${targetSheetName}" not found in workbook.`);
    }

    const worksheet = workbook.Sheets[targetSheetName];
    const data = xlsx.utils.sheet_to_json(worksheet);

    if (data.length === 0) {
      logger.warn("No data found in the worksheet.");
      return;
    }

    logger.info(`Found ${data.length} rows of data.`);

    // Transform raw data to column-value pairs
    const rows = data.map((row: any) => {
      return Object.entries(row).map(([key, value]) => ({
        column: key.trim().toLowerCase().replace(/\s+/g, "_"),
        value: value,
      }));
    });

    // Generate SQL
    const sql = generateBulkInsertStatement(table, rows);

    // Save SQL to file
    saveSqlToFile(sql, outputFile);

    // Execute SQL directly if enabled
    if (directDbInsert) {
      logger.info("Executing SQL directly to the database...");
      await executeSql(sql);
    }

    logger.success("Processing completed successfully.");
  } catch (error) {
    logger.error("Failed to process Excel file", error as Error);
    throw error;
  } finally {
    if (options.directDbInsert) {
      await closeDbConnections();
    }
  }
}

/**
 * Try to use Python helper for pandas-heavy processing
 */
function tryUsePythonHelper(
  inputFile: string,
  outputFile: string
): Promise<void> {
  return new Promise((resolve, reject) => {
    const pythonScript = path.join(__dirname, "insert-data.py");

    if (!fs.existsSync(pythonScript)) {
      logger.info(
        "Python helper script not found, using TypeScript implementation"
      );
      resolve();
      return;
    }

    logger.info("Using Python helper for advanced processing...");

    const pythonProcess = spawn("python", [
      pythonScript,
      inputFile,
      outputFile,
    ]);

    pythonProcess.stdout.on("data", (data) => {
      logger.info(`Python: ${data.toString().trim()}`);
    });

    pythonProcess.stderr.on("data", (data) => {
      logger.warn(`Python error: ${data.toString().trim()}`);
    });

    pythonProcess.on("close", (code) => {
      if (code === 0) {
        logger.success("Python helper executed successfully");
        resolve();
      } else {
        logger.warn(`Python helper exited with code ${code}`);
        resolve(); // Continue with TS implementation even if Python fails
      }
    });

    pythonProcess.on("error", (err) => {
      logger.warn(`Failed to start Python helper: ${err.message}`);
      resolve(); // Continue with TS implementation
    });
  });
}

/**
 * Main CLI program
 */
async function main(): Promise<void> {
  const program = new Command();

  program
    .name("extract-sql")
    .description(
      "Extract data from Excel files and generate SQL insert statements"
    )
    .version("0.1.0")
    .argument("<excel-file>", "Path to Excel file to process")
    .option("-o, --output <file>", "Output SQL file path")
    .option("-d, --direct", "Insert directly to database")
    .option("-t, --table <name>", "Target table name")
    .option("-s, --sheet <name>", "Specific sheet name to process")
    .option("-c, --date-column <name>", "Date column name")
    .option("-p, --use-python", "Try to use Python helper first")
    .action(async (inputFile, options) => {
      try {
        const outputFile = options.output || generateOutputFilename(inputFile);

        // Try Python helper first if option enabled
        if (options.usePython) {
          await tryUsePythonHelper(inputFile, outputFile);
        }

        // Process with TypeScript implementation
        await processExcelFile({
          inputFile,
          outputFile,
          directDbInsert: options.direct,
          table: options.table,
          sheetName: options.sheet,
          dateColumn: options.dateColumn,
        });
      } catch (error) {
        logger.error("Failed to process file", error as Error);
        process.exit(1);
      }
    });

  // Parse the command line arguments
  program.parse(process.argv);
}

// Run the program
if (require.main === module) {
  main();
}
