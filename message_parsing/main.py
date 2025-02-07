from database_functionality.db_operations import handle_adt_a01
from database_functionality.db_operations import handle_oru_a01
from database_functionality.db_operations import update_feature_store
from ml.feature_construct import update
from ml.main import ml_consumer
from parsing.hl7 import mssg_parser

def message_consumer(msg):
    '''
    Handles the incoming messages individually
    -> completes message parsing
    -> Connects to DB to extract patient record
    -> Completes feature construction and sends the record for ML inference
    -> Updates the DB 

    Arg-
    msg: byte format of hl7 message
    '''
    # hl7 message parsing
    mssg_type, data = mssg_parser(msg) 

    # Fetch data from DB 
    if mssg_type=='ADT^A01':
        old_feat = handle_adt_a01(data)
    elif mssg_type=='ORU^R01':
        old_feat = handle_oru_a01(data)
    else:
        old_feat = None

    # feture construction
    if old_feat is not None and mssg_type=='ORU^R01':
        new_feature = update(old_feat, data, mssg_type)  #updates the old feature with incoming data

        # Send to ML Queue when ready for inference
        if new_feature['Ready_for_Inference'] == 'Yes':

            ml_consumer(new_feature)
            new_feature['Ready_for_Inference'] = 'No'
            
        # Update the DB with the new feature
        update_feature_store(new_feature['PID'], new_feature)
