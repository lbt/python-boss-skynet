#!/usr/bin/python
# -*- coding: utf-8; tab-width: 4 -*-
import sys, traceback, signal
import ConfigParser
from  RuoteAMQP.participant import Participant
from SkyNET.Control import WorkItemCtrl
import types

DEFAULT_SKYNET_CONFIG_DIR = "/etc/skynet/"
DEFAULT_SKYNET_CONFIG_FILE = "/etc/skynet/skynet.conf"

class ParticipantHandlerNotDefined(RuntimeError):
    def __init__(self):
        super(ParticipantHandlerNotDefined, self).__init__(
                "ParticipantHandler class not found")

class InvalidParticipantHandlerSignature(RuntimeError):
    pass

class ParticipantConfigError(RuntimeError):
    def __init__(self, opt, section):
        super(ParticipantConfigError,
              self).__init__(
            "No option '%s' provided in section '%s' of any config files." %
            (opt, section))

class ExoParticipant(Participant):
    """
    This class runs the normal participant handling code.
    In order to support some sophisticated Ruote usage it writes a closure
    into the ParticipantHandler namespace called send_to_engine()
    This closure invokes *this* objects send_to_engine() method and
    uses that to call the super write_to_engine()
    """
    def __init__(self, exo=None, *args, **kwargs):
        super(ExoParticipant, self).__init__(*args, **kwargs)
        self.exo = exo
        # Write a closure into the ParticipantHandler namespace
        self.exo.handler.send_to_engine = types.MethodType(
                lambda orig_obj, wi : self.send_to_engine(wi),
                self.exo.handler, self.exo.handler.__class__)

    def consume(self):
        if self.workitem.fields.debug_dump or self.workitem.params.debug_dump:
            print self.workitem.dump()
        self.exo.handler.handle_wi(self.workitem)

    def send_to_engine(self, witem):
        self.reply_to_engine(workitem=witem)

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
          /etc/skynet/skynet.conf
          which can be overridden by the 'local_config_file'
        """
        self.queue = self.amqp_host = self.amqp_user = self.amqp_pwd = \
                self.amqp_vhost = self.code = self.name = self.config = \
                self.graceful_shutdown = None

        self.parse_config(local_config_file)

        # Dynamically load the user code.
        # We are running as a normal user anyway at this point
        # Don't catch any errors here.
        execfile(self.code, globals())

        # Create an I woinstance
        for key in ("name", "amqp_host", "amqp_user", "amqp_pwd", "amqp_vhost"):
            print "%s : %s" % (key, getattr(self, key, "???"))

        # Complain if there is no ParticipantHandler class
        try:
            self.handler = ParticipantHandler()
        except NameError, exobj:
            raise ParticipantHandlerNotDefined()
        except TypeError, exobj:
            raise InvalidParticipantHandlerSignature(str(exobj))
        except Exception, exobj:
            raise exobj

        # An ExoParticipant knows about the handler
        self.p = ExoParticipant(exo=self,
                                ruote_queue=self.queue,
                                amqp_host=self.amqp_host,
                                amqp_user=self.amqp_user,
                                amqp_pass=self.amqp_pwd,
                                amqp_vhost=self.amqp_vhost)

        # FIXME : check for the mandatory methods

    def parse_config(self, config_file):
        config = ConfigParser.SafeConfigParser()
        config.read([DEFAULT_SKYNET_CONFIG_FILE, config_file])

        self.config = config

        # Validate the BOSS section options
        section = "boss"
        for opt in ("amqp_vhost", "amqp_pwd", "amqp_user", "amqp_host"):
            if not config.has_option(section, opt):
                raise ParticipantConfigError(opt, section)
            else:
                setattr(self, opt, config.get(section, opt))
        # Make sure there is a participant name
        section = "participant"
        for opt in ("name", "code"):
            if not config.has_option(section, opt):
                raise ParticipantConfigError(opt, section)
            else:
                setattr(self, opt, config.get(section, opt))

        # If there's a queue, use it
        if config.has_option(section, "queue"):
            self.queue = config.get(section, "queue")
        else:
            self.queue = self.name

        # Finally read "/etc/skynet/<pname>.conf", not caring if it exists
        config.read([DEFAULT_SKYNET_CONFIG_DIR + self.name + ".conf"])


    # Signals and threads are tricky.
    # Ensure that only the main thread sets the handler

    # FIXME: We should see if Pika can catch Interrupted system call

    def sighandler(self, signum, frame):
        print "Caught signal", signum
        if signum == signal.SIGTERM:
            self.p.finish()
            self.graceful_shutdown = True
        elif signum == signal.SIGSTOP:
            pass
        elif signum == signal.SIGHUP:
            pass
        elif signum == signal.SIGALRM:
            pass
        elif signum == signal.SIGINT:
            pass
        else:
            pass

    def run(self):
        # Enter event loop with some trial at clean exit

        self.graceful_shutdown = False
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

                msg = WorkItemCtrl("start")
                msg.config = self.config
                self.handler.handle_lifecycle_control(msg)
                self.p.run()
                if self.graceful_shutdown:
                    break

            except KeyboardInterrupt:
                sys.exit(0)

            except IOError:
                print "p.run() interrupted - IOError"
                if self.graceful_shutdown:
                    print "Now shutting down"
                    self.handler.handle_lifecycle_control(WorkItemCtrl("die"))
                    sys.exit(1)

                print "Trying to shutdown gracefully"
                self.handler.handle_lifecycle_control(WorkItemCtrl("stop"))
                self.graceful_shutdown = True

            except Exception:
                print "p.run() interrupted"
                traceback.print_exc()
                sys.exit(1)
