<?php 
    session_start();
    $usuario="";
    $passwd="";
    $nombre="";
    $ip="";
    $username="master";
    $database="RavenIP";
    $password="CentroAfuera23-";
    $fallo=false;
    if ($_SERVER['REQUEST_METHOD']=='POST'){
        if(isset($_POST['login'])){
            $usuario = $_POST['usuario'];
            $passwd = $_POST['passwd'];
            try{
                $db=new PDO("mysql:host=localhost; dbname=$database", $username, $password);
                foreach($db->query("SELECT passwd,ip FROM Usuarios WHERE nombre='$usuario'") as $row){
                    //True si la cadena y la cadena deshasheada son iguales
                    if($row['passwd'] === hash('sha256', $passwd)){
                        $ip=$row['ip'];
                    }
                }
                if($ip == ""){
                    $fallo=true;
                }
            }catch (PDOException $p){
                $p->getMessage();
                $fallo = true;
            }
            if($fallo){
                echo '<script>alert("Usuario o Password incorrectos");</script>';
            }else{
                $_SESSION['usuario'] = $usuario;
                $_SESSION['ip'] = $ip;
                header("Location: vista.php");
            }
        }
    }
?>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/x-icon" href="./img/Logo.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>RavenIP Login</title>
    <link href="./bootstrap-5.0.2-dist/css/bootstrap.min.css" rel="stylesheet"/>
  </head>
  <body class="d-flex justify-content-center align-items-center vh-100" style="background-color: #BCBCDA;">
    <form action="" method="post">
        <div class="bg-white p-5 rounded-5 text-secondary shadow"style="width: 25rem">
        <div class="d-flex justify-content-center">
            <img src="./img/Logo.ico" alt="login-icon" style="height: 7rem"/>
        </div>
        <div class="input-group mt-4">
            <div class="input-group-text bg-dark">
            <img src="./img/username-icon.svg" alt="UserIcono" style="height: 1rem"/>
            </div>
            <input class="form-control bg-light" type="text" name="usuario" placeholder="Usuario"/>
        </div>
        <div class="input-group mt-1">
            <div class="input-group-text bg-dark">
            <img src="./img/password-icon.svg" alt="passIcono" style="height: 1rem"/>
            </div>
            <input class="form-control bg-light" type="password" name="passwd" placeholder="Password"/>
        </div>
        <div class="d-flex justify-content-around mt-1">
            <button class="btn btn-dark text-white w-100 mt-4 fw-semibold shadow-sm" type="submit" name="login">Login</button>
        </div>
        </div>
    </form>
  </body>
</html>