import sys
import logging

import os

import thread
import threading

# needed for py2exe
import zope.interface
from twisted.internet import reactor
from twisted.internet import error
from twisted.python import log

import autobahn.resource
from autobahn.websocket import HttpException, WebSocketServerFactory, WebSocketServerProtocol, listenWS
from autobahn import httpstatus

import json

import time

import subprocess


import base64
import tempfile

import platform

try:
	import servicemanager
	import _winreg as winreg
	import itertools
except ImportError:
	pass

import gtk

debug = False;

logging.basicConfig(filename='app.log', level=logging.INFO)
logging.info("Starting")

def logout_user_linux(websocket, quit_string):
	d = gtk.Dialog()
	d.add_buttons(gtk.STOCK_OK, 1, gtk.STOCK_CANCEL, 2)

	label = gtk.Label(quit_string)
	label.show()
	d.vbox.pack_start(label)

	result = d.run()
	d.destroy()
	while gtk.events_pending():
		gtk.main_iteration()

	if result == 1:
		print "user selected quit"
		websocket.sendMessage(json.dumps({"type":"user_logout_dialog","success":True}))
		quitWay = logout_way()
        time.sleep(1)
        try:
            if quitWay == 0:
		        os.system("gnome-session-quit --logout --no-prompt")
            else:
                # Older Ubuntu Method to Logout
                os.system("gnome-session-save --logout")
        except:
		    websocket.sendMessage(json.dumps({"type":"user_logout_dialog","success":False}))
		    do_logout_user_linux(websocket, "You REALLY need to log out now.")

def do_logout_user_linux(websocket, quit_string):
	# Create a thread as follows
	try:
		thread.start_new_thread(logout_user_linux, (websocket, quit_string,))
	except:
		print "Error: unable to start thread"

def logout_way():
    # a way to find out how the system logs out
    return subprocess.call(["which", "gnome-session-quit"])

def fucking_check_permissions_linux():
	return os.system("groups | grep $(ls -l /dev/* | grep /dev/ttyS0 | cut -d ' ' -f 5)")

def check_permissions_linux(websocket):
	retval = fucking_check_permissions_linux()
	if retval == 0:
		websocket.sendMessage(json.dumps({"type":"check_permissions","correct":True}))
	else:
		websocket.sendMessage(json.dumps({"type":"check_permissions","correct":False}))

def fucking_fix_permissions_linux():
	return os.system("pkexec gpasswd -a `whoami` $(ls -l /dev/* | grep /dev/ttyS0 | cut -d ' ' -f 5)")

def fix_permissions_linux(websocket):
	retval = fucking_fix_permissions_linux()
	if retval == 0:
		websocket.sendMessage(json.dumps({"type":"permissions_fixing_output","success":True}))
	else:
		websocket.sendMessage(json.dumps({"type":"permissions_fixing_output","success":False, "error": retval}))

def do_fix_permissions_linux(websocket):
	# Create a thread as follows
	try:
		thread.start_new_thread(fix_permissions_linux, (websocket,))
	except:
		print "Error: unable to start thread"


class EchoServerProtocol(WebSocketServerProtocol):
	def onMessage(self, msg, binary):
		try:
			message = json.loads(msg)
		except ValueError:
			logging.info("Received message: %s", msg)
			print "Received message: ", msg
		if message["type"] == "ack":
			self.sendMessage(msg, binary)
		else:
			logging.info("Received message: %s", msg)
			print "Received message: ", msg


		if message["type"] == "version":
			self.sendMessage(json.dumps({"type":"version", "version":"0.1"}) ,binary)
		elif message["type"] == "check_permissions":
			check_permissions_linux(self)
		elif message["type"] == "fix_permissions":
			do_fix_permissions_linux(self)
		elif message["type"] == "logout_user":
			do_logout_user_linux(self, "You need to log out of your system to complete the process.")
		elif message["type"] == "close":
			exit_program("Permission Fixer Exiting..")


	def onConnect(self, request):
		if(debug):
			print "peer " + str(request.peer)
			print "peer_host " + request.peer.host
			print "peerstr " + request.peerstr
			print "headers " + str(request.headers)
			print "host " + request.host
			print "path " + request.path
			print "params " + str(request.params)
			print "version " + str(request.version)
			print "origin " + request.origin
			print "protocols " + str(request.protocols)

		#TODO: For development purposes only. Fix this so it doesn't work for null (localhost) as well.
		if(request.peer.host != "127.0.0.1" or (request.origin != "null" and request.origin != "http://codebender.cc"  and request.origin != "https://codebender.cc")):
			raise HttpException(httpstatus.HTTP_STATUS_CODE_UNAUTHORIZED[0], "You are not authorized for this!")

	def onOpen(self):
		self.factory.register(self)
		self.sendMessage(json.dumps({"text":"Socket Opened"}));

	def connectionLost(self, reason):
		self.factory.unregister(self)
		WebSocketServerProtocol.connectionLost(self, reason)

################### CUSTOM FACTORY ###################
class BroadcastServerFactory(WebSocketServerFactory):
	"""
	Simple broadcast server broadcasting any message it receives to all
	currently connected clients.
	"""

	def __init__(self, url):
		WebSocketServerFactory.__init__(self, url)
		self.clients = []
		self.tick()

	def tick(self):
		self.broadcast(json.dumps({"type":"heartbeat"}))
		reactor.callLater(1, self.tick)

	def register(self, client):
		if not client in self.clients:
			print "registered client " + client.peerstr
			self.clients.append(client)

	def unregister(self, client):
		if client in self.clients:
			print "unregistered client " + client.peerstr
			self.clients.remove(client)

	def broadcast(self, msg):
		# print "broadcasting message '%s' .." % msg
		for c in self.clients:
			c.sendMessage(msg)
			# print "message sent to " + c.peerstr

################### END CUSTOM FACTORY ###################

def exit_program(exit_code):
	d = gtk.Dialog()
	d.add_buttons(gtk.STOCK_QUIT, 1)

	label = gtk.Label(exit_code)
	label.show()
	d.vbox.pack_start(label)

	d.run()
	d.destroy()

	print exit_code
	os._exit(0)


log.startLogging(sys.stdout)

def showDialog(message):
	d = gtk.Dialog()
	d.add_buttons(gtk.STOCK_OK, 1)

	label = gtk.Label(message)
	label.show()
	d.vbox.pack_start(label)

	d.run()
	d.destroy()
	while gtk.events_pending():
		gtk.main_iteration()

def main():

	showDialog("Permissions Fixer Started.\n\nReturn to the codebender walkthrough\nto complete the process.\n")

	try:
		ServerFactory = BroadcastServerFactory

		factory = ServerFactory("ws://localhost:9009")
		# factory = WebSocketServerFactory("ws://localhost:9000", debug = False)
		factory.protocol = EchoServerProtocol
		listenWS(factory)

		reactor.run()
	except error.CannotListenError, e:
		exit_program('ERROR: Could not communicate with the browser.\nSome other service is using the port (9009).\nPlease contact us at girder@codebender.cc\n')


# ?
if __name__ == '__main__':
	main()
