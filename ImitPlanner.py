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
	def __init__(self, unitName=None, nExTotal=1):
		IEventSource.__init__(self)
		self.__unitName=unitName
		self.__nExTotal=nExTotal
		
	def getNExTotal(self):
		return self.__nExTotal
		
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
		AbstractEdSource.__init__(self, unitName, nExTotal)
		# private fields
		self.__author = author
		# solved tasks counter
		self.__exCounter=0
		# book completion flag
		self.__fComplete = False

		self.__title=title
	
	# methods for returning private fields
	def getAuthor(self):
		return self.__author
	def getTitle(self):
		return self.__title
	
	# abstract method
	def getSourceName(self):
		raise Exception("Interface method not implemented")
		
	def solveEx(self, nExSolved):
		if self.__fComplete != True:
			if nExSolved>0:
				
				# Установить MACH_EPS???
				
				if self.__exCounter+nExSolved>=self.getNExTotal():
					self.__fComplete = True
					self.__exCounter = self.getNExTotal()
					self.fireEvent(Event("Source completed!", self))
				else:
					self.__exCounter+=nExSolved
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
		output+=self.__title
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
		AbstractEdSource.__init__(self)
		self.__title=title
		self.__nDays=nDays
		self.__daysCounter=0
		self.__fComplete= False
	def solveEx(self, p):
		if self.__fComplete==False:
			self.__daysCounter+=1
			if self.__daysCounter==self.__nDays:
				self.__fComplete=True
				self.fireEvent(Event("Source completed!", self))
		else:
			raise Exception("Error! This ed. source has already been"
				" completed!")
	def getSourceName(self):
		return "Fixed Time Task"
	def getDescr(self):
		return "("+self.getSourceName()+") " + self.__title
	
class Subject(IDescriptable, IEventSource, IEventListener):
	def __init__(self, name):
		IEventSource.__init__(self)
		self.__edSourceList=[]
		# index of the current ed. source (book) in the list
		self.__curEdSourceIndex=0
		# Learning completion flag
		self.__fComplete=False
		
		self.__name=name
	
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
						(self,event.getPayload())))
				
				if self.__curEdSourceIndex<=len(self.__edSourceList):
					self.__curEdSourceIndex+=1
					if self.__curEdSourceIndex==len(self.__edSourceList):
						self.__fComplete=True
						self.fireEvent(Event("Subject completed!", 
								self))
			else:
				raise Exception("Error! This subject has already"
						+ " been completed!")
	def solveEx(self, nExSolved):
		self.__edSourceList[self.__curEdSourceIndex].solveEx(nExSolved)
		
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
		return dateType
	def getPayload(self):
		return getPayload
	
	# Predefined method to automatically convert 
	# the contents of an object to a string
	def __str__(self):
		s="("+self.__dateType.name+") "
		if self.__dateType!=DateType.ED_SOURCE:
			s+=self.__payload.getDescr()
		else:
			s+= ("("+self.__payload[0].getDescr()+") "
					+ self.__payload[1].getDescr())
			
		
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
	def getSubjName(self):
		return self.__subjName
	def getSubjPerf(self):
		return self.__subjPerf
		
class TimeInterval(object):
	def __init__(self, ms1, ms2):
		self.__ms1=ms1
		self.__ms2=ms2
		self.__sharedPerfSubjRecords=[]
		self.__fixedPerfSubjRecords=[]
	def getStartDate(self):
		return self.__ms1.getDate()
	def getEndDate(self):
		return self.__ms2.getDate()
	def addSharedPerfSubjRecord(self, subjRecord):
		self.__sharedPerfSubjRecords.append(subjRecord)
	def addFixedPerfSubjRecord(self, subjRecord):
		self.__fixedPerfSubjRecords.append(subjRecord)
	def getSharedPerfSubjRecords(self):
		# protection from changes
		return tuple(self.__sharedPerfSubjRecords)
	def getFixedPerfSubjRecords(self):
		# protection from changes
		return tuple(self.__fixedPerfSubjRecords)

class ImitPlanner(IEventSource, IEventListener):
	def __init__(self, trainingModes):
		IEventSource.__init__(self)
		self.__subjectList=[]
		self.__trainingModes=trainingModes
		self.__milestoneList = []

	def addSubject(self, subject):
		self.__subjectList.append(subject)
		subject.addEventListener(self)
		
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
		return (self.__milestoneList[l-1].getDate()
					- self.__milestoneList[0].getDate())
	
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
			if fFirstValue==True:
				nTrainingModes=len(self.__trainingModes[subject])
			else:
				if len(self.__trainingModes[subject])!=nTrainingModes:
					raise Exception("Error! Each subject should have "
						+ "the same number of training modes")
		
		if len(self.__milestoneList)!=nTrainingModes+1:
			raise Exception("Error! The number of training modes must"
					+ " be 1 less than the number of milestones")
		
		if nTrainingModes<1:
			raise Exception("Error! The number of training modes must "
			+"be at least 1")
		return 0
		
	# The function generates key dates by simulation. 
	# Returns true if there is enough time to study all subjects.
	def genKeyDates(self):
		
		self.__inputValidation()
		
		startDate = self.__milestoneList[0].getDate()
		endDate = (
			self.__milestoneList[len(self.__milestoneList)-1].getDate())
			
		self.__refreshCurDate()
		msCounter=0
		
		if len(self.__trainingModes)==0:
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
			
			
			# Studying objects with shared ed. performance 
			# (second value - 0). If the study of one of these subjects 
			# is completed, then the released resources are 
			# redistributed to the remaining subjects.
			# It is assumed that the complexity of the tasks 
			# is approximately the same
			
			# The number of subjects with shared performance, the study 
			# of which has not yet been completed
			nSharedSubjects=0
			
			# Total available performance (number of problems)
			sharedPerformance=0
			
			# Calculation of nSharedSubjects and sharedPerfomance
			for subject in self.__subjectList:
				# if at a given time interval the subject is studied 
				# as part of a group of subjects with x
				if self.__trainingModes[subject][msCounter-1][1]==0:
					sharedPerformance += (
						self.__trainingModes[subject][msCounter-1][0])
					# if its study is already completed
					if subject.isFinished()==False:
						nSharedSubjects+=1
				else:
					# Processing subjects with a fixed performance
					# When their study is completed, the released 
					# resources are not redistributed 
					# in favor of other subjects.
					if subject.isFinished()==False:
						subject.solveEx(
						self.__trainingModes[subject][msCounter-1][0])
					
			if nSharedSubjects>0:
				# Calculation of resource reallocation for items with 
				# shared training performance
				performancePerSubject = (
						sharedPerformance/nSharedSubjects)
				for subject in self.__subjectList:
					if self.__trainingModes[subject][msCounter-1][1]==0:
							if subject.isFinished()==False:
								subject.solveEx(performancePerSubject)
			
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
	
	def genTimeIntDescrRecords(self):
		self.__inputValidation()
		for i in range(0, len(self.__milestoneList)-1):
			interval = TimeInterval(self.__milestoneList[i],
					self.__milestoneList[i+1])
			for subject in self.__subjectList:
				if self.__trainingModes[subject][i][1]==0:
					interval.addSharedPerfSubjRecord(
							TimeIntervalDescrRecord(subject, 
								self.__trainingModes[subject][i][0]))
				else:
					interval.addFixedPerfSubjRecord(
								TimeIntervalDescrRecord(subject, 
								self.__trainingModes[subject][i][0]))
			self.fireEvent(Event("Interval Descr!",	interval))
		
class SimpleView(IEventListener):
	
	def __showSubjRecords(self, recordsTuple):
		for record in recordsTuple:
				print("\t",record.getSubjName(),": ", 
						record.getSubjPerf()," elem. task/day")
		
	def onEvent(self, event):
		if event.getMessage()=="KeyDate":
			print(event.getPayload())
		elif event.getMessage()=="Interval Descr!":
			interval=event.getPayload()
			print("***", interval.getStartDate(),
					"-",interval.getEndDate(), "***")
			print("Subjects with shared training performance:")
			self.__showSubjRecords(interval.getSharedPerfSubjRecords())
			print("Subjects with fixed training performance:")
			self.__showSubjRecords(interval.getFixedPerfSubjRecords())
		elif event.getMessage()=="Promt":
			print(event.getPayload())
