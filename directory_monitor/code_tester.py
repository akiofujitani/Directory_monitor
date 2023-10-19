from tkinter import *

master = Tk()
FrameBIG = Frame(master)

Main = Canvas(FrameBIG,background="blue", height = 500,width =500)
Main.configure(scrollregion=Main.bbox("all"))

scroll = Scrollbar(FrameBIG ,orient="vertical", command=Main.yview)
Main.configure(yscrollcommand=scroll.set)

scroll.pack(side="right", fill="y")
Main.pack(side = BOTTOM, anchor = NW,fill="x")
FrameBIG.pack(anchor = W, fill = "x")

Main.create_line(0, 0, 500, 1000)
Main.configure(scrollregion=Main.bbox("all"))

master.mainloop()