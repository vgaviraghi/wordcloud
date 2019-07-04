
import os
import authentication
import main
from tornado import ioloop, web, wsgi, httpserver
secret_key = 'D7fsdfy0s9ygsa9f8s0sdfoFYLADFBALid7===fd787879'
static_path = os.path.join(os.path.dirname(__file__), "static")

def app():
    # Directory of static files
    settings = dict(template_path=os.path.join(os.path.dirname(__file__), "templates"),
                    static_path=os.path.join(os.path.dirname(__file__), "static"),
                    cookie_secret=secret_key)

    # Root website address
    application = wsgi.WSGIApplication([
        (r"/", main.MainHandler),
        (r"/admin", authentication.AdminHandler),
        (r"/login", authentication.LoginHandler),
        (r"/logout", authentication.LogoutHandler)
    ], **settings)

    http_server = httpserver.HTTPServer(application)
    port = int(os.environ.get("PORT", 8888))
    http_server.listen(port)

    print 'Application started on port 8888'
    print 'Press ctrl+c to stop'

    ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    # Run application
    app()
