# 🗄️ Database Integration Guide

## Overview

The Haidilao Paperwork Automation System now supports direct database integration, allowing you to insert processed Excel data directly into PostgreSQL databases instead of just generating SQL files.

## ✨ Features

- 🔗 **Direct Database Insertion**: Insert data directly to PostgreSQL without intermediate SQL files
- 🧪 **Test Database Support**: Separate test environment with automatic schema setup
- 🛡️ **Connection Management**: Robust connection handling with automatic cleanup
- 📊 **Transaction Safety**: UPSERT operations with conflict resolution
- 🔍 **Database Validation**: Verify database structure and connectivity
- 🚀 **Multiple Entry Points**: Support across Python scripts and TypeScript interface

## 🚀 Quick Start

### 1. Install Database Dependencies

```bash
pip3 install -r requirements-db.txt
```

### 2. Configure Database Connection

Create a `.env` file in the project root with your database credentials:

```env
# Production Database
PG_HOST=your-host.com
PG_PORT=5432
PG_USER=your-username
PG_PASSWORD=your-password
PG_DATABASE=your-database

# Test Database (can be same as production for development)
TEST_PG_HOST=your-test-host.com
TEST_PG_PORT=5432
TEST_PG_USER=your-test-username
TEST_PG_PASSWORD=your-test-password
TEST_PG_DATABASE=your-test-database

# Enable direct database insertion by default
DIRECT_DB_INSERT=false
```

### 3. Setup Test Database (First Time)

```bash
# Setup test database with schema and initial data
npm run db:setup
```

### 4. Verify Database Connection

```bash
# Verify production database
npm run db:verify

# Verify test database
npm run db:verify-test
```

## 📋 Database Schema Requirements

The system expects the following PostgreSQL tables:

### Core Tables

1. **`store`** - Store information with seat capacities
2. **`time_segment`** - Time segment definitions (4 periods)
3. **`daily_report`** - Daily operational data
4. **`store_time_report`** - Time segment performance data
5. **`store_monthly_target`** - Monthly performance targets

### Required SQL Files

The system uses these SQL files for database setup:

- `haidilao-database-querys/reset-db.sql` - Database schema
- `haidilao-database-querys/insert_const_data.sql` - Stores and time segments
- `haidilao-database-querys/insert_monthly_target.sql` - Monthly targets

## 🎯 Usage Examples

### Direct Database Insertion

#### Using Python Scripts

```bash
# Process both daily and time segment data to database
python3 scripts/extract-all.py data.xlsx --direct-db

# Process only daily reports to database
python3 scripts/insert-data.py data.xlsx --direct-db

# Process only time segments to database
python3 scripts/extract-time-segments.py data.xlsx --direct-db

# Use test database
python3 scripts/extract-all.py data.xlsx --direct-db --test-db
```

#### Using NPM Scripts

```bash
# Process to database using convenient NPM scripts
npm run extract-all-db data.xlsx
npm run extract-daily-db data.xlsx
npm run extract-time-db data.xlsx
```

#### Using Enhanced TypeScript Interface

```bash
# Process with database insertion
npm run extract-enhanced process data.xlsx --direct-db

# Use test database
npm run extract-enhanced process data.xlsx --direct-db --test-db

# With custom validation
npm run extract-enhanced process data.xlsx --direct-db --debug
```

### Environment Variable Control

You can also enable database insertion via environment variable:

```bash
# Set environment variable to enable database insertion by default
export DIRECT_DB_INSERT=true

# Now all processing will go directly to database
npm run extract-all data.xlsx
python3 scripts/insert-data.py data.xlsx
```

## 🧪 Testing

### Database Tests

```bash
# Run database-specific tests
npm run test:db

# Run all tests including database
npm run test
```

### Manual Database Testing

```bash
# Test database configuration
python3 test_db_config.py

# Verify database structure
npm run db:check
npm run db:check-test

# Setup fresh test database
npm run db:setup
```

## 🔧 Database Operations

### Database Utilities

The system includes a comprehensive database utility module:

```bash
# Verify database connection
python3 -m utils.database --verify
python3 -m utils.database --verify --test

# Check database structure
python3 -m utils.database --check-structure
python3 -m utils.database --check-structure --test

# Setup test database
python3 -m utils.database --setup --test
```

### Database Manager Features

- **Connection Pooling**: Efficient connection management
- **Transaction Safety**: Automatic rollback on errors
- **SQL File Execution**: Execute schema and data files
- **Structure Validation**: Verify required tables and data
- **Error Handling**: Comprehensive error reporting

## 📊 Data Flow

### Traditional Flow (SQL Files)

```
Excel File → Python Processing → SQL File → Manual DB Import
```

### Enhanced Flow (Direct DB)

```
Excel File → Python Processing → Direct DB Insertion → ✅ Complete
```

### UPSERT Operations

The system uses PostgreSQL UPSERT (INSERT ... ON CONFLICT) for safe data insertion:

```sql
-- Daily reports
INSERT INTO daily_report (...) VALUES (...)
ON CONFLICT (store_id, date) DO UPDATE SET ...

-- Time segments
INSERT INTO store_time_report (...) VALUES (...)
ON CONFLICT (store_id, date, time_segment_id) DO UPDATE SET ...
```

## 🚨 Error Handling

### Connection Errors

```bash
❌ Database connection failed
💡 Check your .env file and database credentials
💡 Verify database server is running and accessible
```

### Schema Errors

```bash
❌ Required table 'daily_report' not found
💡 Run: npm run db:setup
💡 Or manually execute schema SQL files
```

### Data Errors

```bash
❌ Failed to insert data to daily_report
💡 Check data format and constraints
💡 Use --debug flag for detailed error information
```

## 🔍 Troubleshooting

### Common Issues

1. **Missing Environment Variables**

   ```bash
   ❌ Missing required environment variables: PG_PASSWORD
   ```

   **Solution**: Create `.env` file with all required database credentials

2. **Connection Timeout**

   ```bash
   ❌ Database connection failed: timeout
   ```

   **Solution**: Check network connectivity and database server status

3. **Permission Denied**

   ```bash
   ❌ Database connection failed: permission denied
   ```

   **Solution**: Verify database user has INSERT/UPDATE permissions

4. **Table Not Found**
   ```bash
   ❌ Required table 'store' not found
   ```
   **Solution**: Run database setup: `npm run db:setup`

### Debug Mode

Enable debug mode for detailed error information:

```bash
# Python scripts
python3 scripts/extract-all.py data.xlsx --direct-db --debug

# TypeScript interface
npm run extract-enhanced process data.xlsx --direct-db --debug
```

## 📈 Performance

### Benchmarks

- **SQL File Generation**: ~2-3 seconds for 1000 records
- **Direct DB Insertion**: ~3-4 seconds for 1000 records
- **Database Setup**: ~5-10 seconds (one-time)
- **Connection Verification**: ~1-2 seconds

### Optimization Tips

1. **Use Test Database**: For development and testing
2. **Batch Operations**: Process multiple files in sequence
3. **Connection Reuse**: Database connections are automatically managed
4. **Transaction Batching**: UPSERT operations are batched for efficiency

## 🔄 Migration Guide

### From SQL Files to Direct DB

```bash
# Old workflow
python3 scripts/extract-all.py data.xlsx
psql -d database -f output/data.sql

# New workflow
python3 scripts/extract-all.py data.xlsx --direct-db
```

### Environment Setup

```bash
# 1. Install dependencies
pip3 install -r requirements-db.txt

# 2. Configure database
cp .env.example .env
# Edit .env with your credentials

# 3. Setup test database
npm run db:setup

# 4. Verify connection
npm run db:verify-test
```

## 🎯 Best Practices

### Development

1. **Always use test database** for development
2. **Run database setup** before first use
3. **Verify connections** before processing large files
4. **Use debug mode** when troubleshooting

### Production

1. **Test with small files** before processing large datasets
2. **Monitor database performance** during bulk operations
3. **Backup database** before major data imports
4. **Use environment variables** for configuration

### Security

1. **Never commit .env files** to version control
2. **Use strong database passwords**
3. **Limit database user permissions** to required operations only
4. **Use SSL connections** for remote databases

## 📞 Support

### Getting Help

```bash
# Show all available database commands
npm run status

# Get help for specific commands
python3 scripts/extract-all.py --help
npm run extract-enhanced process --help

# Run database diagnostics
npm run db:verify
npm run db:check
```

### Common Commands Reference

```bash
# Database Setup
npm run db:setup                    # Setup test database
npm run db:verify                   # Verify production DB
npm run db:verify-test              # Verify test DB
npm run db:check                    # Check production structure
npm run db:check-test               # Check test structure

# Processing with Database
npm run extract-all-db <file>       # Process to production DB
npm run extract-daily-db <file>     # Daily reports to DB
npm run extract-time-db <file>      # Time segments to DB

# Testing
npm run test:db                     # Database tests
python3 test_db_config.py           # Configuration test
```

---

**🗄️ Built for reliable data operations with PostgreSQL integration**
