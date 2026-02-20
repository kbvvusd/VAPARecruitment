import os
import glob
import pandas as pd
from datetime import datetime

# Configuration
ROOT_DIR = '/Users/ahuntsman/Desktop/Recruitment'
REPORT_FILE = os.path.join(ROOT_DIR, 'recruitment_report.html')

def find_header_row(file_path):
    """Attempts to find the header row by looking for 'Student ID'."""
    try:
        # Read first 15 rows to find header
        df_preview = pd.read_excel(file_path, header=None, nrows=15)
        for idx, row in df_preview.iterrows():
            # Check if likely header row
            row_values = [str(x).lower() for x in row.values if pd.notna(x)]
            if 'student id' in row_values or 'student name' in row_values:
                return idx
        return 0 # Default to 0 if not found
    except Exception as e:
        print(f"Error reading {file_path} to find header: {e}")
        return 0

def load_data(root_dir):
    all_data = []
    
    # Walk through the directory structure
    # Expected: School Name / Type (Band/Choir) / Year.xlsx
    
    schools = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]
    
    for school in schools:
        school_path = os.path.join(root_dir, school)
        types = [d for d in os.listdir(school_path) if os.path.isdir(os.path.join(school_path, d))]
        
        for prog_type in types:
            type_path = os.path.join(school_path, prog_type)
            files = glob.glob(os.path.join(type_path, "*.xlsx"))
            
            for file_path in files:
                filename = os.path.basename(file_path)
                year = os.path.splitext(filename)[0] # Assuming filename is '2023-2024.xlsx'
                
                print(f"Processing {school} - {prog_type} - {year}")
                
                header_row = find_header_row(file_path)
                try:
                    df = pd.read_excel(file_path, header=header_row)
                    
                    # Normalize columns
                    df.columns = [str(c).strip() for c in df.columns]
                    
                    # Map columns if needed
                    # Expected: Student ID, Student Name, GR, Course Title
                    
                    # Basic validation - check if required columns exist
                    required_cols = ['Student ID', 'Student Name', 'GR']
                    missing_cols = [c for c in required_cols if c not in df.columns]
                    
                    if missing_cols:
                        print(f"  WARNING: Missing columns {missing_cols} in {file_path}. Skipping file.")
                        print(f"  Found columns: {df.columns.tolist()}")
                        continue
                        
                    # Extract relevant data
                    df['School'] = school
                    df['Program'] = prog_type
                    df['Year'] = year
                    
                    # Keep only relevant columns
                    cols_to_keep = ['School', 'Program', 'Year', 'Student ID', 'Student Name', 'GR', 'Course Title']
                    # Add Course Title if missing (optional)
                    if 'Course Title' not in df.columns:
                        df['Course Title'] = 'Unknown'
                        
                    subset = df[cols_to_keep].copy()
                    all_data.append(subset)
                    
                except Exception as e:
                    print(f"  Error processing {file_path}: {e}")

    if not all_data:
        return pd.DataFrame()
    
    return pd.concat(all_data, ignore_index=True)

def generate_html_report(df):
    if df.empty:
        return "<html><body><h1>No Data Found</h1></body></html>"
    
    # Aggregations
    
    # 1. Enrollment by School, Program, Year
    enrollment_summary = df.groupby(['School', 'Program', 'Year']).size().reset_index(name='Count')
    enrollment_pivot = enrollment_summary.pivot_table(index=['School', 'Program'], columns='Year', values='Count', fill_value=0)
    
    # 2. Recruitment Pools (8th Graders in current year for next year HS)
    # Assuming current year is the latest year in data
    latest_years = sorted(df['Year'].unique())
    last_year = latest_years[-1] if latest_years else "N/A"
    
    # Filter 8th graders in the latest year
    graduating_8th_graders = df[
        (df['Year'] == last_year) & 
        (df['GR'] == 8)
    ].sort_values(['School', 'Program', 'Student Name'])
    
    # HTML Generation
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Recruitment Resource Report</title>
        <style>
            body {{ font-family: sans-serif; margin: 20px; }}
            h1, h2 {{ color: #2c3e50; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .section {{ margin-bottom: 40px; }}
        </style>
    </head>
    <body>
        <h1>Middle School Music Recruitment Report</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="section">
            <h2>Enrollment Trends</h2>
            {enrollment_pivot.to_html(classes='table table-striped')}
        </div>
        
        <div class="section">
            <h2>Potential Recruits (8th Graders in {last_year})</h2>
            <p>Total: {len(graduating_8th_graders)}</p>
            {graduating_8th_graders[['School', 'Program', 'Student Name', 'Student ID', 'Course Title']].to_html(index=False, classes='table table-striped')}
        </div>
    </body>
    </html>
    """
    return html

def main():
    print("Starting Recruitment Report Generation...")
    df = load_data(ROOT_DIR)
    
    if df.empty:
        print("No valid data found. Please check the directory structure and file formats.")
        return

    print(f"Loaded {len(df)} records.")
    
    html_content = generate_html_report(df)
    
    with open(REPORT_FILE, 'w') as f:
        f.write(html_content)
    
    print(f"Report generated successfully: {REPORT_FILE}")

if __name__ == "__main__":
    main()
