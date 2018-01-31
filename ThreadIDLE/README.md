# Simple thread decorator

Use the decorator `@threadIDLE` to run parallel computing when working with applications on the PC.

A list of the main methods that you might need:
- `terminateThreads()` - interruption of all threads;
- `closeThreads()` - waiting for the completion of all threads.

List of all IDLE threads: `IDLE_THREADS`

Exmaple:
```
class Foo(QLabel):
    def __init__(self, parent = None):
        QLabel.__init__(self, parent)
        self.setFixedSize(320, 240)
        self.digits = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']

    @threadIDLE
    def bar(self, primaryText):
        rows = []
        digits = self.digits
        for item in digits:
            rows.append('%s: %s' % (primaryText, item))
            self.setText('\n'.join(rows), thr_method = 'b')
            sleep(0.5)

    def setText(self, text):
        QLabel.setText(self, text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    foo = Foo()
    foo.show()
    foo.bar('From thread', thr_start = True)
    app.exec_()
```
