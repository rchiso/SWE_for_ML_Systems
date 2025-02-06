
def update(feature, data, mssg_type):
    # First time patient
    #PID, Sex, Age, Min, Max, Mean, Standard_Deviation,
    #                                   Last_Result_Value, Latest_Result_Timestamp, No_of_Samples, Ready_for_Inference
    # data: [patient_id, float(crt_result), test_date]

    # First time patient 
    if mssg_type=='ORU^R01' and feature['Mean'] == None:
        feature['Min'] = data[1]
        feature['Max'] = data[1]
        feature['Mean'] = data[1]
        feature['Standard_Deviation'] = 0
        feature['Last_Result_Value'] = data[1]
        feature['Latest_Result_Timestamp'] = data[2]
        feature['No_of_Samples'] += 1

    
    elif mssg_type=='ORU^R01' and feature['Mean']!=None:
        n = feature['No_of_Samples']
        feature['Min'] = min(data[1], feature['Min'])
        feature['Max'] = max(data[1], feature['Max'])
        feature['Mean'] = (n*feature['Mean'] + data[1])/(n+1)
        feature['Standard_Deviation'] = ( (n/(n+1))*(feature['Standard_Deviation']**2) + ((data[1]-feature['Mean'])**2)/n  )**0.5
        feature['Last_Result_Value'] = data[1]
        feature['Latest_Result_Timestamp'] = data[2]
        feature['No_of_Samples'] += 1

    # Check for inference
    if all(value is not None for value in feature.values()):
        feature['Ready_for_Inference'] ='Yes'

    return feature
