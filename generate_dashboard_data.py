
import os
import glob
import pandas as pd
import json
from datetime import datetime

# Configuration
ROOT_DIR = '/Users/ahuntsman/Desktop/Recruitment'
OUTPUT_FILE = os.path.join(ROOT_DIR, 'dashboard_data.json')

def find_header_info(file_path):
    """
    Attempts to find:
    1. The header row index for student data (looking for 'Student ID').
    2. The Course Title from metadata rows.
    3. The Teacher Name from metadata rows.
    """
    try:
        # Read first 20 rows
        df_preview = pd.read_excel(file_path, header=None, nrows=20)
        
        header_idx = 0
        course_title = "Unknown"
        teacher_name = "Unknown"
        
        # Search for header row and metadata
        for idx, row in df_preview.iterrows():
            row_values_orig = [x for x in row.values]
            row_values_str = [str(x).lower().strip() for x in row_values_orig if pd.notna(x)]
            
            # Check for Student Header
            if 'student id' in row_values_str:
                header_idx = idx
                
            # Check for Metadata labels
            for col_idx, val in enumerate(row_values_orig):
                if not isinstance(val, str): continue
                
                # Course Title
                if 'Course Title' in val:
                    if idx + 1 < len(df_preview):
                        next_row_val = df_preview.iloc[idx + 1, col_idx]
                        if pd.notna(next_row_val):
                            course_title = str(next_row_val).strip()
                
                # Teacher
                if 'Teacher' in val:
                    if idx + 1 < len(df_preview):
                        next_row_val = df_preview.iloc[idx + 1, col_idx]
                        if pd.notna(next_row_val):
                            teacher_name = str(next_row_val).strip()
                            
        return header_idx, course_title, teacher_name
        
    except Exception as e:
        print(f"Error reading {file_path} to find header: {e}")
        return 0, "Unknown", "Unknown"


def clean_column_name(col):
    return str(col).strip()

def process_files(file_paths):
    """
    Reads multiple year files for a single program and merges student data.
    Returns a list of student records.
    """
    students = {} 
    file_paths.sort()
    all_years = set()

    for file_path in file_paths:
        filename = os.path.basename(file_path)
        year = os.path.splitext(filename)[0]
        # Handle cases like "2023-2024 (1)" or similar
        year_clean = year.split(' ')[0]
        all_years.add(year_clean)
        
        print(f"  Reading {year}...")
        header_row_idx, file_course_title, file_teacher_name = find_header_info(file_path)
        
        try:
            # Read enough rows to find the header and data
            df_full = pd.read_excel(file_path, header=None)
            
            col_map = {}
            current_course = file_course_title
            current_teacher = file_teacher_name
            
            # Process rows from top to bottom
            for idx in range(0, len(df_full)):
                row = df_full.iloc[idx]
                row_vals = [str(x).strip() for x in row.values if pd.notna(x)]
                
                # Detect Metadata Section (Course Title, Teacher)
                if 'Course Title' in row_vals:
                    if idx + 1 < len(df_full):
                        next_row = df_full.iloc[idx + 1]
                        for c_idx, val in enumerate(row):
                            if str(val).strip() == 'Course Title':
                                title_val = str(next_row[c_idx]).strip()
                                if title_val and title_val.lower() != 'nan':
                                    current_course = title_val
                
                # Detect Column Headers (Student ID, GR)
                if 'Student ID' in row_vals:
                    col_map = {}
                    for i, val in enumerate(row):
                        v = str(val).lower().strip()
                        if 'student id' in v: col_map['id'] = i
                        if 'student name' in v: col_map['name'] = i
                        if 'gr' == v or 'grade' in v: col_map['grade'] = i
                        if 'course title' in v: col_map['course'] = i
                    continue # Skip labels row

                if 'id' not in col_map:
                    continue

                row = df_full.iloc[idx]
                
                # Detect and handle offsets
                start_col = col_map['id']
                student_id_val = str(row[start_col]).strip().lower()
                
                if (len(student_id_val) <= 2 or student_id_val == 'nan') and start_col + 1 < len(row):
                     next_val = str(row[start_col + 1]).strip()
                     if len(next_val) > 5:
                         id_idx = col_map['id'] + 1
                         name_idx = col_map.get('name', id_idx + 1)
                         if 'name' in col_map: name_idx += 1
                         grade_idx = col_map.get('grade', name_idx + 1)
                         if 'grade' in col_map: grade_idx += 1
                         course_col_idx = col_map.get('course', -1)
                         if course_col_idx != -1: course_col_idx += 1
                     else:
                         id_idx = col_map['id']
                         name_idx = col_map.get('name', id_idx + 1)
                         grade_idx = col_map.get('grade', name_idx + 1)
                         course_col_idx = col_map.get('course', -1)
                else:
                    id_idx = col_map['id']
                    name_idx = col_map.get('name', id_idx + 1)
                    grade_idx = col_map.get('grade', name_idx + 1)
                    course_col_idx = col_map.get('course', -1)

                student_id = str(row[id_idx]).strip()
                if student_id == 'nan' or not student_id:
                    continue
                
                # Basic cleanup of ID
                if student_id.endswith('.0'): student_id = student_id[:-2]
                if len(student_id) <= 2: continue

                student_name = str(row[name_idx]).strip() if name_idx < len(row) else "Unknown"
                grade = str(row[grade_idx]).strip() if grade_idx < len(row) else "N/A"
                if grade == 'nan': grade = "N/A"
                
                row_course = "Unknown"
                if course_col_idx != -1 and course_col_idx < len(row):
                    row_course = str(row[course_col_idx]).strip()
                
                # Use current section's course if row-specific course is missing
                if (row_course == 'nan' or row_course.lower() == 'unknown'):
                    course = current_course
                else:
                    course = row_course

                if student_id not in students:
                    students[student_id] = {
                        'name': student_name,
                        'id': student_id,
                        'years': {}
                    }
                
                if students[student_id]['name'] == 'Unknown' and student_name != 'Unknown':
                    students[student_id]['name'] = student_name
                
                if year_clean not in students[student_id]['years']:
                    students[student_id]['years'][year_clean] = {
                        'grade': grade,
                        'courses': {course} if course != "Unknown" else set()
                    }
                else:
                    # Merge if already exists (handle multiple enrollments)
                    existing = students[student_id]['years'][year_clean]
                    if existing['grade'] == 'N/A' and grade != 'N/A':
                        existing['grade'] = grade
                    if course != "Unknown":
                        existing['courses'].add(course)
                    
        except Exception as e:
            print(f"    Error processing {file_path}: {e}")

    # Convert to list and fill missing years
    result = []
    sorted_years = sorted(list(all_years))
    
    for s_id, s_data in students.items():
        student_record = {
            'id': s_id,
            'name': s_data['name'],
            'history': {}
        }
        
        for year in sorted_years:
            if year in s_data['years']:
                y_data = s_data['years'][year]
                courses_list = sorted(list(y_data['courses']))
                student_record['history'][year] = {
                    'grade': y_data['grade'],
                    'course': ", ".join(courses_list) if courses_list else "Unknown"
                }
            else:
                student_record['history'][year] = {
                    'grade': 'N/A',
                    'course': 'No Enrollment'
                }
                
        years_count = sum(1 for y in sorted_years if student_record['history'][y]['course'] != 'No Enrollment')
        student_record['years_enrolled'] = years_count
        result.append(student_record)
        
    result.sort(key=lambda x: x['name'].lstrip('*-_ ').lower())
    return result, sorted_years

def main():
    print("Starting Dashboard Data Generation...")
    dashboard_data = {}
    schools = [d for d in os.listdir(ROOT_DIR) if os.path.isdir(os.path.join(ROOT_DIR, d)) and d not in ['.git', '.agent', 'recruitment_dashboard']]
    
    for school in schools:
        school_path = os.path.join(ROOT_DIR, school)
        if not any(os.path.isdir(os.path.join(school_path, d)) for d in os.listdir(school_path)):
            continue
            
        print(f"Processing School: {school}")
        dashboard_data[school] = {}
        
        if school == "March Middle School":
            # Special handling for March: bucket by Teacher
            print("  Using Teacher-based bucketing for March Middle School")
            march_files = []
            for program_dir in ['Band', 'Choir', 'Dance', 'Theatre']:
                p_path = os.path.join(school_path, program_dir)
                if os.path.exists(p_path):
                    march_files.extend(glob.glob(os.path.join(p_path, "*.xlsx")))
            
            buckets = {'Band': [], 'Choir': [], 'Dance': [], 'Theatre': []}
            for f_path in march_files:
                _, _, teacher = find_header_info(f_path)
                if "Gray" in teacher:
                    buckets['Band'].append(f_path)
                elif "Mosley" in teacher:
                    buckets['Choir'].append(f_path)
                elif "Delgado" in teacher or "Pelagio" in teacher:
                    buckets['Dance'].append(f_path)
                else:
                    # Fallback to folder name if teacher unknown
                    if "Band" in f_path: buckets['Band'].append(f_path)
                    elif "Choir" in f_path: buckets['Choir'].append(f_path)
                    elif "Dance" in f_path: buckets['Dance'].append(f_path)
                    else: buckets['Theatre'].append(f_path)
            
            for prog, f_list in buckets.items():
                if f_list:
                    print(f"   Processing March {prog} (Teacher-based)...")
                    students, years = process_files(f_list)
                    dashboard_data[school][prog] = {'years': years, 'students': students}
        else:
            programs = [d for d in os.listdir(school_path) if os.path.isdir(os.path.join(school_path, d))]
            for program in programs:
                if program not in ['Band', 'Choir', 'Dance', 'Theatre']: continue
                print(f" Processing Program: {program}")
                program_path = os.path.join(school_path, program)
                files = glob.glob(os.path.join(program_path, "*.xlsx"))
                if not files: continue
                students, years = process_files(files)
                dashboard_data[school][program] = {'years': years, 'students': students}
            
    final_data = {
        "metadata": {"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        "schools": dashboard_data
    }
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(final_data, f, indent=2)
    print(f"Dashboard data generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
