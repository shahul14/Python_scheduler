from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Employee, Shift
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shifts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/shifts/autofill")
def auto_generate_shifts():
    employees = Employee.query.all()
    if len(employees) != 4:
        return "Exactly 4 employees are required for this schedule."

    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    days = 365  # One full year

    # Define fixed 8-hour shifts
    shift_times = [
        (0, 8),   # Shift A
        (8, 16),  # Shift B
        (16, 24)  # Shift C
    ]

    for day in range(days):
        date = start_date + timedelta(days=day)

        # Rotate employee order daily
        rotation = (day % 4)
        rotated_employees = employees[rotation:] + employees[:rotation]

        # Assign 3 shifts to first 3 employees, last one gets day off
        for i, (start_hour, end_hour) in enumerate(shift_times):
            shift_start = date + timedelta(hours=start_hour)
            shift_end = date + timedelta(hours=end_hour)
            shift = Shift(
                employee_id=rotated_employees[i].id,
                start_time=shift_start,
                end_time=shift_end
            )
            db.session.add(shift)

    db.session.commit()
    return f"Automatically generated 8-hour rotating shifts for {days} days."


@app.route("/employees/add", methods=["GET", "POST"])
def add_employee():
    if request.method == "POST":
        name = request.form["name"]
        emp = Employee(name=name)
        db.session.add(emp)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("add_employee.html")

@app.route("/shifts/assign", methods=["GET", "POST"])
def assign_shift():
    employees = Employee.query.all()
    if request.method == "POST":
        emp_id = request.form["employee_id"]
        start_time = datetime.strptime(request.form["start_time"], "%Y-%m-%dT%H:%M")
        end_time = datetime.strptime(request.form["end_time"], "%Y-%m-%dT%H:%M")
        shift = Shift(employee_id=emp_id, start_time=start_time, end_time=end_time)
        db.session.add(shift)
        db.session.commit()
        return redirect(url_for("view_schedule"))
    return render_template("assign_shift.html", employees=employees)

@app.route("/shifts")
def view_schedule():
    shifts = Shift.query.join(Employee).all()
    return render_template("view_schedule.html", shifts=shifts)

if __name__ == "__main__":
    app.run(debug=True)
