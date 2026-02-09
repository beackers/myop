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
1. Open a command line interface and navigate to the folder containing `app.py`, then run `flask run`.
2. On the same device, in a browser, navigate to `localhost:5000/`.
3. You should see the login page pop up!

 ### step five: configure for current incident
1. Log in as username "BOOTSTRAP\_ADMIN" with password "bootstrapbill". This login is the default bootstrap user (if you know how, I'd recommend changing the password. Look for BOOTSTRAP\_ADMIN's definition in `app.py` and change the text inside `generate_password_hash`).
2. The system will then take you a page where you can register the first admin user. This step is not required but is **highly recommended**, as the bootstrap admin is active until the first admin user is created. Fill out the callsign(required) and name (recommended) fields and make sure the "active" checkbox is checked, then change the permissions dropdown to "admin" and enter a password. **Remember your password, because you won't be able to get it back.** (It is possible to change the password, but this method is beyond the scope of this document.) Submit the form.
3. The system will take you to the login page again. Log in as the user you just created.
4. The system will take you to the homepage. Congrats, your system is set up!

### step six: configure the server as an AREDN service
(help wanted! I haven't done this before at the time of writing. instructions would be great.)

---

## during a deployment
1. Run the server with `flask run --host 0.0.0.0`
2. Plug the server into the AREDN node
3. Access the webpage and configure user accounts and settings (located in the control panel)
3. All good to go!

---

## running with Docker
If you prefer a containerized setup, you can use Docker to build and run MyOp.

### build the image
From the repository root:
```
docker build -t myop .
```

### run the container
This starts the app and exposes it on port 5000:
```
docker run --rm -p 5000:5000 myop
```

Then open `http://localhost:5000/` in your browser.

### persisting data
The SQLite database is stored in `myop.db`. To persist data across container restarts, mount a volume:
```
docker run --rm -p 5000:5000 -v "$(pwd)/myop.db:/app/myop.db" myop
```


