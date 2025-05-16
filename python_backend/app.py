-from flask import Flask, jsonify
+import os
+from flask import Flask, jsonify

 app = Flask(__name__)

 @app.route("/")
 def root():
     return jsonify({"message": "Hello from Python backend!"})

 @app.route("/data")
 def data():
     return jsonify({"value": 42})

 if __name__ == "__main__":
-    app.run(host="0.0.0.0", port=8080)
+    # Use PORT env var, default to 8080
+    port = int(os.environ.get("PORT", 8080))
+    app.run(host="0.0.0.0", port=port)
