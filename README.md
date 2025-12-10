# MyOp v1

### new features:
* everything XD (it's the first release)
* control panel
* bulletin board
* live chat
---

THIS CODE HAS NOT BEEN TESTED IN DEPLOYMENT. Author does not warrant that the code will be free of bugs / unintended actions/consequences / what have you. **TL;DR: it might not work. I'm still working on it.**

This software was written by a United States of America radio operator. Different countries may have different laws regarding amateur radio. **This software was intended for USA use and has not been internationalized. If you live outside the continental US, not in a US territory, or outside of US waters, different laws may apply.** Always follow your country's own laws and regulations. Use this software at your own risk.

This software is intended to improve and enhance existing communications between licensed amateur radio operators with AREDN (Amateur Radio Emergency Data Network) nodes. IT IS NOT INTENDED FOR CONTACT WITH EMERGENCY DISPATCHERS. IN AN EMERGENCY, DIAL 911.

---

## about
AREDN nodes have the power to communicate over mesh networks with TCP/IP using regular or ham-specific WiFi channels. Amateur radio operators can leverage this to their advantage when deploying as part of an emergency communications ("emcomm") group like ARES or RACES. This software specifically utilizes Python and a few commonly available libraries to host a small, efficient web server available to each node that concentrates information about the current incident and allows operators to use web browsers to send information that supplements other communications, like pictures or forms. By consolidating information and making it easily accessible, operators can communicate faster and more clearly.

## installing
If your local ARES uses AREDN, give MyOp a shot! Here's how.

### prerequisites
* **Python 3.16 or newer**  
You can download Python at <a href="https://python.org">python.org</a>.
* **pip**  
pip should ship standard with Python. If you don't have it:
    - Linux: run `apt-get install pip`
    - MacOS: (I don't have a Mac, so if someone could help me out that'd be great)
    - Windows: ships with Python
* **a device this can run on, reliably, for however long the deployment lasts**  
Raspberry Pis work PERFECTLY, and most of them even have an Ethernet port that'll hook right on up to your AREDN node. This'll be the server.


### step one: meet the prerequisites
If you haven't already, install Python and pip on the server device.

### step two: install dependencies
(These instructions are for Linux. You may need to find your own OS's commands.)
```
pip install python-flask
pip install flask-socketio
```

### step three: set up MyOp
Find the latest release in the Releases tab and download a package (I generally like .zip, but you can use either) to the server device. Extract the contents into a folder.  
**It pays off to double-check!** The extracted files should include:
* **app.py**
* **myop.db**
* a folder called **templates** with a lot of HTML files
* a folder called **static** with a few .js files, a few .json files,  and a .css file.

### step four: dry-run the server
* Open a command line interface and navigate to the folder containing `app.py`, then run `flask run`.
* On the same device, in a browser, navigate to `localhost:5000/`.
* You should see the home page pop up!

### step five: configure the server as an AREDN service
(help wanted! I haven't done this before at the time of writing. instructions would be great.)

---

## during a deployment
* Run the server with `flask run --host 0.0.0.0`
* Plug the server into the AREDN node
* All good to go!



