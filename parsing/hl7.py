from hl7apy.parser import parse_message
from datetime import datetime

def age_calculator(dob):
    dob_date = datetime.strptime(dob, "%Y%m%d")  # Convert to datetime
    today = datetime.today()
    age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
    return age

def mssg_parser(mssg):
    hl7_str = mssg.decode("utf-8", errors="replace")
    mssg = parse_message(hl7_str, find_groups=False)
    mssg_type = mssg.MSH.MSH_9.value

    if mssg_type == "ADT^A01":
        pid = mssg.PID
        patient_id = pid.PID_3.value
        sex = pid.PID_8.value
        dob = pid.PID_7.value
        age = age_calculator(dob)

        return "ADT^A01", [patient_id, age, sex]
        

    elif mssg_type == "ORU^R01":
        pid = mssg.PID
        obr = mssg.OBR  # Get OBR segment
        obx = mssg.OBX  # Get OBX segment

        patient_id = pid.PID_3.value  # Patient ID
        crt_result = obx.OBX_5.value  # Creatinine Test Result
        test_date = obr.OBR_7.value  # Test Date/Time (Specimen Collection Date/Time)

        return "ORU^R01", [patient_id, float(crt_result), test_date]


    elif mssg_type == "ADT^A03":
        return "ADT^A03", []

    elif mssg_type == "ACK":
        return "ACK", []

    