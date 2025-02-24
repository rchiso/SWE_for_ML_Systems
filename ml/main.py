import time
from ml.inference import predict_aki
from ml.pager import send_pager_request
from monitoring.metrics import PREDICTIONS_MADE, PAGER_REQUESTS, SYSTEM_HEALTH, record_error


RESEND_DELAY = 2

def ml_consumer(data, resend_flag = False):
    '''
    Function to recieve data after feature reconstruction 
    -> Predict using ML model 
    -> Send the result to pager
    '''
    try:
        SYSTEM_HEALTH.labels(component="ml_inference").set(1)
        # print(f"[ml_consumer] Received message: data={data}")

        # send to ml for inference
        aki_result, mrn, timestamp = predict_aki(data)
        if aki_result == None:
            print("[ml_consumer] Prediction Error")
            return

        # Track prediction results
        PREDICTIONS_MADE.labels(
            result="positive" if aki_result[0] == 1 else "negative"
        ).inc()

        if aki_result[0] == 1:
            pager_status = send_pager_request(mrn, timestamp)

            if pager_status == None or pager_status % 100 == 5:
                PAGER_REQUESTS.labels(status="error").inc()
                # Network Error or Pager returned 5xx
                if not resend_flag:
                    print(f"[ml_consumer] Pager error, retrying in {RESEND_DELAY} seconds")
                    time.sleep(RESEND_DELAY)
                    ml_consumer(data, True)
                else:
                    print(f"[ml_consumer] Pager error on second retry")


            elif pager_status == 200:
                PAGER_REQUESTS.labels(status="success").inc()
                # Success => ACK
                print("[ml_consumer] Pager success, ACKing message.")
        else:
            # Add logging for when AKI is not detected
            print("[ml_consumer] AKI not detected")
    except Exception as e:
        record_error(error_type=str(e.__class__.__name__), component="ml_inference")
        print(f"[ml_consumer] ERROR: {e}")
