from hl7apy.parser import parse_message
from datetime import datetime

def age_calculator(dob):
    '''
    Calculate age based on the date of birth
    '''
    dob_date = datetime.strptime(dob, "%Y%m%d")  # Convert to datetime
    today = datetime.today()
    age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
    return age

def mssg_parser(mssg):
    '''
    Parse incoming hl7 message 

    Args-
    mssg: byte format of hl7 message

    Return-
    (str(message_type), List[data])

    data changes according to the message type
    '''
    hl7_str = mssg.decode("utf-8", errors="replace")
    mssg = parse_message(hl7_str, find_groups=False)
    mssg_type = mssg.MSH.MSH_9.value

    # Patient Admission
    if mssg_type == "ADT^A01":
        pid = mssg.PID

        patient_id = pid.PID_3.value # Patient ID
        sex = pid.PID_8.value        # Patient sex
        dob = pid.PID_7.value        # Patient date of birth
        age = age_calculator(dob)

        return "ADT^A01", [patient_id, age, sex]
        
    # Recieve Blood test
    elif mssg_type == "ORU^R01":
        pid = mssg.PID  # Get PID segment
        obr = mssg.OBR  # Get OBR segment
        obx = mssg.OBX  # Get OBX segment

        patient_id = pid.PID_3.value  # Patient ID
        crt_result = obx.OBX_5.value  # Creatinine Test Result
        test_date = obr.OBR_7.value  # Test Date/Time

        return "ORU^R01", [patient_id, float(crt_result), test_date]

    # Patient discharge
    elif mssg_type == "ADT^A03":
        return "ADT^A03", []

    # Acknowledge
    elif mssg_type == "ACK":
        return "ACK", []

    