#! /usr/bin/env python2.7

#Main file for IRC Bot

try:
    import socket
    import sys
    import re

    import config
    from functions import *
    import err
except ImportError:
    sys.exit(err.load_module)

#None of these configuration directives can be empty, so they are checked
cfg = check_cfg(config.owner, config.search, config.server, config.nick,
        config.realName, config.log, config.cmds_list, config.quit)

if not cfg: #Some config-directives were empty
    sys.exit(err.invalid_cfg)

#Any valid channel starts with a '#' character and has no spaces
if not check_channel(config.channels):
    sys.exit(err.invalid_channels)

#name the log file to write into
dt = get_datetime()
logfile = config.log + dt['date'] + '.log'

content = 'Started on {0}:{1}, with nick: {2}'.format(config.server,
        config.port, config.nick)

try:
    log_write(logfile, dt['time'], ' <> ', content + '\n')
except IOError:
    print err.log_failure

#Start connecting
try:
    irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.socket:
    content = err.no_socket
    try:
        log_write(logfile, dt['time'], ' <> ', content + '\n')
    except IOError:
        print err.log_failure

    print content
else:
    try:
        irc.connect((config.server, config.port))
        receive = irc.recv(4096)
    except IOError:
        content = 'Could not connect to {0}:{1}'.format(config.server, config.port)

        try:
            log_write(logfile, dt['time'], ' <> ', content + '\n')
        except IOError:
            print err.log_failure

        print content

    else:
        buff = ""

        content = 'Connected to {0}:{1}'.format(config.server, config.port)
        try:
            log_write(logfile, dt['time'], ' <> ', content + '\n')
        except IOError:
            print err.log_failure

        print content

        #Authenticate
        irc.send(config.nick_auth)
        irc.send(config.user_auth)

        #Join channel(s)
        for channel in config.channels:
            irc.send(config.channel_join + channel + '\r\n')
            content = 'Joined: {0}'.format(channel)

            try:
                log_write(logfile, dt['time'], ' <> ', content + '\n')
            except IOError:
                print err.log_failure

            print content

        while config.alive:
            receive = irc.recv(4096)
            buff = buff + receive
            response = ''

            print receive
            if -1 != buff.find('\n'):
                command = buff[0 : buff.find('\n')]
                buff = buff[buff.find('\n')+1 : ]

                if -1 != command.find('PING'): #PING PONG
                    response = []
                    response.append('PONG')
                    response.append(command.split()[1])

                elif 1 < len(re.findall('!', command)) and \
                    ':' == command[command.rfind('!') - 1] and \
                    ' ' == command[command.rfind('!') - 2]:
                    #search in commands list only if the message from server
                    #contains two '!'(exclamation marks) in it
                    #one from command, the other from the user's nick

                    for k in config.cmds_list:
                        if -1 != command.find('!' + k) and \
                            (' ' == command[command.rfind('!' + k) + len(k) + 1] \
                            or '\r' == command[command.rfind('!' + k) + len(k) +1]):
                            #a command is valid only if it's at the beginning of
                            #the message

                            try: #the needed module is imported from 'cmds/'
                                mod = 'cmds.' + k
                                mod = __import__(mod, globals(), locals(), [k])
                            except ImportError: #inexistent module
                                    response = err.c_inexistent.format(k)
                            else:

                                try: #the module is 'executed'
                                    get_response = getattr(mod, k)
                                except AttributeError: #function not defined in module
                                    response = err.c_invalid.format(k)
                                else:

                                    response = get_response(command)
                                    break

                elif 0 == command.find(config.close_link):# Ping timeout
                    config.alive = False

                #send the response and log it
                if len(response):
                    if type(response) == type(str()):
                        #the module sent just a string so
                        #I have to compose the command

                        sendto = send_to(command)

                        crlf_pos = response[:-2].find('\r\n')
                        if -1 != crlf_pos: #a multi response command
                            crlf_pos = crlf_pos + 2 #jump over '\r\n'
                            response = response[:crlf_pos] + \
                                    sendto + response[crlf_pos:]

                        response = sendto + response
                    else: #the module send a command itself
                        response = ' '.join(response)

                    response = response + '\r\n'
                    irc.send(response)

                    try:
                        dt = get_datetime()
                        log_write(logfile, dt['time'], ' <> ', command + '\n')
                        log_write(logfile, dt['time'], ' <> ', response)
                    except IOError:
                        print err.log_failure

                buff = ""
        #}while config.alive

        #Quit server
        irc.send(config.quit)
        dt = get_datetime()
        try:
            log_write(logfile, dt['time'], ' <> ', config.quit)
        except IOError:
            print err.log_failure

        irc.close()

        content = 'Disconnected from {0}:{1}'.format(config.server, config.port)
        try:
            log_write(logfile, dt['time'], ' <> ', content + '\n')
        except IOError:
            print err.log_failure

        print content

