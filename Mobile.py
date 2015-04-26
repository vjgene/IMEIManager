import cmd
from DB import DB
import sys
from PyQt4.Qt import *

DB.__DEBUG__ = False
################################################################# Imei ##########################################################

class Imei(QDialog):

	OPS = ['Add Imei', 'Update Imei']
	ADD,EDIT=0,1

	def __init__(self, parent=None, operation=ADD,items=None):
		super(Imei,self).__init__(parent)
		self.leadsDialog = parent
		self.items = items
		self.operation = operation
		self.setWindowTitle(Imei.OPS[operation])
		self.buildForm()
		
	def buildForm(self):
		combo_labels = ["Network", "Model", "Customer", "Vendor"]
		[setattr(self,x[0]+'Query',x[1]) for x in list(map(lambda a: [a,'select distinct {0} from imei'.format(a)], combo_labels))]
		[setattr(self, x, QTextEdit()) for x in ["imei", "comments"]]
		fl = QFormLayout()
		self.combos= []
		[self.addComboBox(x+'Query') for x in combo_labels]
		fl.addRow(QLabel("IMEI"), self.imei)
		if	self.operation == Imei.EDIT:
			self.imei.setText(self.items[0])
			self.comments.setText(self.items[5])
			[x.setCurrentIndex(x.findText(self.items[1:5][i])) for i,x in enumerate(self.combos)]
		[fl.addRow(QLabel(x), self.combos[i])	for i,x in enumerate(combo_labels)]
		fl.addRow(QLabel("Comments"), self.comments)
		self.buttons = [QPushButton("Save"), QPushButton("Reset")]
		[self.connect(x, SIGNAL("clicked()"), getattr(self,x.text())) for x in self.buttons]
		self.buildLayout(fl)

	def buildLayout(self, fl):
		self.layout = QVBoxLayout()
		formBoxLayout = QHBoxLayout()
		formBoxLayout.addLayout(fl)
		formBoxLayout.addStretch(1)
		self.layout.addLayout(formBoxLayout)
		boxLayout = QHBoxLayout()
		list(map(boxLayout.addWidget, self.buttons))
		boxLayout.addStretch(1)
		self.layout.addLayout(boxLayout)
		self.layout.addStretch(1)
		self.setLayout(self.layout)

	def Reset(self):
		[i.setText(None)	for i in self.textFields]

	def addTextField(self, label):
		tx = QTextEdit(); 
		self.textFields.append(tx)

	def addComboBox(self, query):
		cb = QComboBox(self)
		cb.setEditable(True)
		res = DB.query_(getattr(self,query))
		cb.addItem(None)
		while res.next():
			cb.addItem(res.value(0))
		self.combos.append(cb)

	def Save(self):
		imeis = []
		[imeis.append(x.strip()) for x in self.imei.toPlainText().split('\n') if x.strip()]
		imeis = list(set(imeis))
		for x in imeis:
			if not self.luhn(x):
				QMessageBox.critical(self, "Error", "Skipping invalid Imei {0}".format(x))
				imeis.remove(x)
		vals = [self.comments.toPlainText()] + [x.currentText() for x in self.combos]
		if	self.operation == Imei.EDIT:
			DB.query_("update imei set comments='%s',network='%s',model='%s',customer='%s',vendor='%s' where imei='{0}'".format(imeis[0]) % tuple([self.comments.toPlainText()]+[x.currentText() for x in self.combos]))
		else:
			[DB.query_("insert into imei(imei,comments,network,model,customer,vendor) values('{0}','%s','%s','%s','%s','%s')".format(x) % tuple(vals)) for x in imeis]
		self.leadsDialog.leads.populateTable()
		self.accept()

	def luhn(self,n):
		r = [int(ch) for ch in str(n)][::-1]
		return (sum(r[0::2]) + sum(sum(divmod(d*2,10)) for d in r[1::2])) % 10 == 0

################################################################# ListLeads ##########################################################

class ListLeads(QWidget):
	LIST_QUERY = 'select created,imei,network,model,unlockstatus,customer,vendor,comments,vendorpaid,customerpaid from imei'

	def __init__(self, parent=None):
		super(ListLeads,self).__init__(parent)
		self.leadsDialog = parent
		self.buildPage()
		self.populateTable()

	def createPushButtons(self):
		self.filterText = QLineEdit()
		self.filterText.setPlaceholderText("Enter Filter Text")
		self.pushButtons = list(map(lambda txt: QPushButton(txt), ["Add","Edit","Delete","Unlock","VendorPaid","CustomerPaid","Filter"]))
		buttons = QHBoxLayout()
		list(map(buttons.addWidget, self.pushButtons[:6] + [self.filterText] + self.pushButtons[6:]))
		[self.connect(x, SIGNAL("clicked()"), getattr(self,x.text().replace(' ','')+'_')) for x in self.pushButtons]
		buttons.addStretch(1)
		return buttons

	def Unlock_(self):
		self.handlePushButton2('unlockstatus', 'Unlock selected Imeis?')

	def VendorPaid_(self):
		self.handlePushButton2('vendorpaid', 'Has selected vendor(s) been paid?')

	def CustomerPaid_(self):
		self.handlePushButton2('customerpaid', 'Has selected customer(s) paid?')

	def Edit_(self):
		if self.noneSelectedError(self.table.selectedItems()):	return
		Imei(self.leadsDialog, Imei.EDIT, [self.table.item(self.table.currentRow(),x).text() for x in [1,2,3,5,6,7]]).exec_()

	def handlePushButton2(self, query, message):
		if self.noneSelectedError(self.table.selectedItems()):	return
		reply = QMessageBox.question(self, 'Message', message, QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
		inClause = ",".join(["'"+self.table.item(x.row(),1).text()+"'" for x in self.table.selectedIndexes()])
		res = 1 if reply==QMessageBox.Yes else 0
		DB.query_("Update imei set {0}={1} where imei in ({2})".format(query,res,inClause))
		self.populateTable()

	def Filter_(self):
		FILTER_QUERY = ListLeads.LIST_QUERY + " where created like '%{0}%' or imei like '%{0}%' or network like '%{0}%' or model like '%{0}%' or customer like '%{0}%' or vendor like '%{0}%' or comments like '%{0}%' order by created desc".format(self.filterText.text())
		self.populateTable(DB.query_(FILTER_QUERY))
		
	VERDANA_BOLD_FONT = QFont("Verdana", 9, QFont.Normal)
	
	def buildPage(self):
		mainLayout = QVBoxLayout()
		self.table = QTableWidget(0,10, self)
		[self.table.setHorizontalHeaderItem(i,QTableWidgetItem(x)) for i,x in enumerate(["Date", "Imei", "Network", "Model", "Unlocked", "Customer", "Vendor", "Comments","VendorPaid", "CustomerPaid"])]
		[self.table.horizontalHeaderItem(i).setFont(ListLeads.VERDANA_BOLD_FONT) for i in range(8)]
		splitter = [QSplitter(Qt.Vertical), QSplitter(Qt.Horizontal)]
		self.splitText = QTextEdit();	self.splitText.setMinimumSize(200,324)
		self.webView = QWebView()
		list(map(splitter[0].addWidget, [self.table, splitter[1]]))
		list(map(splitter[1].addWidget, [self.splitText, self.webView]))
		mainLayout.addLayout(self.createPushButtons())
		mainLayout.addWidget(splitter[0])
		self.setLayout(mainLayout)
		[x.setMinimumSize(1024,324) for x in [self.table, self.webView]]
		self.connect(self.table, SIGNAL("itemSelectionChanged()"), self.rowSelected)

	def populateTable(self,res=None):
		if res==None:
			res = DB.query_(ListLeads.LIST_QUERY + ' order by created desc');
		self.table.setRowCount(0)
		cnt = 0;
		while res.next():
			self.table.insertRow(self.table.rowCount())	
			self.table.setItem(cnt,0, QTableWidgetItem(res.value(0).toString(Qt.SystemLocaleShortDate)));
			[self.table.setItem(cnt,i, QTableWidgetItem((lambda x: "Yes" if x==1 else "No")(res.value(i)))) for i in [4,8,9]];
			[self.table.setItem(cnt,x, QTableWidgetItem(res.value(x))) for x in [1,2,3]+ list(range(5,8))]
			cnt+=1
		self.table.horizontalHeader().setResizeMode(QHeaderView.Stretch)

	def rowSelected(self):
		selected = self.table.selectedItems()
		if self.table.currentRow() == -1: return
		data = [self.table.item(self.table.currentRow(), i).text() for i in [6,7]]
		self.splitText.setText(data[1])

	def Add_(self):
		Imei(self.leadsDialog).exec_()

	def noneSelectedError(self, selected):
		if len(selected) < 1:	
			QMessageBox.critical(self, "Error", "Please select one or more items")
			return True

	def Delete_(self):
		if self.noneSelectedError(self.table.selectedItems()):	return
		ret = QMessageBox.warning(self, "Delete", "Do you want to delete", QMessageBox.Yes | QMessageBox.No)
		if	ret == QMessageBox.Yes:
			DB.query_("delete from imei where imei='{0}'".format(self.table.item(self.table.currentRow(),1).text()))
			self.populateTable()

################################################################# Leads Dialog ##########################################################

class ImeiDialog(QDialog):
	def __init__(self, parent=None):
		super(ImeiDialog,self).__init__(parent)
		self.leadItems = ['L&ist', 'Add', 'E&xit']
		self.createMenu()	
		hLayout = QHBoxLayout()
		hLayout.setMenuBar(self.menuBar)
		self.leads = ListLeads(self)
		hLayout.addWidget(self.leads)
		self.setLayout(hLayout)

	def changePage(self):
		idx = self.leadItems.index(self.sender().text())
		if idx==0: self.leads.populateTable()
		elif idx==1: Imei(self).exec_()

	def createMenu(self):
		self.menuBar = QMenuBar()
		self.fileMenu = QMenu("&Imei", self)
		list(map(self.fileMenu.addAction, self.leadItems))
		self.menuBar.addMenu(self.fileMenu)
		self.fileMenu.actions()[2].triggered.connect(self.accept)
		[x.triggered.connect(self.changePage) for x in self.fileMenu.actions()[0:2]]
		
##############################################################################################################################################

def main():
	app = QApplication(sys.argv)
	w = ImeiDialog()
	w.setWindowTitle("Imei Manager")
	w.show()
	sys.exit(app.exec_())
	
if __name__ == '__main__':
	main()
