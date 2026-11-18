import os
import pandas as pd
from sqlalchemy import Date, String, text
from app.database import engine, Base
import app.models  # Registers all models and constraints with Base.metadata
from auth import hash_password  # Imported from your new auth.py module

def normalize_emp_id(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s.lower() in ['nan', 'none', '']:
        return None
    if s.replace('.', '', 1).isdigit():
        return f"EMP-{int(float(s)):04d}"
    s_upper = s.upper()
    if s_upper.startswith('EMP') and '-' not in s_upper:
        num_part = ''.join(filter(str.isdigit, s_upper))
        if num_part:
            return f"EMP-{int(num_part):04d}"
    if s_upper.startswith('E') and '-' not in s_upper and s_upper[1:].isdigit():
        return f"EMP-{int(s_upper[1:]):04d}"
    return s

def run_seeder():
    print("Starting data seeding from CSV files...")
    
    # Safely drop all existing tables using SQLAlchemy metadata
    Base.metadata.drop_all(bind=engine)
    
    # Recreate tables fresh with all SQLAlchemy model constraints loaded
    Base.metadata.create_all(bind=engine)
    print("Database tables created fresh.")

    data_dir = "."

    # 1. Seed Departments
    dept_path = os.path.join(data_dir, "departments.csv")
    if os.path.exists(dept_path) and os.path.getsize(dept_path) > 0:
        df_dept = pd.read_csv(dept_path)
        for col in df_dept.select_dtypes(include=['object', 'str']).columns:
            df_dept[col] = df_dept[col].astype(str).str.strip()
        df_dept = df_dept.drop_duplicates()
        df_dept.to_sql('departments', con=engine, if_exists='append', index=False, method='multi')
        print(f"Seeded departments: {len(df_dept)} rows.")

    # 2. Seed Roles
    roles_path = os.path.join(data_dir, "roles.csv")
    if os.path.exists(roles_path) and os.path.getsize(roles_path) > 0:
        df_roles = pd.read_csv(roles_path)
        for col in df_roles.select_dtypes(include=['object', 'str']).columns:
            df_roles[col] = df_roles[col].astype(str).str.strip()
        df_roles = df_roles.drop_duplicates()
        df_roles.to_sql('roles', con=engine, if_exists='append', index=False, method='multi')
        print(f"Seeded roles: {len(df_roles)} rows.")

    # 3. Seed Employees
    emp_path = os.path.join(data_dir, "employees.csv")
    if os.path.exists(emp_path) and os.path.getsize(emp_path) > 0:
        df_emp = pd.read_csv(emp_path)
        if 'employee_id' in df_emp.columns:
            df_emp['employee_id'] = df_emp['employee_id'].apply(normalize_emp_id)
            df_emp = df_emp.drop_duplicates(subset=['employee_id'], keep='first').copy()
        
        for col in ['department_id', 'role_id', 'manager_id']:
            if col in df_emp.columns:
                df_emp[col] = df_emp[col].astype(str).str.strip().replace(['nan', 'None', ''], None)

        if 'exit_date' in df_emp.columns:
            df_emp['exit_date'] = pd.to_datetime(df_emp['exit_date'], errors='coerce').dt.date
        if 'hire_date' in df_emp.columns:
            df_emp['hire_date'] = pd.to_datetime(df_emp['hire_date'], errors='coerce').dt.date

        df_emp.to_sql(
            'employees', 
            con=engine, 
            if_exists='append', 
            index=False,
            method='multi',
            dtype={
                'employee_id': String(),
                'first_name': String(),
                'last_name': String(),
                'email': String(),
                'department_id': String(),
                'role_id': String(),
                'manager_id': String(),
                'hire_date': Date(),
                'exit_date': Date(),
            }
        )
        print(f"Seeded employees: {len(df_emp)} rows.")

    # 4. Seed Employee Assignments
    assign_path = os.path.join(data_dir, "employee_assignments.csv")
    if os.path.exists(assign_path) and os.path.getsize(assign_path) > 0:
        df_assign = pd.read_csv(assign_path)
        for col in df_assign.select_dtypes(include=['object', 'str']).columns:
            df_assign[col] = df_assign[col].astype(str).str.strip()
        if 'employee_id' in df_assign.columns:
            df_assign['employee_id'] = df_assign['employee_id'].apply(normalize_emp_id)
        if 'assignment_id' in df_assign.columns:
            df_assign = df_assign.drop_duplicates(subset=['assignment_id'], keep='first')
        else:
            df_assign = df_assign.drop_duplicates()
        df_assign.to_sql('employee_assignments', con=engine, if_exists='append', index=False, method='multi')
        print(f"Seeded employee_assignments: {len(df_assign)} rows.")

    # 5. Seed Salary Components
    comp_path = os.path.join(data_dir, "salary_components.csv")
    df_comp = pd.DataFrame()
    if os.path.exists(comp_path) and os.path.getsize(comp_path) > 0:
        df_comp = pd.read_csv(comp_path)
        for col in df_comp.select_dtypes(include=['object', 'str']).columns:
            df_comp[col] = df_comp[col].astype(str).str.strip()
            
        if 'component_name' in df_comp.columns and 'name' not in df_comp.columns:
            df_comp = df_comp.rename(columns={'component_name': 'name'})
        if 'component_type' in df_comp.columns and 'type' not in df_comp.columns:
            df_comp = df_comp.rename(columns={'component_type': 'type'})
            
        if 'component_id' in df_comp.columns:
            df_comp = df_comp.drop_duplicates(subset=['component_id'], keep='first')
            
    if df_comp.empty or 'COMP-BASIC' not in df_comp.get('component_id', pd.Series()).values:
        default_comp = pd.DataFrame([{'component_id': 'COMP-BASIC', 'name': 'Basic Salary', 'type': 'Earning', 'description': 'Standard Basic Salary'}])
        df_comp = pd.concat([df_comp, default_comp], ignore_index=True)

    valid_comp_cols = ['component_id', 'name', 'type', 'description']
    df_comp = df_comp[[c for c in valid_comp_cols if c in df_comp.columns]]

    df_comp.to_sql('salary_components', con=engine, if_exists='append', index=False, method='multi')
    print(f"Seeded salary_components: {len(df_comp)} rows.")

    # 6. Seed Salary Revisions
    rev_path = os.path.join(data_dir, "salary_revisions.csv")
    if os.path.exists(rev_path) and os.path.getsize(rev_path) > 0:
        df_rev = pd.read_csv(rev_path)
        for col in df_rev.select_dtypes(include=['object', 'str']).columns:
            df_rev[col] = df_rev[col].astype(str).str.strip()
        
        if 'new_annual_fixed' in df_rev.columns:
            df_rev = df_rev.rename(columns={'new_annual_fixed': 'amount'})
        elif 'salary' in df_rev.columns:
            df_rev = df_rev.rename(columns={'salary': 'amount'})
            
        if 'effective_from' in df_rev.columns:
            df_rev = df_rev.rename(columns={'effective_from': 'valid_from'})
        elif 'effective_date' in df_rev.columns:
            df_rev = df_rev.rename(columns={'effective_date': 'valid_from'})
            
        if 'revision_reason' in df_rev.columns:
            df_rev = df_rev.rename(columns={'revision_reason': 'reason'})

        if 'component_id' not in df_rev.columns:
            df_rev['component_id'] = 'COMP-BASIC'

        if 'employee_id' in df_rev.columns:
            df_rev['employee_id'] = df_rev['employee_id'].apply(normalize_emp_id)

        if 'revision_id' in df_rev.columns:
            df_rev = df_rev.drop_duplicates(subset=['revision_id'], keep='first')
            
        if {'employee_id', 'component_id', 'valid_from'}.issubset(df_rev.columns):
            df_rev = df_rev.drop_duplicates(subset=['employee_id', 'component_id', 'valid_from'], keep='first')

        valid_rev_cols = ['revision_id', 'employee_id', 'component_id', 'amount', 'valid_from', 'valid_to', 'reason']
        df_rev = df_rev[[c for c in valid_rev_cols if c in df_rev.columns]]

        df_rev.to_sql('salary_revisions', con=engine, if_exists='append', index=False, method='multi', chunksize=500)
        print(f"Seeded salary_revisions: {len(df_rev)} rows.")
    else:
        print("Skipped salary_revisions.csv: file is empty.")

    # 7. Seed Salary Structures (Chunked to prevent SQLite parameter limits)
    struct_path = os.path.join(data_dir, "salary_structures.csv")
    if os.path.exists(struct_path) and os.path.getsize(struct_path) > 0:
        df_struct = pd.read_csv(struct_path)
        for col in df_struct.select_dtypes(include=['object', 'str']).columns:
            df_struct[col] = df_struct[col].astype(str).str.strip()
            
        if 'monthly_amount' in df_struct.columns:
            df_struct = df_struct.rename(columns={'monthly_amount': 'base_salary'})
        elif 'amount' in df_struct.columns:
            df_struct = df_struct.rename(columns={'amount': 'base_salary'})

        if 'effective_from' in df_struct.columns:
            df_struct = df_struct.rename(columns={'effective_from': 'effective_date'})
        elif 'effective_date' not in df_struct.columns and 'date' in df_struct.columns:
            df_struct = df_struct.rename(columns={'date': 'effective_date'})
            
        if 'structure_id' in df_struct.columns:
            df_struct['structure_id'] = df_struct['structure_id'].apply(
                lambda x: f"SS-{int(float(x)):06d}" if str(x).replace('.', '', 1).isdigit() else str(x)
            )
        else:
            df_struct['structure_id'] = [f"SS-{i+1:06d}" for i in range(len(df_struct))]

        if 'employee_id' in df_struct.columns:
            df_struct['employee_id'] = df_struct['employee_id'].apply(normalize_emp_id)
            
        if 'component_id' in df_struct.columns:
            df_struct['component_id'] = df_struct['component_id'].apply(
                lambda x: 'COMP-BASIC' if str(x).isdigit() or str(x) in ['nan', 'None', ''] else str(x)
            )
        else:
            df_struct['component_id'] = 'COMP-BASIC'

        if 'effective_date' not in df_struct.columns:
            df_struct['effective_date'] = '2026-01-01'

        df_struct = df_struct.drop_duplicates(subset=['structure_id'], keep='first')

        if {'employee_id', 'component_id', 'effective_date'}.issubset(df_struct.columns):
            df_struct = df_struct.drop_duplicates(subset=['employee_id', 'component_id', 'effective_date'], keep='first')

        valid_struct_cols = ['structure_id', 'employee_id', 'component_id', 'base_salary', 'effective_date']
        df_struct = df_struct[[c for c in valid_struct_cols if c in df_struct.columns]]

        df_struct.to_sql('salary_structures', con=engine, if_exists='append', index=False, method='multi', chunksize=500)
        print(f"Seeded salary_structures: {len(df_struct)} rows.")
    else:
        print("Skipped salary_structures.csv: file is empty.")

    # 8. Seed Payrolls (Ensures table creation and multiple test rows explicitly)
    payrolls_path = os.path.join(data_dir, "payrolls.csv")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS payrolls (
                payroll_run_id VARCHAR PRIMARY KEY,
                pay_period_start VARCHAR,
                pay_period_end VARCHAR,
                total_payout FLOAT,
                status VARCHAR,
                created_at VARCHAR
            );
        """))

    if os.path.exists(payrolls_path) and os.path.getsize(payrolls_path) > 0:
        df_payrolls = pd.read_csv(payrolls_path)
        for col in df_payrolls.select_dtypes(include=['object', 'str']).columns:
            df_payrolls[col] = df_payrolls[col].astype(str).str.strip()
        df_payrolls.to_sql('payrolls', con=engine, if_exists='append', index=False, method='multi')
        print(f"Seeded payrolls: {len(df_payrolls)} rows from CSV.")
    
    # Ensure baseline multi-row records exist for testing
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT OR IGNORE INTO payrolls (payroll_run_id, pay_period_start, pay_period_end, total_payout, status, created_at)
            VALUES 
            ('PR-2026-11', '2026-11-01', '2026-11-30', 54000.00, 'completed', '2026-11-15 12:00:00'),
            ('PR-2025-01', '2025-01-01', '2025-04-30', 54000.00, 'completed', '2025-04-15 12:00:00'),
            ('PR-2024-01', '2024-01-01', '2024-04-30', 54000.00, 'completed', '2024-04-15 12:00:00');
        """))
    print("Seeded payrolls: Multiple baseline test rows ensured.")

    # 9. Seed Ledger Entries (Ensures table creation explicitly)
    ledger_path = os.path.join(data_dir, "ledger_entries.csv")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ledger_entries (
                entry_id VARCHAR PRIMARY KEY,
                account_code VARCHAR,
                debit FLOAT,
                credit FLOAT,
                transaction_date VARCHAR,
                description VARCHAR
            );
        """))

    if os.path.exists(ledger_path) and os.path.getsize(ledger_path) > 0:
        df_ledger = pd.read_csv(ledger_path)
        for col in df_ledger.select_dtypes(include=['object', 'str']).columns:
            df_ledger[col] = df_ledger[col].astype(str).str.strip()
        df_ledger.to_sql('ledger_entries', con=engine, if_exists='append', index=False, method='multi')
        print(f"Seeded ledger_entries: {len(df_ledger)} rows.")
    else:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT OR IGNORE INTO ledger_entries (entry_id, account_code, debit, credit, transaction_date, description)
                VALUES ('LEDG-001', '1000', 54000.00, 0.00, '2026-11-15 12:00:00', 'Payroll Disbursement');
            """))
        print("Seeded ledger_entries: 1 default test row added.")

    # 10. Seed Demo Users with Hashed Passwords & Roles
    print("Seeding demo user accounts...")
    from app.models import User
    from app.database import SessionLocal

    db = SessionLocal()
    demo_users = [
        {"username": "admin_user", "password": "AdminPassword123!", "role": "Admin", "is_active": True},
        {"username": "hr_user", "password": "HRPassword123!", "role": "HR", "is_active": True},
        {"username": "employee_user", "password": "EmployeePassword123!", "role": "Employee", "is_active": True},
        {"username": "inactive_user", "password": "Password123!", "role": "Employee", "is_active": False}
    ]

    for u_data in demo_users:
        existing = db.query(User).filter(User.username == u_data["username"]).first()
        if not existing:
            hashed_pw = hash_password(u_data["password"])
            db_user = User(
                username=u_data["username"],
                hashed_password=hashed_pw,
                role=u_data["role"],
                is_active=u_data["is_active"]
            )
            db.add(db_user)
    db.commit()
    db.close()
    print("Seeded users: 4 demo accounts added.")

    print("Database seeding completed successfully!")

    # Automatically print live database table counts
    print("\n--- Final Database Row Counts ---")
    with engine.connect() as conn:
        for table_name in ['departments', 'roles', 'employees', 'employee_assignments', 'salary_components', 'salary_revisions', 'salary_structures', 'payrolls', 'ledger_entries', 'users']:
            try:
                count = conn.execute(text(f"SELECT count(*) FROM {table_name};")).scalar()
                print(f"  - {table_name}: {count} rows")
            except Exception:
                pass
    print("---------------------------------\n")

if __name__ == "__main__":
    run_seeder()