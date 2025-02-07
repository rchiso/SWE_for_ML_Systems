from ml.inference import predict_aki
from ml.pager import send_pager_request


def ml_consumer(data):
    print(f"[ml_consumer] Received message: data={data}")

    # TODO: send to ml for inference
    aki_result, mrn, timestamp = predict_aki(data)
    if aki_result == None:
        print("[ml_consumer] Prediction Error")
        return
    if aki_result[0] == 1:
        try:
            pager_status = send_pager_request(mrn, timestamp)
            
            if pager_status == None or pager_status % 100 == 5:
                # Network Error or Pager returned 5xx => let's retry once, else DLQ
                print("[ml_consumer] Pager error")
            elif pager_status == 200:
                # Success => ACK
                print("[ml_consumer] Pager success, ACKing message.")

        except Exception as e:
            # Python error => direct to DLQ
            print(f"[ml_consumer] ERROR: {e}")
    else:
        #TODO: Add logging for when AKI is not detected
        print("[ml_consumer] AKI not detected")
