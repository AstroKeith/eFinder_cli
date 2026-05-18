<!DOCTYPE html>
<html lang="en">
<head>
	<title>Nexus eFinder</title>
</head>
<body bgcolor="#000000" text="#FFFFFF">
	<h1 align="center">Nexus eFinder Fault Log</h1><br>
<h2>Nexus Mode</h2><br>
<?php
$filename1 = "eFinderLog.txt";
if (file_exists($filename1))
  	{
  	chmod($filename1, 0777);
  	$fp=fopen($filename1, "r");
  	print_r($myVar);
  	while(!feof($fp)) {
		$line = fgets($fp);
		echo $line . "<br>";	
		}
  	}
?>
<h2>Live Mode</h2><br>
<?php
$filename2 = "eFinderLiveLog.txt";
chmod($filename2, 0777);
if (file_exists($filename2))
	{	
	$fp2=fopen($filename2, "r");
	print_r($myVar);
	while(!feof($fp2)) {
        $line2 = fgets($fp2);
        echo $line2 . "<br>";    
		}
	}
?>
</body>
</html>


