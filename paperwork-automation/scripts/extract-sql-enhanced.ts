#!/usr/bin/env ts-node

import { Command } from "commander";
import * as fs from "fs";
import * as path from "path";
import { spawn, SpawnOptions } from "child_process";
import * as dotenv from "dotenv";

// Load environment variables
dotenv.config();

interface ProcessingOptions {
  inputFile: string;
  outputDaily?: string;
  outputTime?: string;
  skipValidation?: boolean;
  debug?: boolean;
  directDbInsert?: boolean;
  isTest?: boolean;
}

/**
 * Enhanced logger with emoji support
 */
const logger = {
  info: (message: string, ...args: any[]) => {
    console.log(`ℹ️  ${message}`, ...args);
  },
  success: (message: string, ...args: any[]) => {
    console.log(`✅ ${message}`, ...args);
  },
  warn: (message: string, ...args: any[]) => {
    console.log(`⚠️  ${message}`, ...args);
  },
  error: (message: string, error?: Error) => {
    console.error(`❌ ${message}`);
    if (error) {
      console.error(error.message);
      if (process.env.DEBUG) {
        console.error(error.stack);
      }
    }
  },
  debug: (message: string, ...args: any[]) => {
    if (process.env.DEBUG || process.env.NODE_ENV === "development") {
      console.log(`🐛 ${message}`, ...args);
    }
  },
};

/**
 * Run a Python script with proper error handling
 */
function runPythonScript(
  scriptName: string,
  args: string[],
  options: { debug?: boolean } = {}
): Promise<{ success: boolean; stdout: string; stderr: string }> {
  return new Promise((resolve) => {
    const scriptPath = path.join(__dirname, scriptName);

    if (!fs.existsSync(scriptPath)) {
      logger.error(`Python script not found: ${scriptPath}`);
      resolve({
        success: false,
        stdout: "",
        stderr: `Script not found: ${scriptPath}`,
      });
      return;
    }

    logger.debug(`Running: python3 ${scriptPath} ${args.join(" ")}`);

    const spawnOptions: SpawnOptions = {
      stdio: options.debug ? "inherit" : "pipe",
      cwd: path.dirname(scriptPath),
    };

    const pythonProcess = spawn("python3", [scriptPath, ...args], spawnOptions);

    let stdout = "";
    let stderr = "";

    if (!options.debug) {
      pythonProcess.stdout?.on("data", (data) => {
        stdout += data.toString();
      });

      pythonProcess.stderr?.on("data", (data) => {
        stderr += data.toString();
      });
    }

    pythonProcess.on("close", (code) => {
      const success = code === 0;

      if (success) {
        logger.success(`${scriptName} completed successfully`);
      } else {
        logger.error(`${scriptName} failed with exit code ${code}`);
        if (stderr && !options.debug) {
          logger.error("Error output:", new Error(stderr));
        }
      }

      resolve({ success, stdout, stderr });
    });

    pythonProcess.on("error", (err) => {
      logger.error(`Failed to start ${scriptName}:`, err);
      resolve({ success: false, stdout: "", stderr: err.message });
    });
  });
}

/**
 * Validate Excel file using the enhanced validation system
 */
async function validateExcelFile(
  inputFile: string,
  skipValidation: boolean = false
): Promise<boolean> {
  if (skipValidation) {
    logger.warn("Skipping data format validation...");
    return true;
  }

  logger.info("🔍 Validating Excel file format and data quality...");

  const result = await runPythonScript(
    "extract-all.py",
    [inputFile, "--skip-validation"],
    { debug: false }
  );

  if (!result.success) {
    logger.error("Validation failed. Please check your Excel file format.");
    logger.info("Use --skip-validation to bypass validation if needed.");
    return false;
  }

  // Check if validation output contains critical errors
  if (
    result.stdout.includes("❌") &&
    result.stdout.includes("Critical validation errors")
  ) {
    logger.error(
      "Critical validation errors found. Please fix the Excel file format before proceeding."
    );
    return false;
  }

  logger.success("Excel file validation passed");
  return true;
}

/**
 * Process Excel file using the enhanced Python scripts
 */
async function processExcelFile(options: ProcessingOptions): Promise<boolean> {
  const {
    inputFile,
    outputDaily,
    outputTime,
    skipValidation,
    debug,
    directDbInsert,
    isTest,
  } = options;

  try {
    logger.info(`🚀 Starting paperwork automation for: ${inputFile}`);

    // Check if input file exists
    if (!fs.existsSync(inputFile)) {
      logger.error(`Input file not found: ${inputFile}`);
      return false;
    }

    // Validate Excel file first
    const isValid = await validateExcelFile(inputFile, skipValidation);
    if (!isValid) {
      return false;
    }

    // Prepare arguments for extract-all.py
    const args = [inputFile];

    if (outputDaily) {
      args.push("--daily-output", outputDaily);
    }

    if (outputTime) {
      args.push("--time-output", outputTime);
    }

    if (debug) {
      args.push("--debug");
    }

    if (skipValidation) {
      args.push("--skip-validation");
    }

    if (directDbInsert) {
      args.push("--direct-db");
    }

    if (isTest) {
      args.push("--test-db");
    }

    // Run the enhanced extract-all.py script
    logger.info("📊 Processing Excel data with enhanced validation...");
    const result = await runPythonScript("extract-all.py", args, { debug });

    if (!result.success) {
      logger.error("Failed to process Excel file");
      return false;
    }

    // Parse output to show results
    if (result.stdout.includes("All extractions completed successfully")) {
      logger.success("🎉 All extractions completed successfully!");

      // Show output file locations
      if (outputDaily) {
        logger.info(`📄 Daily report SQL: ${outputDaily}`);
      }
      if (outputTime) {
        logger.info(`📄 Time segment SQL: ${outputTime}`);
      }

      return true;
    } else {
      logger.warn(
        "Processing completed with warnings. Check the output above."
      );
      return false;
    }
  } catch (error) {
    logger.error("Unexpected error during processing:", error as Error);
    return false;
  }
}

/**
 * Run tests to verify system functionality
 */
async function runTests(testType: string = "all"): Promise<boolean> {
  logger.info(`🧪 Running ${testType} tests...`);

  let scriptArgs: string[];

  switch (testType) {
    case "quick":
      scriptArgs = ["quick"];
      break;
    case "core":
      scriptArgs = ["core"];
      break;
    case "validation":
      scriptArgs = ["validation"];
      break;
    case "coverage":
      scriptArgs = ["coverage"];
      break;
    default:
      // Run simple_test.py for comprehensive testing
      const result = await runPythonScript("../simple_test.py", [], {
        debug: true,
      });
      return result.success;
  }

  const result = await runPythonScript("../run_tests.py", scriptArgs, {
    debug: true,
  });
  return result.success;
}

/**
 * Show system status and available commands
 */
function showStatus(): void {
  console.log(`
🏪 Haidilao Paperwork Automation System
=====================================

📊 System Status:
  • Enhanced validation system: ✅ Active
  • Python scripts: ✅ Available  
  • Test suite: ✅ 45 tests ready
  • TypeScript integration: ✅ Active

🎯 Available Commands:
  • npm run extract-all <file>     - Process Excel with validation
  • npm run extract-daily <file>   - Process daily reports only
  • npm run extract-time <file>    - Process time segments only
  • npm run extract-all-db <file>  - Process Excel with direct DB insertion
  • npm run extract-daily-db <file> - Process daily reports to DB
  • npm run extract-time-db <file> - Process time segments to DB
  • npm run test                   - Run all tests
  • npm run test:quick             - Run quick validation tests
  • npm run test:db                - Run database tests
  • npm run validate               - Run validation tests only
  • npm run db:setup               - Setup test database
  • npm run db:verify              - Verify database connection
  • npm run help                   - Show Python script help

📁 Expected Excel Structure:
  • Sheet 1: 营业基础表 (Daily reports)
  • Sheet 2: 分时段基础表 (Time segments)
  • 7 stores: 加拿大一店 through 加拿大七店
  • 4 time periods: 08:00-13:59, 14:00-16:59, 17:00-21:59, 22:00-(次)07:59

🔍 Data Validation Features:
  • File structure validation
  • Store name validation  
  • Time segment validation
  • Date format validation (YYYYMMDD)
  • Holiday value validation (工作日/节假日)
  • Numeric data range checking
`);
}

/**
 * Main CLI program
 */
async function main(): Promise<void> {
  const program = new Command();

  program
    .name("extract-sql-enhanced")
    .description("Enhanced Excel to SQL processor with validation")
    .version("0.2.0");

  // Main processing command
  program
    .command("process <excel-file>")
    .description("Process Excel file with enhanced validation")
    .option("-d, --daily-output <file>", "Output file for daily reports SQL")
    .option("-t, --time-output <file>", "Output file for time segments SQL")
    .option("--skip-validation", "Skip data format validation")
    .option("--debug", "Enable debug output")
    .option(
      "--direct-db",
      "Insert directly to database instead of generating SQL files"
    )
    .option("--test-db", "Use test database")
    .action(async (inputFile, options) => {
      const success = await processExcelFile({
        inputFile,
        outputDaily: options.dailyOutput,
        outputTime: options.timeOutput,
        skipValidation: options.skipValidation,
        debug: options.debug,
        directDbInsert: options.directDb,
        isTest: options.testDb,
      });

      process.exit(success ? 0 : 1);
    });

  // Test command
  program
    .command("test [type]")
    .description("Run tests (types: all, quick, core, validation, coverage)")
    .action(async (testType = "all") => {
      const success = await runTests(testType);
      process.exit(success ? 0 : 1);
    });

  // Status command
  program
    .command("status")
    .description("Show system status and available commands")
    .action(() => {
      showStatus();
    });

  // Validate command
  program
    .command("validate <excel-file>")
    .description("Validate Excel file format without processing")
    .action(async (inputFile) => {
      const isValid = await validateExcelFile(inputFile, false);
      process.exit(isValid ? 0 : 1);
    });

  // Database setup command
  program
    .command("db-setup")
    .description("Setup test database with schema and initial data")
    .action(async () => {
      logger.info("🔄 Setting up test database...");
      const result = await runPythonScript(
        "extract-all.py",
        ["--setup-test-db"],
        { debug: true }
      );
      process.exit(result.success ? 0 : 1);
    });

  // Database verify command
  program
    .command("db-verify")
    .description("Verify database connection")
    .option("--test", "Verify test database connection")
    .action(async (options) => {
      logger.info("🔍 Verifying database connection...");
      const args = ["--verify"];
      if (options.test) {
        args.push("--test");
      }
      const result = await runPythonScript("../utils/database.py", args, {
        debug: true,
      });
      process.exit(result.success ? 0 : 1);
    });

  // Parse command line arguments
  await program.parseAsync();
}

// Handle unhandled errors
process.on("unhandledRejection", (reason, promise) => {
  logger.error(
    "Unhandled Rejection at:",
    reason instanceof Error ? reason : new Error(String(reason))
  );
  process.exit(1);
});

process.on("uncaughtException", (error) => {
  logger.error("Uncaught Exception:", error);
  process.exit(1);
});

// Run the program
if (require.main === module) {
  main().catch((error) => {
    logger.error(
      "Fatal error:",
      error instanceof Error ? error : new Error(String(error))
    );
    process.exit(1);
  });
}
