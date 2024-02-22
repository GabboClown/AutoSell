import keyboard # Automated keyboard input
import os       # Directory reading
import glob     # Globbing the log directory
import time     # Add time stops

# Used in log reading
class FiveMLog:

    # Returns latest log location
    def getLogLocation(self):
        path = f'{os.getenv('LOCALAPPDATA')}\\FiveM\\FiveM.app\\logs\\'                 # FiveM log folder
        list_of_files = glob.glob(path + '*.log')                                       # Folder list of file
        latest_file = max(list_of_files, key=os.path.getctime)                          # Latest log
        return latest_file

    # CLASS ATTRIBUTES
    def __init__(self):
        self.location = self.getLogLocation() # self.location : log path
        # Log path refresh keybind, invokes self.logRefresh() when pressed
        keyboard.add_hotkey('F5', self.logRefresh)

    # Aggiorna il valore di self.location
    def logRefresh(self):
        self.location = self.getLogLocation()
        print('I updated the log file...')
        print(f'The log I\'m using: {self.location}\n')

    # Returns the nth before last line of a file (n=1 gives last line)
    def read_n_to_last_line(self, n):
        num_newlines = 0
        with open(self.location, 'rb') as f:
            try:
                f.seek(-2, os.SEEK_END)    
                while num_newlines < n:
                    f.seek(-2, os.SEEK_CUR)
                    if f.read(1) == b'\n':
                        num_newlines += 1
            except OSError:
                f.seek(0)
            last_line = f.readline().decode()
        return last_line
    
    # Tries to return the value of money in a string, if found. If there's no money found in the string, returns 0
    # String example:
        # [   8590687] [b2545_GTAProce]             MainThrd/ Notification: You sold ^610g ^0of ^1Heroin ^0to an NPC for ^2$26,813^0.
    def readMoneyfromLine(self, line):
        try:
            start = line.find('^2') # E' sempre presente il tag '^2' prima dei soldi acquisiti, siccome e' il tag per colorare il valore di soldi
            end = line.find('.')

            # Slices the string where the money is
                # string contains the characters between line[start + 3] and line[end - 2]
            string = line[start + 3 : end - 2] 
            
            string = string.replace(',' , '') # Removes commas
            return int(string) # Returns an integer amount of money
        except:
            return 0

# Player class, contains everything correlated to the player actions
class Player:

    # ATTRIBUTI CLASSE
    def __init__(self):
        self.sell_trigger = 'The ^3NPC ^0wants'         # String trigger used to find a sell prompt
        self.transaction_trigger = 'You sold '          # String trigger used to find a transaction prompt
        self.newMoney = 0                               # Amount of money received in a sell
        self.totalMoney = 0                             # Overall money made from the start of the script
        self.moneyWasAdded = False                      # Flag used to avoid redundancy in transaction recording
        self.isScriptRunning = True                     # Flag used to recognize if the script is running
        self.sell_counter = 0                           # Sell counter

        keyboard.add_hotkey('x', self.deactivateScript) # Keybind used to stop script compilation
    
    # Stops the script
    def deactivateScript(self):
        self.isScriptRunning = False                    # Maked the self.isScriptRunning flag LOW

    # Recognized the drug in the string given, if found
    def recognizeDrug(self, line):
        coke = 'Cocaine'
        her = 'Heroin'
        meth = 'Meth'

        if coke in line:
            return coke
        elif her in line:
            return her
        elif meth in line:
            return meth
        else:
            return 'Not Found'
        
    
    # Manipulates the string to recognize the grams of drug to sell, if any
    def recognizeGrams(self, line, phase):
        # The type of sales phase is specified, as the log lines are different for each phase
        if phase == 1: # Phase n.1: NPC asks to buy
            f_index = line.find('wants') + 8
        elif phase == 2:# Phase n.2: NPC bought
            f_index = line.find('sold') + 7
        else:
            return -1
        l_index = line.find('of') - 4
        stringa = line[f_index : l_index]
        
        try:
            return int(stringa)
        except:
            return -1
    
    # Don't sell 1g deals (all drugs), 2g deals (meth and heroin) and 3g deals (heroin)
    def canSellAvoidingSnitch(self, line):
        drug = self.recognizeDrug(line)
        grams = self.recognizeGrams(line, 1)

        rule = {
            'Heroin': 3,
            'Meth' : 2,
            'Cocaine' : 1
        }

        # Will return true if the grams are more than the rule wants them to be
        return grams > rule[drug]

    # Starts sell sequence
    def sell(self):
        keyboard.send('y')                              # FiveM sell keybind
        self.moneyWasAdded = False                      # Flag is set LOW, since the transaction isn't registered yet
    
    def registerTransaction(self, money):
        self.newMoney = money                           # Assigns the money from the transaction at the self.newMoney attribute
        self.totalMoney += money                        # Adds the money from the transaction to the overall money made
        self.moneyWasAdded = True                       # Transaction got registered
        self.sell_counter += 1                          # Money counter gets increased


def main():
    myLog = FiveMLog()
    myPlayer = Player()

    print('Listening to the log, press X to stop the script')
    print(f'Log used: {myLog.location}')
    print('If you think the script isn\'t working properly, try refreshing with F5\n')

    # Potentially infinite loop, but can be stopped by pressing 'x' or terminated by pressing 'CTRL+C'
    while True:
        last_line = myLog.read_n_to_last_line(1)
        grams = myPlayer.recognizeGrams(last_line, 2)
        drug = myPlayer.recognizeDrug(last_line)
        # If the script isn't running
        if not myPlayer.isScriptRunning:
            print('You stopped the script, press Y to resume')
            keyboard.wait('y')                  # Stops the script until user presses Y
            myPlayer.isScriptRunning = True     # Once script is resumed, the attribute self.isScriptRunning turns HIGH
            print('You resumed the script\n')

        # If the last log line contains the sell trigger, sell, but only if you can avoid getting snitched    
        if myPlayer.sell_trigger in last_line:
            if not myPlayer.canSellAvoidingSnitch(last_line):
                print('I can\'t sell, or you\'ll get snitched...\n')
                time.sleep(15)
            else:
                myPlayer.sell() # Selling sequence

        # If the last log line contains the transaction trigger AND the transaction isn't registered yet, register it
        if myPlayer.transaction_trigger in last_line and not myPlayer.moneyWasAdded:
            myPlayer.registerTransaction(myLog.readMoneyfromLine(last_line))
            print(f'You made ${myPlayer.newMoney} selling {grams}g of {drug}')
            print(f'As of right now, you made ${myPlayer.totalMoney} with {myPlayer.sell_counter} sells\n')

if __name__ == "__main__":
    main()
