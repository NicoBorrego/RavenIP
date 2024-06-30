The project architecture consists of the following elements: a websocket server, clients, and a web server.

The websocket server is the central core of the RavenIP architecture. Developed in Python, it manages communications between the different components of the system, providing a secure and efficient way to transmit data and commands. The main functions of the websocket server are:

- **Screenshot Relay:** Receives screenshots from client devices and retransmits them to the web client.
- **Instruction Sending:** Sends commands to client devices to execute various actions, simulating remote control.
- **Security:** Uses SSL certificates to ensure all communications are encrypted and protected against unauthorized access.

Student or employee clients run a websocket client that communicates with the websocket server. This client consists of three Python scripts:

- **Main Script:**
  - **Screenshot Sending:** Periodically takes screenshots.
  - **Instruction Execution:** Receives and executes commands sent by the websocket server, such as remote control, command execution via SSH, and shutting down or restarting the machine.
  - **Data Sending:** Sends stored data to the websocket server for analysis and action by the supervisor when required.
  - **Security:** Connects to the websocket server via a TLS client certificate.

- **Second Script:**
  - **Screenshot Sending:** Sends the screenshots taken by the main script to the websocket server.
  - **Remote Control Simulation:** Executes instructions received from the websocket server, providing a smooth remote control experience.

- **Third Script:**
  - **System Data Collection:** Gathers relevant system information, such as performance metrics and application usage statistics.
  - **Data Storage:** Saves the collected data in JSON format.

The web server acts as the graphical interface for teachers or supervisors, allowing them to monitor and control client devices in a centralized and secure manner. The main features of the web server are:

- **Connection to the Websocket Server:** Connects to the websocket server to receive screenshots and send commands to client devices.
- **Graphical Interface:** Provides a graphical user interface (GUI) that allows supervisors to perform various actions:
  - **Real-time Viewing:** View real-time screenshots of client devices.
  - **Remote Control:** Take remote control of client devices.
  - **Command Execution:** Execute advanced commands via SSH.
  - **Device Management:** Manage the power state (on, off, restart) of client devices.
  - **Data Analysis:** Access and analyze system data sent by client devices.
  - **Security:** Uses HTTPS to ensure all communications with end users are secure and encrypted.
