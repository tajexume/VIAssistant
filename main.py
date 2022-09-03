import assistant

if __name__ == '__main__':
    assistant = Assistant()
    while True:


        keyboard.wait('ctrl+shift+v')   #waits to hear this button combo, even if window or terminal is not focus
        press = True    #button combo has been pressed
        assistant.trigger(press)  #starts/ends the assistant
        press = False   #resets back to sleep state

