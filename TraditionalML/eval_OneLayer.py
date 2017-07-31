'''
Reads a pcap and updates the stored representation of the source using
the one layer feedforward model.
'''

import sys
import numpy as np
from OneLayer import OneLayerModel

def update_representation(source_ip, representations, timestamps):
    '''
    Updates the stored representaion with the new information

    Args:
        source_ip: Address of the representaion to update
        representations: New observations of representations
        timestamps: Time at which each representation was observed
    '''

    # Set the information decay rate to 1 day
    time_const = 60*60*24

    # TODO: Read the old representation from storage. The key should be
    # The IP address string source_ip and the value should contain the 
    # Timestamp of the last update and the previous representation vector
    representation = None

    if representation is None:
        prev_time = None
        representation = np.zeros(representations.shape[1])

    for i, rep in enumerate(representations):
        time = timestamps[i].timestamp()
        if prev_time is None:
            representation = rep
            prev_time = time
        elif time > prev_time:
            time_diff = time - prev_time
            alpha = 1 - np.exp(-time_diff/time_const)
            print(alpha)
            representation += alpha*(rep - representation)
            prev_time = time

    # TODO: instead of printing, save this info 
    print('IP address', source_ip,
          '\nLast update', time,
          '\nRepresentation:', representation)

if __name__ == '__main__':
    # path to the pcap to get the update from
    pcap_path = sys.argv[1]
    # Initialize and load the model
    load_path = sys.argv[2]
    model = OneLayerModel(duration=None, hidden_size=None)
    model.load(load_path)
    # Get representations from the model
    reps, source_ip, timestamps = model.get_representation(
                                                            pcap_path,
                                                            mean=False
                                                          )
    # Update the stored representation
    update_representation(source_ip, reps, timestamps)
