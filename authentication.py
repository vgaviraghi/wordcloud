from helpers import decode_string
from tornado import web, escape
from main import conn_db, conn
from app import secret_key

class BaseHandler(web.RequestHandler):
    """Base Handler
    """
    def get_current_user(self):
        # Returns the cookie for the logged in user
        return self.get_secure_cookie("user")

class AdminHandler(BaseHandler):
    """Admin Handler
    """
    def get(self):
        # Verifies that the user is already logged in
        # If the aren't logged in, then redirects to the login page
        if not self.current_user:
            self.redirect("/login")
            return

        # Get the name of the user logged in
        name = escape.xhtml_escape(self.current_user)

        # Get all words saved in the database sorted by frequency descending
        conn_db.execute("select * from top_words order by word_frequency desc")
        all_words = conn_db.fetchall()

        # Mount a dictionary with the word (decrypted) and frequency
        items = []
        for word in all_words:
            items.append({'word': decode_string(secret_key, (str(word[0]))),
                          'frequency': word[1]})

        # Shows the admin template with a table that contains the words and frequencies
        self.render('admin.html', user_name=name, items=items)

class LoginHandler(BaseHandler):
    """Login Handler
    """
    def get(self):
        # Shows the login page
        self.render('login.html')

    def post(self):
        # Set the cookies for the user logged in
        self.set_secure_cookie("user", self.get_argument("user_name"))

        # Redirects to the admin page
        self.redirect("/admin")

class LogoutHandler(BaseHandler):
    """Logout Handler
    """
    def get(self):
        # Clear the cookies
        self.clear_cookie("user")

        # Redirects to the login page
        self.redirect("/login")
