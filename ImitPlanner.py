 # ImitPlanner
 
 # Copyright 2023 Alexander Chernokrylov <CodeDesign2763@gmail.com>
 
 # This program is free software: you can redistribute it and/or 
 # modify it under the terms of the GNU General Public License as 
 # published by the Free Software Foundation, either version 3 of the 
 # License, or (at your option) any later version.

 # This program is distributed in the hope that it will be useful,
 # but WITHOUT ANY WARRANTY; without even the implied warranty of
 # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 # GNU General Public License for more details.

 # You should have received a copy of the GNU General Public License
 # along with this program.  
 # If not, see <https://www.gnu.org/licenses/>.


import datetime
import math
import enum

from jinja2 import Template, Environment, FileSystemLoader

class Event(object):
	def __init__(self, message, payload=None):
		self.__message=message
		self.__payload=payload
	def getMessage(self):
		return self.__message
	def getPayload(self):
		return self.__payload

class IEventSource(object):
	def __init__(self):
		self.__eventListeners=[]
	def addEventListener(self, listener):
		self.__eventListeners.append(listener)
	def fireEvent(self, event):
		for listener in self.__eventListeners:
			listener.onEvent(event)
			
class IEventListener(object): #informal interface
	def onEvent(self, event): # abstract method
		raise Exception("Interface method not implemented")
	
class IDescriptable(object): #informal interface
	# Abstract method
	# Returns a string with a text description of the object
	def getDescr(self):
		raise Exception("Interface method not implemented")

class AbstractEdSource(IEventSource, IDescriptable):
	def __init__(self, title, unitName=None, nExTotal=1):
		IEventSource.__init__(self)
		self.__unitName=unitName
		self.__nExTotal=nExTotal
		
		# Has the source been used at least once? (issue #5)
		self.__fUse=False
		
		self.__title=title
		
	def getNExTotal(self):
		return self.__nExTotal
	
	def getTitle(self):
		return self.__title
	
	# To send a message when the source is used for the first time
	# issue #5
	def use(self, nExSolve=None, verbose=False):
		if self.__fUse==False and verbose==True:
			self.__fUse=True
			self.fireEvent(Event("Source started!", self))
		return self.solveEx(nExSolve)
		
	def solveEx(self, nExSolve):
		raise Exception("Interface method not implemented")
		
	def getSourceName(self):
		raise Exception("Interface method not implemented")
		
	# Unit of measurement (tasks, videos, pages, etc)
	def getUnitName(self):
		return self.__unitName
		
# AbstractEdSource implementation
class AbstractProblemBook(AbstractEdSource): 
	# Class constructor
	# The first parameter must be "self" in all methods
	def __init__(self, title, nExTotal, author=None, unitName=None):
		# Base class constructor call
		AbstractEdSource.__init__(self, title, unitName, nExTotal)
		# private fields
		self.__author = author
		# solved tasks counter
		self.__exCounter=0
		# book completion flag
		self.__fComplete = False

	# methods for returning private fields
	def getAuthor(self):
		return self.__author

	# abstract method
	def getSourceName(self):
		raise Exception("Interface method not implemented")
		
	def solveEx(self, nExSolved):
		if self.__fComplete != True:
			if nExSolved>0:
				
				# Установить MACH_EPS???
				
				if self.__exCounter+nExSolved>=self.getNExTotal():
					rem = self.__exCounter+nExSolved-self.getNExTotal()
					self.__fComplete = True
					self.__exCounter = self.getNExTotal()
					self.fireEvent(Event("Source completed!", self))
					return rem
				else:
					self.__exCounter+=nExSolved
					return 0
			else:
				# input validation
				raise Exception("Error! The number of solved examples"
				+ " is less then zero!")
		else:
			raise Exception("Error! This ed. source has already been"
				" completed!")
			
	def getExCounter(self):
		return self.__exCounter
		
	def getDescr(self):
		output="("+self.getSourceName()+") " 
		if self.__author!=None:
			output+=self.__author + ", "
		output+=self.getTitle()
		return output
		

class Book(AbstractProblemBook):
	def __init__(self, title, nExTotal, author=None, unitName=None):	
		AbstractProblemBook.__init__(self, title, nExTotal, 
				author, unitName)
	def getSourceName(self):
		return "BOOK"

class YTVideo(AbstractProblemBook):
	def __init__(self, title, nExTotal, author=None, unitName=None):	
		AbstractProblemBook.__init__(self, title, nExTotal, 
				author, unitName)
	def getSourceName(self):
		return "YT VIDEO"
		
# this source is considered studied after a certain number of days, 
# regardless of the value of productivity in the subject
class FixedTimeTask(AbstractEdSource):
	def __init__(self, title, nDays):
		AbstractEdSource.__init__(self, title)
		self.__nDays=nDays
		self.__daysCounter=0
		self.__fComplete= False
	def solveEx(self, p):
		if self.__fComplete==False:
			self.__daysCounter+=1
			if self.__daysCounter==self.__nDays:
				self.__fComplete=True
				self.fireEvent(Event("Source completed!", self))
			return 0
		else:
			raise Exception("Error! This ed. source has already been"
				+ " completed!")
	def getSourceName(self):
		return "Fixed Time Task"
	def getDescr(self):
		return "("+self.getSourceName()+") " + self.getTitle()

class SubjectSolveExReturnCode(enum.Enum):
	OK=0
	LOCKED=1
	
class Subject(IDescriptable, IEventSource, IEventListener):
	def __init__(self, name, startAfter=None):
		IEventSource.__init__(self)
		self.__edSourceList=[]
		# index of the current ed. source (book) in the list
		self.__curEdSourceIndex=0
		# Learning completion flag
		self.__fComplete=False
		
		self.__name=name
		self.__prevSubj=startAfter
		
		# Has the subject been used at least once? (issue #5)
		self.__fUse=False
		
		# reopened issue #1
		if startAfter!=None:
			self.__fLocked=True
		else:
			self.__fLocked=False
	
	def isLocked(self):
		return self.__fLocked

	# issue #7 
	def unlock(self):
		if (self.__prevSubj != None):
			if (self.__prevSubj.isFinished()):
				self.__fLocked=False
				return 0
			else:
				return 1
		else:
			return 1
	
	def getPrevSubject(self):
		return self.__prevSubj
	
	def addEdSource(self, book):
		# Add an element to the end of the list
		self.__edSourceList.append(book)
		book.addEventListener(self)
	
	# Event handler	
	def onEvent(self, event):
		if event.getMessage()=="Source completed!":
			if self.__fComplete==False:
				
				# Duplicate event in planner
				self.fireEvent(Event(event.getMessage(), 
						SubjectAndEdSource(self,event.getPayload())))
				
				if self.__curEdSourceIndex<=len(self.__edSourceList):
					self.__curEdSourceIndex+=1
					if self.__curEdSourceIndex==len(self.__edSourceList):
						self.__fComplete=True
						self.fireEvent(Event("Subject completed!", 
								self))
			else:
				raise Exception("Error! This subject has already"
						+ " been completed!")
		
		if event.getMessage()=="Source started!": #issue #5
			# Duplicate event in planner
				self.fireEvent(Event(event.getMessage(), 
						SubjectAndEdSource(self,event.getPayload())))
	# issue #5
	def __checkFirstUse(self, verbose):
		if self.__fUse==False and verbose==True:
			self.__fUse=True
			self.fireEvent(Event("Subject started!", self))
	
	# To comply with the DRY principle
	# def __subjProcessing(self, nExSolved, verbose):
		# self.__checkFirstUse(verbose) # issue #5
		# rem=self.__edSourceList[self.__curEdSourceIndex].use(
						# nExSolved, verbose)
		# if rem>0: # issue #6
			# if self.isFinished()==False:
				# self.__edSourceList[self.__curEdSourceIndex].use(
						# rem, verbose)
	
	def solveEx(self, nExSolved, verbose=False):

		if self.__fLocked==False:
			self.__checkFirstUse(verbose) # issue #5
			
			rem=self.__edSourceList[self.__curEdSourceIndex].use(
						nExSolved, verbose)
			if rem>0: # issue #6
				if self.isFinished()==False:
					self.__edSourceList[self.__curEdSourceIndex].use(
						rem, verbose)
						
			return SubjectSolveExReturnCode.OK
		else:
			return SubjectSolveExReturnCode.LOCKED
			
	def getNExTotal(self):
		sum=0
		for book in self.__edSourceList:
			sum+=book.getNExTotal()
		return sum
	
	def isFinished(self):
		return self.__fComplete
		
	def getName(self):
		return self.__name
		
	def getDescr(self):
		return self.getName()
		
	# For debug purpose
	def getCurEdSource(self):
		return self.__edSourceList[self.__curEdSourceIndex]
		
class DateType(enum.Enum):
	ED_SOURCE=1
	SUBJECT=2
	MILESTONE=3

class KeyDate(object):
	def __init__(self, date, dateType, fEnd, payload=None):
		self.__date=date
		self.__dateType=dateType
		self.__fEnd=fEnd
		self.__payload=payload
	def getDate(self):
		return self.__date
	def getDateType(self):
		return self.__dateType
	def getPayload(self):
		return self.__payload
	def getFEnd(self):
		return self.__fEnd
	
	# Predefined method to automatically convert 
	# the contents of an object to a string
	def __str__(self):
		s="("+self.__dateType.name+") "
		s+=self.__payload.getDescr()

		# start/end
		if self.__fEnd!=None:
			s+=" ("
			if self.__fEnd:
				s+="END"
			else:
				s+="START"
			s+=")"
		
		s+= ": "+ self.__date.isoformat()
		return s

class SubjectAndEdSource(IDescriptable):
	def __init__(self, subj, edSource):
		self.__subj=subj
		self.__edSource=edSource
	
	def getSubject(self):
		return self.__subj
	def getEdSource(self):
		return self.__edSource
	
	def getDescr(self):
		return "("+self.__subj.getDescr() + ") " \
				+ self.__edSource.getDescr()
				

class Milestone(IDescriptable):
	def __init__(self, date, descr):
		self.__date=date
		self.__descr=descr
	def getDate(self):
		return self.__date
	def getDescr(self):
		return self.__descr

class TimeIntervalDescrRecord(object):
	def __init__(self, subj, subjPerf):
		self.__subjName=subj.getName()
		self.__subjPerf=subjPerf
		self.__prevSubjName=None
		if subj.getPrevSubject()!=None:
			self.__prevSubjName=subj.getPrevSubject().getDescr()
	def getSubjName(self):
		return self.__subjName
	def getSubjPerf(self):
		return self.__subjPerf
	def getPrevSubjName(self):
		return self.__prevSubjName
		
class TimeInterval(object):
	def __init__(self, ms1, ms2):
		self.__ms1=ms1
		self.__ms2=ms2
		self.__sharedPerfSubjRecords={}
		self.__fixedPerfSubjRecords=[]
	def getStartDate(self):
		return self.__ms1.getDate()
	def getEndDate(self):
		return self.__ms2.getDate()
	def addSharedPerfSubjRecord(self, GID, subjRecord):
		d = self.__sharedPerfSubjRecords # alias
		if GID not in d:
			d[GID]=[]
		d[GID].append(subjRecord)
	def addFixedPerfSubjRecord(self, subjRecord):
		self.__fixedPerfSubjRecords.append(subjRecord)
	def getSharedPerfSubjRecords(self):
		return self.__sharedPerfSubjRecords
	def getFixedPerfSubjRecords(self):
		# protection from changes
		return tuple(self.__fixedPerfSubjRecords)
		
	def getSimpleDescr(self): # (issue #3) for jinja
		outputList=[]
		d = self.__sharedPerfSubjRecords # alias
		for GID in d:
			for intDescr in d[GID]:
				tempDict={}
				tempDict["subjName"]=intDescr.getSubjName()
				tempDict["subjPerf"]=intDescr.getSubjPerf()
				outputList.append(tempDict)
				
		for intDescr in self.__fixedPerfSubjRecords:
				tempDict={}
				tempDict["subjName"]=intDescr.getSubjName()
				tempDict["subjPerf"]=intDescr.getSubjPerf()
				outputList.append(tempDict)
				
		return {"startDate":self.getStartDate().isoformat(),
				"endDate":self.getEndDate().isoformat(),
				"descr": outputList}
				

class TrainingModesSharedFlag(enum.Enum):
	SharedMode=0
	FixedMode=1

# issue #2
class TrainingModes(object):
	def __init__ (self, trainingModes):
		self.__tm=trainingModes
	
	def getGID(self,subj, intervalIndex):
		if not self.isShared(subj, intervalIndex):
			return -1
		else:
			if len(self.__tm[subj][intervalIndex])==3:
				return self.__tm[subj][intervalIndex][2]
			else: 
				return 0 # GID is zero, if not specified
	
	def isShared(self,subj, intervalIndex):
		if (self.__tm[subj][intervalIndex][1])==\
				TrainingModesSharedFlag.SharedMode.value:
			return True
		else:
			return False
	
	def getPerf(self,subj, intervalIndex):
		return self.__tm[subj][intervalIndex][0]
	
	def getModes(self):
		return self.__tm
	
	def getNModesPerSubject(self, subject):
		return len(self.__tm[subject])
	
	def hasSubject(self, subject):
		if subject in self.__tm:
			return True
		else:
			return False

class ImitPlanner(IEventSource, IEventListener):
	def __init__(self, trainingModes):
		IEventSource.__init__(self)
		self.__subjectList=[]
		self.__trainingModes=TrainingModes(trainingModes)
		self.__milestoneList = []
		self.__subjUnlockList = []

	def addSubject(self, subject):
		self.__subjectList.append(subject)
		subject.addEventListener(self)
	
	# issue #7
	def __addSubjToUnlockList(self, subject):
		self.__subjUnlockList.append(subject)

	# issue #7
	def __unlockSubjFromUnlockList(self):
		for subject in self.__subjUnlockList:
			subject.unlock()
		
	def addMilestone(self, milestone):
		self.__milestoneList.append(milestone)
	
	def __checkMilestoneListLength(self):
		if len(self.__milestoneList)<2:
			raise Exception(("Error!"
					+ " Calculation requires at least 2 milestones"))
		return 0
	
	def __checkSubjListLength(self):
		if len(self.__subjectList)==0:
			raise Exception("Error! subjectList is empty")
		return 0
		
	# self.__curDate is used not only in method genKeyDates 
	# but also in method onEvent. Its used as a global variable
	# within its scope. 
	# Private methods are used to work with this variable
	def __refreshCurDate(self):
		self.__checkMilestoneListLength()
		self.__curDate=self.__milestoneList[0].getDate()
			
	def __incCurDate(self):
		self.__curDate+=datetime.timedelta(days=1)
	def __getCurDate(self):
		return self.__curDate
	
	# Duration of training in days
	def getNDays(self):
		self.__checkMilestoneListLength()
		l = len(self.__milestoneList)
		delta = self.__milestoneList[l-1].getDate() \
					- self.__milestoneList[0].getDate()
		return delta.days
	
	# The total number of tasks in all subjects
	def getNExTotal(self):
		n=0
		self.__checkSubjListLength()
		for subject in self.__subjectList:
			n+=subject.getNExTotal()
		return n
	
	def __inputValidation(self):
		# Input validation
		
		self.__checkMilestoneListLength()
		self.__checkSubjListLength()
		
		fFirstValue=True
		nTrainingModes=0
		for subject in self.__subjectList:
			
			# Check for the presence of all subjects OBJECT ID
			# in trainingModes (issue #4)
			if not self.__trainingModes.hasSubject(subject):
				raise Exception("Error! All subjects must" 
						+ " be in trainingModes as keys")
			
			if fFirstValue==True:
				nTrainingModes= \
					self.__trainingModes.getNModesPerSubject(subject)
			else:
				if self.__trainingModes.getNModesPerSubject(subject)!= \
						nTrainingModes:
					raise Exception("Error! Each subject should have "
						+ "the same number of training modes")
		
		if len(self.__milestoneList)!=nTrainingModes+1:
			raise Exception("Error! The number of training modes must"
					+ " be 1 less than the number of milestones")
		
		if nTrainingModes<1:
			raise Exception("Error! The number of training modes must "
			+"be at least 1")
		return 0
	
	def __add2Dict(self,dictionary, key, value):
		if key not in dictionary:
			dictionary[key]=0
		dictionary[key]+= value
		
	# The function generates key dates by simulation. 
	# Returns true if there is enough time to study all subjects.
	def genKeyDates(self, verbose=False):
		
		self.__inputValidation()
		
		# startDate & endDate calculation
		startDate = self.__milestoneList[0].getDate()
		endDate = (
			self.__milestoneList[len(self.__milestoneList)-1].getDate())
			
		# sending verbose flag information (issue #3)
		self.fireEvent(Event("fVerbose",verbose))
		
		# Current date & msCounter initialization	
		self.__refreshCurDate()
		msCounter=0
		
		if len(self.__trainingModes.getModes())==0:
			raise Exception("Error! Training mode list is empty!")
			
		while self.__getCurDate()<=endDate:
			# Milestone processing
			if (self.__getCurDate() 
					== self.__milestoneList[msCounter].getDate()):
				msCounter+=1
				self.fireEvent(Event("KeyDate",
						KeyDate(self.__getCurDate(),
						DateType.MILESTONE, None,
						self.__milestoneList[msCounter-1])))
			if msCounter==len(self.__milestoneList):
				break
			
			# Unlock subjects(issue #7)
			# Unlock items for which the study of items 
			# marked in option X was completed on the previous day
			
			self.__unlockSubjFromUnlockList()
			
			# Studying objects with shared ed. performance 
			# (second value - 0). If the study of one of these subjects 
			# is completed, then the released resources are 
			# redistributed to the remaining subjects.
			# It is assumed that the complexity of the tasks 
			# is approximately the same
			
			# Number of subjects with shared performance per GID
			nSharedSubjects={} # issue 2: dict instead of int
			
			# Available performance per GID
			sharedPerformance={} # issue 2: dict instead of int
			
			# Calculation of nSharedSubjects and sharedPerfomance values
			for subject in self.__subjectList:
				if self.__trainingModes.isShared(subject,
						msCounter-1) \
					and subject.isLocked()==False:
					
					self.__add2Dict(sharedPerformance, 
							self.__trainingModes.getGID(subject, 
								msCounter-1), 
							self.__trainingModes.getPerf(	
								subject,msCounter-1))
					
					if subject.isFinished()==False:
						self.__add2Dict(nSharedSubjects, 
							self.__trainingModes.getGID(subject, 
								msCounter-1), 1)
				else:
					# Processing subjects with a fixed performance
					# When their study is completed, the released 
					# resources are not redistributed 
					# in favor of other subjects.
					if subject.isFinished()==False:
						subject.solveEx(
						self.__trainingModes.getPerf(subject,
								msCounter-1),
								verbose)
					
			if len(nSharedSubjects)>0:
				# Calculation of resource reallocation for items with 
				# shared training performance
				performancePerSubjPerGID={} #issue #2
				for GID in nSharedSubjects:
					
					performancePerSubjPerGID[GID]= \
						sharedPerformance[GID]/nSharedSubjects[GID]
				
				for subject in self.__subjectList:
					if self.__trainingModes.isShared(subject, \
						msCounter-1) and subject.isFinished()==False \
						and subject.isLocked()==False:
							GID = self.__trainingModes.getGID(subject, 
									msCounter-1)
							subject.solveEx(
									performancePerSubjPerGID[GID],
										verbose)
			
			# Cycle step
			self.__incCurDate()
				
		# Verification of successful completion of training
		fSuccess=True
		for subject in self.__subjectList:
			if subject.isFinished()==False:
				fSuccess=False
		return fSuccess
					
	def onEvent(self, event):
		if event.getMessage()=="Source completed!":
			self.fireEvent(Event("KeyDate", 
					KeyDate(self.__getCurDate(), DateType.ED_SOURCE,
							True, event.getPayload() )))
		elif event.getMessage()=="Subject completed!":
			self.fireEvent(Event("KeyDate", 
					KeyDate(self.__getCurDate(), DateType.SUBJECT,
							True, event.getPayload() )))
			# issue 7
			for subject in self.__subjectList:
				if subject.getPrevSubject()==event.getPayload():
					self.__addSubjToUnlockList(subject)
					
					
		elif event.getMessage()=="Source started!": #issue 5
			self.fireEvent(Event("KeyDate", 
					KeyDate(self.__getCurDate(), DateType.ED_SOURCE,
							False, event.getPayload() )))
		elif event.getMessage()=="Subject started!":
			self.fireEvent(Event("KeyDate", 
					KeyDate(self.__getCurDate(), DateType.SUBJECT,
						False, event.getPayload() )))
	
	def genTimeIntDescrRecords(self):
		self.__inputValidation()
		for i in range(0, len(self.__milestoneList)-1):
			interval = TimeInterval(self.__milestoneList[i],
					self.__milestoneList[i+1])
			for subject in self.__subjectList:
				if self.__trainingModes.isShared(subject,i):
					
					GID = self.__trainingModes.getGID(subject, i)
					interval.addSharedPerfSubjRecord(GID,
						TimeIntervalDescrRecord(subject, 
							self.__trainingModes.getPerf(subject,i)))
				else:
					interval.addFixedPerfSubjRecord(
						TimeIntervalDescrRecord(subject, 
							self.__trainingModes.getPerf(subject,i)))
			self.fireEvent(Event("Interval Descr!",	interval))
	
	def sentData4PUMLGeneration(self):
		self.fireEvent(event("SetMSList", self.__milestoneList))
		self.fireEvent(event("SetNDays", self.getNDays()))
		
		
class SimpleView(IEventListener):
	
	def __showSubjRecords(self, recordsTuple):
		for record in recordsTuple:
				s=""
				if record.getPrevSubjName()!=None:
					s+=" StartAfter="+record.getPrevSubjName()
				print("\t",record.getSubjName(),": ", 
						record.getSubjPerf()," elem. task/day"
						, s)
		
	def onEvent(self, event):
		if event.getMessage()=="KeyDate":
			print(event.getPayload())
		elif event.getMessage()=="Interval Descr!":
			interval=event.getPayload()
			print("***", interval.getStartDate(),
					"-",interval.getEndDate(), "***")
			print("Subjects with shared training performance:")
			
			d = interval.getSharedPerfSubjRecords() # alias
			for GID in d:
				print("Group #",GID)
				self.__showSubjRecords(d[GID])
			
			print("Subjects with fixed training performance:")
			self.__showSubjRecords(interval.getFixedPerfSubjRecords())
			
		elif event.getMessage()=="Promt":
			print(event.getPayload())

class DataBase(object): # issue #3
	
	def __init__(self):
		self.refresh()
		
	def refresh(self):
		self.__db={}
		self.__idCounter=-1
		
	def regItem(self, item):
		if item not in self.__db:
			self.__idCounter+=1
			self.__db[item]={}
			self.__db[item]["ID"]=self.__idCounter
			
	def getID(self, item):
		if item in self.__db:
			return self.__db[item]["ID"]
		else:
			return -1
	
	def addData(self, item, key, date):
		if key=="ID":
			raise Exception("Error! Key cannot be 'ID'!")
			
		if item in self.__db:
			if key not in self.__db[item]:
				self.__db[item][key]=date
				return 0
			else:
				return -1
		else:
			raise Exception("Error! No such onbjects in DB")
	
	def getData(self, item, key, date):
		if item in self.__db:
			if key in self.__db[item]:
				return self.__db[item][key]
			else:
				raise Exception("Error! No such data!")
		else:
			raise Exception("Error! No such item!")
	
	def makeTuple(self):
		l= []
		for item in self.__db:
			l.append(self.__db[item])
		return tuple(l)

class PlantUMLCodeGenerator(IEventListener): # issue #3 
	PUML_COLORS=[
		"turquoise",
		"violet",
		"wheat",
		"orange",
		"yellowgreen",
		"darksalmon",
		"goldenrod",
		"lightgray",
		"khaki",
		"gray",
		"olive",
		"yellow"]
		
	def __init__(self):
		self.__subjDB=DataBase()
		self.__edSourceDB=DataBase()
		self.refresh()
		
	def __getColor(self, ID):
		return PlantUMLCodeGenerator.PUML_COLORS[ID % \
				len(PlantUMLCodeGenerator.PUML_COLORS)]
		
	def refresh(self):
		self.__msList=[]
		self.__startDate=None
		self.__endDate=None
		
		self.__subjDB.refresh()
		self.__edSourceDB.refresh()
		
		#self.__edSourceDict={}
		self.__intervalList=[]
		
	def onEvent(self, event):
		if event.getMessage()=="KeyDate":
			kd = event.getPayload()
			if kd.getDateType()==DateType.MILESTONE:
				if self.__startDate==None:
					self.__startDate=kd.getDate()
				self.__endDate=kd.getDate()
				ms = kd.getPayload()
				self.__msList.append(
					{"date":ms.getDate().isoformat(), 
					"descr":ms.getDescr()})
			elif kd.getDateType()==DateType.ED_SOURCE:
				subjAndSource = kd.getPayload()
				subj = subjAndSource.getSubject()
				edSource = subjAndSource.getEdSource()
				
				# Data collecting
				self.__subjDB.regItem(subj) 
				self.__edSourceDB.regItem(edSource)
				
				# determining type of edSource (string)
				self.__edSourceDB.addData(edSource,"type",
						edSource.getSourceName())
				
				# determining description of edSource (string)
				self.__edSourceDB.addData(edSource,"name",
						edSource.getTitle())
				
				# determining color
				self.__edSourceDB.addData(edSource, "color",
						self.__getColor( self.__subjDB.getID(subj) ) )
				
				# determining start and end dates
				if (kd.getFEnd()):
					self.__edSourceDB.addData(edSource, "endDate", 
							kd.getDate().isoformat())
				else:
					self.__edSourceDB.addData(edSource, "startDate", 
							kd.getDate().isoformat())
			elif kd.getDateType()==DateType.SUBJECT:
				subj = kd.getPayload()
				self.__subjDB.regItem(subj)
				self.__subjDB.addData(subj, "name", subj.getDescr())
				self.__subjDB.addData(subj, "color", 
				self.__getColor( self.__subjDB.getID(subj) ) ) 
				
		if event.getMessage()=="fVerbose":
			if event.getPayload()==False:
				raise Exception("Error! You must use 'verbose'"
						+" mode in class ImitPlanner!")
		if event.getMessage()=="Interval Descr!":
			self.__intervalList.append(
					event.getPayload().getSimpleDescr())
			
	def __getNDays(self):
		return (self.__endDate-self.__startDate).days
		
	def __inputValidation(self):
		if len(self.__msList)==0:
			raise Expression("Error! Milestone list is empty!")
		if len(self.__intervalList)==0:
			raise Expression("Error! Interval list is empty!")
		# if self.__getNDays()>0:
			# raise Expression("Error! nDays doesn't set!")
			
	def genPlantUMLCode(self, filename, title=None):
		self.__inputValidation()
		
		# Determining the start date
		startDate = self.__msList[0]["date"]
		
		# Scale calculation
		if self.__getNDays()>60:
			scale="weekly"
		else:
			scale="daily"
		
		fileLoader = FileSystemLoader("./Templates")
		env = Environment(loader=fileLoader)
		pUMLTemplate = env.get_template("gantt.tmpl")
		code = pUMLTemplate.render(title=title,
				scale=scale,
				startdate=startDate,
				msList=self.__msList,
				edSourceList=self.__edSourceDB.makeTuple(),
				subjList = self.__subjDB.makeTuple(),
				intervalList = self.__intervalList)
		
		# write generated code to file
		puml_file = open(filename, "w")
		n = puml_file.write(code)
		puml_file.close()
