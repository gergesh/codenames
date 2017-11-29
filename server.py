import random
import socket
from termcolor import colored
import cPickle as pickle
import sys
from copy import deepcopy
import select

HOST = 'localhost'
PORT = 9003
GRID_SIZE = 5
ASSASSIN_COLOR = 'Cyan'
CIVILIAN_COLOR = 'Yellow'
TEAM_ONE_COLOR = 'Red'
TEAM_TWO_COLOR = 'Blue'
HIDDEN_COLOR = 'White'
ORIGINAL_DICT = 'Original.txt'
DUET_DICT = 'Duet.txt'
UNDERCOVER_DICT = 'Undercover.txt'
DICTIONARIES = [ORIGINAL_DICT, DUET_DICT]
DEFAULT_MSG = 'msg&sender=%s&data=%s'

class Card(object):
    def __init__(self, t):
        self.text = t
        # position is defined by its place in the list

    def __repr__(self):
        if hasattr(self, 'color'):
            return "%s %s" % (self.color, self.text)
        else:
            return "colorless %s" % self.text


PLAYERS_LIST = []
class Player(object):
    def __init__(self, n, c, t, r):
        self.name = n
        self.conn = c
        self.color = t
        self.role = r

    def __repr__(self):
        return "%s is a %s %s, with connection %s" % (self.name.self.color, self.role, self.conn)


def player_by_sock(s):
    for p in PLAYERS_LIST:
        if p.conn == s:
            return p
    else:
        print 'Received data from an unknown player, wtf?'


def txt_to_dict(txt, ls):
    with open(txt, 'r') as dict_file:
        for line in dict_file:
            ls.append(line)
        return ls


USED_WORDS = []
def generate_matrix(dictionary):
    """
    Receives a seed, uses it to generate a list of words the size of the from the dictionary.
    """
    # random.seed(seed)
    # no need for that since we're using a server now
    cards_grid = []
    for i in range(GRID_SIZE):
        cards_grid.append([])
        for j in range(GRID_SIZE):
            w = random.choice(dictionary).upper().strip()
            while w in USED_WORDS:
                w = random.choice(dictionary).upper().strip()
            cards_grid[i].append(Card(w))
            USED_WORDS.append(w)

    # decide who goes first
    team_one_now = random.randint(0, 1)
    if team_one_now:
        print '%s goes first!' % colored(TEAM_ONE_COLOR, TEAM_ONE_COLOR.lower())
        curr_turn = TEAM_ONE_COLOR+'_s'
    else:
        print "%s goes first!" % colored(TEAM_TWO_COLOR, TEAM_TWO_COLOR.lower())
        curr_turn = TEAM_TWO_COLOR+'_s'



    # assign red and blue colors to cards
    for i in xrange(int(GRID_SIZE * GRID_SIZE * 0.6)):  # 25 will give 15, that's all I care about.
        curr_card = cards_grid[random.randint(0, GRID_SIZE - 1)][random.randint(0, GRID_SIZE - 1)]
        while hasattr(curr_card, 'color'):
            curr_card = cards_grid[random.randint(0, GRID_SIZE - 1)][random.randint(0, GRID_SIZE - 1)]
        curr_card.color = TEAM_ONE_COLOR if team_one_now else TEAM_TWO_COLOR
        team_one_now = team_one_now != 1  # flip it

    # find assassins
    for i in xrange(int(GRID_SIZE * GRID_SIZE * 0.04)):
        curr_card = cards_grid[random.randint(0, GRID_SIZE - 1)][random.randint(0, GRID_SIZE - 1)]
        while hasattr(curr_card, 'color'):
            curr_card = cards_grid[random.randint(0, GRID_SIZE - 1)][random.randint(0, GRID_SIZE - 1)]
        curr_card.color = ASSASSIN_COLOR

    # make all of the rest civilians
    for row in cards_grid:
        for cell in row:
            if not hasattr(cell, 'color'):
                cell.color = CIVILIAN_COLOR

    return cards_grid, curr_turn


def print_matrix(ls):
    for line in ls:
        for cell in line:
            print colored(cell.text, cell.color.lower()) + ' ' * (12 - len(cell.text)),
        print


def dictionaries_unite(dlist):
    d = []
    for i in dlist:
        d = txt_to_dict(sys.path[0] + '/Dictionaries/' + i, d)
    if len(dlist) > 1:
        d.sort()
    elif len(dlist) == 0:
        DICTIONARIES.append('Original')
        d = txt_to_dict(sys.path[0] + '/Dictionaries/' + ORIGINAL_DICT, d)
        print 'No dictionaries were selected, defaulting to the one from the original game.'
    return d


def decolorize(ls):
    ls2 = deepcopy(ls)
    for line in ls2:
        for card in line:
            if not hasattr(card, 'visible'):
                card.color = HIDDEN_COLOR
            else:
                del card.visible
    return ls2


def reveal_color(ls, r, c):
    return ls[r][c].color


def broadcast(send_to, message):
    for s in SOCKET_LIST:
        if s in send_to:
            try:
                s.send(message)
            except:
                sys.stdout.write('Closed socket %s\n' % s)
                s.close()
                if s in SOCKET_LIST:
                    SOCKET_LIST.remove(s)


def find_in_matrix(word):
    for i in xrange(GRID_SIZE):
        for j in xrange(GRID_SIZE):
            if MATRIX[i][j].text.upper() == word.upper():
                return i, j
    else:
        # not a word
        return -1, -1


def find_in_data(d, attr):
    beg = d.find('&' + attr + '=') + len('&' + attr + '=')
    end = d.find('&', d.find('&' + attr + '=') + len('&' + attr + '=')) if d.find('&', d.find('&' + attr + '=') + len('&' + attr + '=')) != -1 else len(data)
    return d[beg:end]


DICTIONARY = dictionaries_unite(DICTIONARIES)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(10)
SOCKET_LIST = [server_socket]
sys.stdout.write('Server started! Waiting for commands on %s:%s\n' % (HOST, PORT))

MATRIX, CURR_TURN = generate_matrix(DICTIONARY)
STARTING_TEAM = CURR_TURN[:-2]

if CURR_TURN == TEAM_ONE_COLOR + '_s':
    TEAM_ONE_LEFT = int(GRID_SIZE * GRID_SIZE * 0.6)/2+1
    TEAM_TWO_LEFT = int(GRID_SIZE * GRID_SIZE * 0.6)/2
elif CURR_TURN == TEAM_TWO_COLOR + '_s':
    TEAM_TWO_LEFT = int(GRID_SIZE * GRID_SIZE * 0.6)/2+1
    TEAM_ONE_LEFT = int(GRID_SIZE * GRID_SIZE * 0.6)/2
else:
    print "Something happened when trying to choose who's turn it is. You should Probably fix that."
    sys.exit()

print_matrix(MATRIX)
while True:
    ready_to_read, ready_to_write, in_error = select.select(SOCKET_LIST, [], [], 0)
    for sock in ready_to_read:
        if sock == server_socket:
            # new connection, data from the server socket
            sockfd, addr = server_socket.accept()
            SOCKET_LIST.append(sockfd)
            print 'Client (%s, %s) connected' % addr
            data = sockfd.recv(1024)
            print 'Received data from him: {}'.format(data)
            name = find_in_data(data, 'name')
            team_temp = find_in_data(data, 'team')
            if team_temp == '1':
                team = TEAM_ONE_COLOR
            elif team_temp == '2':
                team = TEAM_TWO_COLOR
            else:
                # Doesn't care which team he is on, we'll place him on the one with fewer players. If equal - he will side with the starters.
                t1ct = len([i for i in PLAYERS_LIST if i.color == TEAM_ONE_COLOR])
                t2ct = len([i for i in PLAYERS_LIST if i.color == TEAM_TWO_COLOR])
                if t1ct < t2ct:
                    team = TEAM_ONE_COLOR
                elif t1ct == t2ct:
                    team = TEAM_TWO_COLOR
                else:
                    team = STARTING_TEAM

            role_temp = find_in_data(data, 'role')
            if role_temp in ['spymaster', 'guesser']:
                role = role_temp
            else:
                # does his team have a spymaster?
                role = 'spymaster' if len([i for i in PLAYERS_LIST if i.color == team and i.role == 'spymaster']) == 0 else 'guesser'
            PLAYERS_LIST.append(Player(name, sockfd, team, role))
            print 'His name is %s, he is a part of team %s and he is a %s.' % (name, team, role)
            mts = pickle.dumps(MATRIX) if role == 'spymaster' else pickle.dumps(decolorize(MATRIX))
            sockfd.send('gameboard&board=%s&turn=%s&color=%s&role=%s' % (mts, CURR_TURN, team, role))

        else:
            # data from a client
            try:
                data = sock.recv(1024)
                if data:
                    data = data.strip()
                    sys.stdout.write('Received data: %s\n' % repr(data))

                    if data.startswith('gamereq'):
                        print 'data = %s' % data
                        req = find_in_data(data, 'req')
                        if player_by_sock(sock).role == 'guesser':
                            if player_by_sock(sock).color == CURR_TURN:
                                if req.strip() == '':
                                    # wants to end his turn
                                    prev = CURR_TURN
                                    if CURR_TURN == TEAM_ONE_COLOR:
                                        CURR_TURN = TEAM_TWO_COLOR + '_s'
                                    else:
                                        CURR_TURN = TEAM_ONE_COLOR + '_s'
                                    msg = 'turnend&turn={}&prev={}'.format(CURR_TURN, prev)
                                    broadcast([i.conn for i in PLAYERS_LIST], msg)
                                else:
                                    # received a word
                                    i, j = find_in_matrix(req.lower())
                                    sys.stdout.write('Received a word request from %s. The word is %s, i is %s and j is %s\n' % (player_by_sock(sock).name, req, i, j))
                                    sys.stdout.flush()
                                    if i == -1:
                                        # if it's not a real word
                                        broadcast([sock], DEFAULT_MSG % ('Server', 'Please enter a valid word.'))
                                    else:
                                        # a valid input (word from the grid)
                                        if hasattr(MATRIX[i][j], 'visible'):
                                            broadcast([sock], DEFAULT_MSG % ('Server', 'This word is already open, genius.'))
                                        else:
                                            MATRIX[i][j].visible = True
                                            # msg = 'colorreveal&i=%s&j=%s&color=%s&revealer=%s' % (str(i), str(j), MATRIX[i][j].color, player_by_sock(sock).name)
                                            # broadcast([i.conn for i in PLAYERS_LIST if i.role == 'guesser'], msg)
                                            # msg = 'colorreveal&i=%s&j=%s&color=%s&revealer=%s' % (str(i), str(j), HIDDEN_COLOR, player_by_sock(sock).name)
                                            # broadcast([i.conn for i in PLAYERS_LIST if i.role == 'spymaster'], msg)
                                            CLUES_LEFT -= 1

                                            # substract from counter
                                            if MATRIX[i][j].color == TEAM_ONE_COLOR:
                                                TEAM_ONE_LEFT -= 1
                                            elif MATRIX[i][j].color == TEAM_TWO_COLOR:
                                                TEAM_TWO_LEFT -= 1

                                            # check for game end conditions
                                            if MATRIX[i][j].color == ASSASSIN_COLOR:
                                                not_playing_team = TEAM_ONE_COLOR if CURR_TURN == TEAM_TWO_COLOR else TEAM_TWO_COLOR
                                                broadcast([i.conn for i in PLAYERS_LIST], DEFAULT_MSG % ('Server', 'Team ' + not_playing_team + ' won!'))
                                                sys.exit()
                                            elif TEAM_ONE_LEFT == 0:
                                                broadcast([i.conn for i in PLAYERS_LIST], DEFAULT_MSG % ('Server', 'Team ' + TEAM_ONE_COLOR + ' won!'))
                                            elif TEAM_TWO_LEFT == 0:
                                                broadcast([i.conn for i in PLAYERS_LIST], DEFAULT_MSG % ('Server', 'Team ' + TEAM_TWO_COLOR + ' won!'))

                                            # check for turn end
                                            if CLUES_LEFT == 0 or MATRIX[i][j].color != CURR_TURN:
                                                if CURR_TURN == TEAM_ONE_COLOR:
                                                    CURR_TURN = TEAM_TWO_COLOR + '_s'
                                                else:
                                                    CURR_TURN = TEAM_ONE_COLOR + '_s'

                                            # now, after figuring everything out, we should tell it to the clients.
                                            guesser_msg = 'colorreveal&i=%s&j=%s&color=%s&revealer=%s&turn=%s' % (str(i), str(j), MATRIX[i][j].color, player_by_sock(sock).name, CURR_TURN)
                                            spymaster_msg = 'colorreveal&i=%s&j=%s&color=%s&revealer=%s&turn=%s' % (str(i), str(j), HIDDEN_COLOR, player_by_sock(sock).name, CURR_TURN)
                                            broadcast([i.conn for i in PLAYERS_LIST if i.role == 'guesser'], guesser_msg)
                                            broadcast([i.conn for i in PLAYERS_LIST if i.role == 'spymaster'], spymaster_msg)
                            else:
                                # someone tried to guess when it isn't his turn
                                broadcast([sock], DEFAULT_MSG % ('Server', 'It is not your turn now.'))
                        elif player_by_sock(sock).role == 'spymaster':
                            if player_by_sock(sock).color + '_s' == CURR_TURN:
                                # received a clue
                                count = [int(i) for i in req.split() if i.isdigit()]
                                print count
                                if len(count) != 1:
                                    broadcast([sock], DEFAULT_MSG % ('Server', 'Please include a single number in your clue.'))
                                    continue
                                count = count[0]
                                clue = req.replace(str(count), '').strip()

                                # validity checks
                                if clue.upper() in USED_WORDS:
                                    broadcast([sock], DEFAULT_MSG % ('Server', "You can't use a word from the board as a clue."))
                                # elif clue not in ALL_WORDS_EVER:
                                    # broadcast([sock], DEFAULT_MSG % ('Server', 'Cheater.'))
                                else:
                                    # reaching this point means that item 0 is a valid word and item 1 is an integer.
                                    print 'Received clue from %s: %s %s' % (player_by_sock(sock).name, clue, count)
                                    CLUES_LEFT = count + 1
                                    CURR_TURN = CURR_TURN[:-2]
                                    broadcast([i.conn for i in PLAYERS_LIST], 'newclue&sender=%s&clue=%s %s&turn=%s' % (player_by_sock(sock).name, clue, str(count), CURR_TURN))

                            else:
                                # a spymaster sent something when it wasn't his turn
                                broadcast([sock], DEFAULT_MSG % ('Server', "I know that you're eager to play, but it isn't your turn yet. Please be patient."))


                        else:
                            # non-existent role
                            print 'Wtf'
                            sys.exit()
                    elif data.startswith('chatmsg'):
                        msg = find_in_data(data, 'msg')
                        if player_by_sock(sock).role == 'guesser':
                            broadcast([i.conn for i in PLAYERS_LIST if i.conn != sock], DEFAULT_MSG % (player_by_sock(sock).name, msg))
                        else:
                            broadcast([sock], DEFAULT_MSG % ('Server', 'You cannot chat with your friends if you are a spymaster. Please use / at the beggining of your query to send a clue.'))
                    else:
                        sys.stdout.write('Data of unknown type received:\n%s\n' % repr(data))
                else:
                    if sock in SOCKET_LIST:
                        SOCKET_LIST.remove(sock)
                    if player_by_sock(sock) in PLAYERS_LIST:
                        PLAYERS_LIST.remove(player_by_sock(sock))
                    sys.stdout.write('%s has disconnected 1\n' % sock)
            except Exception as e:
                sys.stdout.write('%s' % e)
                if sock in SOCKET_LIST:
                    SOCKET_LIST.remove(sock)
                if player_by_sock(sock) in PLAYERS_LIST:
                    PLAYERS_LIST.remove(player_by_sock(sock))
                sys.stdout.write('%s has disconnected 2\n' % sock)
                continue

server_socket.close()
print "I've reached this, somehow"
