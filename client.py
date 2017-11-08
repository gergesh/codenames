import socket
import cPickle as pickle
from termcolor import colored
import sys
import select
import os
import argparse

SERVER_ADDRESS = 'localhost'
SERVER_PORT = 9003

parser = argparse.ArgumentParser(description='Argument parser, I guess')
parser.add_argument('-n', '--name', type=str, help="The player's name")
parser.add_argument('-t', '--team', type=int, help="The player's team. Should be either 1 or 2.")
parser.add_argument('--guesser', action='store_true', help="If specified, the player's role will be set to a guesser.")
parser.add_argument('--spymaster', action='store_true', help="If specified, the player's role will be set to a spymaster.")
args = parser.parse_args()
if args.name is None:
    print 'Please enter your name using -n'
    sys.exit()
name = args.name

if args.guesser and args.spymaster:
    print "You can't be both a spymaster and a guesser."

if args.team is not None:
    if args.team in ['1', '2']:
        team = int(args.team)
    else:
        print 'The team you have chosen is invalid. Please go for 1 or 2.'
        sys.exit()
else:
    # user doesn't care if he's #TEAMRED or an intel fanboy
    team = 0

if args.spymaster:
    role = 'spymaster'
elif args.guesser:
    role = 'guesser'
else:
    role = 'whatever'


class Card(object):
    def __init__(self, t):
        self.text = t
        # position is defined by its place in the list

    def __repr__(self):
        if hasattr(self, 'color'):
            return "%s %s" % (self.color, self.text)
        else:
            return "colorless %s" % self.text


def print_matrix_colored(ls):
    for line in ls:
        for cell in line:
            print colored(cell.text, cell.color.lower()) + ' '*(12-len(cell.text)),
        print


def find_in_data(d, attr):
    beg = d.find('&' + attr + '=') + len('&' + attr + '=')
    end = d.find('&', d.find('&' + attr + '=') + len('&' + attr + '=')) if d.find('&', d.find('&' + attr + '=') + len('&' + attr + '=')) != -1 else len(data)
    return d[beg:end]



def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((SERVER_ADDRESS, SERVER_PORT))
s.send('newconnection&name=%s&team=%s&role=%s' % (name, team, role))
sys.stdout.write('Connected to server. You may start playing!\n')

while True:
    socket_list = [s, sys.stdin]
    read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])
    for sock in read_sockets:
        if sock == s:
            # server socket
            data = sock.recv(4096)
            if not data:
                sys.stdout.write('Disconnected from chat server.')
                sys.exit()
            else:
                # if there is data
                # sys.stdout.write('Received data from server:\n%s\n' % repr(data))
                if data.startswith('colorreveal'):
                    # someone has pressed a word
                    i = int(find_in_data(data, 'i'))
                    j = int(find_in_data(data, 'j'))
                    col = find_in_data(data, 'color')
                    revealer = find_in_data(data, 'revealer')
                    t = find_in_data('turn')
                    turn = (t if t[-2:] != '_s' else t[:-2] + ' Spymaster').split(' ')
                    matrix[i][j].color = col
                    clear()
                    print_matrix_colored(matrix)
                    sys.stdout.write('%s has revealed the word %s.\n' % (revealer, matrix[i][j].text))
                    sys.stdout.write("It is now %s's turn.\n" % colored(' '.join(turn), turn[0].lower()))
                    sys.stdout.write('-> ')
                    sys.stdout.flush()
                elif data.startswith('gameboard'):
                    board = find_in_data(data, 'board')
                    t = find_in_data(data, 'turn')
                    turn = t if t[-2:] != '_s' else t[:-2] + ' Spymaster'
                    matrix = pickle.loads(board)
                    t = data[data.find('&turn=') + 6:data.find('&color=')]
                    turn = (t if t[-2:] != '_s' else t[:-2] + ' Spymaster').split(' ')
                    color = find_in_data(data, 'color')
                    role = find_in_data(data, 'role')
                    clear()
                    sys.stdout.write('You are a %s %s!\n' % (colored(color, color.lower()), role))
                    sys.stdout.flush()
                    print_matrix_colored(matrix)
                    sys.stdout.write("It is now %s's turn.\n" % colored(' '.join(turn), turn[0].lower()))
                    sys.stdout.write('-> ')
                    sys.stdout.flush()
                elif data.startswith('msg'):
                    sender = find_in_data(data, 'sender').strip()
                    contents = find_in_data(data, 'data').strip()
                    sys.stdout.write('New message from %s: %s\n' % (sender, contents))
                    sys.stdout.write('-> ')
                    sys.stdout.flush()
                elif data.startswith('newclue'):
                    sender = find_in_data(data, 'sender')
                    clue = find_in_data(data, 'clue')
                    t = find_in_data(data, 'turn')
                    turn = (t if t[-2:] != '_s' else t[:-2] + ' Spymaster').split(' ')
                    sys.stdout.write('New clue from %s: %s\n' % (sender, clue))
                    sys.stdout.write("It is now %s's turn.\n" % colored(' '.join(turn), turn[0].lower()))
                    sys.stdout.write('-> ')
                    sys.stdout.flush()

        else:
            # user inputted something
            line = sys.stdin.readline().strip()
            if line[0] == '/':
                # chat message
                s.send('gamereq&req=%s' % line[1:])
            else:
                s.send('chatmsg&msg=%s' % line)  # gamereq means this is not a chat message, but a command.
            sys.stdout.write('-> ')
            sys.stdout.flush()
