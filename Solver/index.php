<!doctype html>
<html>
  <head>
    <title>eFinderCli</title>
  </head>
  <body bgcolor="#A00000" text="#FFFFFF">
    <?php
     header("refresh:1");
     $image = '/home/efinder/Solver/images/capture.jpg';
     $imageData = base64_encode(file_get_contents($image));
     echo '<img src="data:image/jpg;base64,'.$imageData.'">';
    ?>
  </body>
</html>
