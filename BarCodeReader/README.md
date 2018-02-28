# COM-port barcode reader

Used to start a thread that listens on the COM port of the device
and through the "signal-slot" mechanism communicates with the impurity `CBarCodeMixin`.

This impurity is used in the dialog box in which you need to work
with a scanner.
For correct work, you need to override the methods in the dialog box class:

* readOMS (self, result)
* setVerifiedAction (self, result)
* read (self, result)
