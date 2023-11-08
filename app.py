from flask import Flask, flash, get_flashed_messages
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
import re
from datetime import datetime
import mysql.connector
from mysql.connector import FieldType
import connect
import secrets

app = Flask(__name__)
# Generate a secure random secret key
app.secret_key = secrets.token_hex(16)  # Change 16 to the desired key length

dbconn = None
connection = None

def getCursor():
    global dbconn
    global connection
    connection = mysql.connector.connect(user=connect.dbuser, \
    password=connect.dbpass, host=connect.dbhost, \
    database=connect.dbname, autocommit=True)
    dbconn = connection.cursor()
    return dbconn

@app.route("/")
def home():
    return render_template("base.html")

@app.route("/listdrivers")
def listdrivers():
    connection = getCursor()
    sql = '''SELECT driver.driver_id, driver.first_name, driver.surname, driver.date_of_birth, 
    driver.age, driver.caregiver, car.model, car.drive_class
    FROM driver LEFT JOIN car ON driver.car = car.car_num;'''
    connection.execute(sql)
    driverList = connection.fetchall()
    print(driverList)
    # add conditions so that I can choose different content displayed using the same template
    is_junior = False
    is_admin = False
    return render_template("driverlist.html", driver_list = driverList, is_junior = is_junior, is_admin = is_admin)    

@app.route("/listdrivers/rundetails", methods = ["GET", "POST"])
def rundetails():
    if request.method == "POST":
        # Handle POST request
        selected_driver = request.form.get("driver")
    elif request.method == "GET":
        # Handle GET request
        selected_driver = request.args.get("driver_id")
    connection = getCursor()
    # query to get a certain driver's all run details
    sql = '''SELECT d.driver_id, d.first_name,d.surname,ca.model AS car_model,ca.drive_class AS car_drive_class,
    c.course_id,c.name,r.run_num,r.seconds,r.cones, CASE WHEN r.wd = 0 THEN 'NO' WHEN r.wd = 1 THEN 'YES' ELSE NULL
    END AS wd_status,COALESCE(
        ROUND(r.seconds + COALESCE(r.cones * 5, 0) + CASE WHEN r.wd = 1 THEN 10 ELSE 0 END, 2),'dnf') AS run_total
        FROM driver d INNER JOIN run r ON d.driver_id = r.dr_id INNER JOIN course c ON r.crs_id = c.course_id
        INNER JOIN car ca ON d.car = ca.car_num WHERE d.driver_id = %s ORDER BY d.driver_id, c.course_id, r.run_num;'''
    connection.execute(sql, (selected_driver, ))
    runDetails = connection.fetchall()
    is_admin = False
    print(runDetails)
    return render_template("rundetails.html", run_details = runDetails, is_admin = is_admin)

@app.route("/listcourses")
def listcourses():
    connection = getCursor()
    connection.execute("SELECT * FROM course;")
    courseList = connection.fetchall()
    return render_template("courselist.html", course_list = courseList)

@app.route("/overallresults")
def overallresults():
    connection = getCursor()
    # sql_allCourseTime to get results of run details of six courses for each driver
    sql_allCourseTime = '''SELECT d.driver_id, CONCAT(d.surname, ' ', d.first_name, IF(d.age < 26, ' (J)', '')) AS driver_name,
    ca.model, c.course_id, c.name,
    COALESCE(
        ROUND(MIN(r.seconds + COALESCE(r.cones * 5, 0) + CASE WHEN r.wd = 1 THEN 10 ELSE 0 END), 2),'dnf') AS course_time 
    FROM driver d INNER JOIN run r ON d.driver_id = r.dr_id INNER JOIN course c ON r.crs_id = c.course_id
    INNER JOIN car ca on d.car = ca.car_num
    GROUP BY d.driver_id, d.first_name, d.surname, c.name, c.course_id ORDER BY d.driver_id, c.course_id; ''' ###calculate course time
    connection.execute(sql_allCourseTime)
    overallResult = connection.fetchall()
    print(overallResult)
    # query sql_runTotalRank to get drivers' run total and display them from the best to worst
    sql_runTotalRank = '''SELECT d.driver_id, 
    CONCAT(d.surname, ' ', d.first_name, IF(d.age < 26, ' (J)', '')) AS driver_name,
    ca.model AS car_model,
    SUM(CASE WHEN subquery.total_course_time != 'dnf' THEN 1 ELSE 0 END) AS completed_courses,
    ROUND(SUM(subquery.total_course_time), 2) AS run_total
    FROM driver d INNER JOIN (SELECT r.dr_id,r.crs_id,
    COALESCE(ROUND(SUM(r.seconds + COALESCE(r.cones * 5, 0) + CASE WHEN r.wd = 1 THEN 10 ELSE 0 END), 2),
    'dnf') AS total_course_time FROM run r GROUP BY r.dr_id, r.crs_id) AS subquery 
    ON d.driver_id = subquery.dr_id
    INNER JOIN car ca ON d.car = ca.car_num 
    GROUP BY d.driver_id, d.first_name, d.surname, ca.model ORDER BY completed_courses DESC, run_total ASC;'''
    connection.execute(sql_runTotalRank)
    runTotalRank = connection.fetchall()
    print(runTotalRank)
    return render_template("overallresults.html", overall_result = overallResult, runtotal_rank = runTotalRank)   

@app.route("/graph")
def showgraph():
    connection = getCursor()
    # Insert code to get top 5 drivers overall, ordered by their final results.
    # Use that to construct 2 lists: bestDriverList containing the names, resultsList containing the final result values
    # Names should include their ID and a trailing space, eg '133 Oliver Ngatai '
    sql = '''SELECT CONCAT(d.driver_id, ' ', d.surname, ' ', d.first_name, '    ') AS driver_name,
    ca.model AS car_model,
    SUM(CASE WHEN subquery.total_course_time != 'dnf' THEN 1 ELSE 0 END) AS completed_courses,
    ROUND(SUM(subquery.total_course_time), 2) AS run_total
    FROM driver d INNER JOIN (SELECT r.dr_id,r.crs_id,
    COALESCE(ROUND(SUM(r.seconds + COALESCE(r.cones * 5, 0) + CASE WHEN r.wd = 1 THEN 10 ELSE 0 END), 2),
    'dnf') AS total_course_time FROM run r GROUP BY r.dr_id, r.crs_id) AS subquery 
    ON d.driver_id = subquery.dr_id
    INNER JOIN car ca ON d.car = ca.car_num 
    GROUP BY d.driver_id, d.first_name, d.surname, ca.model ORDER BY completed_courses DESC, run_total ASC LIMIT 5;'''
    connection.execute(sql)
    topfive_detail = connection.fetchall()
    bestDriverList = [row[0] for row in topfive_detail]
    print(bestDriverList)
    resultsList = [row[3] for row in topfive_detail]
    print(resultsList)
    return render_template("top5graph.html", name_list = bestDriverList, value_list = resultsList)

@app.route("/adminportal")
def adminportal():
    return render_template("adminportal.html")

@app.route("/listjunior")
def listjunior():
    connection = getCursor()
    sql_viewJunior = '''SELECT d.driver_id, CONCAT(d.surname, ' ', d.first_name) AS driver_name, d.date_of_birth, 
    d.age, CONCAT(c.surname, ' ', c.first_name) AS caregiver_name, 
    ca.model, ca.drive_class FROM driver d
    LEFT JOIN driver c ON d.caregiver = c.driver_id
    LEFT JOIN car ca on d.car = ca.car_num
    WHERE d.age < 26 ORDER BY d.age DESC, d.surname;'''
    connection.execute(sql_viewJunior)
    juniorDriver = connection.fetchall()
    is_junior = True
    return render_template("driverlist.html", junior_driver = juniorDriver, is_junior = is_junior)
     
@app.route("/searchdriver", methods=["POST"])
def searchdriver():
    if request.method == "POST":
        search_text = request.form.get("search_text")
        print(search_text)
        
        if search_text:
            connection = getCursor()
            sql = '''SELECT driver.driver_id, driver.first_name, driver.surname, driver.date_of_birth, 
                driver.age, driver.caregiver, car.model, car.drive_class
                FROM driver LEFT JOIN car ON driver.car = car.car_num
                WHERE driver.first_name LIKE %s OR driver.surname LIKE %s;'''
            connection.execute(sql, (f"%{search_text}%", f"%{search_text}%"))
            searchResults = connection.fetchall()
            return render_template("searchresult.html", search_results=searchResults)
    
    return redirect(url_for("listdrivers"))

@app.route("/admin/driverlist")
def admindriver():
    connection = getCursor()
    sql_driver = '''SELECT driver.driver_id, driver.first_name, driver.surname, driver.date_of_birth, 
    driver.age, driver.caregiver, car.model, car.drive_class
    FROM driver LEFT JOIN car ON driver.car = car.car_num;'''
    connection.execute(sql_driver)
    driverList = connection.fetchall()
    sql_course = '''SELECT * FROM course;'''
    connection.execute(sql_course)
    courseList = connection.fetchall()
    is_admin = True
    return render_template("driverlist.html", is_admin = is_admin, driver_list = driverList, course_list = courseList)

@app.route("/admin/viewrundetails", methods=["GET", 'POST'])
def adminviewrun():
    if request.method == "POST":
        # Handle POST request
        selected_driver = request.form.get("driver_id")
    elif request.method == "GET":
        # Handle GET request
        selected_driver = request.args.get("driver_id")
    # Fetch the flashed messages and pass them to the template
    flash_messages = get_flashed_messages(with_categories=True)
    connection = getCursor()
    sql = '''SELECT d.driver_id, d.first_name,d.surname,ca.model AS car_model,ca.drive_class AS car_drive_class,
    c.course_id,c.name,r.run_num,r.seconds,r.cones, CASE WHEN r.wd = 0 THEN 'NO' WHEN r.wd = 1 THEN 'YES' ELSE NULL
    END AS wd_status,COALESCE(
        ROUND(r.seconds + COALESCE(r.cones * 5, 0) + CASE WHEN r.wd = 1 THEN 10 ELSE 0 END, 2),'dnf') AS run_total
        FROM driver d INNER JOIN run r ON d.driver_id = r.dr_id INNER JOIN course c ON r.crs_id = c.course_id
        INNER JOIN car ca ON d.car = ca.car_num WHERE d.driver_id = %s ORDER BY d.driver_id, c.course_id, r.run_num;'''
    connection.execute(sql, (selected_driver, ))
    runDetails = connection.fetchall()
    is_admin = True
    is_course = False
    print(runDetails)
    return render_template("rundetails.html", run_details = runDetails, is_admin = is_admin, 
                           is_course = is_course, flash_messages=flash_messages)

@app.route("/admin/viewcourserundetails", methods=["GET", 'POST'])
def adminviewcourserun():
    if request.method == "POST":
        # Handle POST request
        selected_course = request.form.get("course")
    elif request.method == "GET":
        # Handle GET request
        selected_course = request.args.get("course")
    print(selected_course)
    # Fetch the flashed messages and pass them to the template
    flash_messages = get_flashed_messages(with_categories=True)
    connection = getCursor()
    sql = '''SELECT c.course_id,c.name,d.driver_id,CONCAT(d.surname, ' ', d.first_name) AS driver_name,
    r.run_num,r.seconds,r.cones,
    CASE WHEN r.wd = 0 THEN 'NO' WHEN r.wd = 1 THEN 'YES' ELSE NULL END AS run_wd_status,
    COALESCE(
        ROUND(r.seconds + COALESCE(r.cones * 5, 0) + CASE WHEN r.wd = 1 THEN 10 ELSE 0 END, 2),
        'dnf') AS run_total FROM course c INNER JOIN run r ON c.course_id = r.crs_id 
        INNER JOIN driver d ON r.dr_id = d.driver_id WHERE c.course_id = %s;'''
    connection.execute(sql, (selected_course, ))
    courseRunDetails = connection.fetchall()
    is_admin = True
    is_course = True
    print(courseRunDetails)
    return render_template("rundetails.html", courserun_details = courseRunDetails, 
                           is_admin = is_admin, is_course = is_course, flash_messages=flash_messages)

@app.route("/editruns", methods=["GET", "POST"])
def editruns():
    if request.method == "POST":
        # Handle the form submission and update the run details in the database
        driver_id = request.form.get("driver_id")
        course_id = request.form.get("course_id")
        run_num = request.form.get("run_num")
        new_time = request.form.get("new_time")
        new_cones = request.form.get("new_cones")
        new_wd = request.form.get("new_wd")
        
        # Validate user inputs
        if not driver_id or not course_id or not run_num:
            return "Invalid request. Please try again."

        # Update the run details in the database
        connection = getCursor()
        sql = '''UPDATE run 
                 SET seconds = %s, cones = %s, wd = %s 
                 WHERE dr_id = %s AND crs_id = %s AND run_num = %s;'''
        connection.execute(sql, (new_time, new_cones, new_wd, driver_id, course_id, run_num))
        flash( "Updated successfully!")  # Flash the success message

        # Redirect to the run details page or a confirmation page
        return redirect(url_for("adminviewrun", driver_id=driver_id))
    
    # Handle the GET request to display the form
    driver_id = request.args.get("driver_id")
    course_id = request.args.get("course_id")
    run_num = request.args.get("run_num")
    
    # Fetch the existing run details from the database
    connection = getCursor()
    sql = '''SELECT r.seconds, r.cones, r.wd, d.first_name, d.surname, c.name 
         FROM run r
         JOIN driver d ON r.dr_id = d.driver_id
         JOIN course c ON r.crs_id = c.course_id
         WHERE r.dr_id = %s AND r.crs_id = %s AND r.run_num = %s;'''

    connection.execute(sql, (driver_id, course_id, run_num))
    run_details = connection.fetchone()
    
    # Pass the existing run details to the template
    existing_time, existing_cones, existing_wd, first_name, surname, course_name = run_details
    run_details = {
        "driver_id": driver_id,
        "course_id": course_id,
        "run_num": run_num,
        "existing_time": existing_time,
        "existing_cones": existing_cones,
        "existing_wd": existing_wd,
        "firstname": first_name,
        "surname": surname,
        "course_name": course_name
    }
    
    return render_template("editruns.html", run_details=run_details)

@app.route("/addnewdriver", methods=["GET", "POST"])
def adddriver():
    connection = getCursor()
    sql = '''SELECT * FROM car;'''
    connection.execute(sql)
    carList = connection.fetchall()
    print(carList)

    if request.method == "POST":
        first_name = request.form["first_name"]
        surname = request.form["last_name"]
        car_id = request.form["car"]
        
        connection = getCursor()
        insertdriver = '''INSERT INTO driver (first_name, surname, date_of_birth, age, 
        caregiver, car) VALUES (%s, %s, NULL, NULL, NULL, %s);'''
        connection.execute(insertdriver, (first_name, surname, car_id))

        # After the driver is inserted, retrieve the ID of the newly inserted driver
        get_lastid = "SELECT LAST_INSERT_ID();"
        connection.execute(get_lastid)
        driver_id = connection.fetchone()[0] 

        connection = getCursor()
        get_course = "SELECT course_id FROM course;"
        connection.execute(get_course)
        courses = [row[0] for row in connection.fetchall()]

        for aCourse in courses:
            for run_num in range(1, 3):
                newrun = '''INSERT INTO run (dr_id, crs_id, run_num, seconds, cones, wd) 
                VALUES (%s, %s, %s, NULL, NULL, 0);'''
                connection.execute(newrun, (driver_id, aCourse, run_num))
        
        flash( "New driver added successfully!")  # Flash the success message

        # Redirect to the run details page or a confirmation page
        return redirect(url_for("adminviewrun", driver_id=driver_id))

    is_junior = False
    return render_template("adddriver.html", car_list = carList, is_junior = is_junior)

@app.route("/addjunior", methods=["GET", "POST"])
def addjunior():
    connection = getCursor()
    sql_car = '''SELECT * FROM car;'''
    connection.execute(sql_car)
    carList = connection.fetchall()
    print(carList)
    sql_caregiver = '''SELECT * FROM driver WHERE age IS NULL;'''
    connection.execute(sql_caregiver)
    caregiverList = connection.fetchall()

    if request.method == "POST":
        first_name = request.form["first_name"]
        surname = request.form["last_name"]
        car_id = request.form["car"]
        dob = request.form["dob"]
        cargiver = request.form["caregiver"]

        # Convert the DOB string to a datetime object
        dob_date = datetime.strptime(dob, "%Y-%m-%d")
        # Calculate the current date
        current_date = datetime.now()
        # Calculate the age
        age = current_date.year - dob_date.year - ((current_date.month, current_date.day) < (dob_date.month, dob_date.day))

        connection = getCursor()
        insertdriver = '''INSERT INTO driver (first_name, surname, date_of_birth, age, 
        caregiver, car) VALUES (%s, %s, %s, %s, %s, %s);'''
        connection.execute(insertdriver, (first_name, surname, dob, age, cargiver, car_id))
        
        # After the driver is inserted, retrieve the ID of the newly inserted driver
        get_lastid = "SELECT LAST_INSERT_ID();"
        connection.execute(get_lastid)
        driver_id = connection.fetchone()[0] 
        # get a list of course ids
        connection = getCursor()
        get_course = "SELECT course_id FROM course;"
        connection.execute(get_course)
        courses = [row[0] for row in connection.fetchall()]

        for aCourse in courses:
            for run_num in range(1, 3):
                newrun = '''INSERT INTO run (dr_id, crs_id, run_num, seconds, cones, wd) 
                VALUES (%s, %s, %s, NULL, NULL, 0);'''
                connection.execute(newrun, (driver_id, aCourse, run_num))
        
        flash( "New driver added successfully!")  # Flash the success message

        # Redirect to the run details page or a confirmation page
        return redirect(url_for("adminviewrun", driver_id=driver_id))


    is_junior = True
    return render_template("adddriver.html", car_list = carList, caregiver_list = caregiverList, is_junior = is_junior)


if __name__ == "__main__":
    app.run(debug=True)