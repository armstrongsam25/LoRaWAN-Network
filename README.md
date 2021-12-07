<div id="top"></div>

<!-- PROJECT LOGO -->
<br />
<div align="center">

<h3 align="center">A LoRaWan Network Implementation</h3>

  <p align="center">
     Long Range Wide Area Network (LoRaWAN) is an emerging technology that uses low-cost, low-energy intermediate gateways between a central network and end devices. Starting in 2009, LoRaWAN has gained popularity and has been deployed in many environments including agriculture, healthcare, and cities. With the tremendous amount of data that is being generated today, LoRaWAN can distribute network traffic and manage networks efficiently by converting radio frequency (RF) packets from various sensors to internet protocol (IP) packets bidirectionally. LoRaWAN has already proven to be a beneficial resource when managing data and providing a low-cost alternative to conventional network computations. 
    This project uses a LoRaWAN gateway and 2 end devices to create a proof-of-concept to show how a LoRaWAN network could work.
    <br />
    <br />
    <a href="https://github.com/armstrongsam25/LoRaWAN-Network/issues">Report Bug</a>
    ·
    <a href="https://github.com/armstrongsam25/LoRaWAN-Network/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#license">License</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

One of the challenges of working with LoRaWAN is understanding how the underlying protocol works. LoRaWAN networks are made up of three device categories: end devices, gateways, and servers. 

First, end devices can range from GPS trackers to door sensors to soil moisture sensors with many more options in between. These devices, at least in the United States, operate on the 915 MHz radio band. For comparison, WiFi networks usually operate on the 2.4 or 5.0 GHz bands, which is around 3 to 5 times greater than frequency of LoRaWAN. This means that the radio frequency (RF) packets produced on these devices have the ability to travel greater distances based on the longer wavelength. End devices are primarily data collectors that create and send RF packets to gateways. This is usually referred to as an uplink message.

Next, gateways are used as intermediary points between end devices and servers. Their main use is to convert RF packets transmitted by end devices to internet protocol (IP) packets that can be sent via the internet to a server. Gateways also have the ability to form and send RF packets back to end devices, usually referred to as downlink messages. This messages are usually formed on the server and sent to the gateway for transmission to the specified end device.

Finally, a servers main purpose is to receive and decrypt IP packets from gateways and provide data aggregation on information being collected by end devices. Servers also handle the acceptance or denial of devices on a network. This is a crucial exchange between devices and the server because end devices will not start collecting data if they are denied, unacknowledged, or sent a malformed acceptance message. If a device is accepted, a "join-accept" message is sent to the specific gateway for transmission to the end device.

This network is built and tested with a Dragino PG1301 Concentrator, a Dragino LGT-01 GPS, a Dragino LDS-01 door sensor, and a Raspberry Pi. As data is received from the GPS and door sensors, it is decrypted and decoded into human readable format and inserted into a MySQL database. This project also provides API endpoints that control all aspects of the project. 
<p align="right">(<a href="#top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started

To get a local copy up and running follow these simple example steps.
<ol>
  <li>Start a MySQL instance, input credentials into DB.py, and create a database (LoRaWAN_DB is default).</li>
  <li>Clone this repo and cd into it</li>
  <li>Start the API (python api.py) (this runs on localhost by default)</li>
  <li>Create tables and register end devices</li>
  <li>Start the packet listener (python listen.py)
    <ul><li>The API and Listener can be run independently, but they work better when running together.</li></ul>
  </li>
  <li>You are now able to retreive data being generated from the devices and the gateway.</li>
</ol>

### Prerequisites
Assuming we are running on a Raspberry Pi on Raspberry Pi OS.
* Python3
  ```sh
  pip install socket json base64 datetime binascii time flask mysql-connector-python cryptography
  ```
  * MySQL
  https://bytesofgigabytes.com/raspberrypi/how-to-install-mysql-database-on-raspberry-pi/


<!-- USAGE EXAMPLES -->
## Usage

API Usage:
  * Create initial tables
    ```sh
    curl http://localhost:42069/createtables/
    ```
  * Remove initial tables
    ```sh
    curl http://localhost:42069/resettables/
    ```
  
  * Register an end device (dev_type = 0 if GPS, dev_type = 1 for door sensor)
  ```sh
  curl -H 'Content-Type: application/json' -X POST http://localhost:42069/register -d '{"dev_addr": "XXXXXXXX", "dev_eui": "XXXXXXXXXXXXXXXX", "app_eui": "XXXXXXXXXXXXXXXX", "app_key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", "app_s_key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", "net_s_key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", "dev_type": "X"}'
  ```
   * Get device info
    ```sh
    curl http://localhost:42069/getdevice/<put dev_eui here>
    ```
    * Removes device from database
    ```sh
    curl http://localhost:42069/removedevice/<put dev_eui here>
    ```
    * Get all data from a device
    ```sh
    curl http://localhost:42069/getalldata/<put dev_eui here>
    ```
    * Get last data from a device
    ```sh
    curl http://localhost:42069/getlastdata/<put dev_eui here>
    ```
    * Get server status (00DEAD is default net_id)
    ```sh
    curl http://localhost:42069/serverstatus/<put net_id here>
    ```
   
<p align="right">(<a href="#top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/github_username/repo_name.svg?style=for-the-badge
[contributors-url]: https://github.com/github_username/repo_name/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/github_username/repo_name.svg?style=for-the-badge
[forks-url]: https://github.com/github_username/repo_name/network/members
[stars-shield]: https://img.shields.io/github/stars/github_username/repo_name.svg?style=for-the-badge
[stars-url]: https://github.com/github_username/repo_name/stargazers
[issues-shield]: https://img.shields.io/github/issues/github_username/repo_name.svg?style=for-the-badge
[issues-url]: https://github.com/github_username/repo_name/issues
[license-shield]: https://img.shields.io/github/license/github_username/repo_name.svg?style=for-the-badge
[license-url]: https://github.com/github_username/repo_name/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/linkedin_username
[product-screenshot]: images/screenshot.png
