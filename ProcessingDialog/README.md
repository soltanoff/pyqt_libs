# Processing Dialog

Timer calculation window, (blocking).

A window with text placed by `self.lblLoading` opens, in order to inform the user about the execution of any actions.

This class allows you to start calculations that can be interrupted by a timer (see Self.isTerminated).

By default, the timer does not work (see the `waitTime` parameter in the main class).


For example: (wait 2 seconds, and after interrupt the calculations if this not finished)
```
def slowFunc(a, b, sleepTime):
    import time
    time.sleep(sleepTime)
    print("THREAD ARE FINISHED!")
    print(">> " + a + " " + b)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    print("START\n")
    dialog = CProcessingDialog(slowFunc, ("a", "iop", 7), waitTime=2)
    dialog.exec_()
    if dialog.isTerminated:
        print("Function calculating is interrupted!")
    else:
        print("Function calculating is finished")
    print("\nSTOP")

    sys.exit()
```
Output:
```
START

Function calculating is interrupted!

STOP
```