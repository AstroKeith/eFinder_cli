import math
import os
from datetime import datetime

class Coordinates:
    """Coordinates utility class"""

    def __init__(self) -> None:
        self.t = 26
        self.T = self.t/100
        self.m = 3.07496 + 0.00186 * self.T
        self.n2 = 20.0431 - 0.0085 * self.T
        self.n1 = 1.33621 - 0.00057 * self.T
        print('Coordinates imported')

    def dateSet(self,timeOffset,timeStr,dateStr):
        days = 0
        sg = float(timeOffset) # add to local time to get UTC
        hours,minutes,seconds = timeStr.split(':')
        hours = int(hours) + sg
        if hours > 24:
            hours = str(int(hours - 24))
            days = +1
        elif hours < 0:
            hours = str(int(hours + 24))
            days = -1
        else:
            hours = str(int(hours))
        timeStr = hours +':'+minutes+':'+seconds

        month,day,year = dateStr.split('/')
        day = (str(int(day) + days))
        dateStr = month + '/' + day + '/20' + year 

        dt_str = dateStr + " " + timeStr #format = "%m/%d/%Y %H:%M:%S"
    
        print("Calculated UTC", dt_str)
        os.system('sudo date -u --set "%s"' % dt_str + ".000Z")
        
        now = datetime.now()
        decY = int(now.year) + int(now.strftime('%j'))/360
        
        self.t = (decY - 2000)
        self.T = self.t/100
        self.m = 3.07496 + 0.00186 * self.T
        self.n2 = 20.0431 - 0.0085 * self.T
        self.n1 = 1.33621 - 0.00057 * self.T
        
    def precess(self,r,d): # J2000 RA & Dec in decimal degrees
        dR = self.m + self.n1 * math.sin(r * math.pi/180) * math.tan(d * math.pi/180)# arcsecs
        dD = self.n2 * math.cos(r * math.pi/180)# arcsecs
        r = r + dR/240 * self.t
        d = d + dD/3600 * self.t
        return r,d # Jnow RA & Dec in decimal degrees

    def dd2dms(self, dd: float) -> str:
        """Convert decimal degrees to a string (dd:mm:ss)

        Parameters:
        dd (float): The degrees to convert

        Returns:
        str: The degrees in human readable format
        """
        is_positive = dd >= 0
        dd = abs(dd)
        minutes, seconds = divmod(dd * 3600, 60)
        degrees, minutes = divmod(minutes, 60)
        sign = "+" if is_positive else "-"
        dms = "%s%02d:%02d:%02d" % (sign, degrees, minutes, seconds)
        return dms

    def dd2aligndms(self, dd: float) -> str:
        """Convert decimal degrees to a string (sDD*MM:SS)

        Parameters:
        dd (float): The degrees to convert

        Returns:
        str: The degrees in the format needed to send to the Nexus
        """
        is_positive = dd >= 0
        dd = abs(dd)
        minutes, seconds = divmod(dd * 3600, 60)
        degrees, minutes = divmod(minutes, 60)
        sign = "+" if is_positive else "-"
        dms = "%s%02d*%02d:%02d" % (sign, degrees, minutes, seconds)
        return dms

    def ddd2dms(self, dd: float) -> str:
        """Convert decimal degrees to a string (ddd:mm:ss)

        Parameters:
        dd (float): The degrees to convert

        Returns:
        str: The degrees in human readable format
        """
        minutes, seconds = divmod(dd * 3600, 60)
        degrees, minutes = divmod(minutes, 60)
        dms = "%03d:%02d:%02d" % (degrees, minutes, seconds)
        return dms

    def hh2dms(self, dd: float) -> str:
        """Convert decimal hours to a string (dd:mm:ss)

        Parameters:
        dd (float): The hours to convert

        Returns:
        str: The hours in human readable format (without sign)
        """
        minutes, seconds = divmod(dd * 3600, 60)
        degrees, minutes = divmod(minutes, 60)
        dms = "%02d:%02d:%02d" % (degrees, minutes, seconds)
        return dms

    
