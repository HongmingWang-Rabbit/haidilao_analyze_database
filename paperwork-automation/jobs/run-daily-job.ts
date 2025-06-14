#!/usr/bin/env ts-node

import * as path from "path";
import * as fs from "fs";
import * as chokidar from "chokidar";
import * as dotenv from "dotenv";
import { logger } from "../utils/file";
import { spawn } from "child_process";

// Load environment variables
dotenv.config();

// Path settings
const DATA_DIR = path.resolve(
  process.env.DATA_DIR || path.join(__dirname, "../data")
);
const WATCH_MODE = process.env.WATCH_MODE === "true";

/**
 * Execute the extract-sql script for a given file
 */
function processFile(filePath: string, directDbInsert = false): Promise<void> {
  return new Promise((resolve, reject) => {
    const extractScript = path.join(__dirname, "../scripts/extract-sql.ts");
    const args = [extractScript, filePath];

    if (directDbInsert) {
      args.push("--direct");
    }

    logger.info(`Processing file: ${filePath}`);

    const child = spawn("ts-node", args, {
      stdio: "pipe",
      shell: true,
    });

    child.stdout.on("data", (data) => {
      logger.info(data.toString().trim());
    });

    child.stderr.on("data", (data) => {
      logger.error(data.toString().trim());
    });

    child.on("close", (code) => {
      if (code === 0) {
        logger.success(`Successfully processed: ${path.basename(filePath)}`);
        resolve();
      } else {
        logger.error(`Failed to process file (exit code: ${code})`);
        reject(new Error(`Process exited with code ${code}`));
      }
    });

    child.on("error", (err) => {
      logger.error(`Failed to start process: ${err.message}`);
      reject(err);
    });
  });
}

/**
 * Process all pending Excel files in the data directory
 */
async function processPendingFiles(directDbInsert = false): Promise<void> {
  try {
    // Ensure data directory exists
    if (!fs.existsSync(DATA_DIR)) {
      fs.mkdirSync(DATA_DIR, { recursive: true });
      logger.info(`Created data directory: ${DATA_DIR}`);
      return; // No files to process yet
    }

    // Get all Excel files in the data directory
    const files = fs
      .readdirSync(DATA_DIR)
      .filter((file) => file.endsWith(".xlsx") || file.endsWith(".xls"))
      .map((file) => path.join(DATA_DIR, file))
      .sort(); // Process in alphabetical (roughly chronological) order

    logger.info(`Found ${files.length} Excel files to process`);

    // Process each file sequentially
    for (const file of files) {
      try {
        await processFile(file, directDbInsert);
      } catch (error) {
        logger.error(`Error processing ${file}`, error as Error);
        // Continue with the next file
      }
    }
  } catch (error) {
    logger.error("Failed to process pending files", error as Error);
    throw error;
  }
}

/**
 * Watch the data directory for new Excel files
 */
function watchDataDirectory(directDbInsert = false): void {
  logger.info(`Watching directory for new Excel files: ${DATA_DIR}`);

  const watcher = chokidar.watch(path.join(DATA_DIR, "*.xlsx"), {
    persistent: true,
    ignoreInitial: false,
    awaitWriteFinish: {
      stabilityThreshold: 2000, // Wait for file to be stable for 2 seconds
      pollInterval: 100,
    },
  });

  // Add .xls files too
  watcher.add(path.join(DATA_DIR, "*.xls"));

  watcher.on("add", async (filePath) => {
    try {
      await processFile(filePath, directDbInsert);
    } catch (error) {
      logger.error(`Error processing new file ${filePath}`, error as Error);
    }
  });

  watcher.on("error", (error) => {
    logger.error("Watcher error", error);
  });

  // Keep the process running
  process.on("SIGINT", () => {
    logger.info("Stopping file watcher...");
    watcher.close().then(() => {
      logger.info("File watcher stopped.");
      process.exit(0);
    });
  });
}

/**
 * Main job runner function
 */
async function runDailyJob(): Promise<void> {
  const directDbInsert = process.env.DIRECT_DB_INSERT === "true";
  logger.info(`Starting daily job runner (directDbInsert=${directDbInsert})`);

  try {
    // Run once to process pending files
    await processPendingFiles(directDbInsert);

    // If in watch mode, keep watching for new files
    if (WATCH_MODE) {
      watchDataDirectory(directDbInsert);
    }

    logger.success("Daily job completed successfully");
  } catch (error) {
    logger.error("Daily job failed", error as Error);
    process.exit(1);
  }
}

// Run the job when this script is executed directly
if (require.main === module) {
  runDailyJob();
}

export { runDailyJob, processPendingFiles, watchDataDirectory };
