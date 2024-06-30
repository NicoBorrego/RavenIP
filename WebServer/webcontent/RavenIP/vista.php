<?php 
    session_start();
    $usuario="";
    $ip="";
    $username="master";
    $database="RavenIP";
    $password="CentroAfuera23-";

    $nombres=[];
    $ips=[];
    $i=0;

    if(isset($_SESSION['usuario'])){
        $usuario=$_SESSION['usuario'];
        $ip=$_SESSION['ip'];
        unset($_SESSION['usuario']);
        unset($_SESSION['ip']);
    }

    try{
        $db=new PDO("mysql:host=localhost; dbname=$database", $username, $password);
        foreach($db->query("SELECT * FROM Clientes WHERE master='$usuario'") as $row){
            $nombres[$i] = $row['nombre'];
            $ips[$i] = $row['ip'];
            $i++;
        }
    }catch (PDOException $p){
        $p->getMessage();
    }
?>
<html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="./control.css"/>
        <link href="./bootstrap-5.0.2-dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="icon" href="./img/Logo.png" type="image/png">
        <title>RavenIP</title>
    </head>
    <body>
        <div class="container-fluid" id="divGeneral">
            <div class="row mx-0 w-100" id="controles">
                <div class="col-1">
                    <img class="img-fluid" src="./img/Logo.png"/>
                </div>
                <div class="col-2"><br></div>
                <div class="col-1" id="botones">
                    <br>
                </div>
                <div class="col-1" id="botones">
                    <button class="btn" id="btnControl">
                        <img class="img-fluid" src="./img/Control.png"/>
                    </button>
                    <p id="info">Control</p>
                </div>
                <div class="col-1" id="botones">
                    <button class="btn" id="btnShell" onclick="openTerminal()">
                        <img class="img-fluid" src="./img/Terminal.png"/>
                    </button>
                    <p id="info">Línea de comandos</p>
                </div>
                <div class="col-1" id="botones">
                    <button class="btn" id="btnApagar">
                        <img class="img-fluid" src="./img/Apagar.png"/>
                    </button>
                    <p id="info">Apagar terminal</p>
                </div>
                <div class="col-1" id="botones">
                    <button class="btn" id="btnReiniciar">
                        <img class="img-fluid" src="./img/Reiniciar.png"/>
                    </button>
                    <p id="info">Reiniciar terminal</p>
                </div>
                <div class="col-1" id="botones">
                    <button class="btn" id="btnInforme">
                        <img class="img-fluid" src="./img/Informe.png"/>
                    </button>
                    <p id="info">Informe de terminal</p>
                </div>
                <div class="col-3" id="botones"><br></div>
            </div>
            <div class="row" id="filaAlumnos">
                <div class="col-2" id="alumnos">
                    <p class="lead fw-bold"><?php echo $usuario; ?></p>
                    <ul class="list-group list-group-flush" id="listaAlumnos">
                        
                    </ul>
                </div>
                <div class="col-10" id="pcs">
                    
                </div>
            </div>
        </div>
        <script>
            var alumnoImages = {};
            let selectedClient = null;
            const ipServidor = "<?php echo $ip; ?>";
            const socket = new WebSocket('wss://'+ipServidor+':8765');
            var control = false;
            var informe = false;
            var ventana;
            var cerrado = false;
            var clientes = parseInt("<?php echo count($nombres); ?>");
            var ips = "<?php foreach($ips as $cad){echo $cad.':';} ?>".slice(0, -1).split(':');
            var nombres = "<?php foreach($nombres as $cad){echo $cad.'.';} ?>".slice(0, -1).split('.');
            window.onload = function(){
                for(let i=0;i<clientes;i++){
                    clientid=ips[i];
                    console.log(ips[i]);
                    const container = document.createElement('div');
                    container.id = `pcs_${nombres[i]}`;
                    container.onclick = function() {
                        handleAlumnoClick(container, ips[i]);
                    };
                    document.getElementById('pcs').appendChild(container);

                    const image = document.createElement('img');
                    image.id = `desktopImage_${ips[i]}`;
                    image.className = 'img-fluid';
                    image.src='./img/Terminal.png';
                    container.appendChild(image);
                    alumnoImages[clientid] = image;
                    
                    container.appendChild(document.createElement('br'));
                    
                    const paragraph = document.createElement('p');
                    paragraph.id = `ipParrafo_${ips[i]}`;
                    paragraph.textContent = `${nombres[i]}`;
                    paragraph.style.paddingTop = "2vh";
                    container.appendChild(paragraph);
                    
                    alumnoImages[clientid] = image;

                    // Crear el elemento <li>
                    var listItem = document.createElement("li");

                    // Añadir clases al elemento <li>
                    listItem.classList.add("list-group-item", "list-group-item-danger");
                    listItem.id = `list_${ips[i]}`;
                    // Crear el elemento <label>
                    var label = document.createElement("label");
                    label.textContent = nombres[i]+"           "+ips[i];

                    // Añadir el elemento <label> como hijo del elemento <li>
                    listItem.appendChild(label);

                    // Añadir el elemento <li> al contenedor deseado (por ejemplo, un elemento <ul> con la clase "list-group")
                    var contenedor = document.getElementById("listaAlumnos");
                    contenedor.appendChild(listItem);

                }
            }
            socket.onopen = function(event) {
                console.log('Conexión establecida con el servidor');
            };
            socket.onmessage = function(event) {
                const data = JSON.parse(event.data);
                const clientid = data.clientid;
                var lista = document.getElementById(`list_${clientid}`);

                if(data.action == "informe"){
                    const sistemaOperativo = JSON.stringify(data.datos['Sistema operativo']);
                    const monitoreo = JSON.stringify(data.datos['Monitoreo']);
                    // Construir la URL con los parámetros ocultos
                    const queryString = `sistema=${encodeURIComponent(sistemaOperativo)}&monitoreo=${encodeURIComponent(JSON.stringify(monitoreo))}&cliente=${encodeURIComponent(selectedClient)}`;
                    
                    // Abrir la página HTML en una nueva pestaña con los parámetros ocultos
                    const ventana = window.open(`./informe.html?${queryString}`, '_blank');
                }else if (data.puerto){
                    // Construir los parámetros ocultos (IP y puerto)
                    const parametros = {
                        ip: clientid,
                        puerto: data.puerto,
                        cliente: selectedClient
                    };

                    // Construir la URL con los parámetros ocultos
                    let queryString = '';
                    for (var key in parametros) {
                        if (parametros.hasOwnProperty(key)) {
                            queryString += encodeURIComponent(key) + '=' + encodeURIComponent(parametros[key]) + '&';
                        }
                    }

                    // Abrir la página HTML en una nueva pestaña con los parámetros ocultos
                    ventana = window.open('./control.html?' + queryString, '_blank');
                }else if (clientid && data.imageData){
                    alumnoImages[clientid].style.paddingTop = "1.5vh";
                    alumnoImages[clientid].src = `data:image/png;base64,${data.imageData}`;
                    if(lista.classList.contains("list-group-item-danger")){
                        lista.classList.remove("list-group-item-danger");
                        lista.classList.add("list-group-item-success");
                    }
                }else if(data.estado){
                    if(data.estado == "desconectado"){
                        alumnoImages[clientid].style.paddingTop = "0";
                        alumnoImages[clientid].src = './img/Terminal.png';
                        lista.classList.remove("list-group-item-success");
                        lista.classList.add("list-group-item-danger");
                    }
                }
            };

            document.getElementById('btnApagar').addEventListener('click', function() {
                if(selectedClient){
                    socket.send(JSON.stringify({ action: 'apagar', clientid: selectedClient }));
                }else {
                    alert('Selecciona un alumno para realizar el informe.');
                }
            });

            document.getElementById('btnReiniciar').addEventListener('click', function() {
                if(selectedClient){
                    socket.send(JSON.stringify({ action: 'reiniciar', clientid: selectedClient }));
                }else {
                    alert('Selecciona un alumno para realizar el informe.');
                }
            });

            document.getElementById('btnInforme').addEventListener('click', function() {
                if(selectedClient){
                    socket.send(JSON.stringify({ action: 'informe', clientid: selectedClient }));
                    informe = true;
                }else {
                    alert('Selecciona un alumno para realizar el informe.');
                }
            });
            socket.onclose = function(event) {
                console.error('Conexión cerrada con el servidor: ', event);
            };
            
            socket.onerror = function(event) {
                console.error('Error en la conexión con el servidor: ', event);
            };
            window.addEventListener("message", function (event) {
                // Verificar si el mensaje proviene de la ventana secundaria y contiene la información esperada
                if (event.source === ventana && event.data && event.data.type === "cerrado") {
                    // Actualizar la variable de estado
                    cerrado = event.data.value;
                    console.log("Se cerró la ventana de control");
                    socket.send(JSON.stringify({ action: 'cerrado', puerto: cerrado, clientid: event.data.clientid }));
                }
            });

            document.getElementById('btnShell').addEventListener('click', function() {
                if (selectedClient) {
                    // Obtener la IP del alumno desde el párrafo correspondiente
                    const ipParrafo = document.getElementById(`ipParrafo_${selectedClient}`);
                    if (ipParrafo) {
                        socket.send(JSON.stringify({ command: 'shell', clientid: selectedClient }));
                        console.log("Mensaje enviado, has seleccionado: ", alumnoIP);
                    } else {
                        console.error('No se encontró el párrafo para el selectedClient:', selectedClient);
                    }
                } else {
                    alert('Selecciona un alumno antes de enviar el mensaje.');
                }
            });

            document.getElementById('btnControl').addEventListener('click', function() {
                if (selectedClient) {
                    // Obtener la IP del alumno desde el párrafo correspondiente
                    const ipParrafo = document.getElementById(`ipParrafo_${selectedClient}`);
                    if (ipParrafo) {
                        const parametros = { ipAlumno: selectedClient }; // Crear parámetro oculto

                        console.log("Mensaje enviado, has seleccionado: ", selectedClient);
                        socket.send(JSON.stringify({ command: 'control', clientid: selectedClient }));

                        control = true;
                    } else {
                        console.error('No se encontró el párrafo para el selectedClient:', selectedClient);
                    }
                } else {
                    alert('Selecciona un alumno antes de enviar el mensaje.');
                }
            });

            function handleAlumnoClick(container, clientid) {
                if (container.classList.contains('selected')) {
                    // Si ya está seleccionado, desseleccionar
                    container.classList.remove('selected');
                    container.style.backgroundColor = "white";
                    selectedClient = null;
                } else {
                    // Si no está seleccionado, seleccionar
                    if (selectedClient) {
                        // Si ya hay otro seleccionado, desseleccionar ese primero
                        const prevSelectedContainer = document.getElementById(`pcs_${selectedClient}`);
                        if (prevSelectedContainer) {
                            prevSelectedContainer.classList.remove('selected');
                            prevSelectedContainer.style.backgroundColor = "white";
                        }
                    }
                    container.style.backgroundColor = "#87CEFA";
                    container.classList.add('selected');
                    selectedClient = clientid;
                }
            }
        </script>
        <!-- JavaScript BOOTSTRAP-->
        <script src="./bootstrap-5.0.2-dist/js/bootstrap.min.js"></script>
    </body>
</html>