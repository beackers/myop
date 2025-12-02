from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, send, emit
import secrets, time, socket

app = Flask(__name__.split(".")[0])
app.config["SECRET_KEY"] = secrets.token_hex(16)
print(f"APP SECRET KEY: {app.config['SECRET_KEY']}")
websocket = SocketIO(app)


@app.route("/")
def main():
    return render_template("main.html")

@app.route("/control")
def control():
    return render_template("control.html")

@app.route("/chat")
def chat():
	return render_template("chat.html")

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

# DEPREICATED
# No Zeroconf file, ignore
#from zeroconf import ServiceInfo, Zeroconf
# No Zeroconf file, ignore
#from zeroconf import Servic
