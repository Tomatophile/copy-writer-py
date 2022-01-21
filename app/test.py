from app.threads import InterruptableThread, InterruptedException


def loo():
    try:
        while True:
            pass
    except InterruptedException:
        pass


thread = InterruptableThread(loo)
thread.start()

thread.interrupt()

print()
