def fun(stud_id,date,status):
	import mysql.connector
	mydb = mysql.connector.connect(
	  host="localhost",
	  user="root",
	  password="",
	  database="vc1"
	)

	mycursor = mydb.cursor()

	#sql = "UPDATE status SET status = %s WHERE id = %s"
	sql = "insert into myapp_attendance(student_id, date, status)values(%d,%s,%s)"
	#sql = "insert into wattendence(studentname,date,status)values('test','test','test')"
	#val = ("0", "1")
	val = (stud_id,date,status)

	mycursor.execute(sql, val)
	#mycursor.execute(sql)

	mydb.commit()

#status="0"
#id="1"	
#fun(status,id)

fun("test","test","test")