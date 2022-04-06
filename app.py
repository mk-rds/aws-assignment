from time import sleep
from flask import Flask, redirect,render_template,request
from datetime import datetime, timedelta
from pymysql import connections
from config import *

app = Flask(__name__)
app.secret_key = "magiv"

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)

output = {}
table = 'employee','attendance'
cursor = db_conn.cursor()

date = datetime.utcnow()
now= date.strftime("%A, %d %B, %Y at %H:%M")
headings = ("EmployeeID","First Name","Last Name","Primary Skill","Location","CheckIn")

data = (
    ("1","Tan","Ming Kit","Sleeping","Malaysia",now),
    ("2","Tan","Ming Kit","Eating","Malaysia",date),
    ("3","Tan","Ming Kit","Eating","Malaysia")
)

#MAIN PAGE
@app.route("/")
def home():
    date = datetime.now()
    # now= date.strftime("%A, %d %B, %Y at %X")
  
    return render_template("home.html",date=datetime.now())
    
#ADD EMPLOYEE DONE
@app.route("/addemp/",methods=['GET','POST'])
def addEmp():
    return render_template("AddEmp.html",date=datetime.now())

#EMPLOYEE OUTPUT
@app.route("/addemp/results",methods=['POST','GET'])
def Emp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)

#Attendance 
@app.route("/attendance/")
def checkIn():
    
    return render_template("Attendance.html",date=datetime.now(),headings=headings,data=data)

@app.route("/attendance/output")
def attendanceOutput():
    LoginTime = date
    # sleep(5)
    CheckOutTime = datetime.now()

    Working_Hour = CheckOutTime - LoginTime
    
    
    if request.method == 'POST':
        if LoginTime=='':
            LoginTime = date
        else:
            CheckOutTime = date

        Working_Hour = CheckOutTime - LoginTime

        try:
            return redirect("/attendance/")
        
        except Exception as e:
            return str(e)
    return render_template("AttendanceOutput.html",date=datetime.now(),LoginTime=LoginTime,Checkout=CheckOutTime,TotalWorkingHours=Working_Hour)

#Get Employee DONE
@app.route("/getemp/")
def getEmp():
    
    return render_template('GetEmp.html',date=datetime.now())


#Get Employee Results
@app.route("/getemp/results",methods=['GET','POST'])
def Employee():
    if request.method=='POST':
        #Get Employee
        emp_id = request.form['emp_id']
        # SELECT STATEMENT TO GET DATA FROM MYSQL
        GET_SQL = "SELECT `emp_id`,`first_name`, `last_name`, `pri_skill`, `location` FROM table WHERE `emp_id`=%s"
        cursor = db_conn.cursor()
        
        try:
            cursor.execute(GET_SQL,(emp_id,))
            # #FETCH ONLY ONE ROWS OUTPUT
            result = cursor.fetchall()

        except Exception as e:
            return render_template('GetEmp.html',date=datetime.now())
        
        finally:
            cursor.close()
    else:
         result=''
         return render_template("GetEmp.html",result=result,date=datetime.now())

    return render_template("GetEmpOutput.html",result=result,date=datetime.now())


 #Payroll Calculator  DONE
@app.route("/payroll/",methods=['GET','POST'])
def payRoll():
    return render_template('Payroll.html',date=datetime.now())

#NEED MAKE SURE THE INPUT ARE LINKED TO HERE
@app.route("/payroll/results",methods=['GET','POST'])
def CalpayRoll():
    pay = ''
    working_hour =12
    hourly_salary=12
    workday_perweek=12
    pay = (hourly_salary*working_hour*workday_perweek)
    annual = pay* 12 
    Bonus = round(annual*0.03,2)

    if request.method =='POST' and 'hour' in request.form and 'basic' in request.form and 'days'in request.form:
        print("hi")
        working_hour = float(request.form.get('hour'))
        hourly_salary = float(request.form.get('basic'))
        workday_perweek = float(request.form.get('days'))

        #Monthly salary = hourly salary * working hour per week * working days per week
        pay = round((hourly_salary*working_hour*workday_perweek),2)
        annual = float(pay) * 12 
        # Bonus if 3% of annual salary
        Bonus = annual*0.03
    else:
        print("bye")
        return render_template('Payroll.html',date=datetime.now())

    return render_template('PayrollOutput.html',date=datetime.now(), MonthlySalary= pay , AnnualSalary = annual, WorkingHours = working_hour ,Bonus=Bonus)

# RMB TO CHANGE PORT NUMBER
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True) # or setting host to '0.0.0.0'