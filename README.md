# Car Competition Webapp-

**Motorkhana Competition Project**  

--------------------------------------------------------
*1. Structure of the Website*   
The website for Motokhana has two primary interfaces. One is for public use, and the other one is for administrative purposes.   

I have set out a visual diagram explaining the web application structure below:  
![This is an image](/web-structure.jpeg)


*2. Assumtions and Design Decisions*  
* 1. I made an assumption that admin has a private portal which they can access from the public interface. This is because we are not using a user name and password system, so I made a clickable admin portal button on the home page to separate the two functions from public to administrator.   

* 2. I also made an assumption that the /listdrivers route should display both the list of Driver details and the option to select a driver from the drop down menu box. This is why they are both on driverslist.html.  

* 3. For the requirement of overall results, I made an assumption that the overall result and detailed course results need to be displayed separately. This is why I displayed two separate tables on the page; one is for their overall results, the other is for displaying all six course times for each driver.   

* 4.  For Drivers Search Function in the Administrator interface, I made an assumption that the user might want to have a quick access option to search another person. For this reason, I included a separate search box underneath the search results.  

* 5. For the Admin’s add driver function, I made an assumption that prior to adding any new driver, they already knew if the driver that they were adding is a junior or not. For this reason, I designed the add driver.html I added a separate button indicating to click the button to add a junior driver. Through this, I was able to achieve the requirement that neither age or caregiver options are visible to non-junior driver.  

* 6. I utilised the driverlist.html template for displaying pages that have similar purposes. I used conditions such as if the person was junior or if the user is an admin to choose to display either a whole list of drivers or just junior drivers.  
