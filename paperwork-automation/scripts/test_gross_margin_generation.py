#!/usr/bin/env python3
"""
Test the monthly gross margin report generation
"""

import subprocess
import sys
import os
from pathlib import Path

def test_report_generation():
    """Test report generation with proper environment setup"""
    
    print("Testing Monthly Gross Margin Report Generation")
    print("=" * 60)
    
    # Set up environment variables for database connection
    env = os.environ.copy()
    env['PG_HOST'] = 'localhost'
    env['PG_PORT'] = '5432' 
    env['PG_USER'] = 'hongming'
    env['PG_PASSWORD'] = '8894'
    env['PG_DATABASE'] = 'haidilao-paperwork'
    
    # Add parent directory to Python path
    project_root = Path(__file__).parent.parent
    env['PYTHONPATH'] = str(project_root)
    
    # Command to run
    cmd = [
        sys.executable,
        "-m", "scripts.generate_monthly_gross_margin_report",
        "--target-date", "2025-05-31"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    print(f"Working directory: {project_root}")
    print()
    
    # Run the command
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=project_root,
            env=env
        )
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n✅ Report generation completed successfully!")
            
            # Check if output file exists
            output_file = project_root / "output" / "monthly_gross_margin" / "毛利相关分析指标-202505.xlsx"
            if output_file.exists():
                print(f"\n✅ Output file created: {output_file}")
                print(f"   File size: {output_file.stat().st_size:,} bytes")
                
                # Try to peek at the file structure
                try:
                    import zipfile
                    with zipfile.ZipFile(output_file, 'r') as z:
                        sheets = [f for f in z.namelist() if 'worksheets' in f and f.endswith('.xml')]
                        print(f"   Sheets found: {len(sheets)}")
                except:
                    pass
            else:
                print(f"\n❌ Output file not found: {output_file}")
                
        else:
            print(f"\n❌ Report generation failed with return code: {result.returncode}")
            
    except Exception as e:
        print(f"\n❌ Error running command: {e}")
        import traceback
        traceback.print_exc()
    
    # Show SQL verification info
    print("\n" + "=" * 60)
    print("To verify the data in the database, run:")
    print("psql -U hongming -d haidilao-paperwork -f scripts/verify_gross_margin_queries.sql")
    print("\nThis will show:")
    print("1. Store gross profit data with revenue and costs")
    print("2. Material cost analysis with price changes")
    print("3. Monthly summary for all stores")
    print("4. Data availability statistics")

if __name__ == "__main__":
    test_report_generation()