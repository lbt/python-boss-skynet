#!/usr/bin/python
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-
import os, sys, traceback, imp, signal
import ConfigParser
from  RuoteAMQP.workitem import Workitem
from  RuoteAMQP.participant import Participant

try:
    import json
except ImportError:
    import simplejson as json

DEFAULT_BOSS_CONFIG_FILE = "/etc/skynet/boss.config"

if __name__ == "__main__":
    main()

class ParticipantConfigError(RuntimeError):
	def __init__(self, opt, section):
		super(ParticipantConfigError, 
			  self).__init__(
			"No option '%s' provided in section '%s' of any config files." %
			(opt, section))

class ExoParticipant(Participant):
	def __init__(self, exo=None, *args, **kwargs):
		super(ExoParticipant,self).__init__(*args, **kwargs)
		self.exo=exo

	def consume(self):
		self.exo.handler.handle_wi(self.wi)

class Exo(object):
    """
    The Exo class provides the SkyNET participant exoskeleton.  This
    allows a consistent control framework to be applied to all BOSS
    participants. It requires a ParticipantHandler class to be provided in a
    dynamically imported python file. This class must provide the
    following interface:

    ParticipantHandler.handle_wi_control(WorkItemCtrl)
      This method is called with messages relating to the work being
      done and possibly from the process engine Typically this
      includes "cancel" and "status" messages.

    ParticipantHandler.handle_lifecycle_control(ParticipantCtrl)
      This method is called by SkyNET with messages relating to the
      Participant itself. Typically this includes "shutdown" type
      messages.

    ParticipantHandler.handle_wi(Workitem)
    
      This replaces the old consume() method and passes in a Workitem;
      code like:

        def consume(self):
          wi = self.workitem
          ...

      is replaced by:

        def handle_wi(wi):
          ...

    The messages objects passed are obtained using:
      from SkyNET import (WorkItemCtrl, ParticipantCtrl, Workitem)

    In SkyNET, Exo provides:

    Exo.WorkT : This thread is where work takes place and calls 

    Exo.ControlT : This thread is where SkyNET control messages are handled

    Exo.BOSST : This thread is where BOSS control messages are handled

    Logging is done via stdout which is connected to a reliable
    logging service.

    """

    def __init__(self, local_config_file=None):
        """
        An Exo object is initialised with a config file providing values
        for this participant.

        Config information is read from the default location : 
          /etc/skynet/boss.config
          which can be overridden by the 'local_config_file'
          """

		self.parse_config(local_config_file)

		# Dynamically load the user code.
		# We are running as a normal user anyway at this point
		# Don't catch any errors here.
		execfile(self.code, globals())

		# Create an I woinstance
		print "name : %s \namqp_host: %s\namqp_user: %s\namqp_pass: %s\namqp_vhost: %s" % (
			self.name, self.amqp_host, self.amqp_user,
			self.amqp_pwd,  self.amqp_vhost)

		# Complain if there is no ParticipantHandler class
		try:
			self.handler = ParticipantHandler()
		except NameError,e:
			raise ParticipantHandlerNotDefined()
		except TypeError,e:
			raise InvalidParticipantHandlerSignature()
		except Exception,e:
			raise e

		# An ExoParticipant knows about the handler
		self.p = ExoParticipant(exo=self,
								ruote_queue=self.name,
								amqp_host=self.amqp_host,
								amqp_user=self.amqp_user,
								amqp_pass=self.amqp_pwd,
								amqp_vhost=self.amqp_vhost)

		# FIXME : check for the mandatory methods

		# Register with BOSS
		# FIXME : This is going to be a process in it's own right.
		print "Registered"
		self.p.register(self.name, {'queue':self.name})

	def parse_config(self, config_file):
        config = ConfigParser.SafeConfigParser()
        config.read([DEFAULT_BOSS_CONFIG_FILE, config_file])

		# Validate the BOSS section options
		section="boss"
		for opt in ("amqp_vhost", "amqp_pwd", "amqp_user", "amqp_host"):
			if not config.has_option(section, opt):
				raise ParticipantConfigError(opt, section)
			else:
				self.__dict__[opt] = config.get(section, opt)
		# Make sure there is a participant name
		section="participant"
		for opt in ("name", "code"):
			if not config.has_option(section, opt):
				raise ParticipantConfigError(opt, section)
			else:
				self.__dict__[opt] = config.get(section, opt)

	# Signals and threads are tricky.
	# Ensure that only the main thread sets the handler

	# FIXME: We should see if Pika can catch Interrupted system call

	def sighandler(self, signum, frame):
		print "Caught signal", signum
		if signum == signal.SIGTERM:
			pass
		elif signum == signal.SIGSTOP:
			pass
		elif signum == signal.SIGHUP:
			pass
		elif signum == signal.SIGALARM:
			pass
		elif signum == signal.SIGINT:
			pass
		else:
			pass
		
	def run(self):
		# Enter event loop with some trial at clean exit
		
		self.graceful_shutdown=False
		# while self.p.running
		while True:
			try:
				# Install a handler
				signal.signal(signal.SIGTERM, self.sighandler)
				# Now ensure that system calls are restarted.  The
				# handler won't be called until the system call
				# returns
				#
				# mmm - actually this causes python to not exit the
				# run() loop if the system is quiet. We should allow
				# run to be re-startable and escalate from graceful to
				# hard.
				#
				# signal.siginterrupt(signal.SIGTERM, False)
				self.p.run()
			except KeyboardInterrupt:
				sys.exit(0)
			except IOError:
				print "p.run() interrupted - IOError"
				if self.graceful_shutdown:
					print "Graceful didn't work - hard shutdown"
					sys.exit(1)
				print "Trying to shutdown gracefully"
				self.graceful_shutdown=True
				sys.exit(0)
			except Exception:
				print "p.run() interrupted"
				traceback.print_exc()
				sys.exit(1)
