#!/usr/bin/env python3
"""
Polyglot v3 node server Example 3
Copyright (C) 2021 Robert Paauwe

MIT License
"""
import udi_interface
import sys
import requests

LOGGER = udi_interface.LOGGER
Custom = udi_interface.Custom
# response = requests.get(http://192.168.0.2) #/rest/53 46 70 F
# LOGGER.info(f'Response from 192.168.0.2 {response}')

'''
This is our Counter device node.  All it does is update the count at the
poll interval.
'''
class CounterNode(udi_interface.Node):
    id = 'child'
    
    drivers = [
            {'driver': 'ST', 'value': 1, 'uom': 2},
            {'driver': 'GV0', 'value': 0, 'uom': 56},
            {'driver': 'GV1', 'value': 0, 'uom': 56},
            {'driver': 'GV2', 'value': 0, 'uom': 2},
            {'driver': 'GV3', 'value': 0, 'uom': 51}
            ]

    def __init__(self, polyglot, parent, address, name):
        super(CounterNode, self).__init__(polyglot, parent, address, name)

        self.poly = polyglot
        self.count = 0
        self.cool = 1
        self.fan = 0
        self.CustomData = Custom(polyglot, 'customdata')
        self.Parameters = Custom(polyglot, 'customparams')

        # subscribe to the events we want
        polyglot.subscribe(polyglot.CUSTOMPARAMS, self.parameterHandler)
        polyglot.subscribe(polyglot.POLL, self.poll)

    '''
    Read the user entered custom parameters. In this case, it is just
    the 'multiplier' value that we want.  
    '''
    def parameterHandler(self, params):
        self.Parameters.load(params)


    '''
    This is where the real work happens.  When we get a shortPoll, increment the
    count, report the current count in GV0 and the current count multiplied by
    the user defined value in GV1. Then display a notice on the dashboard.
    '''
    def poll(self, polltype):

        if 'shortPoll' in polltype:
            if self.Parameters['multiplier'] is not None:
                mult = int(self.Parameters['multiplier'])
            else:
                mult = 1

            self.count += 1

            # COUNTERS
            self.setDriver('GV0', self.count, True, True)
            self.setDriver('GV1', (self.count * mult), True, True)
            LOGGER.info('GV0 and GV1 has been set')

            # DONOVAN IS COOL 
            if self.cool is 1:
                self.cool = 0
            else:
                self.cool = 1
            LOGGER.info(f'Coolness has been set to {self.cool}')
            self.setDriver('GV2', self.cool, True, True)

            # FAN LEVEL 
            if self.fan <100:
                self.fan += 10
            else:
                self.fan = 0
            self.setDriver('GV3', self.fan, True, True)

            # be fancy and display a notice on the polyglot dashboard
            self.poly.Notices[self.name] = '{}: Current count is {}'.format(self.name, self.count)

    def turnOn(self, command):
        LOGGER.info(f'on command received on {self.name}')

    def turnOff(self, command):
        LOGGER.info(f'off command received on {self.name}')

    def query(self, command=None):
        isy = self.ISY.pyisy()
        if isy is not None:
            for name, node in isy.nodes:
                
                # check to make sure this is a device node, not group(scene)
                if re.match(r'^Group', type(node).__name__):
                    continue

                if node.family != None and node.family != "ZWave":
                    continue

                #LOGGER.info('*  {} {} {} {}   {} -- {}'.format(node.family, node.status, node.uom, node.type, type(node.uom), name))
                if node.status is not self.ISY.constants.ISY_VALUE_UNKNOWN:
                    #if node.uom == 100 or node.uom == 51:
                    if node.uom == "100" or node.uom == "51":
                        category = node.type.split('.')[0]
                        if node.family == None and (category == '1' or category == '2'):
                            # insteon categories 1 and 2
                            LOGGER.debug('   Found node {} with type {} category {} and status {}'.format(node.name, node.type, category, node.status))
                            entry = {
                                        'name': node.name, 
                                        'value': node.status 
                                    }
                            self.CustomData[node.address] = entry
                
                LOGGER.info(f'CustomData has finished {self.CustomData}')

    
    commands = {'DON': turnOn, 'DOF': turnOff, 'Query': query}

    