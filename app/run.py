import sys
sys.path.append('..')

from app import app
from app import routes  # This line is important to ensure your routes are registered

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5002)
