from PyQt4.QtSql import *

class DB:
	db = None
	ok = False

	remote = ['host', 'db', 'user', 'password']
	local  = ['localhost', 'mobile', 'root', 'root']

	current = local

	def init():
		if DB.db is None:
			DB.db = QSqlDatabase.addDatabase("QMYSQL")	
			DB.db.setHostName(DB.current[0])
			DB.db.setDatabaseName(DB.current[1])
			DB.db.setUserName(DB.current[2])
			DB.db.setPassword(DB.current[3])
			DB.ok = DB.db.open()

	def query_(sql):
		if DB.db is None:
			DB.init()
		if DB.ok:
			if	DB.__DEBUG__: print(sql)
			query = QSqlQuery(DB.db)
			query.exec_(sql)
			return query
		return None

	def close():
		DB.db.close()
