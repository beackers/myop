from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, send, emit
import secrets, time, socket, hashlib, json

app = Flask(__name__.split(".")[0])
app.config["SECRET_KEY"] = secrets.token_hex(16)
key = hashlib.sha256(app.config["SECRET_KEY"].encode("utf-8")).hexdigest()
print(f"Secret key generated! Hash: {key}")
websocket = SocketIO(app)

with open("static/bulletins.json", "w") as file:
    data = {
                "bulletins": []
            }
    json.dump(data)

@app.route("/")
def main():
    return render_template("main.html")

@app.route("/control")
def control():
    return render_template("login.html")

@app.route("/chat")
def chat():
	return render_template("chat.html")

@app.route("/bulletins", methods=['GET'])
def bulletins():
    with open("static/bulletins.json", "r") as file:
        data = json.load(file)
    return render_template("bulletins.html")

@websocket.on("message")
def newMsg(data):
	try:
		print("New Message:" + data.get("msg", " "))
		dataToSend = {
			"timestamp": time.asctime(),
			"username": data.get("username", "unknown"),
			"message": data.get("msg", "<blank>")
		}
		dataType = "message"
	except Exception as e:
		dataToSend = {
			"timestamp": "SYSTEM",
			"username": str(type(e)),
			"message": str(e)
		}
		print("Handled exception in newMsg()")
		dataType = "error"

	finally:
		emit(dataType, dataToSend, broadcast=True)

if __name__ == "__main__":
	try:
		websocket.run(app, host="0.0.0.0", port=5000)
	except Exception as inst:
		emit("error", {
			"timestamp": time.asctime(),
			"title": str(type(inst)),
			"detail": str(e)
		})
		pass

