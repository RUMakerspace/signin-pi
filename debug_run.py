import passenger_wsgi as pw
import os

if __name__ == "__main__":
    pw.application.run(host="0.0.0.0", debug=True)
