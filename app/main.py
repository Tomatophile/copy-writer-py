from app.layout import layout
from app.threads import ApplicationThread

application = ApplicationThread('application', 'main', 'CopyWriter', layout)
application.start()
