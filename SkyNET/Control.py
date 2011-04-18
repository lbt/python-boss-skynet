#!/usr/bin/python
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

class WorkItemCtrl(object):
    """
    Message object for workitems
	Explicitly supports start(), stop() and die()

	A ConfigParser is available in the config attribute of start()
	messages

    """
	def __init__(self, msg):
		self.message = msg

	def start(): return msg == "start"
	def stop(): return msg == "stop"
	def die(): return msg == "die"


class ParticipantCtrl:
    """
    Message object for participant control (startup, shutdown)
    """
    pass
