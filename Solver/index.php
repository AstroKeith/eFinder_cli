<!doctype html>
<html>
  <head>
    <title>eFinderCli</title>
  </head>
  <body bgcolor="#000000" text="#FFFFFF">
    <?php
     header("refresh:1");
     $image = '/home/efinder/Solver/images/capture.png';
     $imageData = base64_encode(file_get_contents($image));
     echo '<img src="data:image/png;base64,'.$imageData.'">';
    ?>
  </body>
</html>
