from Tkinter import *
import tkMessageBox
import ttk
from ScrolledText import *
import tkFont

from subprocess import Popen
import subprocess
import os
import time
import random
import re

from workers import WorkerThread
from wifi import get_wipi_list, get_server_list

class Application(Frame):

    def submit(self, sandisk_id, nb):
	# if string does not meet requirements, display error and correct syntax
	if not re.match("^[A-Za-z0-9]{4}$", sandisk_id):
		tkMessageBox.showinfo("SSID Invalid Syntax", "Please enter inputs with format 'abc1' or 'ABC1'.\nLetters and numbers only.")
		self.SSID_entry.delete(0, END)
		return

	sandisk_id = sandisk_id.upper()
	sandisk_id = sandisk_id.replace('O','0')
	sandisk_id = sandisk_id.replace('L', '1')
	# check for ID tabs already in use
	for x in range(len(nb.tabs())):
		if sandisk_id == nb.tab(x)['text'].split()[0]:
			tkMessageBox.showerror("SSID Already In Use", "There is already a tab open for Sandisk ID: %s.\nPlease close the tab or try a different ID." % sandisk_id)
			return
        result = tkMessageBox.askyesno("SSID Confirmation", "Is SSID %s correct?" % sandisk_id)
	if result:
		self.SSID_entry.delete(0, END)
		# use default notebook page or create new one
		if 'Waiting' in nb.tab(0, option='text'):
			page = self.default_page
			output_text = self.default_text
			nb.tab(0, text='%s (LOADING)' % sandisk_id)
		else:
			page = ttk.Frame(nb)
			output_text = ScrolledText(page)
			nb.add(page, text='%s (LOADING)' % sandisk_id)
		# create notebook tab, and update GUI
		output_text.pack(expand=1, fill="both")
		self.SSID_submit.config(state=DISABLED)
		tab_id = len(nb.tabs()) - 1
		nb.select(tab_id)
		self.update_idletasks()
		
		# find available sandisks and available wipis
		wipi_list = get_wipi_list()
		self.total_wipis = len(wipi_list)
		sandisk_list = get_server_list(wipi_list)

		# remove wipis and sandisks in use
		for worker in WorkerThread.get_active():
			if worker.sandisk_id in sandisk_list:
				sandisk_list.remove(worker.sandisk_id)
			if worker.wipi_name in wipi_list: 
				wipi_list.remove(worker.wipi_name)
		
		self.available_wipis = len(wipi_list)

		# show errors for sandisks or wipis in GUI
		if sandisk_id not in sandisk_list:
			tkMessageBox.showerror("SSID Unavailable", "SanDisk ID: %s not in list of available SanDisks.\nPlease check connection or SanDisk ID." % sandisk_id)
			if len(nb.tabs()) == 1:
				nb.tab(0, text='Waiting for input')
			else:
				nb.forget(tab_id)
			self.SSID_submit.config(state=NORMAL)
			return

		if self.available_wipis == 0 or len(nb.tabs()) > self.total_wipis:
			tkMessageBox.showerror("Wifi Adapter Unavailable", "There are no available wifi adapters. \nOr try to close completed tabs.")
			if len(nb.tabs()) == 1:
				nb.tab(0, text='Waiting for input')
			else:
				nb.forget(tab_id)
			self.SSID_submit.config(state=NORMAL)
			return

		# choose random wipi and assign id
		wipi_name = random.choice(wipi_list)	
		if wipi_name not in self.wipi_dict:
			self.wipi_dict[wipi_name] = len(self.wipi_dict) + 1
		
		# update tab name
		nb.tab(tab_id, text=sandisk_id)		

		#Create worker thread with this wifi, sandisk pair
		thread = WorkerThread(wipi_name, sandisk_id, output_text, self.wipi_dict[wipi_name], nb)
		self.thread_list.append(thread)
		self.wifi.set("%s/%s wifi adapters available" % (self.total_wipis - len(nb.tabs()), self.total_wipis))
		self.SSID_submit.config(state=NORMAL)
		
		# add button to page
		button = Button(page, text='Close Tab')
		button.config(command=lambda: self.closeTab(page, thread, output_text, button))
		button.pack(side=LEFT)
		
		#Start the thread
		thread.start()

    def closeTab(self, tab, th, output_text, button):
	# prevent user from closing tab if thread is active
	if th.isAlive():
		tkMessageBox.showerror('Closing Tab Error', 'Process is still running.\n Please wait for it to finish.')
		return
	# close tab on user request
	result = tkMessageBox.askyesno('Close Tab Confirmation', 'Are you sure want to close the current tab?')
	if result:
		# update tab ids for each thread
		index = self.thread_list.index(th)
		for thread in self.thread_list[index:]:
			thread.tab_id = thread.tab_id - 1
		self.thread_list.remove(th)
		# update or destroy tab
		if len(self.nb.tabs()) == 1:
			self.nb.tab(0, text='Waiting for input')
			output_text.config(state=NORMAL)
			output_text.delete('1.0', END)
			output_text.config(state=DISABLED)
			self.wifi.set("%s/%s wifi adapters available" % (self.total_wipis - len(self.nb.tabs()) + 1, self.total_wipis))
		else:
			tab.destroy()
			self.wifi.set("%s/%s wifi adapters available" % (self.total_wipis - len(self.nb.tabs()), self.total_wipis))
		button.destroy()

    def createWidgets(self):
	# SSID label widget
	self.SSID_label = Label(self, text="Please Enter SSID:")
	self.SSID_label.grid(row=0, column=0, sticky=E)
	
	# User supplied string widget
	SSID = StringVar()
	self.SSID_entry = Entry(self, textvariable=SSID)
	self.SSID_entry.grid(row=0, column=1, sticky=W)

	# display number of available wifi adapters
	self.total_wipis = len(get_wipi_list())
	self.wifi = StringVar()
	self.wifi_label = Label(self, textvariable=self.wifi)
	self.wifi.set("%s/%s wifi adapters available" % (self.total_wipis, self.total_wipis))
	self.wifi_label.grid(columnspan=2)

	# add notebook to GUI
	self.nb = ttk.Notebook(self)

	# submit button which starts Sandisk configuration process
	self.SSID_submit = Button(self, text="Start Configuration", command=lambda: self.submit(SSID.get(), self.nb) )
	self.SSID_submit.grid(columnspan=2)

	# create default notebook page
	self.nb.grid(columnspan=2)
	self.default_page = ttk.Frame(self.nb)
	self.nb.add(self.default_page, text='Waiting for input')
	self.default_text = ScrolledText(self.default_page)
	self.default_text.pack(expand=1, fill="both")
	self.default_text.config(state=DISABLED)

    def checkThreads(self):
	workers = WorkerThread.get_active()
	# do not allow user to close program if there are still active threads
	if len(workers) != 0:
		tkMessageBox.showerror('Closing Window Error', 'Processes are still running.\n Please wait for them to finish.')
		#close = tkMessageBox.askyesno('Close Window', 'Are you absolutely sure you want to close the window? Sandisks are still being configured and disconnecting will cause them not to be configured properly!!')
		return
	self.master.destroy()
	
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.grid(sticky=N+S+E+W)
	master.rowconfigure(0, weight=1)
	master.rowconfigure(1, weight=1)
        self.createWidgets()
	self.wipi_dict = dict()
	self.thread_list = list()

root = Tk()
root.option_add("*Font", "TkDefaultFont")
tkFont.nametofont("TkDefaultFont").config(size=14)
root.resizable(width=False, height=False)
root.wm_title("Sandisk Configuration")
app = Application(master=root)
root.protocol("WM_DELETE_WINDOW", app.checkThreads)
app.mainloop()
