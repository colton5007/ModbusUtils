# ModbusUtils
## Inspiration
Throughout my professional career there have been many times where I wish I had a competent means of troubleshooting, simulating, or testing a Modbus client/slave. Unfortuantely, nearly every existing solution is ancient, very costly, and often miserable to work with. Because of the prohibitive market that Industrial Automation poses for the Open Source community, we desired to create a new solution that would allow for easy creation and testing of ModbusTCP masters and slaves.

## What It Does

ModbusUtils has two main sides:
1. The Modbus Master
Often times being able to simulate Modbus requests on a Modbus slave is incredibly useful. If you are trying to demo a system without a PLC or if you are trying to compartamentalize your development of such operations, having a nice, user friendly, free, and no-trial software is wondeful. The Modbus Master component allows for the user to access a web interface, connect to a Modbus slave, execute function codes (including custom ones and supporting fc 15/16), and present the read data in a human readable format.
2. The Modbus Slave
This component allows for the easy creation of Modbus Servers that can be quickly built, populated, and left running (in fact, while these can be used for troubleshooting purposes, they can exist on their own entirely as a persistent open source and free Modbus Server). In addition, we can carefully monitor the data coming in and out of the server and have added functionality for custom function codes on your Modbus server.

## How We Built It

We built this project primarily around flask and the PyModbusTcp API. We started by building up the infrastructure to easily hook into the API to create robust TCP clients and servers and with enough customization to never be worried if its not enough. After building the backend, we constructed the front end to interface quickly and easily with the backend providing near instance poll times on reads and writes.

## Challenges We Ran Into

We wanted to make sure this project was easily expandable and that it would be possible to host 100s or 1000s of slaves on a single connection. Because of these constraints, managing the multithreading structure was at times challenging and certainly became a pain as the hours became later. In addition to these, we struggled with some TCP issues due to ports not being closed properly near the beginning of the development (with them continuing to be open hours later and messing up opening new ports).

## Accomplishments

It works and its free and there's not limits or constraints! 

## What We Learned

1. Multiprocessing has to be handled well to prevent cpu and network scaling issues.
2. First designs are not always best and sometimes its good to redo work that isn't great.

## Next Steps
The interface still needs some polishing to say the least. In addition there are a few minor create comforts such as readable function codes, auto-updating read tables, and csv upload of write data that will be nice additions and help to make the utility truly uncontested in its niche.# ModbusUtils
