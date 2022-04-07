from flask import Flask, render_template,request
from datetime import datetime
from pymysql import connections
from config import *
import boto3

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
table = 'employee'


#MAIN PAGE
@app.route("/")
def home():
    
    return render_template("home.html",date=datetime.now())
    
#ADD EMPLOYEE DONE
@app.route("/addemp/",methods=['GET','POST'])
def addEmp():
    return render_template("AddEmp.html",date=datetime.now())

#EMPLOYEE OUTPUT
@app.route("/addemp/results",methods=['GET','POST'])
def Emp():

    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']
    check_in =''
    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s,%s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location,check_in))
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
def attendance():
    return render_template("Attendance.html",date=datetime.now())

#CHECK IN BUTTON
@app.route("/attendance/checkIn",methods=['GET','POST'])
def checkIn():
    emp_id = request.form['emp_id']

    #UPDATE STATEMENT
    update_stmt= "UPDATE employee SET check_in =(%(check_in)s) WHERE emp_id = %(emp_id)s"

    cursor = db_conn.cursor()

    LoginTime = datetime.now()
    formatted_login = LoginTime.strftime('%Y-%m-%d %H:%M:%S')
    print ("Check in time:{}",formatted_login)

    try:
        cursor.execute(update_stmt, { 'check_in': formatted_login ,'emp_id':int(emp_id)})
        db_conn.commit()
        print(" Data Updated into MySQL")

    except Exception as e:
        return str(e)

    finally:
        cursor.close()
        
    return render_template("AttendanceOutput.html",date=datetime.now(),
    LoginTime=formatted_login)

#CHECK OUT BUTTON
@app.route("/attendance/output",methods=['GET','POST'])
def checkOut():

    emp_id = request.form['emp_id']
    # SELECT STATEMENT TO GET DATA FROM MYSQL
    select_stmt = "SELECT check_in FROM employee WHERE emp_id = %(emp_id)s"
    insert_statement="INSERT INTO attendance VALUES (%s,%s,%s,%s)"
    

    cursor = db_conn.cursor()
        
    try:
        cursor.execute(select_stmt,{'emp_id':int(emp_id)})
        LoginTime= cursor.fetchall()
       
        for row in LoginTime:
            formatted_login = row
            print(formatted_login[0])
        

        CheckoutTime=datetime.now()
        LogininDate = datetime.strptime(formatted_login[0],'%Y-%m-%d %H:%M:%S')
        

      
        formatted_checkout = CheckoutTime.strftime('%Y-%m-%d %H:%M:%S')
        Total_Working_Hours = CheckoutTime - LogininDate
        print(Total_Working_Hours)

         
        try:
            cursor.execute(insert_statement,(emp_id,formatted_login[0],formatted_checkout,Total_Working_Hours))
            db_conn.commit()
            print(" Data Inserted into MySQL")
            
            
        except Exception as e:
             return str(e)
                    
                    
    except Exception as e:
        return str(e)

    finally:
        cursor.close()
        
    return render_template("AttendanceOutput.html",date=datetime.now(),Checkout = formatted_checkout,
     LoginTime=formatted_login[0],TotalWorkingHours=Total_Working_Hours)

   
    

#Get Employee DONE
@app.route("/getemp/")
def getEmp():
    
    return render_template('GetEmp.html',date=datetime.now())


#Get Employee Results
@app.route("/getemp/results",methods=['GET','POST'])
def Employee():
    
     #Get Employee
     emp_id = request.form['emp_id']
    # SELECT STATEMENT TO GET DATA FROM MYSQL
     select_stmt = "SELECT * FROM employee WHERE emp_id = %(emp_id)s"

     
     cursor = db_conn.cursor()
        
     try:
         cursor.execute(select_stmt, { 'emp_id': int(emp_id) })
         # #FETCH ONLY ONE ROWS OUTPUT
         for result in cursor:
            print(result)
        

     except Exception as e:
        return str(e)
        
     finally:
        cursor.close()
    

     return render_template("GetEmpOutput.html",result=result,date=datetime.now())


 #Payroll Calculator  DONE
@app.route("/payroll/",methods=['GET','POST'])
def payRoll():
    return render_template('Payroll.html',date=datetime.now())

#NEED MAKE SURE THE INPUT ARE LINKED TO HERE
@app.route("/payroll/results",methods=['GET','POST'])
def CalpayRoll():

    select_statement="SELECT total_working_hours FROM attendance WHERE emp_id = %(emp_id)s"
    cursor = db_conn.cursor()
   

    if 'emp_id' in request.form and 'basic' in request.form and 'days'in request.form:
        emp_id = int(request.form.get('emp_id'))
        hourly_salary = int(request.form.get('basic'))
        workday_perweek = int(request.form.get('days'))

        try:
            cursor.execute(select_statement,{'emp_id': emp_id})
            WorkHour= cursor.fetchall()
            Final=0

            for row in WorkHour:
                
                Hour=row[0]
                NewHour = datetime.strptime(Hour,'%H:%M:%S.%f')
                
                total_seconds = NewHour.second + NewHour.minute*60 + NewHour.hour*3600
                Final += total_seconds
                Final = Final/3600
                working_hour= round(Final,2)
                print(Final)

        except Exception as e:
            return str(e)

        # #Monthly salary = hourly salary * working hour per week * working days per week
        pay = round((hourly_salary*working_hour*workday_perweek),2)
        annual = float(pay) * 12 
        annual = int(annual)
            # # Bonus if 3% of annual salary
        Bonus = annual*0.03
    else:
        print("Something Missing")
        return render_template('Payroll.html',date=datetime.now())

    return render_template('PayrollOutput.html',date=datetime.now(),emp_id=emp_id, MonthlySalary= pay , AnnualSalary = annual, WorkingHours = working_hour ,Bonus=Bonus)

# RMB TO CHANGE PORT NUMBER
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True) # or setting host to '0.0.0.0'