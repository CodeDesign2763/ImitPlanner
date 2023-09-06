 # Example of using the ImitPlanner Library
 
 # Copyright 2023 Alexander Chernokrylov <CodeDesign2763@gmail.com>
 
 # This is a part of ImitPlanner Library
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
import enum
from ImitPlanner import *
		
#Example of usage
	
book1 = Book("Book1", 800)
book2 = Book("Book2", 567)
book3 = Book("Book3", 688)
book4 = Book("Book4", 289)
book5 = Book("Book5", 22)
book6 = Book("Book6", 28)

subj1 = Subject("Subject1")
subj1.addEdSource(book1)
subj1.addEdSource(book2)
subj1.addEdSource(FixedTimeTask("Reserve", 7))

subj2 = Subject("Subject2")
subj2.addEdSource(book3)
subj2.addEdSource(book4)

subj3 = Subject("Subject3")
subj3.addEdSource(book5)
subj3.addEdSource(book6)

view = SimpleView()

planner = ImitPlanner( 
		{subj1:[[5,0],[10,0]], subj2:[[5,0],[10,0]], 
		 subj3:[[1/7,1],[1,1]]})

planner.addMilestone(Milestone(datetime.date(2023,9,5),
		"Start date"))
		
planner.addMilestone(Milestone(datetime.date(2024,1,25), 
		"Start date of intensive training period"))

planner.addMilestone(Milestone(datetime.date(2024,3,19),
		"Day before exam"))

planner.addEventListener(view)

planner.addSubject(subj1)
planner.addSubject(subj2)
planner.addSubject(subj3)

if planner.genKeyDates():
	print("The plan is possible")
else:
	print("The plan is impossible")

print("\nDescription of time intervals:")
planner.genTimeIntDescrRecords()
